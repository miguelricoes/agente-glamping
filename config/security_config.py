# Gestor seguro de configuración para producción
# Protege API keys y datos sensibles mediante encriptación

import os
import base64
import secrets
from typing import Dict, Any, Optional
from utils.logger import get_logger

# Importación condicional de cryptography
try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("⚠️ WARNING: cryptography no disponible. Instala: pip install cryptography")

logger = get_logger(__name__)

class SecureConfigManager:
    """
    Gestor seguro de configuración para producción
    Encripta y valida datos sensibles como API keys y tokens
    """

    def __init__(self):
        """Inicializar gestor seguro de configuración"""
        self.encryption_key = None
        self.cipher = None
        self.environment = os.getenv('ENV', 'development')
        
        # Solo usar encriptación en producción si cryptography está disponible
        if CRYPTOGRAPHY_AVAILABLE and self.environment == 'production':
            try:
                self.encryption_key = self._get_or_create_encryption_key()
                self.cipher = Fernet(self.encryption_key)
                logger.info("Gestor de configuración segura inicializado con encriptación")
            except Exception as e:
                logger.error(f"Error inicializando encriptación: {e}")
                self.encryption_key = None
                self.cipher = None
        else:
            logger.info("Gestor de configuración segura inicializado sin encriptación (desarrollo)")

    def _get_or_create_encryption_key(self) -> bytes:
        """Obtener clave de encriptación desde variable de entorno"""
        key = os.environ.get('ENCRYPTION_KEY')
        
        if not key:
            # Generar nueva clave para desarrollo
            new_key = Fernet.generate_key().decode()
            logger.warning("⚠️ Generando nueva clave de encriptación")
            logger.warning(f"Agrega esta clave como ENCRYPTION_KEY: {new_key}")
            return new_key.encode()
        
        # Validar formato de clave
        try:
            key_bytes = key.encode() if isinstance(key, str) else key
            # Probar que la clave sea válida
            Fernet(key_bytes)
            return key_bytes
        except Exception as e:
            logger.error(f"Clave de encriptación inválida: {e}")
            raise ValueError("ENCRYPTION_KEY tiene formato inválido")

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encriptar datos sensibles"""
        if not self.cipher:
            logger.warning("Encriptación no disponible, devolviendo datos sin encriptar")
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encriptando datos: {e}")
            raise

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Desencriptar datos sensibles"""
        if not self.cipher:
            logger.warning("Encriptación no disponible, devolviendo datos tal como están")
            return encrypted_data
        
        try:
            # Decodificar base64 y luego desencriptar
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error desencriptando datos: {e}")
            # Intentar devolver datos sin encriptar como fallback
            return encrypted_data

    def get_secure_config(self, key: str, encrypted: bool = False, required: bool = True) -> Optional[str]:
        """
        Obtener configuración de forma segura
        
        Args:
            key: Nombre de la variable de entorno
            encrypted: Si el valor está encriptado
            required: Si la variable es requerida
            
        Returns:
            Valor de la configuración o None si no es requerida y no existe
        """
        try:
            value = os.environ.get(key)
            
            if not value:
                if required:
                    logger.error(f"Variable de entorno requerida no encontrada: {key}")
                    raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
                return None

            if encrypted and self.cipher:
                return self.decrypt_sensitive_data(value)
            
            return value
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración segura para {key}: {e}")
            if required:
                raise
            return None

    def validate_api_key_security(self) -> Dict[str, Any]:
        """
        Validar seguridad de API keys y detectar exposición
        
        Returns:
            Diccionario con resultados de validación
        """
        validation_results = {
            "environment": self.environment,
            "encryption_available": self.cipher is not None,
            "exposed_keys": [],
            "missing_keys": [],
            "security_score": 100
        }
        
        # Definir patrones de API keys conocidos
        sensitive_patterns = {
            'OPENAI_API_KEY': {
                'patterns': ['sk-', 'sk_'],
                'min_length': 50,
                'description': 'OpenAI API Key'
            },
            'TWILIO_ACCOUNT_SID': {
                'patterns': ['AC'],
                'min_length': 34,
                'description': 'Twilio Account SID'
            },
            'TWILIO_AUTH_TOKEN': {
                'patterns': [],
                'min_length': 32,
                'description': 'Twilio Auth Token'
            },
            'DATABASE_PRIVATE_URL': {
                'patterns': ['postgresql://', 'postgres://'],
                'min_length': 20,
                'description': 'Database URL'
            }
        }
        
        for key, config in sensitive_patterns.items():
            value = os.getenv(key)
            
            if not value:
                validation_results["missing_keys"].append({
                    "key": key,
                    "description": config["description"]
                })
                validation_results["security_score"] -= 20
                continue
            
            # Verificar si la key está potencialmente expuesta
            is_exposed = False
            exposure_reasons = []
            
            # Verificar patrones conocidos
            for pattern in config["patterns"]:
                if value.startswith(pattern):
                    is_exposed = True
                    exposure_reasons.append(f"Inicia con patrón conocido: {pattern}")
            
            # Verificar longitud
            if len(value) >= config["min_length"]:
                is_exposed = True
                exposure_reasons.append(f"Longitud sospechosa: {len(value)} chars")
            
            # En producción, cualquier key visible es un problema
            if self.environment == 'production' and is_exposed:
                validation_results["exposed_keys"].append({
                    "key": key,
                    "description": config["description"],
                    "reasons": exposure_reasons,
                    "severity": "CRITICAL"
                })
                validation_results["security_score"] -= 30
            
            # En desarrollo, solo advertir
            elif self.environment != 'production' and is_exposed:
                validation_results["exposed_keys"].append({
                    "key": key,
                    "description": config["description"],
                    "reasons": exposure_reasons,
                    "severity": "WARNING"
                })
                validation_results["security_score"] -= 5
        
        # Verificar encriptación en producción
        if self.environment == 'production' and not self.cipher:
            validation_results["security_score"] -= 25
        
        # Determinar nivel de seguridad
        if validation_results["security_score"] >= 90:
            validation_results["security_level"] = "EXCELLENT"
        elif validation_results["security_score"] >= 70:
            validation_results["security_level"] = "GOOD"
        elif validation_results["security_score"] >= 50:
            validation_results["security_level"] = "FAIR"
        else:
            validation_results["security_level"] = "POOR"
        
        return validation_results

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generar token seguro para uso interno
        
        Args:
            length: Longitud del token
            
        Returns:
            Token seguro generado
        """
        return secrets.token_urlsafe(length)

    def mask_sensitive_value(self, value: str, visible_chars: int = 4) -> str:
        """
        Enmascarar valor sensible para logging seguro
        
        Args:
            value: Valor a enmascarar
            visible_chars: Caracteres visibles al inicio y final
            
        Returns:
            Valor enmascarado
        """
        if not value or len(value) <= visible_chars * 2:
            return "*" * len(value) if value else ""
        
        start = value[:visible_chars]
        end = value[-visible_chars:]
        middle = "*" * (len(value) - visible_chars * 2)
        
        return f"{start}{middle}{end}"

    def get_security_headers(self) -> Dict[str, str]:
        """
        Obtener headers de seguridad para producción
        
        Returns:
            Diccionario con headers de seguridad
        """
        headers = {
            # Prevenir clickjacking
            'X-Frame-Options': 'DENY',
            
            # Prevenir MIME sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # XSS Protection
            'X-XSS-Protection': '1; mode=block',
            
            # Referrer Policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Content Security Policy básico
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        }
        
        # Headers adicionales para HTTPS en producción
        if self.environment == 'production':
            headers.update({
                # Forzar HTTPS
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                
                # Política de permisos
                'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
            })
        
        return headers

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de configuración para debugging seguro
        
        Returns:
            Resumen de configuración con valores enmascarados
        """
        try:
            summary = {
                "environment": self.environment,
                "encryption_enabled": self.cipher is not None,
                "cryptography_available": CRYPTOGRAPHY_AVAILABLE,
                "config_keys": {}
            }
            
            # Lista de keys a revisar
            sensitive_keys = [
                'OPENAI_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN',
                'DATABASE_PRIVATE_URL', 'DATABASE_PUBLIC_URL', 'DATABASE_URL',
                'SECRET_KEY', 'ENCRYPTION_KEY'
            ]
            
            for key in sensitive_keys:
                value = os.getenv(key)
                summary["config_keys"][key] = {
                    "configured": value is not None,
                    "length": len(value) if value else 0,
                    "masked_value": self.mask_sensitive_value(value) if value else None
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generando resumen de configuración: {e}")
            return {"error": str(e)}

# Instancia global del gestor seguro
secure_config_manager = SecureConfigManager()

def get_secure_config_manager() -> SecureConfigManager:
    """
    Obtener instancia global del gestor de configuración segura
    
    Returns:
        SecureConfigManager: Instancia del gestor
    """
    return secure_config_manager

def get_secure_env_var(key: str, encrypted: bool = False, required: bool = True) -> Optional[str]:
    """
    Función de utilidad para obtener variable de entorno segura
    
    Args:
        key: Nombre de la variable de entorno
        encrypted: Si el valor está encriptado
        required: Si la variable es requerida
        
    Returns:
        Valor de la variable o None
    """
    return secure_config_manager.get_secure_config(key, encrypted, required)

def validate_production_security() -> bool:
    """
    Validar configuración de seguridad para producción
    
    Returns:
        True si la configuración es segura para producción
    """
    results = secure_config_manager.validate_api_key_security()
    
    # En producción, no debe haber keys expuestas
    if os.getenv('ENV') == 'production':
        critical_exposures = [
            key for key in results["exposed_keys"] 
            if key.get("severity") == "CRITICAL"
        ]
        
        if critical_exposures:
            logger.error("🚨 CRÍTICO: API Keys expuestas en producción detectadas")
            for exposure in critical_exposures:
                logger.error(f"  - {exposure['key']}: {exposure['reasons']}")
            return False
        
        if results["missing_keys"]:
            logger.error("🚨 CRÍTICO: Variables de entorno requeridas faltantes en producción")
            for missing in results["missing_keys"]:
                logger.error(f"  - {missing['key']}: {missing['description']}")
            return False
    
    return True