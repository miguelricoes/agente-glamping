# Servicio de optimización de rendimiento
# Maneja concurrencia, cache de respuestas y monitoreo de performance

import asyncio
import time
import threading
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceOptimizer:
    """
    Servicio de optimización de rendimiento para mejorar concurrencia
    Implementa cache inteligente, threading y monitoreo de performance
    """

    def __init__(self, max_workers: int = 4, cache_ttl: int = 300):
        """
        Inicializar optimizador de rendimiento
        
        Args:
            max_workers: Número máximo de threads para operaciones concurrentes
            cache_ttl: Tiempo de vida del cache en segundos (default 5 minutos)
        """
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        
        # Thread pool para operaciones asíncronas
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="perf_worker")
        
        # Cache inteligente con TTL
        self.response_cache = {}
        self.cache_access_count = {}
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
        # Cache específico para respuestas de IA
        self.ai_response_cache = {}
        
        # Métricas de rendimiento
        self.performance_metrics = {
            "total_requests": 0,
            "average_response_time": 0,
            "slow_requests_count": 0,
            "cache_hit_rate": 0
        }
        
        # Lock para thread safety
        self._cache_lock = threading.RLock()
        self._metrics_lock = threading.RLock()
        
        logger.info("PerformanceOptimizer inicializado", 
                   extra={"max_workers": max_workers, "cache_ttl": cache_ttl})

    def cache_response(self, cache_key: str, response: str, ttl: int = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Cache de respuestas con TTL y metadata
        
        Args:
            cache_key: Clave única para el cache
            response: Respuesta a cachear
            ttl: Tiempo de vida personalizado (opcional)
            metadata: Metadata adicional (usuario, tipo de consulta, etc.)
            
        Returns:
            bool: True si se cacheó exitosamente
        """
        try:
            ttl = ttl or self.cache_ttl
            timestamp = time.time()
            
            with self._cache_lock:
                cache_entry = {
                    'response': response,
                    'timestamp': timestamp,
                    'ttl': ttl,
                    'access_count': 0,
                    'metadata': metadata or {}
                }
                
                self.response_cache[cache_key] = cache_entry
                self.cache_access_count[cache_key] = 0
                
            logger.debug(f"Respuesta cacheada: {cache_key[:16]}... (TTL: {ttl}s)",
                        extra={"cache_key_preview": cache_key[:16], "ttl": ttl})
            
            return True
            
        except Exception as e:
            logger.error(f"Error cacheando respuesta: {e}")
            return False

    def get_cached_response(self, cache_key: str) -> Optional[str]:
        """
        Obtener respuesta cacheada si es válida
        
        Args:
            cache_key: Clave del cache
            
        Returns:
            Optional[str]: Respuesta cacheada o None si no existe/expiró
        """
        try:
            with self._cache_lock:
                if cache_key not in self.response_cache:
                    self.cache_miss_count += 1
                    return None

                cached_entry = self.response_cache[cache_key]
                age = time.time() - cached_entry['timestamp']

                # Verificar si el cache expiró
                if age > cached_entry['ttl']:
                    del self.response_cache[cache_key]
                    if cache_key in self.cache_access_count:
                        del self.cache_access_count[cache_key]
                    self.cache_miss_count += 1
                    return None

                # Incrementar contador de acceso y hits
                cached_entry['access_count'] += 1
                self.cache_access_count[cache_key] += 1
                self.cache_hit_count += 1
                
                logger.debug(f"Cache hit: {cache_key[:16]}... (edad: {age:.1f}s, accesos: {cached_entry['access_count']})",
                           extra={"cache_key_preview": cache_key[:16], "age": age, "access_count": cached_entry['access_count']})

                return cached_entry['response']
                
        except Exception as e:
            logger.error(f"Error obteniendo respuesta cacheada: {e}")
            self.cache_miss_count += 1
            return None

    def generate_cache_key(self, user_input: str, context: str = "", user_id: str = "") -> str:
        """
        Generar clave de cache inteligente para consulta
        
        Args:
            user_input: Mensaje del usuario
            context: Contexto adicional
            user_id: ID del usuario (para cache personalizado)
            
        Returns:
            str: Clave de cache MD5
        """
        try:
            # Normalizar entrada para mejores hits de cache
            normalized_input = self._normalize_text_for_cache(user_input)
            
            # Crear contenido de clave
            if user_id and self._is_personalized_query(user_input):
                # Cache personalizado por usuario para consultas específicas
                content = f"user:{user_id}:{normalized_input}:{context}"
            else:
                # Cache global para consultas genéricas
                content = f"global:{normalized_input}:{context}"
            
            # Generar hash
            cache_key = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            logger.debug(f"Cache key generada: {cache_key[:16]}... para input: '{user_input[:30]}...'",
                        extra={"cache_key_preview": cache_key[:16], "input_preview": user_input[:30]})
            
            return cache_key
            
        except Exception as e:
            logger.error(f"Error generando cache key: {e}")
            # Fallback: generar clave simple
            return hashlib.md5(f"{user_input}:{int(time.time() / 60)}".encode()).hexdigest()

    def _normalize_text_for_cache(self, text: str) -> str:
        """Normalizar texto para mejorar hits de cache"""
        try:
            # Convertir a minúsculas y limpiar espacios
            normalized = text.lower().strip()
            
            # Remover signos de puntuación comunes que no afectan el significado
            import re
            normalized = re.sub(r'[¿?¡!.,;:]', '', normalized)
            
            # Normalizar espacios múltiples
            normalized = re.sub(r'\s+', ' ', normalized)
            
            # Remover palabras de relleno comunes en español
            filler_words = ['por favor', 'gracias', 'hola', 'buenos días', 'buenas tardes', 'buenas noches']
            for filler in filler_words:
                normalized = normalized.replace(filler, '').strip()
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizando texto: {e}")
            return text.lower().strip()

    def _is_personalized_query(self, query: str) -> bool:
        """Determinar si una consulta requiere cache personalizado"""
        personalized_patterns = [
            'reserva', 'mi reserva', 'disponibilidad', 'precio', 'fecha',
            'confirmar', 'cancelar', 'modificar', 'mi solicitud'
        ]
        
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in personalized_patterns)

    def should_cache_response(self, response: str, user_input: str = "") -> bool:
        """
        Determinar si una respuesta debe ser cacheada
        
        Args:
            response: Respuesta a evaluar
            user_input: Input del usuario (para contexto)
            
        Returns:
            bool: True si debe ser cacheada
        """
        try:
            # No cachear respuestas vacías o muy cortas
            if not response or len(response.strip()) < 10:
                return False
            
            # No cachear respuestas personalizadas o con estado
            no_cache_patterns = [
                'tu reserva', 'tu solicitud', 'nombre', 'teléfono',
                'disponibilidad para el', 'precio para', 'fecha específica',
                'confirmar tu', 'tu número', 'gracias por'
            ]
            
            response_lower = response.lower()
            if any(pattern in response_lower for pattern in no_cache_patterns):
                logger.debug("Respuesta no cacheada por contener información personalizada")
                return False
            
            # Cachear respuestas informativas generales
            cacheable_patterns = [
                'información sobre', 'qué es', 'cómo funciona', 'preguntas frecuentes',
                'política', 'ubicación', 'servicios incluidos', 'actividades disponibles'
            ]
            
            if any(pattern in response_lower for pattern in cacheable_patterns):
                logger.debug("Respuesta marcada para cache por ser informativa")
                return True
            
            # Cachear si es una respuesta larga e informativa (probablemente de FAQ/info)
            if len(response) > 100 and not self._contains_dynamic_content(response):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error evaluando si cachear respuesta: {e}")
            return False

    def _contains_dynamic_content(self, response: str) -> bool:
        """Detectar si la respuesta contiene contenido dinámico"""
        dynamic_indicators = [
            datetime.now().strftime("%d"), datetime.now().strftime("%m"),
            "hoy", "mañana", "fecha actual", "precio actual", "disponible ahora"
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in dynamic_indicators)

    def run_in_thread(self, func: Callable, *args, **kwargs):
        """
        Ejecutar función en thread pool
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Future object
        """
        try:
            future = self.thread_pool.submit(func, *args, **kwargs)
            logger.debug(f"Función {func.__name__} enviada al thread pool")
            return future
            
        except Exception as e:
            logger.error(f"Error enviando función al thread pool: {e}")
            # Fallback: ejecutar sincrónicamente
            return func(*args, **kwargs)

    def run_multiple_in_threads(self, tasks: List[Dict[str, Any]], timeout: float = 30.0) -> List[Any]:
        """
        Ejecutar múltiples tareas en paralelo
        
        Args:
            tasks: Lista de diccionarios {'func': callable, 'args': tuple, 'kwargs': dict}
            timeout: Timeout total para todas las tareas
            
        Returns:
            Lista de resultados
        """
        try:
            # Enviar todas las tareas
            futures = []
            for task in tasks:
                func = task['func']
                args = task.get('args', ())
                kwargs = task.get('kwargs', {})
                future = self.thread_pool.submit(func, *args, **kwargs)
                futures.append(future)
            
            # Recolectar resultados
            results = []
            for future in as_completed(futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error en tarea paralela: {e}")
                    results.append(None)
            
            logger.info(f"Ejecutadas {len(tasks)} tareas en paralelo, {len([r for r in results if r is not None])} exitosas")
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando tareas en paralelo: {e}")
            return []

    def update_performance_metrics(self, response_time: float, was_cached: bool = False):
        """
        Actualizar métricas de rendimiento
        
        Args:
            response_time: Tiempo de respuesta en segundos
            was_cached: Si la respuesta fue servida desde cache
        """
        try:
            with self._metrics_lock:
                self.performance_metrics["total_requests"] += 1
                
                # Actualizar promedio de tiempo de respuesta
                current_avg = self.performance_metrics["average_response_time"]
                total_requests = self.performance_metrics["total_requests"]
                
                new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
                self.performance_metrics["average_response_time"] = new_avg
                
                # Contar requests lentos (>5 segundos = timeout de WhatsApp)
                if response_time > 5.0:
                    self.performance_metrics["slow_requests_count"] += 1
                
                # Calcular hit rate del cache
                total_cache_requests = self.cache_hit_count + self.cache_miss_count
                if total_cache_requests > 0:
                    self.performance_metrics["cache_hit_rate"] = (self.cache_hit_count / total_cache_requests) * 100
                
                logger.debug(f"Métricas actualizadas - Tiempo: {response_time:.2f}s, Cache: {'HIT' if was_cached else 'MISS'}",
                           extra={"response_time": response_time, "cached": was_cached})
                
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de rendimiento
        
        Returns:
            Dict con estadísticas actuales
        """
        try:
            with self._metrics_lock, self._cache_lock:
                current_time = time.time()
                
                # Limpiar cache expirado para estadísticas precisas
                expired_keys = []
                for key, entry in self.response_cache.items():
                    if current_time - entry['timestamp'] > entry['ttl']:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.response_cache[key]
                    if key in self.cache_access_count:
                        del self.cache_access_count[key]
                
                # Calcular estadísticas de cache
                total_cache_entries = len(self.response_cache)
                most_accessed = max(self.cache_access_count.items(), key=lambda x: x[1]) if self.cache_access_count else ("none", 0)
                
                stats = {
                    "performance_metrics": self.performance_metrics.copy(),
                    "cache_stats": {
                        "total_entries": total_cache_entries,
                        "cache_hits": self.cache_hit_count,
                        "cache_misses": self.cache_miss_count,
                        "hit_rate": self.performance_metrics["cache_hit_rate"],
                        "most_accessed_key": most_accessed[0][:16] + "..." if most_accessed[0] != "none" else "none",
                        "most_accessed_count": most_accessed[1]
                    },
                    "thread_pool_stats": {
                        "max_workers": self.max_workers,
                        "active_threads": len(self.thread_pool._threads) if hasattr(self.thread_pool, '_threads') else "unknown"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

    def cleanup_cache(self, force_cleanup: bool = False):
        """
        Limpiar entradas de cache expiradas
        
        Args:
            force_cleanup: Si forzar limpieza completa del cache
        """
        try:
            with self._cache_lock:
                current_time = time.time()
                expired_keys = []
                
                if force_cleanup:
                    expired_keys = list(self.response_cache.keys())
                    logger.info("Limpieza forzada del cache ejecutada")
                else:
                    # Solo limpiar entradas expiradas
                    for key, entry in self.response_cache.items():
                        if current_time - entry['timestamp'] > entry['ttl']:
                            expired_keys.append(key)
                
                # Remover entradas expiradas
                for key in expired_keys:
                    del self.response_cache[key]
                    if key in self.cache_access_count:
                        del self.cache_access_count[key]
                
                logger.info(f"Cache cleanup: {len(expired_keys)} entradas removidas")
                
        except Exception as e:
            logger.error(f"Error en cleanup de cache: {e}")

    def __del__(self):
        """Cleanup al destruir la instancia"""
        try:
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=True)
                logger.info("Thread pool cerrado correctamente")
        except Exception as e:
            logger.error(f"Error cerrando thread pool: {e}")

# Decoradores para monitoreo de rendimiento

def performance_monitor(func: Callable) -> Callable:
    """
    Decorator para monitorear rendimiento de funciones
    
    Args:
        func: Función a monitorear
        
    Returns:
        Función decorada con monitoreo
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log básico de rendimiento
            logger.info(f"Rendimiento {func.__name__}: {execution_time:.2f}s",
                       extra={
                           "function": func.__name__,
                           "execution_time": execution_time,
                           "module": func.__module__
                       })
            
            # Warning para funciones lentas (crítico para WhatsApp)
            if execution_time > 5.0:
                logger.warning(f"⚠️ FUNCIÓN LENTA detectada: {func.__name__} ({execution_time:.2f}s) - Risk of WhatsApp timeout",
                             extra={
                                 "function": func.__name__,
                                 "execution_time": execution_time,
                                 "risk_level": "high"
                             })
            elif execution_time > 3.0:
                logger.warning(f"Función lenta: {func.__name__} ({execution_time:.2f}s)",
                             extra={
                                 "function": func.__name__,
                                 "execution_time": execution_time,
                                 "risk_level": "medium"
                             })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error en {func.__name__} después de {execution_time:.2f}s: {e}",
                        extra={
                            "function": func.__name__,
                            "execution_time": execution_time,
                            "error": str(e)
                        })
            raise
        
    return wrapper

def async_cache(cache_ttl: int = 300, cache_key_func: Optional[Callable] = None):
    """
    Decorator para cache automático con soporte asíncrono
    
    Args:
        cache_ttl: Tiempo de vida del cache
        cache_key_func: Función personalizada para generar cache key
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener instancia de performance optimizer (debe estar disponible globalmente)
            try:
                perf_optimizer = kwargs.get('perf_optimizer') or getattr(func, '_perf_optimizer', None)
                if not perf_optimizer:
                    # Fallback: ejecutar función sin cache
                    return func(*args, **kwargs)
                
                # Generar cache key
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    # Cache key por defecto basado en argumentos
                    import hashlib
                    key_content = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                    cache_key = hashlib.md5(key_content.encode()).hexdigest()
                
                # Intentar obtener desde cache
                cached_result = perf_optimizer.get_cached_response(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit para {func.__name__}")
                    return cached_result
                
                # Ejecutar función y cachear resultado
                result = func(*args, **kwargs)
                if result and isinstance(result, str):
                    perf_optimizer.cache_response(cache_key, result, ttl=cache_ttl)
                
                return result
                
            except Exception as e:
                logger.error(f"Error en async_cache decorator: {e}")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Instancia global del optimizador
_global_performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """
    Obtener instancia global del optimizador de rendimiento
    
    Returns:
        PerformanceOptimizer: Instancia global
    """
    global _global_performance_optimizer
    
    if _global_performance_optimizer is None:
        _global_performance_optimizer = PerformanceOptimizer()
        logger.info("Instancia global de PerformanceOptimizer creada")
    
    return _global_performance_optimizer

def reset_performance_optimizer():
    """Resetear instancia global (útil para testing)"""
    global _global_performance_optimizer
    
    if _global_performance_optimizer:
        _global_performance_optimizer.cleanup_cache(force_cleanup=True)
        _global_performance_optimizer = None
        logger.info("Instancia global de PerformanceOptimizer reseteada")