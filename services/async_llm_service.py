# Servicio asíncrono para llamadas LLM
# Previene bloqueo de threads principales con operaciones LLM costosas

import asyncio
import concurrent.futures
import time
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import queue
import threading
from datetime import datetime

from services.performance_service import performance_monitor, get_performance_optimizer
from services.llm_service import LLMService
from utils.logger import get_logger

logger = get_logger(__name__)

class AsyncLLMService:
    """
    Servicio asíncrono para llamadas LLM que previene bloqueo
    Implementa patterns de circuit breaker y fallback para alta disponibilidad
    """
    
    def __init__(self, llm_service: LLMService, max_concurrent_requests: int = 3):
        """
        Inicializar servicio LLM asíncrono
        
        Args:
            llm_service: Instancia del servicio LLM sincrónico
            max_concurrent_requests: Máximo número de requests concurrentes a OpenAI
        """
        self.llm_service = llm_service
        self.max_concurrent_requests = max_concurrent_requests
        self.performance_optimizer = get_performance_optimizer()
        
        # Semáforo para controlar concurrencia
        self.semaphore = threading.Semaphore(max_concurrent_requests)
        
        # Cola de requests con prioridad
        self.request_queue = queue.PriorityQueue()
        
        # Circuit breaker para manejar fallos de OpenAI
        self.circuit_breaker = {
            "failures": 0,
            "last_failure_time": None,
            "failure_threshold": 5,  # Fallos antes de abrir circuito
            "recovery_timeout": 60,  # Segundos antes de reintentar
            "state": "closed"  # closed, open, half-open
        }
        
        # Métricas específicas de LLM
        self.llm_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "openai_quota_errors": 0,
            "timeout_errors": 0,
            "cache_hits": 0
        }
        
        # Worker thread para procesar requests
        self.worker_thread = None
        self.shutdown_event = threading.Event()
        
        logger.info("AsyncLLMService inicializado",
                   extra={"max_concurrent": max_concurrent_requests})

    def _check_circuit_breaker(self) -> bool:
        """
        Verificar estado del circuit breaker
        
        Returns:
            bool: True si el circuito está cerrado (operacional)
        """
        current_time = time.time()
        
        # Si el circuito está abierto, verificar si es tiempo de recuperación
        if self.circuit_breaker["state"] == "open":
            if (current_time - self.circuit_breaker["last_failure_time"]) > self.circuit_breaker["recovery_timeout"]:
                self.circuit_breaker["state"] = "half-open"
                logger.info("Circuit breaker cambiado a half-open - intentando recuperación")
                return True
            return False
        
        return True  # closed o half-open

    def _update_circuit_breaker(self, success: bool):
        """
        Actualizar estado del circuit breaker basado en resultado
        
        Args:
            success: Si la operación fue exitosa
        """
        current_time = time.time()
        
        if success:
            if self.circuit_breaker["state"] == "half-open":
                # Recuperación exitosa
                self.circuit_breaker["state"] = "closed"
                self.circuit_breaker["failures"] = 0
                logger.info("Circuit breaker recuperado - estado: closed")
            elif self.circuit_breaker["state"] == "closed":
                # Reset contador si hay éxito en estado normal
                self.circuit_breaker["failures"] = max(0, self.circuit_breaker["failures"] - 1)
        else:
            self.circuit_breaker["failures"] += 1
            self.circuit_breaker["last_failure_time"] = current_time
            
            if self.circuit_breaker["failures"] >= self.circuit_breaker["failure_threshold"]:
                self.circuit_breaker["state"] = "open"
                logger.warning(f"Circuit breaker ABIERTO - {self.circuit_breaker['failures']} fallos consecutivos")

    @performance_monitor
    def process_message_async(self, mensaje: str, user_id: str, context: Dict[str, Any] = None, 
                             priority: int = 1, timeout: float = 25.0) -> Dict[str, Any]:
        """
        Procesar mensaje de forma asíncrona con cache y fallbacks
        
        Args:
            mensaje: Mensaje del usuario
            user_id: ID del usuario
            context: Contexto adicional
            priority: Prioridad del request (1=alta, 5=baja)
            timeout: Timeout para la operación
            
        Returns:
            Dict con respuesta y metadata
        """
        start_time = time.time()
        
        try:
            # Verificar circuit breaker
            if not self._check_circuit_breaker():
                logger.warning("Circuit breaker abierto - usando respuesta de fallback")
                return self._get_fallback_response(mensaje, "circuit_breaker_open")
            
            # Generar cache key
            cache_key = self.performance_optimizer.generate_cache_key(mensaje, 
                                                                     context=str(context) if context else "",
                                                                     user_id=user_id)
            
            # Verificar cache primero
            cached_response = self.performance_optimizer.get_cached_response(cache_key)
            if cached_response:
                self.llm_metrics["cache_hits"] += 1
                logger.info(f"Respuesta LLM servida desde cache para {user_id}")
                return {
                    "response": cached_response,
                    "source": "cache",
                    "processing_time": time.time() - start_time,
                    "cached": True
                }
            
            # Procesar con thread pool para no bloquear
            future = self.performance_optimizer.run_in_thread(
                self._process_llm_request_safe,
                mensaje, user_id, context, timeout
            )
            
            # Esperar resultado con timeout
            try:
                result = future.result(timeout=timeout)
                
                # Cachear si es apropiado
                if (result.get("success") and 
                    result.get("response") and 
                    self.performance_optimizer.should_cache_response(result["response"], mensaje)):
                    
                    self.performance_optimizer.cache_response(
                        cache_key, 
                        result["response"], 
                        ttl=300,  # 5 minutos para respuestas LLM
                        metadata={"user_id": user_id, "message_length": len(mensaje)}
                    )
                
                # Actualizar métricas
                processing_time = time.time() - start_time
                self._update_llm_metrics(success=result.get("success", False), 
                                       processing_time=processing_time,
                                       error_type=result.get("error_type"))
                
                return result
                
            except concurrent.futures.TimeoutError:
                logger.warning(f"Timeout en procesamiento LLM para {user_id} después de {timeout}s")
                self.llm_metrics["timeout_errors"] += 1
                return self._get_fallback_response(mensaje, "timeout")
                
        except Exception as e:
            logger.error(f"Error en process_message_async: {e}")
            processing_time = time.time() - start_time
            self._update_llm_metrics(success=False, processing_time=processing_time, 
                                   error_type="async_processing_error")
            return self._get_fallback_response(mensaje, "processing_error")

    def _process_llm_request_safe(self, mensaje: str, user_id: str, 
                                 context: Dict[str, Any] = None, timeout: float = 25.0) -> Dict[str, Any]:
        """
        Procesar request LLM de forma segura con manejo de errores
        
        Args:
            mensaje: Mensaje del usuario
            user_id: ID del usuario  
            context: Contexto adicional
            timeout: Timeout para la operación
            
        Returns:
            Dict con resultado y metadata
        """
        start_time = time.time()
        
        try:
            # Adquirir semáforo para controlar concurrencia
            with self.semaphore:
                logger.debug(f"Procesando request LLM para {user_id}")
                
                # Procesar con el servicio LLM original
                if hasattr(self.llm_service, 'process_message'):
                    response = self.llm_service.process_message(mensaje, user_id, context)
                elif hasattr(self.llm_service, 'generate_response'):
                    response = self.llm_service.generate_response(mensaje, context)
                else:
                    # Fallback genérico
                    response = self._call_llm_fallback(mensaje, context)
                
                processing_time = time.time() - start_time
                
                # Actualizar circuit breaker con éxito
                self._update_circuit_breaker(success=True)
                
                return {
                    "response": response,
                    "source": "llm",
                    "processing_time": processing_time,
                    "success": True,
                    "cached": False
                }
                
        except Exception as e:
            error_str = str(e).lower()
            processing_time = time.time() - start_time
            
            # Clasificar tipo de error
            error_type = "unknown_error"
            if "quota" in error_str or "rate" in error_str or "429" in error_str:
                error_type = "quota_exceeded"
                self.llm_metrics["openai_quota_errors"] += 1
            elif "timeout" in error_str or "connection" in error_str:
                error_type = "connection_error"
            elif "invalid" in error_str or "api" in error_str:
                error_type = "api_error"
            
            # Actualizar circuit breaker con fallo
            self._update_circuit_breaker(success=False)
            
            logger.error(f"Error en LLM request para {user_id}: {e}",
                        extra={"user_id": user_id, "error_type": error_type, "processing_time": processing_time})
            
            return {
                "response": None,
                "source": "error",
                "processing_time": processing_time,
                "success": False,
                "error": str(e),
                "error_type": error_type,
                "cached": False
            }

    def _call_llm_fallback(self, mensaje: str, context: Dict[str, Any] = None) -> str:
        """
        Fallback para llamar LLM cuando el servicio no tiene métodos estándar
        
        Args:
            mensaje: Mensaje del usuario
            context: Contexto adicional
            
        Returns:
            str: Respuesta del LLM
        """
        try:
            # Intentar diferentes métodos comunes del LLM service
            if hasattr(self.llm_service, 'chat_completion'):
                return self.llm_service.chat_completion(mensaje)
            elif hasattr(self.llm_service, 'get_response'):
                return self.llm_service.get_response(mensaje)
            elif hasattr(self.llm_service, '__call__'):
                return self.llm_service(mensaje)
            else:
                raise AttributeError("No se encontró método válido en LLMService")
                
        except Exception as e:
            logger.error(f"Error en LLM fallback: {e}")
            raise

    def _get_fallback_response(self, mensaje: str, reason: str) -> Dict[str, Any]:
        """
        Generar respuesta de fallback cuando LLM no está disponible
        
        Args:
            mensaje: Mensaje original del usuario
            reason: Razón del fallback
            
        Returns:
            Dict con respuesta de fallback
        """
        fallback_responses = {
            "circuit_breaker_open": "Lo siento, estamos experimentando dificultades técnicas temporales. Por favor intenta de nuevo en unos minutos o contacta directamente a nuestro WhatsApp.",
            
            "timeout": "Tu consulta está siendo procesada. Por favor espera un momento o reformula tu pregunta de manera más específica.",
            
            "quota_exceeded": "Estamos experimentando alta demanda. Por favor intenta de nuevo en unos minutos o contacta directamente para asistencia inmediata.",
            
            "processing_error": "Ocurrió un error procesando tu consulta. Por favor intenta reformular tu pregunta o contacta a nuestro equipo de soporte.",
            
            "connection_error": "Problemas de conectividad temporales. Por favor intenta de nuevo en unos momentos."
        }
        
        # Intentar dar respuesta contextual básica
        mensaje_lower = mensaje.lower()
        if any(word in mensaje_lower for word in ['precio', 'costo', 'tarifa']):
            contextual_response = "Para información sobre precios, puedes contactarnos directamente al WhatsApp +57 XXX XXX XXXX o consultar nuestra página web."
        elif any(word in mensaje_lower for word in ['disponibilidad', 'reserva', 'fecha']):
            contextual_response = "Para verificar disponibilidad y hacer reservas, contacta directamente a nuestro equipo al WhatsApp +57 XXX XXX XXXX."
        elif any(word in mensaje_lower for word in ['ubicación', 'dirección', 'llegar']):
            contextual_response = "Estamos ubicados en [ubicación del glamping]. Puedes contactarnos para direcciones detalladas."
        else:
            contextual_response = fallback_responses.get(reason, fallback_responses["processing_error"])
        
        return {
            "response": contextual_response,
            "source": "fallback",
            "reason": reason,
            "processing_time": 0,
            "success": False,
            "cached": False
        }

    def _update_llm_metrics(self, success: bool, processing_time: float, error_type: str = None):
        """
        Actualizar métricas específicas de LLM
        
        Args:
            success: Si la operación fue exitosa
            processing_time: Tiempo de procesamiento
            error_type: Tipo de error si falló
        """
        try:
            self.llm_metrics["total_requests"] += 1
            
            if success:
                self.llm_metrics["successful_requests"] += 1
            else:
                self.llm_metrics["failed_requests"] += 1
            
            # Actualizar promedio de tiempo de respuesta
            total_requests = self.llm_metrics["total_requests"]
            current_avg = self.llm_metrics["average_response_time"]
            new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
            self.llm_metrics["average_response_time"] = new_avg
            
            logger.debug(f"Métricas LLM actualizadas - Total: {total_requests}, Exitosos: {self.llm_metrics['successful_requests']}, Avg Time: {new_avg:.2f}s")
            
        except Exception as e:
            logger.error(f"Error actualizando métricas LLM: {e}")

    def batch_process_messages(self, messages: List[Dict[str, Any]], timeout: float = 30.0) -> List[Dict[str, Any]]:
        """
        Procesar múltiples mensajes en lote de forma asíncrona
        
        Args:
            messages: Lista de diccionarios con 'mensaje', 'user_id', 'context'
            timeout: Timeout total para el lote
            
        Returns:
            Lista de respuestas
        """
        try:
            logger.info(f"Procesando lote de {len(messages)} mensajes")
            
            # Crear tareas para cada mensaje
            tasks = []
            for msg_data in messages:
                task = {
                    'func': self.process_message_async,
                    'args': (msg_data['mensaje'], msg_data['user_id']),
                    'kwargs': {'context': msg_data.get('context'), 'timeout': timeout / len(messages)}
                }
                tasks.append(task)
            
            # Ejecutar en paralelo
            results = self.performance_optimizer.run_multiple_in_threads(tasks, timeout=timeout)
            
            logger.info(f"Lote procesado - {len([r for r in results if r and r.get('success')])} exitosos de {len(messages)}")
            return results
            
        except Exception as e:
            logger.error(f"Error en batch_process_messages: {e}")
            return [self._get_fallback_response(msg['mensaje'], 'batch_processing_error') for msg in messages]

    def get_llm_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del servicio LLM asíncrono
        
        Returns:
            Dict con estadísticas completas
        """
        try:
            # Estadísticas básicas
            total_requests = self.llm_metrics["total_requests"]
            success_rate = (self.llm_metrics["successful_requests"] / total_requests * 100) if total_requests > 0 else 0
            
            stats = {
                "llm_metrics": self.llm_metrics.copy(),
                "success_rate": success_rate,
                "circuit_breaker": self.circuit_breaker.copy(),
                "performance_stats": self.performance_optimizer.get_performance_stats(),
                "concurrent_limit": self.max_concurrent_requests,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas LLM: {e}")
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """
        Health check del servicio LLM asíncrono
        
        Returns:
            Dict con estado de salud
        """
        try:
            # Test básico del circuit breaker
            circuit_ok = self.circuit_breaker["state"] in ["closed", "half-open"]
            
            # Verificar métricas recientes
            total_requests = self.llm_metrics["total_requests"]
            recent_success_rate = 100.0
            
            if total_requests > 0:
                recent_success_rate = (self.llm_metrics["successful_requests"] / total_requests) * 100
            
            # Determinar estado general
            if circuit_ok and recent_success_rate > 80:
                health_status = "healthy"
            elif circuit_ok and recent_success_rate > 50:
                health_status = "degraded"
            else:
                health_status = "unhealthy"
            
            return {
                "status": health_status,
                "circuit_breaker_state": self.circuit_breaker["state"],
                "success_rate": recent_success_rate,
                "average_response_time": self.llm_metrics["average_response_time"],
                "total_requests": total_requests,
                "cache_hit_rate": self.performance_optimizer.get_performance_stats().get("cache_stats", {}).get("hit_rate", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Factory function para crear instancia
def create_async_llm_service(llm_service: LLMService, max_concurrent: int = 3) -> AsyncLLMService:
    """
    Factory para crear servicio LLM asíncrono
    
    Args:
        llm_service: Servicio LLM sincrónico base
        max_concurrent: Máximo requests concurrentes
        
    Returns:
        AsyncLLMService configurado
    """
    return AsyncLLMService(llm_service, max_concurrent)

# Instancia global (opcional)
_global_async_llm_service = None

def get_global_async_llm_service() -> Optional[AsyncLLMService]:
    """Obtener instancia global del servicio LLM asíncrono"""
    return _global_async_llm_service

def set_global_async_llm_service(service: AsyncLLMService):
    """Configurar instancia global del servicio LLM asíncrono"""
    global _global_async_llm_service
    _global_async_llm_service = service