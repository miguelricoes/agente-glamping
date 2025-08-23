# Validador de inputs para todos los endpoints
# Previene inyecciones, ataques XSS y datos maliciosos

import re
import json
from datetime import datetime, date
from typing import Any, Dict, List, Tuple, Optional, Union
from functools import wraps
from flask import request, abort, g
from dataclasses import dataclass
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ValidationRule:
    """Regla de validación para un campo"""
    field_name: str
    required: bool = False
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    pattern: Optional[str] = None
    data_type: type = str
    custom_validator: Optional[callable] = None
    sanitizer: Optional[callable] = None
    description: str = ""

class InputValidator:
    """
    Validador comprehensivo de inputs para seguridad
    Valida tipos, longitudes, patrones y contenido malicioso
    """
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.InputValidator")
        
        # Patrones maliciosos comunes
        self.malicious_patterns = [
            # SQL Injection
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|\#|/\*|\*/)",
            
            # XSS
            r"<script[^>]*>.*?</script>",
            r"javascript\s*:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            
            # Command Injection
            r"(\b(sh|bash|cmd|powershell|exec)\b)",
            r"(\||&&|;|\$\()",
            
            # Path Traversal
            r"(\.\./|\.\.\\)",
            r"(/etc/|/windows/|c:\\)",
            
            # LDAP Injection
            r"(\*|\(|\)|\\|\||&)",
        ]
        
        # Compilar patrones
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
        
        # Reglas de validación predefinidas por endpoint
        self.endpoint_rules = self._define_endpoint_rules()

    def _define_endpoint_rules(self) -> Dict[str, List[ValidationRule]]:
        """Definir reglas de validación por endpoint"""
        return {
            'whatsapp_webhook': [
                ValidationRule(
                    field_name='Body',
                    required=True,
                    max_length=1000,
                    min_length=1,
                    sanitizer=self._sanitize_message_content,
                    description="Contenido del mensaje de WhatsApp"
                ),
                ValidationRule(
                    field_name='From',
                    required=True,
                    max_length=50,
                    pattern=r'^whatsapp:\+\d{10,15}$',
                    sanitizer=self._sanitize_phone_number,
                    description="Número de WhatsApp en formato whatsapp:+country_code_number"
                ),
                ValidationRule(
                    field_name='To',
                    required=False,
                    max_length=50,
                    pattern=r'^whatsapp:\+\d{10,15}$',
                    sanitizer=self._sanitize_phone_number,
                    description="Número de destino de WhatsApp"
                )
            ],
            
            'api_reserva_create': [
                ValidationRule(
                    field_name='email_contacto',
                    required=True,
                    max_length=100,
                    custom_validator=self._validate_email,
                    sanitizer=self._sanitize_email,
                    description="Email de contacto válido"
                ),
                ValidationRule(
                    field_name='numero_whatsapp',
                    required=True,
                    max_length=20,
                    custom_validator=self._validate_phone_number,
                    sanitizer=self._sanitize_phone_number,
                    description="Número de WhatsApp válido"
                ),
                ValidationRule(
                    field_name='nombres_huespedes',
                    required=True,
                    max_length=200,
                    min_length=2,
                    pattern=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s,.-]+$',
                    sanitizer=self._sanitize_names,
                    description="Nombres de huéspedes (solo letras, espacios y puntuación básica)"
                ),
                ValidationRule(
                    field_name='cantidad_huespedes',
                    required=True,
                    data_type=int,
                    custom_validator=lambda x: 1 <= int(x) <= 20,
                    description="Cantidad de huéspedes entre 1 y 20"
                ),
                ValidationRule(
                    field_name='domo',
                    required=True,
                    max_length=50,
                    pattern=r'^(Antares|Polaris|Sirius|Centaury)$',
                    description="Domo válido: Antares, Polaris, Sirius o Centaury"
                ),
                ValidationRule(
                    field_name='fecha_entrada',
                    required=True,
                    custom_validator=self._validate_date,
                    sanitizer=self._sanitize_date,
                    description="Fecha de entrada válida (YYYY-MM-DD)"
                ),
                ValidationRule(
                    field_name='fecha_salida',
                    required=True,
                    custom_validator=self._validate_date,
                    sanitizer=self._sanitize_date,
                    description="Fecha de salida válida (YYYY-MM-DD)"
                )
            ],
            
            'admin_endpoints': [
                ValidationRule(
                    field_name='admin_key',
                    required=True,
                    min_length=10,
                    description="Clave de administrador válida"
                )
            ]
        }

    def validate_request(self, endpoint: str, data: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validar request completo según endpoint
        
        Args:
            endpoint: Nombre del endpoint
            data: Datos a validar (opcional, usa request.form/json si no se proporciona)
            
        Returns:
            Tuple[bool, Dict[str, Any], List[str]]: (válido, datos_sanitizados, errores)
        """
        try:
            # Obtener datos si no se proporcionan
            if data is None:
                data = self._extract_request_data()
            
            # Obtener reglas para el endpoint
            rules = self.endpoint_rules.get(endpoint, [])
            
            validated_data = {}
            errors = []
            
            # Validar cada regla
            for rule in rules:
                field_value = data.get(rule.field_name)
                
                # Verificar si es requerido
                if rule.required and (field_value is None or field_value == ""):
                    errors.append(f"Campo requerido: {rule.field_name}")
                    continue
                
                # Si no es requerido y está vacío, continuar
                if not rule.required and (field_value is None or field_value == ""):
                    validated_data[rule.field_name] = field_value
                    continue
                
                # Validar tipo de dato
                if rule.data_type != str:
                    try:
                        if rule.data_type == int:
                            field_value = int(field_value)
                        elif rule.data_type == float:
                            field_value = float(field_value)
                        elif rule.data_type == bool:
                            field_value = str(field_value).lower() in ('true', '1', 'yes', 'on')
                    except (ValueError, TypeError) as e:
                        errors.append(f"Tipo de dato inválido para {rule.field_name}: esperado {rule.data_type.__name__}")
                        continue
                
                # Convertir a string para validaciones de string
                field_str = str(field_value)
                
                # Validar longitud mínima
                if rule.min_length and len(field_str) < rule.min_length:
                    errors.append(f"Campo {rule.field_name} muy corto: mínimo {rule.min_length} caracteres")
                    continue
                
                # Validar longitud máxima
                if rule.max_length and len(field_str) > rule.max_length:
                    errors.append(f"Campo {rule.field_name} muy largo: máximo {rule.max_length} caracteres")
                    continue
                
                # Validar patrón
                if rule.pattern:
                    if not re.match(rule.pattern, field_str, re.IGNORECASE):
                        errors.append(f"Formato inválido para {rule.field_name}: {rule.description}")
                        continue
                
                # Verificar contenido malicioso
                if self._contains_malicious_content(field_str):
                    errors.append(f"Contenido potencialmente malicioso detectado en {rule.field_name}")
                    self.logger.warning(f"Contenido malicioso detectado en {rule.field_name}: {field_str[:50]}...",
                                      extra={"field": rule.field_name, "content_preview": field_str[:50]})
                    continue
                
                # Validador personalizado
                if rule.custom_validator:
                    try:
                        if not rule.custom_validator(field_value):
                            errors.append(f"Validación personalizada fallida para {rule.field_name}: {rule.description}")
                            continue
                    except Exception as e:
                        errors.append(f"Error en validación personalizada para {rule.field_name}: {str(e)}")
                        continue
                
                # Sanitizar valor
                if rule.sanitizer:
                    try:
                        field_value = rule.sanitizer(field_value)
                    except Exception as e:
                        self.logger.error(f"Error sanitizando {rule.field_name}: {e}")
                        # Usar valor original si la sanitización falla
                
                validated_data[rule.field_name] = field_value
            
            # Agregar campos no validados (pero sanitizados básicamente)
            for key, value in data.items():
                if key not in validated_data and key not in [rule.field_name for rule in rules]:
                    if isinstance(value, str) and len(value) <= 1000:  # Límite básico
                        validated_data[key] = self._basic_sanitize(value)
                    else:
                        validated_data[key] = value
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                self.logger.warning(f"Validación fallida para endpoint {endpoint}: {errors}",
                                  extra={"endpoint": endpoint, "errors": errors, "field_count": len(data)})
            
            return is_valid, validated_data, errors
            
        except Exception as e:
            self.logger.error(f"Error en validate_request: {e}")
            return False, {}, [f"Error interno de validación: {str(e)}"]

    def _extract_request_data(self) -> Dict[str, Any]:
        """Extraer datos del request actual"""
        data = {}
        
        try:
            # Datos de formulario
            if hasattr(request, 'form') and request.form:
                data.update(request.form.to_dict())
            
            # Datos JSON
            if hasattr(request, 'is_json') and request.is_json:
                json_data = request.get_json()
                if isinstance(json_data, dict):
                    data.update(json_data)
            
            # Query parameters
            if hasattr(request, 'args') and request.args:
                data.update(request.args.to_dict())
            
            # Headers importantes
            data['user_agent'] = request.headers.get('User-Agent', '')
            data['content_type'] = request.headers.get('Content-Type', '')
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos del request: {e}")
        
        return data

    def _contains_malicious_content(self, content: str) -> bool:
        """Verificar si el contenido contiene patrones maliciosos"""
        try:
            content_lower = content.lower()
            
            # Verificar patrones compilados
            for pattern in self.compiled_patterns:
                if pattern.search(content):
                    return True
            
            # Verificaciones adicionales específicas
            if self._contains_excessive_special_chars(content):
                return True
            
            if self._contains_suspicious_encoding(content):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verificando contenido malicioso: {e}")
            return False

    def _contains_excessive_special_chars(self, content: str) -> bool:
        """Detectar exceso de caracteres especiales sospechosos"""
        special_chars = r"[<>\"';\\(){}[\]|&$`]"
        special_count = len(re.findall(special_chars, content))
        
        # Si más del 20% son caracteres especiales, es sospechoso
        if len(content) > 0 and (special_count / len(content)) > 0.2:
            return True
        
        # O si hay muchos caracteres especiales seguidos
        if re.search(r"[<>\"';\\(){}[\]|&$`]{5,}", content):
            return True
        
        return False

    def _contains_suspicious_encoding(self, content: str) -> bool:
        """Detectar encoding sospechoso (ataques de encoding)"""
        # Detectar encoding URL sospechoso
        if re.search(r"%[0-9a-fA-F]{2}", content):
            # Decodificar y verificar
            try:
                import urllib.parse
                decoded = urllib.parse.unquote(content)
                if decoded != content and self._contains_malicious_content(decoded):
                    return True
            except:
                pass
        
        # Detectar encoding HTML sospechoso
        if re.search(r"&(#\d+|#x[0-9a-fA-F]+|\w+);", content):
            try:
                import html
                decoded = html.unescape(content)
                if decoded != content and self._contains_malicious_content(decoded):
                    return True
            except:
                pass
        
        return False

    # SANITIZADORES ESPECÍFICOS
    
    def _sanitize_message_content(self, content: str) -> str:
        """Sanitizar contenido de mensajes de WhatsApp"""
        if not content:
            return ""
        
        # Permitir emojis y caracteres especiales normales de WhatsApp
        # Remover solo contenido claramente malicioso
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript\s*:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized)
        
        # Limitar longitud
        return sanitized[:1000] if len(sanitized) > 1000 else sanitized

    def _sanitize_phone_number(self, phone: str) -> str:
        """Sanitizar número de teléfono"""
        if not phone:
            return ""
        
        # Mantener solo dígitos, + y prefijo whatsapp:
        sanitized = re.sub(r'[^\d\+:]', '', phone)
        
        # Restaurar prefijo whatsapp si estaba presente
        if phone.startswith('whatsapp:'):
            sanitized = 'whatsapp:' + sanitized.replace('whatsapp:', '').replace(':', '')
        
        return sanitized

    def _sanitize_email(self, email: str) -> str:
        """Sanitizar email"""
        if not email:
            return ""
        
        # Convertir a minúsculas y remover espacios
        sanitized = email.lower().strip()
        
        # Validar que tenga formato básico
        if '@' not in sanitized or '.' not in sanitized.split('@')[1]:
            return sanitized  # Será rechazado por el validador
        
        return sanitized

    def _sanitize_names(self, names: str) -> str:
        """Sanitizar nombres de huéspedes"""
        if not names:
            return ""
        
        # Mantener solo letras, espacios, comas, puntos y guiones
        sanitized = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s,.-]', '', names)
        
        # Normalizar espacios
        sanitized = re.sub(r'\s+', ' ', sanitized.strip())
        
        return sanitized

    def _sanitize_date(self, date_str: str) -> str:
        """Sanitizar fecha"""
        if not date_str:
            return ""
        
        # Mantener solo dígitos y guiones
        sanitized = re.sub(r'[^\d-]', '', str(date_str))
        
        return sanitized

    def _basic_sanitize(self, content: str) -> str:
        """Sanitización básica para campos no específicos"""
        if not content or not isinstance(content, str):
            return str(content) if content is not None else ""
        
        # Remover scripts y contenido malicioso obvio
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript\s*:', '', sanitized, flags=re.IGNORECASE)
        
        # Limitar longitud
        return sanitized[:1000] if len(sanitized) > 1000 else sanitized

    # VALIDADORES PERSONALIZADOS
    
    def _validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        try:
            validate_email(email)
            return True
        except (EmailNotValidError, ImportError):
            # Fallback a regex básico si email-validator no está disponible
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None

    def _validate_phone_number(self, phone: str) -> bool:
        """Validar número de teléfono"""
        try:
            # Extraer número sin prefijo whatsapp:
            number = phone.replace('whatsapp:', '') if phone.startswith('whatsapp:') else phone
            
            # Usar librería phonenumbers si está disponible
            try:
                parsed = phonenumbers.parse(number, None)
                return phonenumbers.is_valid_number(parsed)
            except (phonenumbers.NumberParseException, ImportError):
                # Fallback a validación básica
                # Número debe empezar con + y tener entre 10-15 dígitos
                pattern = r'^\+\d{10,15}$'
                return re.match(pattern, number) is not None
                
        except Exception as e:
            self.logger.error(f"Error validando teléfono: {e}")
            return False

    def _validate_date(self, date_str: str) -> bool:
        """Validar formato de fecha"""
        try:
            datetime.strptime(str(date_str), '%Y-%m-%d')
            
            # Verificar que la fecha no sea muy antigua o muy futura
            parsed_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
            today = date.today()
            
            # No permitir fechas muy antiguas (más de 1 año atrás)
            if parsed_date < today.replace(year=today.year - 1):
                return False
            
            # No permitir fechas muy futuras (más de 2 años adelante)
            if parsed_date > today.replace(year=today.year + 2):
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False

# Decorador para validación automática
def validate_input(endpoint: str):
    """
    Decorator para validación automática de inputs
    
    Args:
        endpoint: Nombre del endpoint para aplicar reglas específicas
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                validator = InputValidator()
                is_valid, validated_data, errors = validator.validate_request(endpoint)
                
                if not is_valid:
                    # Log errores de validación
                    logger.warning(f"Validación de input fallida para {endpoint}: {errors}",
                                 extra={
                                     "endpoint": endpoint,
                                     "errors": errors,
                                     "client_ip": g.get('security_context', {}).get('client_ip')
                                 })
                    
                    # Retornar error
                    abort(400, f"Datos de entrada inválidos: {', '.join(errors)}")
                
                # Almacenar datos validados en g para uso en la función
                g.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error en validación de input para {endpoint}: {e}")
                abort(500, "Error interno de validación")
        
        return decorated_function
    return decorator

# Función de utilidad para obtener datos validados
def get_validated_data(key: str, default: Any = None) -> Any:
    """Obtener dato validado y sanitizado"""
    if hasattr(g, 'validated_data'):
        return g.validated_data.get(key, default)
    return default

# Instancia global del validador
_global_input_validator = None

def get_input_validator() -> InputValidator:
    """Obtener instancia global del validador"""
    global _global_input_validator
    
    if _global_input_validator is None:
        _global_input_validator = InputValidator()
    
    return _global_input_validator