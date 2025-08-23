# Middleware de seguridad para producción
# Protege contra vulnerabilidades críticas: HTTPS, inyección, logs inseguros

import os
import re
import html
import json
from datetime import datetime, timedelta
from flask import request, abort, g, current_app
from functools import wraps
from typing import Dict, Any, Optional
from collections import defaultdict
import time
import hashlib

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    print("⚠️ WARNING: bleach no disponible. Instala: pip install bleach")

from utils.logger import get_logger

logger = get_logger(__name__)

class SecurityMiddleware:
    """
    Middleware de seguridad para protección en producción
    Maneja HTTPS, sanitización, validación y logging seguro
    """

    def __init__(self, app):
        """
        Inicializar middleware de seguridad
        
        Args:
            app: Instancia de Flask
        """
        self.app = app
        self.environment = os.environ.get('ENV', 'development')
        
        # Rate limiting storage
        self.request_counts = defaultdict(lambda: {"count": 0, "window_start": time.time()})
        self.suspicious_ips = set()
        self.blocked_ips = defaultdict(float)  # IP -> block_until_timestamp
        
        # Security rules
        self.max_requests_per_minute = 60
        self.suspicious_threshold = 10  # requests per minute
        self.block_duration = 300  # 5 minutes
        
        # Hook into Flask request cycle
        app.before_request(self.security_checks)
        app.after_request(self.security_headers)
        
        # Register error handlers
        self.register_security_handlers(app)
        
        logger.info("SecurityMiddleware inicializado",
                   extra={"environment": self.environment, "component": "security_middleware"})

    def security_checks(self):
        """Verificaciones de seguridad antes de cada request"""
        try:
            request_start = time.time()
            client_ip = self.get_client_ip()
            
            # Store in g for use in other parts of the request
            g.security_context = {
                "client_ip": client_ip,
                "request_start": request_start,
                "endpoint": request.endpoint,
                "method": request.method
            }
            
            # 1. Verificar IP bloqueada
            if self.is_ip_blocked(client_ip):
                logger.warning(f"Request bloqueado de IP: {client_ip}",
                             extra={"client_ip": client_ip, "reason": "ip_blocked"})
                abort(429, "IP temporalmente bloqueada")
            
            # 2. Rate limiting
            if not self.check_rate_limit(client_ip):
                logger.warning(f"Rate limit excedido: {client_ip}",
                             extra={"client_ip": client_ip, "reason": "rate_limit_exceeded"})
                abort(429, "Rate limit excedido")
            
            # 3. Forzar HTTPS en producción
            if self.environment == 'production':
                if not self.is_secure_request():
                    logger.error(f"Request HTTP no seguro en producción: {client_ip}",
                               extra={"client_ip": client_ip, "reason": "http_not_allowed"})
                    abort(400, "HTTPS requerido en producción")
            
            # 4. Validar tamaño de request
            if request.content_length and request.content_length > 2 * 1024 * 1024:  # 2MB max
                logger.warning(f"Request demasiado grande: {request.content_length} bytes de {client_ip}",
                             extra={"client_ip": client_ip, "content_length": request.content_length})
                abort(413, "Request demasiado grande")
            
            # 5. Validaciones específicas por endpoint
            self.endpoint_specific_checks()
            
            # 6. Detectar patrones de ataque
            self.detect_attack_patterns()
            
        except Exception as e:
            # No bloquear requests por errores del middleware
            logger.error(f"Error en SecurityMiddleware: {e}",
                        extra={"component": "security_middleware"})

    def security_headers(self, response):
        """Añadir headers de seguridad a todas las respuestas"""
        try:
            if self.environment == 'production':
                # Headers críticos para producción
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
                
                # Headers adicionales
                response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
                response.headers['X-Robots-Tag'] = 'noindex, nofollow'
            
            # Headers siempre presentes
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Server'] = 'Glamping-Server'  # Ocultar servidor real
            
            # Log request completion time
            if hasattr(g, 'security_context'):
                processing_time = time.time() - g.security_context.get('request_start', time.time())
                if processing_time > 10.0:  # Log slow requests
                    logger.warning(f"Request lento: {processing_time:.2f}s desde {g.security_context.get('client_ip')}",
                                 extra={
                                     "processing_time": processing_time,
                                     "client_ip": g.security_context.get('client_ip'),
                                     "endpoint": g.security_context.get('endpoint')
                                 })
            
            return response
            
        except Exception as e:
            logger.error(f"Error añadiendo headers de seguridad: {e}")
            return response

    def get_client_ip(self) -> str:
        """Obtener IP real del cliente considerando proxies"""
        # Verificar headers de proxy en orden de preferencia
        ip_headers = [
            'HTTP_CF_CONNECTING_IP',  # Cloudflare
            'HTTP_X_FORWARDED_FOR',   # Standard proxy
            'HTTP_X_REAL_IP',         # Nginx
            'HTTP_X_FORWARDED',
            'HTTP_X_CLUSTER_CLIENT_IP',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED'
        ]
        
        for header in ip_headers:
            ip = request.environ.get(header)
            if ip:
                # Tomar primera IP si hay múltiples
                ip = ip.split(',')[0].strip()
                if self.is_valid_ip(ip):
                    return ip
        
        # Fallback a REMOTE_ADDR
        return request.environ.get('REMOTE_ADDR', '127.0.0.1')

    def is_valid_ip(self, ip: str) -> bool:
        """Validar formato de IP"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def is_secure_request(self) -> bool:
        """Verificar si el request es HTTPS"""
        # Verificar múltiples indicadores de HTTPS
        return (
            request.is_secure or
            request.environ.get('HTTP_X_FORWARDED_PROTO') == 'https' or
            request.environ.get('HTTP_X_FORWARDED_SSL') == 'on' or
            request.headers.get('X-Forwarded-Proto') == 'https'
        )

    def check_rate_limit(self, ip: str) -> bool:
        """Verificar rate limiting por IP"""
        current_time = time.time()
        
        # Limpiar ventana antigua
        if current_time - self.request_counts[ip]["window_start"] > 60:  # 1 minuto
            self.request_counts[ip]["count"] = 0
            self.request_counts[ip]["window_start"] = current_time
        
        # Incrementar contador
        self.request_counts[ip]["count"] += 1
        
        # Verificar si es sospechoso
        if self.request_counts[ip]["count"] > self.suspicious_threshold:
            self.suspicious_ips.add(ip)
            logger.warning(f"IP marcada como sospechosa: {ip}",
                         extra={"client_ip": ip, "requests_per_minute": self.request_counts[ip]["count"]})
        
        # Verificar límite
        if self.request_counts[ip]["count"] > self.max_requests_per_minute:
            # Bloquear IP temporalmente
            self.blocked_ips[ip] = current_time + self.block_duration
            logger.error(f"IP bloqueada por rate limit: {ip}",
                       extra={"client_ip": ip, "requests_per_minute": self.request_counts[ip]["count"]})
            return False
        
        return True

    def is_ip_blocked(self, ip: str) -> bool:
        """Verificar si IP está bloqueada"""
        current_time = time.time()
        
        # Limpiar IPs que ya no están bloqueadas
        expired_ips = [blocked_ip for blocked_ip, block_until in self.blocked_ips.items() 
                       if current_time > block_until]
        for expired_ip in expired_ips:
            del self.blocked_ips[expired_ip]
        
        return ip in self.blocked_ips

    def endpoint_specific_checks(self):
        """Validaciones específicas por endpoint"""
        try:
            endpoint = request.endpoint
            
            # Validaciones para webhook de WhatsApp
            if endpoint == 'whatsapp_webhook':
                self.validate_whatsapp_webhook()
            
            # Validaciones para endpoints de admin
            elif endpoint and ('admin' in endpoint or 'performance' in endpoint):
                self.validate_admin_endpoint()
            
            # Validaciones para APIs
            elif endpoint and 'api' in endpoint:
                self.validate_api_endpoint()
                
        except Exception as e:
            logger.error(f"Error en validaciones específicas de endpoint: {e}")

    def validate_whatsapp_webhook(self):
        """Validaciones específicas para webhook de WhatsApp"""
        try:
            # 1. Verificar User-Agent de Twilio
            user_agent = request.headers.get('User-Agent', '')
            if 'TwilioProxy' not in user_agent and 'Twilio' not in user_agent:
                logger.warning(f"User-Agent sospechoso en webhook: {user_agent}",
                             extra={"user_agent": user_agent, "endpoint": "whatsapp_webhook"})
                # No bloquear completamente, pero alertar
            
            # 2. Verificar que sea POST
            if request.method != 'POST':
                logger.warning(f"Método inválido para webhook: {request.method}")
                abort(405, "Método no permitido")
            
            # 3. Verificar Content-Type
            content_type = request.headers.get('Content-Type', '')
            if 'application/x-www-form-urlencoded' not in content_type:
                logger.warning(f"Content-Type inválido para webhook: {content_type}")
            
            # 4. Validar presencia de signature de Twilio
            twilio_signature = request.headers.get('X-Twilio-Signature')
            if not twilio_signature:
                logger.error("Signature de Twilio faltante",
                           extra={"client_ip": g.security_context.get("client_ip")})
                # El decorator validate_twilio_signature manejará la validación
            
        except Exception as e:
            logger.error(f"Error validando webhook de WhatsApp: {e}")

    def validate_admin_endpoint(self):
        """Validaciones para endpoints de administración"""
        try:
            # Verificar autenticación básica
            admin_key = request.headers.get('X-Admin-Key')
            expected_key = os.environ.get('ADMIN_KEY')
            
            if request.method in ['POST', 'PUT', 'DELETE']:
                if not admin_key or not expected_key:
                    logger.error("Intento de acceso admin sin credenciales",
                               extra={"client_ip": g.security_context.get("client_ip")})
                    abort(401, "Credenciales requeridas")
        
        except Exception as e:
            logger.error(f"Error validando endpoint admin: {e}")

    def validate_api_endpoint(self):
        """Validaciones para endpoints de API"""
        try:
            # Verificar JSON válido para requests con body
            if request.method in ['POST', 'PUT'] and request.is_json:
                try:
                    request.get_json()
                except Exception:
                    logger.warning("JSON inválido recibido",
                                 extra={"client_ip": g.security_context.get("client_ip")})
                    abort(400, "JSON inválido")
        
        except Exception as e:
            logger.error(f"Error validando endpoint API: {e}")

    def detect_attack_patterns(self):
        """Detectar patrones de ataque comunes"""
        try:
            # Obtener datos del request
            path = request.path.lower()
            query_string = request.query_string.decode('utf-8', errors='ignore').lower()
            user_agent = request.headers.get('User-Agent', '').lower()
            
            suspicious_patterns = [
                # SQL Injection
                "' or '1'='1", "union select", "drop table", "insert into",
                # XSS
                "<script>", "javascript:", "onerror=", "onload=",
                # Path traversal
                "../", "..\\", "/etc/passwd", "/windows/system32",
                # Command injection
                "; cat ", "; ls ", "| whoami", "&& dir"
            ]
            
            # Verificar patrones sospechosos
            all_content = f"{path} {query_string} {user_agent}"
            for pattern in suspicious_patterns:
                if pattern in all_content:
                    client_ip = g.security_context.get("client_ip")
                    logger.error(f"Patrón de ataque detectado: {pattern} desde {client_ip}",
                               extra={
                                   "client_ip": client_ip,
                                   "attack_pattern": pattern,
                                   "path": path[:100],  # Limitar longitud
                                   "user_agent": user_agent[:100]
                               })
                    
                    # Marcar IP como altamente sospechosa
                    self.suspicious_ips.add(client_ip)
                    
                    # Para ataques muy obvios, bloquear inmediatamente
                    if any(dangerous in pattern for dangerous in ['drop table', '/etc/passwd', '<script>']):
                        self.blocked_ips[client_ip] = time.time() + self.block_duration * 2  # Bloqueo más largo
                        abort(403, "Actividad maliciosa detectada")
        
        except Exception as e:
            logger.error(f"Error detectando patrones de ataque: {e}")

    def register_security_handlers(self, app):
        """Registrar handlers de errores de seguridad"""
        
        @app.errorhandler(400)
        def handle_bad_request(error):
            logger.warning(f"Bad request: {error}",
                          extra={"client_ip": g.get('security_context', {}).get('client_ip')})
            return {"error": "Bad request", "code": 400}, 400
        
        @app.errorhandler(401)
        def handle_unauthorized(error):
            logger.warning(f"Unauthorized access attempt: {error}",
                          extra={"client_ip": g.get('security_context', {}).get('client_ip')})
            return {"error": "Unauthorized", "code": 401}, 401
        
        @app.errorhandler(403)
        def handle_forbidden(error):
            logger.error(f"Forbidden access: {error}",
                        extra={"client_ip": g.get('security_context', {}).get('client_ip')})
            return {"error": "Forbidden", "code": 403}, 403
        
        @app.errorhandler(413)
        def handle_too_large(error):
            logger.warning(f"Request too large: {error}",
                          extra={"client_ip": g.get('security_context', {}).get('client_ip')})
            return {"error": "Request too large", "code": 413}, 413
        
        @app.errorhandler(429)
        def handle_rate_limit(error):
            logger.warning(f"Rate limit exceeded: {error}",
                          extra={"client_ip": g.get('security_context', {}).get('client_ip')})
            return {"error": "Rate limit exceeded", "code": 429}, 429

    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """
        Sanitizar input del usuario
        
        Args:
            text: Texto a sanitizar
            max_length: Longitud máxima permitida
            
        Returns:
            str: Texto sanitizado
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remover HTML/scripts usando bleach si está disponible
        if BLEACH_AVAILABLE:
            cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)
        else:
            # Fallback básico
            cleaned = html.escape(text, quote=True)
        
        # Remover caracteres peligrosos adicionales
        cleaned = re.sub(r'[<>"\';\\`]', '', cleaned)
        
        # Remover caracteres de control
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        # Normalizar espacios
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        
        # Limitar longitud
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
            
        return cleaned

    @staticmethod
    def sanitize_phone_number(phone: str) -> str:
        """Sanitizar número de teléfono para logging"""
        if not phone or len(phone) < 4:
            return "[REDACTED]"
        
        # Mantener prefijo de país y últimos 2 dígitos
        if phone.startswith('whatsapp:+'):
            # whatsapp:+57xxxxxxxxx -> whatsapp:+57****xx
            return phone[:13] + '*' * (len(phone) - 15) + phone[-2:] if len(phone) > 15 else phone[:13] + "**"
        else:
            # +57xxxxxxxxx -> +57****xx
            return phone[:5] + '*' * (len(phone) - 7) + phone[-2:] if len(phone) > 7 else phone[:3] + "**"

    @staticmethod
    def secure_log_data(data: dict) -> dict:
        """
        Sanitizar datos para logs seguros
        
        Args:
            data: Diccionario con datos a logear
            
        Returns:
            dict: Datos sanitizados para logging seguro
        """
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = [
            'password', 'token', 'key', 'secret', 'api_key', 'auth_token',
            'phone', 'telephone', 'numero', 'whatsapp', 'email', 'mail',
            'nombre', 'name', 'address', 'direccion', 'location'
        ]
        
        secure_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Verificar si es una clave sensible
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_keys)
            
            if is_sensitive:
                if isinstance(value, str):
                    if 'phone' in key_lower or 'whatsapp' in key_lower or 'numero' in key_lower:
                        secure_data[key] = SecurityMiddleware.sanitize_phone_number(value)
                    elif len(value) > 4:
                        secure_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                    else:
                        secure_data[key] = '[REDACTED]'
                else:
                    secure_data[key] = '[REDACTED]'
            else:
                # Para datos no sensibles, sanitizar si es string
                if isinstance(value, str):
                    secure_data[key] = SecurityMiddleware.sanitize_input(value, max_length=200)
                elif isinstance(value, dict):
                    secure_data[key] = SecurityMiddleware.secure_log_data(value)
                elif isinstance(value, list):
                    secure_data[key] = [SecurityMiddleware.secure_log_data(item) if isinstance(item, dict) 
                                       else SecurityMiddleware.sanitize_input(str(item), max_length=100) 
                                       if isinstance(item, str) else item for item in value[:5]]  # Limitar a 5 items
                else:
                    secure_data[key] = value
        
        return secure_data

    def get_security_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de seguridad"""
        try:
            current_time = time.time()
            
            # Limpiar datos antiguos
            active_ips = len([ip for ip, data in self.request_counts.items() 
                            if current_time - data["window_start"] <= 60])
            
            blocked_ips_count = len([ip for ip, block_until in self.blocked_ips.items() 
                                   if current_time < block_until])
            
            return {
                "active_ips_last_minute": active_ips,
                "suspicious_ips": len(self.suspicious_ips),
                "blocked_ips": blocked_ips_count,
                "total_requests_tracked": sum(data["count"] for data in self.request_counts.values()),
                "environment": self.environment,
                "https_enforced": self.environment == 'production',
                "rate_limit_per_minute": self.max_requests_per_minute,
                "block_duration_seconds": self.block_duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de seguridad: {e}")
            return {"error": str(e)}

def create_security_middleware(app) -> SecurityMiddleware:
    """
    Factory function para crear SecurityMiddleware
    
    Args:
        app: Instancia de Flask
        
    Returns:
        SecurityMiddleware configurado
    """
    return SecurityMiddleware(app)

# Decorador para sanitización automática
def sanitize_request_data(f):
    """Decorator para sanitizar automáticamente datos del request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Sanitizar form data
            if hasattr(request, 'form'):
                for key in request.form.keys():
                    original_value = request.form.get(key)
                    if isinstance(original_value, str):
                        sanitized = SecurityMiddleware.sanitize_input(original_value)
                        # Note: request.form is immutable, so we store in g
                        if not hasattr(g, 'sanitized_form'):
                            g.sanitized_form = {}
                        g.sanitized_form[key] = sanitized
            
            # Sanitizar JSON data
            if hasattr(request, 'is_json') and request.is_json:
                try:
                    json_data = request.get_json()
                    if isinstance(json_data, dict):
                        g.sanitized_json = SecurityMiddleware.secure_log_data(json_data)
                except Exception as e:
                    logger.warning(f"Error sanitizando JSON data: {e}")
                    g.sanitized_json = {}
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error en sanitize_request_data decorator: {e}")
            return f(*args, **kwargs)
    
    return decorated_function

# Función de utilidad para obtener datos sanitizados
def get_sanitized_form_data(key: str, default: str = "") -> str:
    """Obtener dato sanitizado del form"""
    if hasattr(g, 'sanitized_form') and key in g.sanitized_form:
        return g.sanitized_form[key]
    return SecurityMiddleware.sanitize_input(request.form.get(key, default))

def get_sanitized_json_data() -> dict:
    """Obtener JSON data sanitizado"""
    if hasattr(g, 'sanitized_json'):
        return g.sanitized_json
    return {}