# Routes para monitoreo de rendimiento y métricas
# Proporciona endpoints para monitorear la salud y performance del sistema

from flask import jsonify, request
from datetime import datetime
import psutil
import os
from services.performance_service import get_performance_optimizer
from services.async_llm_service import get_global_async_llm_service
from utils.logger import get_logger

logger = get_logger(__name__)

def register_performance_routes(app):
    """
    Registrar rutas de monitoreo de rendimiento
    
    Args:
        app: Instancia de Flask
    """
    
    @app.route("/performance/stats", methods=["GET"])
    def get_performance_stats():
        """Obtener estadísticas detalladas de rendimiento"""
        try:
            perf_optimizer = get_performance_optimizer()
            async_llm_service = get_global_async_llm_service()
            
            # Estadísticas del sistema
            system_stats = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.path.exists('/') else None,
                "uptime_seconds": (datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
                "process_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "open_files": len(psutil.Process().open_files()) if hasattr(psutil.Process(), 'open_files') else 0
            }
            
            # Estadísticas de rendimiento
            performance_stats = perf_optimizer.get_performance_stats()
            
            # Estadísticas de LLM asíncrono
            llm_stats = {}
            if async_llm_service:
                llm_stats = async_llm_service.get_llm_stats()
            
            return jsonify({
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_stats,
                "performance": performance_stats,
                "llm": llm_stats,
                "environment": {
                    "env": os.getenv('ENV', 'development'),
                    "port": os.getenv('PORT', '8080'),
                    "workers": os.getenv('GUNICORN_WORKERS', 'auto'),
                    "threads": os.getenv('GUNICORN_THREADS', 'auto')
                }
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de rendimiento: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    @app.route("/performance/health", methods=["GET"])
    def performance_health_check():
        """Health check específico para rendimiento"""
        try:
            perf_optimizer = get_performance_optimizer()
            async_llm_service = get_global_async_llm_service()
            
            # Verificar salud del optimizador
            perf_stats = perf_optimizer.get_performance_stats()
            cache_stats = perf_stats.get("cache_stats", {})
            
            # Verificar salud del servicio LLM asíncrono
            llm_health = {"status": "not_available"}
            if async_llm_service:
                llm_health = async_llm_service.health_check()
            
            # Verificar sistema
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Determinar estado general
            health_status = "healthy"
            issues = []
            
            if cpu_percent > 90:
                health_status = "degraded"
                issues.append("high_cpu_usage")
            
            if memory_percent > 85:
                health_status = "degraded"
                issues.append("high_memory_usage")
            
            if llm_health.get("status") == "unhealthy":
                health_status = "degraded"
                issues.append("llm_service_unhealthy")
            
            # Performance metrics
            avg_response_time = perf_stats.get("performance_metrics", {}).get("average_response_time", 0)
            if avg_response_time > 10.0:
                health_status = "degraded"
                issues.append("slow_response_times")
            
            cache_hit_rate = cache_stats.get("hit_rate", 0)
            
            return jsonify({
                "status": health_status,
                "timestamp": datetime.utcnow().isoformat(),
                "issues": issues,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "avg_response_time": avg_response_time,
                    "cache_hit_rate": cache_hit_rate,
                    "llm_health": llm_health.get("status"),
                    "total_requests": perf_stats.get("performance_metrics", {}).get("total_requests", 0)
                }
            })
            
        except Exception as e:
            logger.error(f"Error en health check de rendimiento: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    @app.route("/performance/cache/clear", methods=["POST"])
    def clear_performance_cache():
        """Limpiar cache de rendimiento (admin only)"""
        try:
            # Verificar autorización (básica)
            auth_key = request.headers.get('X-Admin-Key')
            expected_key = os.getenv('ADMIN_KEY')
            
            if not expected_key or auth_key != expected_key:
                return jsonify({
                    "status": "error",
                    "error": "Unauthorized"
                }), 401
            
            perf_optimizer = get_performance_optimizer()
            
            # Limpiar cache
            cache_stats_before = perf_optimizer.get_performance_stats().get("cache_stats", {})
            perf_optimizer.cleanup_cache(force_cleanup=True)
            cache_stats_after = perf_optimizer.get_performance_stats().get("cache_stats", {})
            
            return jsonify({
                "status": "success",
                "message": "Cache cleared successfully",
                "cache_before": {
                    "total_entries": cache_stats_before.get("total_entries", 0),
                    "cache_hits": cache_stats_before.get("cache_hits", 0)
                },
                "cache_after": {
                    "total_entries": cache_stats_after.get("total_entries", 0),
                    "cache_hits": cache_stats_after.get("cache_hits", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error limpiando cache: {e}")
            return jsonify({
                "status": "error", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    @app.route("/performance/metrics/reset", methods=["POST"])
    def reset_performance_metrics():
        """Resetear métricas de rendimiento (admin only)"""
        try:
            # Verificar autorización
            auth_key = request.headers.get('X-Admin-Key')
            expected_key = os.getenv('ADMIN_KEY')
            
            if not expected_key or auth_key != expected_key:
                return jsonify({
                    "status": "error",
                    "error": "Unauthorized"
                }), 401
            
            # Reset performance optimizer
            from services.performance_service import reset_performance_optimizer
            reset_performance_optimizer()
            
            return jsonify({
                "status": "success",
                "message": "Performance metrics reset successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error reseteando métricas: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    @app.route("/performance/concurrent-test", methods=["POST"])
    def test_concurrency():
        """Test básico de concurrencia (desarrollo/testing)"""
        try:
            # Solo permitir en desarrollo
            if os.getenv('ENV') == 'production':
                return jsonify({
                    "status": "error",
                    "error": "Not available in production"
                }), 403
            
            import time
            import concurrent.futures
            
            def dummy_task(task_id):
                time.sleep(0.1)  # Simular trabajo
                return f"Task {task_id} completed"
            
            # Ejecutar tareas concurrentes
            start_time = time.time()
            perf_optimizer = get_performance_optimizer()
            
            tasks = [{"func": dummy_task, "args": (i,), "kwargs": {}} for i in range(10)]
            results = perf_optimizer.run_multiple_in_threads(tasks, timeout=5.0)
            
            execution_time = time.time() - start_time
            successful_tasks = len([r for r in results if r])
            
            return jsonify({
                "status": "success",
                "message": "Concurrency test completed",
                "results": {
                    "total_tasks": len(tasks),
                    "successful_tasks": successful_tasks,
                    "execution_time": execution_time,
                    "tasks_per_second": len(tasks) / execution_time if execution_time > 0 else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error en test de concurrencia: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    @app.route("/performance/llm/circuit-breaker", methods=["GET"])
    def get_circuit_breaker_status():
        """Obtener estado del circuit breaker del servicio LLM"""
        try:
            async_llm_service = get_global_async_llm_service()
            
            if not async_llm_service:
                return jsonify({
                    "status": "error",
                    "error": "Async LLM service not available"
                }), 404
            
            llm_stats = async_llm_service.get_llm_stats()
            circuit_breaker = llm_stats.get("circuit_breaker", {})
            
            return jsonify({
                "status": "success",
                "circuit_breaker": circuit_breaker,
                "recommendations": {
                    "action": "monitor" if circuit_breaker.get("state") == "closed" else "investigate",
                    "health": "good" if circuit_breaker.get("failures", 0) < 3 else "degraded"
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del circuit breaker: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500

    logger.info("Performance monitoring routes registered")
    return app