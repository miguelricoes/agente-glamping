# Configuración centralizada de la aplicación Flask
# Extrae toda la configuración de aplicación de agente.py

import os
import sys
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from utils.logger import get_logger
from config.security_config import get_secure_config_manager, validate_production_security

logger = get_logger(__name__)

class AppConfig:
    """
    Configuración centralizada de la aplicación Flask
    Maneja inicialización, CORS, variables de entorno y validaciones
    """
    
    def __init__(self):
        """Inicializar configuración de aplicación"""
        self.app = None
        self.cors = None
        self.security_manager = get_secure_config_manager()
        
        logger.info("AppConfig inicializado", 
                   extra={"component": "app_config", "phase": "startup"})
    
    def validate_environment_variables(self) -> bool:
        """
        Valida variables de entorno críticas (extraído de agente.py líneas 74-120)
        
        Returns:
            bool: True si las variables críticas están configuradas
        """
        try:
            logger.info("Validando variables de entorno", 
                       extra={"component": "app_config", "action": "validate_env"})
            
            # Variables críticas
            critical_vars = [
                'OPENAI_API_KEY'
            ]
            
            # Variables opcionales pero importantes
            optional_vars = [
                'DATABASE_URL',
                'DATABASE_PRIVATE_URL', 
                'DATABASE_PUBLIC_URL',
                'TWILIO_ACCOUNT_SID',
                'TWILIO_AUTH_TOKEN'
            ]
            
            missing_critical = []
            missing_optional = []
            
            # Verificar variables críticas
            for var in critical_vars:
                if not os.getenv(var):
                    missing_critical.append(var)
            
            # Verificar variables opcionales
            for var in optional_vars:
                if not os.getenv(var):
                    missing_optional.append(var)
            
            # Reportar resultados
            if missing_critical:
                logger.error(f"Variables críticas faltantes: {missing_critical}", 
                            extra={"component": "app_config", "missing_vars": missing_critical})
                return False
            
            if missing_optional:
                logger.warning(f"Variables opcionales faltantes: {missing_optional}", 
                              extra={"component": "app_config", "missing_optional": missing_optional})
            
            logger.info("Validación de variables de entorno completada", 
                       extra={"component": "app_config", "critical_vars": len(critical_vars), 
                              "optional_vars": len(optional_vars) - len(missing_optional)})
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando variables de entorno: {e}", 
                        extra={"component": "app_config"})
            return False
    
    def setup_environment(self) -> bool:
        """
        Configura el entorno de la aplicación
        
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            logger.info("Configurando entorno de aplicación", 
                       extra={"component": "app_config", "action": "setup_env"})
            
            # Cargar variables de entorno
            load_dotenv()
            
            # Configurar encoding para Windows
            if sys.platform.startswith('win'):
                if hasattr(sys.stdout, 'reconfigure'):
                    try:
                        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
                        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
                    except Exception:
                        pass
            
            # Validar variables de entorno
            if not self.validate_environment_variables():
                logger.warning("Algunas variables de entorno no están configuradas", 
                              extra={"component": "app_config"})
            
            logger.info("Entorno configurado exitosamente", 
                       extra={"component": "app_config"})
            
            return True
            
        except Exception as e:
            logger.error(f"Error configurando entorno: {e}", 
                        extra={"component": "app_config"})
            return False
    
    def create_flask_app(self, app_name: str = __name__) -> Flask:
        """
        Crea y configura la aplicación Flask (extraído de agente.py líneas 194-210)
        
        Args:
            app_name: Nombre de la aplicación
            
        Returns:
            Flask: Aplicación Flask configurada
        """
        try:
            logger.info("Creando aplicación Flask", 
                       extra={"component": "app_config", "action": "create_app"})
            
            # Crear aplicación Flask
            self.app = Flask(app_name)
            
            # Configuración básica de Flask
            self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
            self.app.config['JSON_AS_ASCII'] = False  # Soporte para caracteres UTF-8
            
            # Configurar CORS de forma segura
            cors_origins = ["*"]  # Desarrollo por defecto
            
            # Restringir orígenes en producción
            env_mode = os.getenv('ENV', 'development')
            if env_mode == 'production':
                cors_origin = os.getenv('CORS_ORIGIN')
                if cors_origin:
                    cors_origins = [cors_origin]
                else:
                    logger.warning("CORS_ORIGIN no configurado en producción")
                    cors_origins = []  # Sin CORS si no está configurado
            
            self.cors = CORS(self.app, resources={
                r"/*": {
                    "origins": cors_origins,
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"]
                }
            })
            
            logger.info("Aplicación Flask creada exitosamente", 
                       extra={"component": "app_config", "app_name": app_name})
            
            return self.app
            
        except Exception as e:
            logger.error(f"Error creando aplicación Flask: {e}", 
                        extra={"component": "app_config"})
            raise
    
    def validate_twilio_credentials(self) -> bool:
        """
        Valida credenciales de Twilio (extraído de agente.py líneas 623-647)
        
        Returns:
            bool: True si las credenciales son válidas
        """
        try:
            logger.info("Validando credenciales de Twilio", 
                       extra={"component": "app_config", "action": "validate_twilio"})
            
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if not account_sid or not auth_token:
                logger.warning("Credenciales de Twilio no configuradas", 
                              extra={"component": "app_config"})
                return False
            
            # Validación básica de formato
            if not account_sid.startswith('AC') or len(account_sid) != 34:
                logger.error("TWILIO_ACCOUNT_SID tiene formato inválido", 
                            extra={"component": "app_config"})
                return False
            
            if len(auth_token) != 32:
                logger.error("TWILIO_AUTH_TOKEN tiene formato inválido", 
                            extra={"component": "app_config"})
                return False
            
            logger.info("Credenciales de Twilio validadas exitosamente", 
                       extra={"component": "app_config"})
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando credenciales de Twilio: {e}", 
                        extra={"component": "app_config"})
            return False
    
    def get_app_info(self) -> dict:
        """
        Obtiene información de la aplicación
        
        Returns:
            dict: Información de la aplicación
        """
        try:
            return {
                'app_configured': self.app is not None,
                'cors_enabled': self.cors is not None,
                'environment': os.getenv('FLASK_ENV', 'development'),
                'debug_mode': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
                'secret_key_configured': bool(self.app and self.app.config.get('SECRET_KEY')),
                'twilio_configured': self.validate_twilio_credentials()
            }
        except Exception as e:
            logger.error(f"Error obteniendo información de aplicación: {e}", 
                        extra={"component": "app_config"})
            return {'error': str(e)}
    
    def setup_production_config(self) -> None:
        """
        Configura la aplicación para producción
        """
        try:
            if self.app:
                # Configuraciones de producción
                self.app.config['DEBUG'] = False
                self.app.config['TESTING'] = False
                
                # Configuraciones de seguridad
                self.app.config['SESSION_COOKIE_SECURE'] = True
                self.app.config['SESSION_COOKIE_HTTPONLY'] = True
                self.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
                
                # Headers de seguridad
                @self.app.after_request
                def add_security_headers(response):
                    # Prevenir clickjacking
                    response.headers['X-Frame-Options'] = 'DENY'
                    # Prevenir MIME sniffing
                    response.headers['X-Content-Type-Options'] = 'nosniff'
                    # XSS Protection
                    response.headers['X-XSS-Protection'] = '1; mode=block'
                    # Referrer Policy
                    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                    # Content Security Policy básico
                    response.headers['Content-Security-Policy'] = "default-src 'self'"
                    return response
                
                logger.info("Configuración de producción aplicada", 
                           extra={"component": "app_config", "mode": "production"})
        except Exception as e:
            logger.error(f"Error configurando para producción: {e}", 
                        extra={"component": "app_config"})


def create_app(validate_env: bool = True) -> Flask:
    """
    Factory function para crear aplicación Flask configurada
    
    Args:
        validate_env: Si validar variables de entorno
        
    Returns:
        Flask: Aplicación Flask lista para usar
    """
    config = AppConfig()
    
    # Configurar entorno
    if validate_env:
        config.setup_environment()
    
    # Crear aplicación
    app = config.create_flask_app()
    
    # Configurar para producción si es necesario
    env_mode = os.getenv('ENV', 'development')
    if env_mode == 'production':
        config.setup_production_config()
    
    return app


def get_app_config() -> AppConfig:
    """
    Obtiene instancia global de configuración de aplicación
    
    Returns:
        AppConfig: Configuración de aplicación
    """
    return AppConfig()