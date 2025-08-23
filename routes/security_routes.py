# Routes para auditoría y monitoreo de seguridad
# Endpoints para verificar vulnerabilidades y estado de seguridad

from flask import jsonify, request, g
from datetime import datetime
import os
import re
from typing import Dict, Any, List

from security.security_middleware import SecurityMiddleware
from security.input_validator import InputValidator, get_input_validator
from config.security_config import get_secure_config_manager, validate_production_security
from utils.logger import get_logger

logger = get_logger(__name__)

def register_security_routes(app):
    """
    Registrar rutas de auditoría de seguridad
    
    Args:
        app: Instancia de Flask
    """
    
    @app.route("/security/audit", methods=["GET"])
    def security_audit():
        """Endpoint de auditoría completa de seguridad"""
        try:
            # Verificar autorización básica
            admin_key = request.headers.get('X-Admin-Key')
            expected_key = os.environ.get('ADMIN_KEY')
            
            if not admin_key or admin_key != expected_key:
                logger.warning("Acceso no autorizado a security audit",
                             extra={"client_ip": g.get('security_context', {}).get('client_ip')})
                return jsonify({
                    "status": "error",
                    "error": "Unauthorized - Admin key required"
                }), 401
            
            # Ejecutar auditoría completa
            audit_results = run_comprehensive_security_audit()
            
            return jsonify({
                "status": "success",
                "audit_timestamp": datetime.utcnow().isoformat(),
                "environment": os.getenv('ENV', 'development'),
                "audit_results": audit_results
            })
            
        except Exception as e:
            logger.error(f"Error en auditoría de seguridad: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    @app.route("/security/vulnerabilities", methods=["GET"])
    def check_vulnerabilities():
        """Verificar vulnerabilidades específicas del sistema"""
        try:
            # Verificar autorización
            admin_key = request.headers.get('X-Admin-Key')
            expected_key = os.environ.get('ADMIN_KEY')
            
            if not admin_key or admin_key != expected_key:
                return jsonify({
                    "status": "error",
                    "error": "Unauthorized"
                }), 401
            
            # Verificar vulnerabilidades críticas
            vulnerabilities = check_critical_vulnerabilities()
            
            # Clasificar por severidad
            critical = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
            high = [v for v in vulnerabilities if v.get("severity") == "HIGH"]
            medium = [v for v in vulnerabilities if v.get("severity") == "MEDIUM"]
            
            overall_status = "CRITICAL" if critical else "HIGH" if high else "MEDIUM" if medium else "SECURE"
            
            return jsonify({
                "status": "success",
                "overall_security_status": overall_status,
                "vulnerability_count": {
                    "critical": len(critical),
                    "high": len(high),
                    "medium": len(medium),
                    "total": len(vulnerabilities)
                },
                "vulnerabilities": {
                    "critical": critical,
                    "high": high,
                    "medium": medium
                },
                "production_ready": len(critical) == 0 and len(high) == 0,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error verificando vulnerabilidades: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    @app.route("/security/config-check", methods=["GET"])
    def security_config_check():
        """Verificar configuración de seguridad"""
        try:
            # Autorización básica
            admin_key = request.headers.get('X-Admin-Key')
            expected_key = os.environ.get('ADMIN_KEY')
            
            if not admin_key or admin_key != expected_key:
                return jsonify({
                    "status": "error",
                    "error": "Unauthorized"
                }), 401
            
            # Verificar configuración de seguridad
            config_check = check_security_configuration()
            
            return jsonify({
                "status": "success",
                "config_check": config_check,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error verificando configuración de seguridad: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    @app.route("/security/middleware-stats", methods=["GET"])
    def middleware_stats():
        """Obtener estadísticas del middleware de seguridad"""
        try:
            # Obtener estadísticas del middleware si está disponible
            security_middleware = getattr(app, '_security_middleware', None)
            
            if security_middleware:
                stats = security_middleware.get_security_stats()
            else:
                stats = {"error": "Security middleware not available"}
            
            return jsonify({
                "status": "success",
                "middleware_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de middleware: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    @app.route("/security/test-input-validation", methods=["POST"])
    def test_input_validation():
        """Endpoint para probar validación de inputs (solo desarrollo)"""
        try:
            # Solo disponible en desarrollo
            if os.getenv('ENV') == 'production':
                return jsonify({
                    "status": "error",
                    "error": "Not available in production"
                }), 403
            
            # Obtener datos de prueba
            test_data = request.get_json() or {}
            endpoint_name = test_data.get('endpoint', 'whatsapp_webhook')
            test_inputs = test_data.get('inputs', {})
            
            # Validar inputs
            validator = get_input_validator()
            is_valid, validated_data, errors = validator.validate_request(endpoint_name, test_inputs)
            
            return jsonify({
                "status": "success",
                "validation_result": {
                    "is_valid": is_valid,
                    "validated_data": validated_data,
                    "errors": errors,
                    "endpoint": endpoint_name,
                    "original_inputs": test_inputs
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error probando validación de inputs: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    logger.info("Security audit routes registered")
    return app

def run_comprehensive_security_audit() -> Dict[str, Any]:
    """Ejecutar auditoría completa de seguridad"""
    try:
        audit_results = {
            "environment_variables": audit_environment_variables(),
            "file_permissions": audit_file_permissions(),
            "network_security": audit_network_security(),
            "input_validation": audit_input_validation(),
            "logging_security": audit_logging_security(),
            "dependencies": audit_dependencies(),
            "configuration": audit_configuration()
        }
        
        # Calcular score general
        total_checks = 0
        passed_checks = 0
        
        for category, results in audit_results.items():
            if isinstance(results, dict) and "checks" in results:
                total_checks += results.get("total_checks", 0)
                passed_checks += results.get("passed_checks", 0)
        
        overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        audit_results["summary"] = {
            "overall_score": overall_score,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "status": "SECURE" if overall_score >= 90 else "NEEDS_IMPROVEMENT" if overall_score >= 70 else "INSECURE"
        }
        
        return audit_results
        
    except Exception as e:
        logger.error(f"Error en auditoría completa: {e}")
        return {"error": str(e)}

def check_critical_vulnerabilities() -> List[Dict[str, Any]]:
    """Verificar vulnerabilidades críticas específicas"""
    vulnerabilities = []
    
    try:
        # 1. API Keys expuestas
        env_file_path = ".env"
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                if any(key in env_content for key in ['OPENAI_API_KEY', 'TWILIO_AUTH_TOKEN']):
                    vulnerabilities.append({
                        "id": "EXPOSED_API_KEYS",
                        "severity": "CRITICAL",
                        "title": "API Keys expuestas en archivo .env",
                        "description": "Las claves API están almacenadas en texto plano en archivo .env",
                        "impact": "Compromiso total del sistema si el archivo es accesible",
                        "remediation": "Usar variables de entorno del sistema o encriptación"
                    })
        
        # 2. Validación de firma Twilio
        try:
            from routes.whatsapp_routes import validate_twilio_signature
            has_twilio_validation = True
        except ImportError:
            vulnerabilities.append({
                "id": "MISSING_TWILIO_SIGNATURE",
                "severity": "CRITICAL", 
                "title": "Sin validación de firma Twilio",
                "description": "Los webhooks de Twilio no validan firmas",
                "impact": "Spoofing de mensajes de WhatsApp",
                "remediation": "Implementar validación de firma HMAC"
            })
        
        # 3. HTTPS no enforced
        env = os.getenv('ENV', 'development')
        if env == 'production':
            # Verificar si hay enforcement de HTTPS
            try:
                from security.security_middleware import SecurityMiddleware
                has_https_enforcement = True
            except ImportError:
                vulnerabilities.append({
                    "id": "NO_HTTPS_ENFORCEMENT",
                    "severity": "HIGH",
                    "title": "HTTPS no enforced en producción",
                    "description": "La aplicación acepta conexiones HTTP en producción",
                    "impact": "Man-in-the-middle attacks, datos interceptables",
                    "remediation": "Implementar middleware de HTTPS enforcement"
                })
        
        # 4. Rate limiting
        if not os.getenv('RATE_LIMIT_ENABLED'):
            vulnerabilities.append({
                "id": "NO_RATE_LIMITING",
                "severity": "HIGH",
                "title": "Sin rate limiting implementado",
                "description": "No hay protección contra ataques de fuerza bruta",
                "impact": "DDoS, abuso de recursos",
                "remediation": "Implementar rate limiting por IP y usuario"
            })
        
        # 5. Sanitización de inputs
        try:
            from security.input_validator import InputValidator
            validator_available = True
        except ImportError:
            vulnerabilities.append({
                "id": "NO_INPUT_SANITIZATION",
                "severity": "HIGH",
                "title": "Sin sanitización de inputs",
                "description": "Los inputs del usuario no son sanitizados",
                "impact": "XSS, inyección SQL, command injection",
                "remediation": "Implementar InputValidator completo"
            })
        
        # 6. Logging inseguro
        if not check_secure_logging():
            vulnerabilities.append({
                "id": "INSECURE_LOGGING",
                "severity": "MEDIUM",
                "title": "Logging potencialmente inseguro",
                "description": "Los logs pueden contener datos sensibles",
                "impact": "Exposición de datos personales en logs",
                "remediation": "Implementar sanitización de datos en logs"
            })
        
        # 7. Dependencias vulnerables
        vulnerable_deps = check_vulnerable_dependencies()
        if vulnerable_deps:
            vulnerabilities.append({
                "id": "VULNERABLE_DEPENDENCIES",
                "severity": "MEDIUM",
                "title": f"Dependencias vulnerables: {', '.join(vulnerable_deps)}",
                "description": "Algunas dependencias tienen vulnerabilidades conocidas",
                "impact": "Explotación de vulnerabilidades conocidas",
                "remediation": "Actualizar dependencias a versiones seguras"
            })
        
    except Exception as e:
        logger.error(f"Error verificando vulnerabilidades: {e}")
        vulnerabilities.append({
            "id": "AUDIT_ERROR",
            "severity": "HIGH",
            "title": "Error en auditoría de seguridad",
            "description": f"No se pudo completar la verificación: {str(e)}",
            "impact": "Estado de seguridad desconocido",
            "remediation": "Revisar sistema de auditoría"
        })
    
    return vulnerabilities

def check_security_configuration() -> Dict[str, Any]:
    """Verificar configuración de seguridad"""
    config_check = {
        "environment": os.getenv('ENV', 'development'),
        "https_enforced": False,
        "cors_restricted": False,
        "security_headers": False,
        "input_validation": False,
        "rate_limiting": False,
        "secure_logging": False,
        "encryption_available": False
    }
    
    try:
        # Verificar configuración de seguridad
        security_manager = get_secure_config_manager()
        
        config_check["encryption_available"] = security_manager.cipher is not None
        
        # Verificar otras configuraciones...
        env = os.getenv('ENV', 'development')
        config_check["https_enforced"] = env == 'production'
        
        # Verificar si hay middleware de seguridad
        try:
            from security.security_middleware import SecurityMiddleware
            config_check["security_headers"] = True
            config_check["rate_limiting"] = True
        except ImportError:
            pass
        
        # Verificar validación de input
        try:
            from security.input_validator import InputValidator
            config_check["input_validation"] = True
        except ImportError:
            pass
        
        config_check["secure_logging"] = check_secure_logging()
        
    except Exception as e:
        logger.error(f"Error verificando configuración: {e}")
        config_check["error"] = str(e)
    
    return config_check

def audit_environment_variables() -> Dict[str, Any]:
    """Auditar variables de entorno"""
    critical_vars = ['OPENAI_API_KEY', 'TWILIO_AUTH_TOKEN', 'DATABASE_PRIVATE_URL']
    optional_vars = ['ADMIN_KEY', 'ENCRYPTION_KEY', 'SECRET_KEY']
    
    checks = []
    for var in critical_vars:
        value = os.getenv(var)
        checks.append({
            "variable": var,
            "configured": value is not None,
            "exposed_in_env_file": check_if_in_env_file(var),
            "critical": True
        })
    
    for var in optional_vars:
        value = os.getenv(var)
        checks.append({
            "variable": var,
            "configured": value is not None,
            "exposed_in_env_file": check_if_in_env_file(var),
            "critical": False
        })
    
    total_checks = len(checks)
    passed_checks = len([c for c in checks if c["configured"] and not c["exposed_in_env_file"]])
    
    return {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "checks": checks
    }

def check_if_in_env_file(var_name: str) -> bool:
    """Verificar si variable está en archivo .env"""
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                content = f.read()
                return var_name in content
    except Exception:
        pass
    return False

def audit_file_permissions() -> Dict[str, Any]:
    """Auditar permisos de archivos críticos"""
    critical_files = ['.env', 'config/', 'security/']
    checks = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                import stat
                file_stat = os.stat(file_path)
                mode = stat.filemode(file_stat.st_mode)
                
                checks.append({
                    "file": file_path,
                    "exists": True,
                    "permissions": mode,
                    "secure": not (file_stat.st_mode & stat.S_IROTH or file_stat.st_mode & stat.S_IWOTH)
                })
            except Exception as e:
                checks.append({
                    "file": file_path,
                    "exists": True,
                    "error": str(e)
                })
        else:
            checks.append({
                "file": file_path,
                "exists": False
            })
    
    passed_checks = len([c for c in checks if c.get("secure", False) or not c.get("exists", True)])
    
    return {
        "total_checks": len(checks),
        "passed_checks": passed_checks,
        "checks": checks
    }

def audit_network_security() -> Dict[str, Any]:
    """Auditar seguridad de red"""
    checks = []
    
    # Verificar configuración HTTPS
    env = os.getenv('ENV', 'development')
    checks.append({
        "check": "HTTPS_ENFORCEMENT",
        "passed": env == 'production',
        "description": "HTTPS enforced in production"
    })
    
    # Verificar CORS
    cors_origin = os.getenv('CORS_ORIGIN')
    checks.append({
        "check": "CORS_RESTRICTED",
        "passed": cors_origin is not None,
        "description": "CORS origins restricted"
    })
    
    passed_checks = len([c for c in checks if c["passed"]])
    
    return {
        "total_checks": len(checks),
        "passed_checks": passed_checks,
        "checks": checks
    }

def audit_input_validation() -> Dict[str, Any]:
    """Auditar validación de inputs"""
    checks = []
    
    try:
        from security.input_validator import InputValidator
        validator = InputValidator()
        
        checks.append({
            "check": "INPUT_VALIDATOR_AVAILABLE",
            "passed": True,
            "description": "Input validator is implemented"
        })
        
        # Test básico de validación
        test_result = validator._contains_malicious_content("<script>alert('xss')</script>")
        checks.append({
            "check": "XSS_DETECTION",
            "passed": test_result,
            "description": "XSS content detection works"
        })
        
    except ImportError:
        checks.append({
            "check": "INPUT_VALIDATOR_AVAILABLE",
            "passed": False,
            "description": "Input validator is not implemented"
        })
    
    passed_checks = len([c for c in checks if c["passed"]])
    
    return {
        "total_checks": len(checks),
        "passed_checks": passed_checks,
        "checks": checks
    }

def audit_logging_security() -> Dict[str, Any]:
    """Auditar seguridad de logging"""
    checks = []
    
    secure_logging = check_secure_logging()
    checks.append({
        "check": "SECURE_LOGGING",
        "passed": secure_logging,
        "description": "Secure logging implementation available"
    })
    
    return {
        "total_checks": len(checks),
        "passed_checks": len([c for c in checks if c["passed"]]),
        "checks": checks
    }

def audit_dependencies() -> Dict[str, Any]:
    """Auditar dependencias"""
    checks = []
    
    vulnerable_deps = check_vulnerable_dependencies()
    checks.append({
        "check": "NO_VULNERABLE_DEPENDENCIES",
        "passed": len(vulnerable_deps) == 0,
        "description": f"Vulnerable dependencies: {vulnerable_deps}"
    })
    
    return {
        "total_checks": len(checks),
        "passed_checks": len([c for c in checks if c["passed"]]),
        "checks": checks
    }

def audit_configuration() -> Dict[str, Any]:
    """Auditar configuración general"""
    checks = []
    
    # Verificar production readiness
    production_ready = validate_production_security()
    checks.append({
        "check": "PRODUCTION_READY",
        "passed": production_ready,
        "description": "System ready for production deployment"
    })
    
    return {
        "total_checks": len(checks),
        "passed_checks": len([c for c in checks if c["passed"]]),
        "checks": checks
    }

def check_secure_logging() -> bool:
    """Verificar si hay logging seguro implementado"""
    try:
        from security.security_middleware import SecurityMiddleware
        # Si puede importar, asumimos que tiene logging seguro
        return hasattr(SecurityMiddleware, 'secure_log_data')
    except ImportError:
        return False

def check_vulnerable_dependencies() -> List[str]:
    """Verificar dependencias vulnerables (básico)"""
    # Esta es una implementación básica
    # En un sistema real, usarías herramientas como safety o snyk
    vulnerable = []
    
    try:
        import pkg_resources
        installed_packages = [d for d in pkg_resources.working_set]
        
        # Lista básica de versiones vulnerables conocidas
        known_vulnerabilities = {
            'werkzeug': ['0.15.0', '0.16.0'],  # Ejemplo
            'flask': ['1.0.0'],  # Ejemplo
        }
        
        for package in installed_packages:
            package_name = package.project_name.lower()
            if package_name in known_vulnerabilities:
                if package.version in known_vulnerabilities[package_name]:
                    vulnerable.append(f"{package_name}=={package.version}")
    
    except Exception:
        pass
    
    return vulnerable