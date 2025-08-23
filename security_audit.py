#!/usr/bin/env python3
"""
Script de auditoría de seguridad para el sistema de glamping
Valida configuraciones de seguridad y detecta vulnerabilidades
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Configurar path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger
from config.security_config import get_secure_config_manager, validate_production_security

logger = get_logger(__name__)

class SecurityAuditor:
    """Auditor de seguridad para validar configuraciones y detectar vulnerabilidades"""
    
    def __init__(self):
        self.security_manager = get_secure_config_manager()
        self.audit_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv('ENV', 'development'),
            "tests": {}
        }
    
    def audit_api_key_exposure(self) -> Dict[str, Any]:
        """Auditar exposición de API keys"""
        logger.info("🔍 Auditando exposición de API keys...")
        
        try:
            # Usar el validador del security manager
            validation_results = self.security_manager.validate_api_key_security()
            
            audit_result = {
                "status": "PASS" if validation_results["security_score"] >= 70 else "FAIL",
                "security_score": validation_results["security_score"],
                "security_level": validation_results["security_level"],
                "exposed_keys": validation_results["exposed_keys"],
                "missing_keys": validation_results["missing_keys"],
                "recommendations": []
            }
            
            # Generar recomendaciones específicas
            if validation_results["exposed_keys"]:
                for exposed in validation_results["exposed_keys"]:
                    if exposed.get("severity") == "CRITICAL":
                        audit_result["recommendations"].append({
                            "priority": "CRITICAL",
                            "issue": f"API Key expuesta: {exposed['key']}",
                            "solution": "Mover a variables de entorno seguras o encriptar"
                        })
                    else:
                        audit_result["recommendations"].append({
                            "priority": "WARNING",
                            "issue": f"Posible exposición: {exposed['key']}",
                            "solution": "Verificar si está en archivo .env accesible"
                        })
            
            if validation_results["missing_keys"]:
                for missing in validation_results["missing_keys"]:
                    audit_result["recommendations"].append({
                        "priority": "HIGH",
                        "issue": f"Variable faltante: {missing['key']}",
                        "solution": f"Configurar {missing['description']}"
                    })
            
            if not validation_results["encryption_available"] and self.audit_results["environment"] == "production":
                audit_result["recommendations"].append({
                    "priority": "CRITICAL",
                    "issue": "Encriptación no disponible en producción",
                    "solution": "Instalar cryptography y configurar ENCRYPTION_KEY"
                })
            
            return audit_result
            
        except Exception as e:
            logger.error(f"Error en auditoría de API keys: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "recommendations": [{"priority": "HIGH", "issue": "Error en auditoría", "solution": "Revisar configuración del security manager"}]
            }
    
    def audit_file_permissions(self) -> Dict[str, Any]:
        """Auditar permisos de archivos críticos"""
        logger.info("🔍 Auditando permisos de archivos...")
        
        try:
            critical_files = [
                ".env",
                "config/security_config.py",
                "config/app_config.py",
                "config/database_config.py"
            ]
            
            file_issues = []
            files_checked = 0
            
            for file_path in critical_files:
                full_path = Path(file_path)
                if full_path.exists():
                    files_checked += 1
                    stat_info = full_path.stat()
                    
                    # Verificar permisos (en sistemas Unix)
                    if hasattr(stat_info, 'st_mode'):
                        mode = oct(stat_info.st_mode)[-3:]
                        
                        # .env debería tener permisos restrictivos (600)
                        if file_path == ".env" and mode != "600":
                            file_issues.append({
                                "file": file_path,
                                "issue": f"Permisos demasiado abiertos: {mode}",
                                "recommended": "600 (solo propietario)"
                            })
                        
                        # Archivos de configuración no deberían ser ejecutables
                        if file_path.endswith(".py") and int(mode[2]) % 2 == 1:
                            file_issues.append({
                                "file": file_path,
                                "issue": f"Archivo ejecutable: {mode}",
                                "recommended": "644 (lectura/escritura propietario, lectura otros)"
                            })
            
            return {
                "status": "PASS" if len(file_issues) == 0 else "WARNING",
                "files_checked": files_checked,
                "issues_found": len(file_issues),
                "file_issues": file_issues,
                "recommendations": [
                    {
                        "priority": "MEDIUM",
                        "issue": f"Problemas de permisos en {issue['file']}",
                        "solution": f"chmod {issue['recommended']} {issue['file']}"
                    } for issue in file_issues
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en auditoría de permisos: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "recommendations": []
            }
    
    def audit_docker_security(self) -> Dict[str, Any]:
        """Auditar configuración de seguridad en Docker"""
        logger.info("🔍 Auditando seguridad de Docker...")
        
        try:
            dockerfile_path = Path("Dockerfile")
            if not dockerfile_path.exists():
                return {
                    "status": "SKIP",
                    "reason": "Dockerfile no encontrado",
                    "recommendations": []
                }
            
            dockerfile_content = dockerfile_path.read_text()
            security_checks = []
            
            # Verificar usuario no-root
            if "USER appuser" in dockerfile_content or "USER " in dockerfile_content:
                security_checks.append({"check": "Non-root user", "status": "PASS"})
            else:
                security_checks.append({"check": "Non-root user", "status": "FAIL"})
            
            # Verificar health check
            if "HEALTHCHECK" in dockerfile_content:
                security_checks.append({"check": "Health check", "status": "PASS"})
            else:
                security_checks.append({"check": "Health check", "status": "FAIL"})
            
            # Verificar limpieza de cache
            if "rm -rf" in dockerfile_content and "cache" in dockerfile_content:
                security_checks.append({"check": "Cache cleanup", "status": "PASS"})
            else:
                security_checks.append({"check": "Cache cleanup", "status": "FAIL"})
            
            # Verificar variables de entorno seguras
            if "PYTHONDONTWRITEBYTECODE" in dockerfile_content:
                security_checks.append({"check": "Secure Python env", "status": "PASS"})
            else:
                security_checks.append({"check": "Secure Python env", "status": "FAIL"})
            
            failed_checks = [check for check in security_checks if check["status"] == "FAIL"]
            
            return {
                "status": "PASS" if len(failed_checks) == 0 else "WARNING",
                "checks_performed": len(security_checks),
                "checks_passed": len(security_checks) - len(failed_checks),
                "security_checks": security_checks,
                "recommendations": [
                    {
                        "priority": "MEDIUM",
                        "issue": f"Docker security check failed: {check['check']}",
                        "solution": "Actualizar Dockerfile según mejores prácticas de seguridad"
                    } for check in failed_checks
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en auditoría de Docker: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "recommendations": []
            }
    
    def audit_dependency_security(self) -> Dict[str, Any]:
        """Auditar seguridad de dependencias"""
        logger.info("🔍 Auditando seguridad de dependencias...")
        
        try:
            requirements_path = Path("requirements.txt")
            if not requirements_path.exists():
                return {
                    "status": "FAIL",
                    "reason": "requirements.txt no encontrado",
                    "recommendations": [{"priority": "HIGH", "issue": "Sin requirements.txt", "solution": "Crear archivo requirements.txt"}]
                }
            
            requirements_content = requirements_path.read_text()
            
            # Verificar dependencias de seguridad
            security_deps = {
                "cryptography": "Encriptación de datos sensibles",
                "certifi": "Certificados SSL actualizados",
                "urllib3": "HTTP seguro"
            }
            
            missing_deps = []
            found_deps = []
            
            for dep, description in security_deps.items():
                if dep in requirements_content:
                    found_deps.append({"dependency": dep, "description": description})
                else:
                    missing_deps.append({"dependency": dep, "description": description})
            
            # Verificar versiones pinneadas
            lines = [line.strip() for line in requirements_content.split('\n') if line.strip() and not line.startswith('#')]
            unpinned_versions = []
            
            for line in lines:
                if '==' not in line and '>=' in line:
                    unpinned_versions.append(line)
            
            return {
                "status": "PASS" if len(missing_deps) == 0 and len(unpinned_versions) < 3 else "WARNING",
                "security_dependencies_found": len(found_deps),
                "security_dependencies_missing": len(missing_deps),
                "unpinned_versions": len(unpinned_versions),
                "found_deps": found_deps,
                "missing_deps": missing_deps,
                "recommendations": [
                    {
                        "priority": "MEDIUM",
                        "issue": f"Dependencia de seguridad faltante: {dep['dependency']}",
                        "solution": f"Agregar {dep['dependency']} para {dep['description']}"
                    } for dep in missing_deps
                ] + [
                    {
                        "priority": "LOW",
                        "issue": f"Versión no pinneada: {dep}",
                        "solution": "Usar versión específica (==x.y.z) para mayor seguridad"
                    } for dep in unpinned_versions[:3]  # Solo mostrar primeras 3
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en auditoría de dependencias: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "recommendations": []
            }
    
    def audit_production_readiness(self) -> Dict[str, Any]:
        """Auditar preparación para producción"""
        logger.info("🔍 Auditando preparación para producción...")
        
        try:
            production_ready = validate_production_security()
            
            readiness_checks = []
            
            # Verificar variables de entorno críticas
            critical_vars = ['OPENAI_API_KEY', 'DATABASE_PRIVATE_URL', 'SECRET_KEY']
            for var in critical_vars:
                if os.getenv(var):
                    readiness_checks.append({"check": f"{var} configured", "status": "PASS"})
                else:
                    readiness_checks.append({"check": f"{var} configured", "status": "FAIL"})
            
            # Verificar entorno
            env = os.getenv('ENV', 'development')
            if env == 'production':
                readiness_checks.append({"check": "Production environment set", "status": "PASS"})
            else:
                readiness_checks.append({"check": "Production environment set", "status": "WARNING"})
            
            # Verificar encriptación
            if self.security_manager.cipher:
                readiness_checks.append({"check": "Encryption available", "status": "PASS"})
            else:
                readiness_checks.append({"check": "Encryption available", "status": "FAIL"})
            
            failed_checks = [check for check in readiness_checks if check["status"] == "FAIL"]
            warning_checks = [check for check in readiness_checks if check["status"] == "WARNING"]
            
            return {
                "status": "PASS" if len(failed_checks) == 0 else "FAIL",
                "production_ready": production_ready,
                "checks_performed": len(readiness_checks),
                "checks_passed": len(readiness_checks) - len(failed_checks) - len(warning_checks),
                "readiness_checks": readiness_checks,
                "recommendations": [
                    {
                        "priority": "CRITICAL",
                        "issue": f"Production readiness check failed: {check['check']}",
                        "solution": "Configurar variable antes del despliegue"
                    } for check in failed_checks
                ] + [
                    {
                        "priority": "HIGH",
                        "issue": f"Production readiness warning: {check['check']}",
                        "solution": "Verificar configuración para producción"
                    } for check in warning_checks
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en auditoría de producción: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "recommendations": []
            }
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Ejecutar auditoría completa de seguridad"""
        logger.info("🚀 Iniciando auditoría completa de seguridad...")
        
        # Ejecutar todas las auditorías
        self.audit_results["tests"]["api_key_exposure"] = self.audit_api_key_exposure()
        self.audit_results["tests"]["file_permissions"] = self.audit_file_permissions()
        self.audit_results["tests"]["docker_security"] = self.audit_docker_security()
        self.audit_results["tests"]["dependency_security"] = self.audit_dependency_security()
        self.audit_results["tests"]["production_readiness"] = self.audit_production_readiness()
        
        # Calcular resumen general
        total_tests = len(self.audit_results["tests"])
        passed_tests = sum(1 for test in self.audit_results["tests"].values() if test["status"] == "PASS")
        failed_tests = sum(1 for test in self.audit_results["tests"].values() if test["status"] == "FAIL")
        warning_tests = sum(1 for test in self.audit_results["tests"].values() if test["status"] == "WARNING")
        error_tests = sum(1 for test in self.audit_results["tests"].values() if test["status"] == "ERROR")
        
        # Recopilar todas las recomendaciones
        all_recommendations = []
        for test_results in self.audit_results["tests"].values():
            all_recommendations.extend(test_results.get("recommendations", []))
        
        # Agrupar recomendaciones por prioridad
        critical_recs = [r for r in all_recommendations if r.get("priority") == "CRITICAL"]
        high_recs = [r for r in all_recommendations if r.get("priority") == "HIGH"]
        medium_recs = [r for r in all_recommendations if r.get("priority") == "MEDIUM"]
        low_recs = [r for r in all_recommendations if r.get("priority") == "LOW"]
        
        # Determinar estado general
        if failed_tests > 0 or len(critical_recs) > 0:
            overall_status = "CRITICAL"
        elif warning_tests > 0 or len(high_recs) > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"
        
        self.audit_results["summary"] = {
            "overall_status": overall_status,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warning_tests": warning_tests,
            "error_tests": error_tests,
            "recommendations_by_priority": {
                "critical": len(critical_recs),
                "high": len(high_recs),
                "medium": len(medium_recs),
                "low": len(low_recs)
            },
            "security_score": ((passed_tests + (warning_tests * 0.5)) / total_tests) * 100 if total_tests > 0 else 0
        }
        
        return self.audit_results
    
    def generate_report(self) -> str:
        """Generar reporte de auditoría legible"""
        results = self.audit_results
        
        report = f"""
🔒 REPORTE DE AUDITORÍA DE SEGURIDAD
{'='*50}

🕐 Timestamp: {results['timestamp']}
🌍 Environment: {results['environment']}

📊 RESUMEN GENERAL
{'-'*30}
Estado General: {results['summary']['overall_status']}
Puntuación de Seguridad: {results['summary']['security_score']:.1f}/100

Tests Ejecutados: {results['summary']['total_tests']}
✅ Aprobados: {results['summary']['passed_tests']}
⚠️  Advertencias: {results['summary']['warning_tests']}
❌ Fallidos: {results['summary']['failed_tests']}
💥 Errores: {results['summary']['error_tests']}

🚨 RECOMENDACIONES POR PRIORIDAD
{'-'*40}
🔴 Críticas: {results['summary']['recommendations_by_priority']['critical']}
🟠 Altas: {results['summary']['recommendations_by_priority']['high']}
🟡 Medias: {results['summary']['recommendations_by_priority']['medium']}
🟢 Bajas: {results['summary']['recommendations_by_priority']['low']}

"""

        # Detalles de cada test
        for test_name, test_results in results['tests'].items():
            status_icon = {
                'PASS': '✅',
                'WARNING': '⚠️',
                'FAIL': '❌',
                'ERROR': '💥',
                'SKIP': '⏭️'
            }.get(test_results['status'], '❓')
            
            report += f"\n{status_icon} {test_name.upper().replace('_', ' ')}: {test_results['status']}\n"
            
            if test_results.get('recommendations'):
                for rec in test_results['recommendations'][:3]:  # Mostrar solo primeras 3
                    priority_icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(rec['priority'], '⚪')
                    report += f"  {priority_icon} {rec['issue']}: {rec['solution']}\n"
        
        return report

def main():
    """Función principal"""
    print("🔒 AUDITORÍA DE SEGURIDAD DEL SISTEMA GLAMPING")
    print("=" * 60)
    
    auditor = SecurityAuditor()
    
    try:
        # Ejecutar auditoría completa
        results = auditor.run_full_audit()
        
        # Generar y mostrar reporte
        report = auditor.generate_report()
        print(report)
        
        # Guardar resultados en archivo JSON
        output_file = f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte detallado guardado en: {output_file}")
        
        # Código de salida basado en el estado
        exit_code = 0
        if results['summary']['overall_status'] == 'CRITICAL':
            exit_code = 2
        elif results['summary']['overall_status'] == 'WARNING':
            exit_code = 1
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Error ejecutando auditoría: {e}")
        print(f"\n💥 ERROR: {e}")
        return 3

if __name__ == "__main__":
    sys.exit(main())