# Servicio de recuperación automática del LLM
# Maneja recuperación inteligente con cooldown y límites de reintentos

import os
import time
from typing import Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMRecoveryService:
    """Servicio para recuperación automática de LLM"""

    def __init__(self):
        self.last_attempt = 0
        self.retry_interval = 300  # 5 minutos entre intentos
        self.max_consecutive_failures = 3
        self.consecutive_failures = 0
        self.recovery_history = []
        self.total_recovery_attempts = 0
        
        logger.info("LLMRecoveryService inicializado", 
                   extra={"retry_interval": self.retry_interval, 
                         "max_failures": self.max_consecutive_failures})

    def should_attempt_recovery(self) -> bool:
        """
        Determina si debe intentar recuperar LLM
        
        Returns:
            bool: True si debe intentar recuperación
        """
        current_time = time.time()

        # No intentar si está en cooldown
        if current_time - self.last_attempt < self.retry_interval:
            time_left = self.retry_interval - (current_time - self.last_attempt)
            logger.debug(f"Recovery en cooldown: {time_left:.0f} segundos restantes")
            return False

        # No intentar si ya falló muchas veces consecutivas
        if self.consecutive_failures >= self.max_consecutive_failures:
            logger.warning(f"Recovery deshabilitado: {self.consecutive_failures} fallos consecutivos")
            return False

        logger.info("Recovery disponible para intento")
        return True

    def attempt_llm_recovery(self) -> Tuple[bool, str]:
        """
        Intenta recuperar LLM con verificación completa
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.last_attempt = time.time()
            self.total_recovery_attempts += 1
            
            logger.info(f"Iniciando intento de recovery #{self.total_recovery_attempts}")

            # 1. Verificar API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                error_msg = "No OPENAI_API_KEY configurada"
                logger.error(error_msg)
                self.consecutive_failures += 1
                return False, error_msg

            if api_key == "fallback-mode":
                error_msg = "API key en modo fallback"
                logger.warning(error_msg)
                self.consecutive_failures += 1
                return False, error_msg

            # 2. Intentar crear LLM simple para test
            try:
                from langchain_openai import ChatOpenAI
                test_llm = ChatOpenAI(
                    temperature=0,
                    model="gpt-3.5-turbo",
                    max_tokens=10,  # Mínimo para test
                    openai_api_key=api_key
                )
                logger.debug("Test LLM creado exitosamente")
                
            except ImportError:
                try:
                    # Fallback a import anterior
                    from langchain.chat_models import ChatOpenAI
                    test_llm = ChatOpenAI(
                        temperature=0,
                        model="gpt-3.5-turbo",
                        max_tokens=10,
                        openai_api_key=api_key
                    )
                    logger.debug("Test LLM creado con fallback import")
                    
                except ImportError as ie:
                    error_msg = f"Error importando ChatOpenAI: {ie}"
                    logger.error(error_msg)
                    self.consecutive_failures += 1
                    return False, error_msg

            # 3. Test simple de funcionalidad
            try:
                response = test_llm.predict("Test")
                
                if response and len(response.strip()) > 0:
                    # Recovery exitoso
                    self.consecutive_failures = 0
                    recovery_info = {
                        "timestamp": time.time(),
                        "attempt_number": self.total_recovery_attempts,
                        "success": True,
                        "response_preview": response[:20]
                    }
                    self.recovery_history.append(recovery_info)
                    
                    logger.info(f"LLM recovery exitoso en intento #{self.total_recovery_attempts}")
                    return True, "Recovery successful"
                else:
                    error_msg = "LLM respuesta vacía en test"
                    logger.warning(error_msg)
                    self.consecutive_failures += 1
                    return False, error_msg
                    
            except Exception as test_error:
                error_msg = f"Error en test LLM: {test_error}"
                logger.warning(error_msg)
                self.consecutive_failures += 1
                return False, error_msg

        except Exception as e:
            self.consecutive_failures += 1
            error_msg = f"Error general en recovery: {e}"
            logger.error(error_msg, extra={"consecutive_failures": self.consecutive_failures})
            
            # Registrar fallo en historial
            recovery_info = {
                "timestamp": time.time(),
                "attempt_number": self.total_recovery_attempts,
                "success": False,
                "error": str(e)
            }
            self.recovery_history.append(recovery_info)
            
            return False, error_msg

    def get_recovery_stats(self) -> dict:
        """
        Obtiene estadísticas del servicio de recovery
        
        Returns:
            dict: Estadísticas de recovery
        """
        successful_recoveries = len([r for r in self.recovery_history if r["success"]])
        failed_recoveries = len([r for r in self.recovery_history if not r["success"]])
        
        return {
            "total_attempts": self.total_recovery_attempts,
            "consecutive_failures": self.consecutive_failures,
            "successful_recoveries": successful_recoveries,
            "failed_recoveries": failed_recoveries,
            "last_attempt_time": self.last_attempt,
            "next_attempt_available": time.time() + self.retry_interval if self.last_attempt else 0,
            "recovery_enabled": self.consecutive_failures < self.max_consecutive_failures,
            "recent_history": self.recovery_history[-5:]  # Últimos 5 intentos
        }

    def reset_failure_count(self):
        """Resetea el contador de fallos consecutivos (para uso manual)"""
        logger.info(f"Reseteando contador de fallos: {self.consecutive_failures} -> 0")
        self.consecutive_failures = 0

    def force_cooldown_reset(self):
        """Fuerza el reset del cooldown (para uso en emergencias)"""
        logger.warning("Forzando reset de cooldown de recovery")
        self.last_attempt = 0

    def is_recovery_healthy(self) -> bool:
        """
        Verifica si el sistema de recovery está en estado saludable
        
        Returns:
            bool: True si el recovery está funcionando bien
        """
        # Saludable si no hay muchos fallos consecutivos
        return self.consecutive_failures < self.max_consecutive_failures

# Instancia global del servicio
llm_recovery_service = LLMRecoveryService()

def get_llm_recovery_service() -> LLMRecoveryService:
    """Obtiene la instancia global del servicio de recovery"""
    return llm_recovery_service