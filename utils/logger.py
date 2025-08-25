# Logging estructurado para Agente Glamping
# Reemplaza los print() con logging profesional para observabilidad
# Incluye sanitización segura de datos sensibles

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import json
import time
from collections import defaultdict

class RateLimitedHandler(logging.Handler):
    """
    Handler que implementa rate limiting para evitar saturar Railway
    Máximo 100 logs por segundo, con burst de 200
    """
    
    def __init__(self, handler, max_logs_per_second=100, burst_limit=200):
        super().__init__()
        self.handler = handler
        self.max_logs_per_second = max_logs_per_second
        self.burst_limit = burst_limit
        self.tokens = burst_limit
        self.last_refill = time.time()
        self.dropped_count = 0
    
    def emit(self, record):
        now = time.time()
        # Refill tokens based on time passed
        time_passed = now - self.last_refill
        self.tokens = min(self.burst_limit, self.tokens + time_passed * self.max_logs_per_second)
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            self.handler.emit(record)
            
            # Log dropped count periodically
            if self.dropped_count > 0:
                dropped_record = logging.LogRecord(
                    name="rate_limiter",
                    level=logging.WARNING,
                    pathname="",
                    lineno=0,
                    msg=f"Dropped {self.dropped_count} log messages due to rate limiting",
                    args=(),
                    exc_info=None
                )
                self.handler.emit(dropped_record)
                self.dropped_count = 0
        else:
            self.dropped_count += 1
    
    def setFormatter(self, formatter):
        self.handler.setFormatter(formatter)
    
    def setLevel(self, level):
        self.handler.setLevel(level)

class StructuredFormatter(logging.Formatter):
    """
    Formatter personalizado para logs estructurados con sanitización segura
    Genera logs en formato JSON para mejor parsing en producción
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Crear estructura base del log
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": self._sanitize_message(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar contexto adicional si existe (con sanitización)
        if hasattr(record, 'user_id'):
            log_data["user_id"] = self._sanitize_user_id(record.user_id)
        if hasattr(record, 'session_id'):
            log_data["session_id"] = self._sanitize_session_id(record.session_id)
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, 'error_code'):
            log_data["error_code"] = record.error_code
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        # Agregar campos extra de forma segura
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            sanitized_extra = self._sanitize_extra_data(record.extra)
            log_data.update(sanitized_extra)
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitizar mensaje de log para remover datos sensibles"""
        try:
            # Importar SecurityMiddleware para sanitización
            try:
                from security.security_middleware import SecurityMiddleware
                return SecurityMiddleware.sanitize_input(message, max_length=500)
            except ImportError:
                # Fallback básico si no está disponible
                import re
                # Remover patrones que parecen tokens o API keys
                sanitized = re.sub(r'\b[A-Za-z0-9]{20,}\b', '[REDACTED_TOKEN]', message)
                # Remover números de teléfono
                sanitized = re.sub(r'\+\d{10,15}', '[REDACTED_PHONE]', sanitized)
                # Remover emails
                sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', sanitized)
                return sanitized[:500]
        except Exception:
            return str(message)[:500]
    
    def _sanitize_user_id(self, user_id: str) -> str:
        """Sanitizar user_id para logging seguro"""
        try:
            # Importar SecurityMiddleware para sanitización de teléfono
            try:
                from security.security_middleware import SecurityMiddleware
                return SecurityMiddleware.sanitize_phone_number(user_id)
            except ImportError:
                # Fallback básico
                if user_id and len(user_id) > 4:
                    return user_id[:4] + '*' * (len(user_id) - 6) + user_id[-2:] if len(user_id) > 6 else user_id[:2] + '**'
                return '[REDACTED]'
        except Exception:
            return '[REDACTED]'
    
    def _sanitize_session_id(self, session_id: str) -> str:
        """Sanitizar session_id"""
        try:
            if session_id and len(session_id) > 8:
                return session_id[:4] + '*' * (len(session_id) - 8) + session_id[-4:]
            return '[REDACTED]'
        except Exception:
            return '[REDACTED]'
    
    def _sanitize_extra_data(self, extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar datos extra de forma segura"""
        try:
            # Importar SecurityMiddleware para sanitización completa
            try:
                from security.security_middleware import SecurityMiddleware
                return SecurityMiddleware.secure_log_data(extra_data)
            except ImportError:
                # Fallback básico
                sanitized = {}
                sensitive_keys = ['password', 'token', 'key', 'secret', 'phone', 'email', 'api_key']
                
                for key, value in extra_data.items():
                    key_lower = key.lower()
                    is_sensitive = any(sensitive in key_lower for sensitive in sensitive_keys)
                    
                    if is_sensitive:
                        sanitized[key] = '[REDACTED]'
                    elif isinstance(value, str) and len(value) > 100:
                        sanitized[key] = value[:97] + '...'
                    else:
                        sanitized[key] = value
                
                return sanitized
        except Exception as e:
            return {"sanitization_error": str(e)}

class ColoredConsoleFormatter(logging.Formatter):
    """
    Formatter para consola con colores para mejor desarrollo local
    """
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Obtener color para el nivel
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Formatear timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Crear mensaje formateado
        formatted_message = (
            f"{color}[{record.levelname:8}]{reset} "
            f"{timestamp} "
            f"{record.name}:{record.module}.{record.funcName}:{record.lineno} - "
            f"{record.getMessage()}"
        )
        
        # Agregar excepción si existe
        if record.exc_info:
            formatted_message += f"\\n{self.formatException(record.exc_info)}"
        
        return formatted_message

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    structured_logs: bool = True,
    console_logs: bool = True
) -> logging.Logger:
    """
    Configurar el sistema de logging para la aplicación
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo donde guardar los logs (opcional)
        structured_logs: Si usar formato JSON estructurado
        console_logs: Si mostrar logs en consola
    
    Returns:
        Logger configurado para la aplicación
    """
    
    # Crear logger principal
    logger = logging.getLogger("agente_glamping")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Limpiar handlers existentes para evitar duplicación
    logger.handlers.clear()
    
    # Handler para consola (desarrollo) - CON RATE LIMITING
    if console_logs:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if structured_logs:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColoredConsoleFormatter())
        
        # Aplicar rate limiting en producción
        is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production" or os.getenv("ENV") == "production"
        if is_production:
            rate_limited_handler = RateLimitedHandler(console_handler, max_logs_per_second=50, burst_limit=100)
            rate_limited_handler.setLevel(getattr(logging, log_level.upper()))
            logger.addHandler(rate_limited_handler)
        else:
            logger.addHandler(console_handler)
    
    # Handler para archivo (producción)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    # Configurar loggers de librerías externas - REDUCIR LOGS PARA RAILWAY
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("langchain").setLevel(logging.ERROR)
    logging.getLogger("openai").setLevel(logging.ERROR)
    
    # Reducir logs de servicios propios que causan loops
    logging.getLogger("agente_glamping.services.validation_service").setLevel(logging.CRITICAL)
    logging.getLogger("agente_glamping.services.llm_service").setLevel(logging.WARNING)
    logging.getLogger("agente_glamping.services.conversation_service").setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Obtener logger para un módulo específico
    
    Args:
        name: Nombre del módulo (usa __name__ por defecto)
    
    Returns:
        Logger configurado
    """
    if name is None:
        name = "agente_glamping"
    elif not name.startswith("agente_glamping"):
        name = f"agente_glamping.{name}"
    
    return logging.getLogger(name)

# Funciones de conveniencia para logging contextual
def log_startup(logger: logging.Logger, component: str, status: str, details: str = ""):
    """Log de inicio de componente"""
    logger.info(
        f"Startup: {component} - {status}",
        extra={
            "component": component,
            "status": status,
            "details": details,
            "phase": "startup"
        }
    )

def log_request(logger: logging.Logger, endpoint: str, user_id: str = None, session_id: str = None):
    """Log de request HTTP/API"""
    logger.info(
        f"Request: {endpoint}",
        extra={
            "endpoint": endpoint,
            "user_id": user_id,
            "session_id": session_id,
            "phase": "request"
        }
    )

def log_response(logger: logging.Logger, endpoint: str, status_code: int, duration_ms: float, user_id: str = None):
    """Log de response HTTP/API"""
    logger.info(
        f"Response: {endpoint} - {status_code} ({duration_ms:.1f}ms)",
        extra={
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "phase": "response"
        }
    )

def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log de error con contexto"""
    logger.error(
        f"Error: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "phase": "error"
        },
        exc_info=True
    )

def log_database_operation(logger: logging.Logger, operation: str, table: str, success: bool, details: str = ""):
    """Log de operación de base de datos"""
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"DB {operation}: {table} - {'SUCCESS' if success else 'FAILED'}",
        extra={
            "database_operation": operation,
            "table": table,
            "success": success,
            "details": details,
            "phase": "database"
        }
    )

def log_conversation(logger: logging.Logger, user_id: str, message_type: str, success: bool, details: str = ""):
    """Log de operación conversacional"""
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        f"Conversation {message_type}: {user_id} - {'SUCCESS' if success else 'FAILED'}",
        extra={
            "user_id": user_id,
            "message_type": message_type,
            "success": success,
            "details": details,
            "phase": "conversation"
        }
    )

# Configuración automática basada en variables de entorno
def auto_configure_logging():
    """
    Configurar logging automáticamente basado en variables de entorno
    """
    # Determinar nivel de log
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Determinar si estamos en producción
    is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production" or os.getenv("ENV") == "production"
    
    # Configurar archivo de logs en producción
    log_file = None
    if is_production:
        log_file = os.getenv("LOG_FILE", "logs/agente_glamping.log")
        # Crear directorio de logs si no existe
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configurar formato estructurado en producción
    structured_logs = is_production or os.getenv("STRUCTURED_LOGS", "false").lower() == "true"
    
    # Configurar consola (siempre en desarrollo, opcional en producción)
    console_logs = not is_production or os.getenv("CONSOLE_LOGS", "true").lower() == "true"
    
    return setup_logging(
        log_level=log_level,
        log_file=log_file,
        structured_logs=structured_logs,
        console_logs=console_logs
    )

# Inicializar logging por defecto
if not logging.getLogger("agente_glamping").handlers:
    auto_configure_logging()