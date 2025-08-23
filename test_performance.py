#!/usr/bin/env python3
"""
Script de testing de rendimiento y concurrencia
Valida las optimizaciones implementadas y detecta cuellos de botella
"""

import asyncio
import time
import concurrent.futures
import threading
import requests
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.performance_service import get_performance_optimizer, performance_monitor
from services.async_llm_service import create_async_llm_service
from utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceTester:
    """Tester para validar optimizaciones de rendimiento"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.perf_optimizer = get_performance_optimizer()
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {}
        }
    
    def test_cache_performance(self) -> Dict[str, Any]:
        """Test de rendimiento del cache"""
        logger.info("🧪 Testing cache performance...")
        
        try:
            test_queries = [
                "¿Qué es Brillo de Luna?",
                "¿Cuáles son los servicios incluidos?",
                "¿Dónde están ubicados?",
                "¿Qué actividades hay disponibles?",
                "¿Cuál es la política de cancelación?"
            ]
            
            # Test 1: Cache misses (primera vez)
            miss_times = []
            for query in test_queries:
                start_time = time.time()
                cache_key = self.perf_optimizer.generate_cache_key(query)
                
                # Simular respuesta y cachearla
                fake_response = f"Respuesta simulada para: {query}"
                self.perf_optimizer.cache_response(cache_key, fake_response)
                
                miss_times.append(time.time() - start_time)
            
            # Test 2: Cache hits (segunda vez)
            hit_times = []
            for query in test_queries:
                start_time = time.time()
                cache_key = self.perf_optimizer.generate_cache_key(query)
                cached_response = self.perf_optimizer.get_cached_response(cache_key)
                hit_times.append(time.time() - start_time)
                
                if not cached_response:
                    raise Exception(f"Cache miss unexpectado para: {query}")
            
            avg_miss_time = statistics.mean(miss_times) * 1000  # ms
            avg_hit_time = statistics.mean(hit_times) * 1000   # ms
            speedup = avg_miss_time / avg_hit_time if avg_hit_time > 0 else float('inf')
            
            return {
                "status": "PASS",
                "cache_miss_avg_ms": avg_miss_time,
                "cache_hit_avg_ms": avg_hit_time,
                "speedup_factor": speedup,
                "test_queries_count": len(test_queries),
                "all_hits_successful": all(hit_times),
                "performance_improvement": f"{((speedup - 1) * 100):.1f}%" if speedup != float('inf') else "∞"
            }
            
        except Exception as e:
            logger.error(f"Error en test de cache: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    def test_concurrent_processing(self, num_tasks: int = 10) -> Dict[str, Any]:
        """Test de procesamiento concurrente"""
        logger.info(f"🧪 Testing concurrent processing with {num_tasks} tasks...")
        
        try:
            def simulate_llm_task(task_id: int) -> Dict[str, Any]:
                """Simular tarea pesada de LLM"""
                start_time = time.time()
                
                # Simular trabajo pesado
                time.sleep(0.5)  # Simular latencia de OpenAI
                
                # Usar performance optimizer
                cache_key = self.perf_optimizer.generate_cache_key(f"task_{task_id}")
                response = f"Respuesta simulada para tarea {task_id}"
                self.perf_optimizer.cache_response(cache_key, response)
                
                processing_time = time.time() - start_time
                return {
                    "task_id": task_id,
                    "processing_time": processing_time,
                    "success": True
                }
            
            # Test 1: Procesamiento secuencial (baseline)
            sequential_start = time.time()
            sequential_results = []
            for i in range(min(num_tasks, 5)):  # Solo 5 para no demorar mucho
                result = simulate_llm_task(i)
                sequential_results.append(result)
            sequential_time = time.time() - sequential_start
            
            # Test 2: Procesamiento concurrente
            concurrent_start = time.time()
            tasks = [
                {"func": simulate_llm_task, "args": (i,), "kwargs": {}} 
                for i in range(num_tasks)
            ]
            
            concurrent_results = self.perf_optimizer.run_multiple_in_threads(
                tasks, 
                timeout=30.0
            )
            concurrent_time = time.time() - concurrent_start
            
            successful_concurrent = len([r for r in concurrent_results if r and r.get("success")])
            successful_sequential = len([r for r in sequential_results if r and r.get("success")])
            
            # Calcular métricas
            sequential_throughput = len(sequential_results) / sequential_time if sequential_time > 0 else 0
            concurrent_throughput = successful_concurrent / concurrent_time if concurrent_time > 0 else 0
            
            throughput_improvement = (concurrent_throughput / sequential_throughput - 1) * 100 if sequential_throughput > 0 else 0
            
            return {
                "status": "PASS" if successful_concurrent >= num_tasks * 0.8 else "FAIL",
                "sequential_time": sequential_time,
                "concurrent_time": concurrent_time,
                "sequential_throughput": sequential_throughput,
                "concurrent_throughput": concurrent_throughput,
                "throughput_improvement_percent": throughput_improvement,
                "tasks_completed": successful_concurrent,
                "tasks_total": num_tasks,
                "success_rate": (successful_concurrent / num_tasks) * 100,
                "concurrency_effective": concurrent_time < (sequential_time * 0.7)  # Al menos 30% mejora
            }
            
        except Exception as e:
            logger.error(f"Error en test de concurrencia: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    def test_performance_monitoring(self) -> Dict[str, Any]:
        """Test del sistema de monitoreo de rendimiento"""
        logger.info("🧪 Testing performance monitoring...")
        
        try:
            @performance_monitor
            def monitored_function(duration: float):
                """Función con monitoreo de rendimiento"""
                time.sleep(duration)
                return f"Completed in {duration}s"
            
            # Test funciones de diferentes duraciones
            test_durations = [0.1, 0.5, 1.0, 2.0]
            results = []
            
            for duration in test_durations:
                start = time.time()
                result = monitored_function(duration)
                actual_duration = time.time() - start
                results.append({
                    "expected_duration": duration,
                    "actual_duration": actual_duration,
                    "result": result,
                    "monitoring_overhead": actual_duration - duration
                })
            
            # Verificar estadísticas del optimizador
            stats = self.perf_optimizer.get_performance_stats()
            
            avg_overhead = statistics.mean([r["monitoring_overhead"] for r in results])
            
            return {
                "status": "PASS" if avg_overhead < 0.1 else "FAIL",  # Overhead < 100ms
                "test_functions_executed": len(results),
                "average_monitoring_overhead": avg_overhead,
                "performance_stats_available": bool(stats),
                "stats_keys": list(stats.keys()) if stats else [],
                "monitoring_working": all(r["actual_duration"] >= r["expected_duration"] for r in results)
            }
            
        except Exception as e:
            logger.error(f"Error en test de monitoreo: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    def test_api_endpoints_performance(self) -> Dict[str, Any]:
        """Test de rendimiento de endpoints API (si la app está corriendo)"""
        logger.info("🧪 Testing API endpoints performance...")
        
        try:
            test_endpoints = [
                {"path": "/health", "expected_max_time": 1.0},
                {"path": "/performance/health", "expected_max_time": 2.0},
                {"path": "/performance/stats", "expected_max_time": 3.0}
            ]
            
            endpoint_results = []
            
            for endpoint in test_endpoints:
                url = f"{self.base_url}{endpoint['path']}"
                
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=5.0)
                    response_time = time.time() - start_time
                    
                    endpoint_results.append({
                        "endpoint": endpoint['path'],
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "expected_max_time": endpoint['expected_max_time'],
                        "within_expected": response_time <= endpoint['expected_max_time'],
                        "available": True
                    })
                    
                except requests.exceptions.ConnectionError:
                    endpoint_results.append({
                        "endpoint": endpoint['path'],
                        "available": False,
                        "error": "Connection refused - app not running"
                    })
                except Exception as e:
                    endpoint_results.append({
                        "endpoint": endpoint['path'],
                        "available": False,
                        "error": str(e)
                    })
            
            available_endpoints = [r for r in endpoint_results if r.get("available")]
            fast_endpoints = [r for r in available_endpoints if r.get("within_expected")]
            
            if not available_endpoints:
                return {
                    "status": "SKIP",
                    "reason": "Application not running - endpoints not available",
                    "tested_endpoints": len(test_endpoints)
                }
            
            return {
                "status": "PASS" if len(fast_endpoints) >= len(available_endpoints) * 0.8 else "FAIL",
                "endpoints_tested": len(test_endpoints),
                "endpoints_available": len(available_endpoints),
                "endpoints_within_expected_time": len(fast_endpoints),
                "average_response_time": statistics.mean([r["response_time"] for r in available_endpoints]),
                "endpoint_results": endpoint_results
            }
            
        except Exception as e:
            logger.error(f"Error en test de endpoints: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test de uso de memoria durante operaciones intensivas"""
        logger.info("🧪 Testing memory usage...")
        
        try:
            import psutil
            process = psutil.Process()
            
            # Memoria inicial
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Operaciones intensivas de cache
            large_data = []
            for i in range(100):
                cache_key = self.perf_optimizer.generate_cache_key(f"large_data_{i}")
                large_response = "X" * 1000  # 1KB de datos
                self.perf_optimizer.cache_response(cache_key, large_response)
                large_data.append(cache_key)
            
            # Memoria después de operaciones
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Limpiar cache
            self.perf_optimizer.cleanup_cache(force_cleanup=True)
            
            # Memoria después de limpieza
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_increase = peak_memory - initial_memory
            memory_recovered = peak_memory - final_memory
            
            return {
                "status": "PASS" if memory_increase < 50 else "WARNING",  # < 50MB increase
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "memory_recovered_mb": memory_recovered,
                "cache_entries_created": len(large_data),
                "memory_efficiency": "good" if memory_increase < 20 else "needs_improvement"
            }
            
        except ImportError:
            return {
                "status": "SKIP",
                "reason": "psutil not available"
            }
        except Exception as e:
            logger.error(f"Error en test de memoria: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests de rendimiento"""
        logger.info("🚀 Iniciando suite completa de tests de rendimiento...")
        
        test_methods = [
            ("cache_performance", self.test_cache_performance),
            ("concurrent_processing", self.test_concurrent_processing),
            ("performance_monitoring", self.test_performance_monitoring),
            ("api_endpoints_performance", self.test_api_endpoints_performance),
            ("memory_usage", self.test_memory_usage)
        ]
        
        for test_name, test_method in test_methods:
            logger.info(f"Ejecutando test: {test_name}")
            try:
                self.results["tests"][test_name] = test_method()
            except Exception as e:
                logger.error(f"Error en test {test_name}: {e}")
                self.results["tests"][test_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
        
        # Calcular resumen
        total_tests = len(self.results["tests"])
        passed_tests = len([t for t in self.results["tests"].values() if t.get("status") == "PASS"])
        failed_tests = len([t for t in self.results["tests"].values() if t.get("status") == "FAIL"])
        skipped_tests = len([t for t in self.results["tests"].values() if t.get("status") == "SKIP"])
        error_tests = len([t for t in self.results["tests"].values() if t.get("status") == "ERROR"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "errors": error_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_status": "PASS" if failed_tests == 0 and error_tests == 0 else "FAIL"
        }
        
        return self.results
    
    def generate_report(self) -> str:
        """Generar reporte legible de los tests"""
        results = self.results
        summary = results.get("summary", {})
        
        report = f"""
🚀 REPORTE DE TESTS DE RENDIMIENTO
{'='*50}

🕐 Timestamp: {results.get('timestamp')}

📊 RESUMEN GENERAL
{'-'*30}
Total Tests: {summary.get('total_tests', 0)}
✅ Aprobados: {summary.get('passed', 0)}
❌ Fallidos: {summary.get('failed', 0)}
⏭️  Omitidos: {summary.get('skipped', 0)}
💥 Errores: {summary.get('errors', 0)}
📈 Tasa de Éxito: {summary.get('success_rate', 0):.1f}%

Estado General: {summary.get('overall_status', 'UNKNOWN')}

"""

        # Detalles de cada test
        for test_name, test_results in results.get("tests", {}).items():
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌',
                'SKIP': '⏭️',
                'ERROR': '💥',
                'WARNING': '⚠️'
            }.get(test_results.get('status'), '❓')
            
            report += f"\n{status_icon} {test_name.upper().replace('_', ' ')}: {test_results.get('status')}\n"
            
            # Métricas específicas por test
            if test_name == "cache_performance" and test_results.get("status") == "PASS":
                report += f"   Speedup: {test_results.get('speedup_factor', 0):.2f}x\n"
                report += f"   Improvement: {test_results.get('performance_improvement', '0%')}\n"
            
            elif test_name == "concurrent_processing" and test_results.get("status") == "PASS":
                report += f"   Throughput improvement: {test_results.get('throughput_improvement_percent', 0):.1f}%\n"
                report += f"   Success rate: {test_results.get('success_rate', 0):.1f}%\n"
            
            elif test_name == "memory_usage":
                report += f"   Memory increase: {test_results.get('memory_increase_mb', 0):.1f}MB\n"
                report += f"   Efficiency: {test_results.get('memory_efficiency', 'unknown')}\n"
            
            if test_results.get("error"):
                report += f"   Error: {test_results['error']}\n"
        
        return report

def main():
    """Función principal"""
    print("🧪 SUITE DE TESTS DE RENDIMIENTO")
    print("=" * 50)
    
    # Permitir especificar URL base
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    tester = PerformanceTester(base_url)
    
    try:
        # Ejecutar tests
        results = tester.run_all_tests()
        
        # Generar y mostrar reporte
        report = tester.generate_report()
        print(report)
        
        # Guardar resultados
        output_file = f"performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Resultados detallados guardados en: {output_file}")
        
        # Código de salida basado en resultados
        return 0 if results["summary"]["overall_status"] == "PASS" else 1
        
    except Exception as e:
        logger.error(f"Error ejecutando tests de rendimiento: {e}")
        print(f"\n💥 ERROR: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())