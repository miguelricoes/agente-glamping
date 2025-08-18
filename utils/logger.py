# Logging estructurado para Agente Glamping
# Reemplaza los print() con logging profesional para observabilidad

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import json

class StructuredFormatter(logging.Formatter):
    """
    Formatter personalizado para logs estructurados
    Genera logs en formato JSON para mejor parsing en producción
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Crear estructura base del log
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar contexto adicional si existe
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'session_id'):
            log_data["session_id"] = record.session_id
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, 'error_code'):
            log_data["error_code"] = record.error_code
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

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
    
    # Handler para consola (desarrollo)
    if console_logs:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if structured_logs:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColoredConsoleFormatter())
        
        logger.addHandler(console_handler)
    
    # Handler para archivo (producción)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    # Configurar loggers de librerías externas
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
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