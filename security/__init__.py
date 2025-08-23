# Paquete de seguridad para Glamping Agent
# Inicialización e integración de todos los componentes de seguridad

import os
from typing import Optional
from flask import Flask

from utils.logger import get_logger

logger = get_logger(__name__)

def initialize_security(app: Flask) -> bool:
    """
    Inicializar todos los componentes de seguridad para la aplicación
    
    Args:
        app: Instancia de Flask
        
    Returns:
        bool: True si la inicialización fue exitosa
    """
    try:
        logger.info("Inicializando sistema de seguridad completo...")
        
        # 1. Inicializar SecurityMiddleware
        success_middleware = initialize_security_middleware(app)
        
        # 2. Registrar rutas de seguridad
        success_routes = register_security_routes(app)
        
        # 3. Configurar validación de inputs
        success_validation = configure_input_validation(app)
        
        # 4. Verificar configuración de seguridad
        success_config = verify_security_configuration()
        
        # 5. Log estado final
        overall_success = all([success_middleware, success_routes, success_validation, success_config])
        
        if overall_success:
            logger.info("✅ Sistema de seguridad inicializado exitosamente",
                       extra={
                           "middleware": success_middleware,
                           "routes": success_routes, 
                           "validation": success_validation,
                           "config": success_config
                       })
        else:
            logger.warning("⚠️ Sistema de seguridad inicializado con advertencias",
                          extra={
                              "middleware": success_middleware,
                              "routes": success_routes,
                              "validation": success_validation,
                              "config": success_config
                          })
        
        return overall_success
        
    except Exception as e:
        logger.error(f"Error inicializando sistema de seguridad: {e}")
        return False

def initialize_security_middleware(app: Flask) -> bool:
    """Inicializar SecurityMiddleware"""
    try:
        from security.security_middleware import create_security_middleware
        
        security_middleware = create_security_middleware(app)
        
        # Almacenar referencia en la app para acceso posterior
        app._security_middleware = security_middleware
        
        logger.info("SecurityMiddleware inicializado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando SecurityMiddleware: {e}")
        return False

def register_security_routes(app: Flask) -> bool:
    """Registrar rutas de seguridad"""
    try:
        from routes.security_routes import register_security_routes
        
        register_security_routes(app)
        
        logger.info("Rutas de seguridad registradas exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error registrando rutas de seguridad: {e}")
        return False

def configure_input_validation(app: Flask) -> bool:
    """Configurar validación de inputs"""
    try:
        from security.input_validator import get_input_validator
        
        # Inicializar validador global
        validator = get_input_validator()
        
        # Almacenar referencia en la app
        app._input_validator = validator
        
        logger.info("Validación de inputs configurada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error configurando validación de inputs: {e}")
        return False

def verify_security_configuration() -> bool:
    """Verificar configuración de seguridad"""
    try:
        from config.security_config import validate_production_security
        
        # Verificar configuración según el entorno
        env = os.getenv('ENV', 'development')
        
        if env == 'production':
            production_ready = validate_production_security()
            if not production_ready:
                logger.warning("⚠️ Sistema NO está listo para producción - vulnerabilidades detectadas")
                return False
            else:
                logger.info("✅ Sistema listo para producción")
        else:
            logger.info(f"Sistema configurado para {env}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando configuración de seguridad: {e}")
        return False

def get_security_status(app: Flask) -> dict:
    """
    Obtener estado completo del sistema de seguridad
    
    Args:
        app: Instancia de Flask
        
    Returns:
        dict: Estado detallado de seguridad
    """
    try:
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv('ENV', 'development'),
            "components": {}
        }
        
        # Estado del middleware
        if hasattr(app, '_security_middleware'):
            middleware_stats = app._security_middleware.get_security_stats()
            status["components"]["middleware"] = {
                "status": "active",
                "stats": middleware_stats
            }
        else:
            status["components"]["middleware"] = {"status": "not_initialized"}
        
        # Estado del validador
        if hasattr(app, '_input_validator'):
            status["components"]["input_validator"] = {"status": "active"}
        else:
            status["components"]["input_validator"] = {"status": "not_initialized"}
        
        # Estado de configuración
        try:
            from config.security_config import get_secure_config_manager
            security_manager = get_secure_config_manager()
            config_summary = security_manager.get_config_summary()
            status["components"]["config"] = {
                "status": "active",
                "summary": config_summary
            }
        except Exception:
            status["components"]["config"] = {"status": "error"}
        
        # Estado general
        active_components = len([c for c in status["components"].values() if c.get("status") == "active"])
        total_components = len(status["components"])
        
        status["overall_status"] = "healthy" if active_components == total_components else "degraded"
        status["component_health"] = f"{active_components}/{total_components}"
        
        return status
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de seguridad: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e)
        }

def run_security_health_check(app: Flask) -> bool:
    """
    Ejecutar health check completo del sistema de seguridad
    
    Args:
        app: Instancia de Flask
        
    Returns:
        bool: True si todos los componentes están saludables
    """
    try:
        logger.info("🔍 Ejecutando health check de seguridad...")
        
        checks = []
        
        # Check 1: Middleware activo
        middleware_ok = hasattr(app, '_security_middleware')
        checks.append(("Security Middleware", middleware_ok))
        
        # Check 2: Validador disponible
        validator_ok = hasattr(app, '_input_validator')
        checks.append(("Input Validator", validator_ok))
        
        # Check 3: Configuración segura
        try:
            from config.security_config import validate_production_security
            config_ok = validate_production_security() if os.getenv('ENV') == 'production' else True
        except Exception:
            config_ok = False
        checks.append(("Security Config", config_ok))
        
        # Check 4: Variables de entorno críticas
        critical_vars = ['OPENAI_API_KEY', 'TWILIO_AUTH_TOKEN']
        env_ok = all(os.getenv(var) for var in critical_vars)
        checks.append(("Environment Variables", env_ok))
        
        # Check 5: Permisos de archivos (básico)
        files_ok = True
        if os.path.exists('.env'):
            import stat
            env_stat = os.stat('.env')
            # Verificar que .env no sea legible por otros
            files_ok = not (env_stat.st_mode & stat.S_IROTH)
        checks.append(("File Permissions", files_ok))
        
        # Resultado final
        passed_checks = len([check for check in checks if check[1]])
        total_checks = len(checks)
        
        success_rate = (passed_checks / total_checks) * 100
        overall_healthy = success_rate >= 80  # 80% de checks deben pasar
        
        # Log resultados
        logger.info(f"Security health check completado: {passed_checks}/{total_checks} checks pasados ({success_rate:.1f}%)")
        
        for check_name, check_result in checks:
            status_icon = "✅" if check_result else "❌"
            logger.info(f"  {status_icon} {check_name}: {'OK' if check_result else 'FAIL'}")
        
        if not overall_healthy:
            logger.warning("⚠️ Sistema de seguridad degradado - algunos checks fallaron")
        
        return overall_healthy
        
    except Exception as e:
        logger.error(f"Error en health check de seguridad: {e}")
        return False

# Funciones de utilidad para integración
def require_security_middleware(f):
    """Decorator que requiere que SecurityMiddleware esté inicializado"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        
        if not hasattr(current_app, '_security_middleware'):
            logger.error("SecurityMiddleware requerido pero no inicializado")
            abort(500, "Sistema de seguridad no disponible")
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_security_context() -> dict:
    """Obtener contexto de seguridad actual"""
    from flask import g
    
    return g.get('security_context', {})

# Importar datetime para uso en las funciones
from datetime import datetime