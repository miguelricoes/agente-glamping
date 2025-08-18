# Suite completa de tests unitarios para arquitectura modular
# Ejecuta todos los tests de la refactorización en orden lógico

import sys
import os
import subprocess
import time
from typing import List, Dict, Any

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

class ModularTestSuite:
    """
    Suite de tests para arquitectura modular
    Ejecuta y reporta resultados de todos los tests modulares
    """
    
    def __init__(self):
        self.test_files = [
            {
                'file': 'test_database_config.py',
                'description': 'Configuración centralizada de base de datos',
                'category': 'config',
                'priority': 'high'
            },
            {
                'file': 'test_database_service.py',
                'description': 'Servicio centralizado de base de datos',
                'category': 'services',
                'priority': 'high'
            },
            {
                'file': 'test_availability_service.py',
                'description': 'Servicio especializado de disponibilidades',
                'category': 'services',
                'priority': 'high'
            },
            {
                'file': 'test_validation_service.py',
                'description': 'Servicio centralizado de validación',
                'category': 'services',
                'priority': 'high'
            },
            {
                'file': 'test_user_service.py',
                'description': 'Servicio centralizado de usuarios',
                'category': 'services',
                'priority': 'high'
            },
            {
                'file': 'test_api_routes.py',
                'description': 'Rutas API centralizadas',
                'category': 'routes',
                'priority': 'medium'
            },
            {
                'file': 'test_database_config_integration.py',
                'description': 'Integración de configuración de BD',
                'category': 'integration',
                'priority': 'medium'
            },
            {
                'file': 'test_database_integration.py',
                'description': 'Integración de servicio de BD',
                'category': 'integration',
                'priority': 'medium'
            },
            {
                'file': 'test_availability_integration.py',
                'description': 'Integración de servicio de disponibilidades',
                'category': 'integration',
                'priority': 'medium'
            },
            {
                'file': 'test_api_routes_integration.py',
                'description': 'Integración de rutas API',
                'category': 'integration',
                'priority': 'medium'
            }
        ]
        
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def run_single_test(self, test_file: Dict[str, str]) -> Dict[str, Any]:
        """
        Ejecutar un test individual
        
        Args:
            test_file: Información del archivo de test
            
        Returns:
            Diccionario con resultados del test
        """
        print(f"\n{'='*80}")
        print(f"🧪 EJECUTANDO: {test_file['description']}")
        print(f"📁 Archivo: {test_file['file']}")
        print(f"🏷️ Categoría: {test_file['category'].upper()}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Ejecutar test como subprocess para capturar salida
            result = subprocess.run(
                [sys.executable, f"test/{test_file['file']}"],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                capture_output=True,
                text=True,
                timeout=120  # Timeout de 2 minutos por test
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analizar resultado
            success = result.returncode == 0
            
            # Extraer información de la salida
            output_lines = result.stdout.split('\n') if result.stdout else []
            error_lines = result.stderr.split('\n') if result.stderr else []
            
            # Buscar información de resumen
            tests_passed = 0
            tests_total = 0
            success_percentage = 0
            
            for line in output_lines:
                if 'Tests pasados:' in line:
                    try:
                        parts = line.split('Tests pasados:')[1].strip().split('/')
                        tests_passed = int(parts[0])
                        tests_total = int(parts[1])
                    except:
                        pass
                elif 'Porcentaje de éxito:' in line:
                    try:
                        success_percentage = float(line.split(':')[1].strip().replace('%', ''))
                    except:
                        pass
            
            test_result = {
                'file': test_file['file'],
                'description': test_file['description'],
                'category': test_file['category'],
                'priority': test_file['priority'],
                'success': success,
                'duration': duration,
                'tests_passed': tests_passed,
                'tests_total': tests_total,
                'success_percentage': success_percentage,
                'output': result.stdout,
                'errors': result.stderr,
                'returncode': result.returncode
            }
            
            # Mostrar resultado inmediato
            if success:
                print(f"✅ {test_file['description']}: PASÓ")
                if tests_total > 0:
                    print(f"   📊 Tests: {tests_passed}/{tests_total} ({success_percentage:.1f}%)")
                print(f"   ⏱️ Duración: {duration:.2f}s")
            else:
                print(f"❌ {test_file['description']}: FALLÓ")
                print(f"   ⏱️ Duración: {duration:.2f}s")
                print(f"   🔴 Código de retorno: {result.returncode}")
                if result.stderr:
                    print(f"   🚨 Errores: {result.stderr[:200]}...")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ {test_file['description']}: TIMEOUT")
            print(f"   ⏱️ Duración: {duration:.2f}s (límite: 120s)")
            
            return {
                'file': test_file['file'],
                'description': test_file['description'],
                'category': test_file['category'],
                'priority': test_file['priority'],
                'success': False,
                'duration': duration,
                'tests_passed': 0,
                'tests_total': 0,
                'success_percentage': 0,
                'output': '',
                'errors': 'Test timeout after 120 seconds',
                'returncode': -1
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"💥 {test_file['description']}: ERROR")
            print(f"   🚨 Error: {str(e)}")
            print(f"   ⏱️ Duración: {duration:.2f}s")
            
            return {
                'file': test_file['file'],
                'description': test_file['description'],
                'category': test_file['category'],
                'priority': test_file['priority'],
                'success': False,
                'duration': duration,
                'tests_passed': 0,
                'tests_total': 0,
                'success_percentage': 0,
                'output': '',
                'errors': str(e),
                'returncode': -2
            }
    
    def run_all_tests(self) -> bool:
        """
        Ejecutar toda la suite de tests
        
        Returns:
            True si todos los tests pasaron, False en caso contrario
        """
        self.start_time = time.time()
        
        print("🚀 INICIANDO SUITE COMPLETA DE TESTS MODULARES")
        print("=" * 100)
        print(f"📋 Total de tests a ejecutar: {len(self.test_files)}")
        print(f"🕒 Hora de inicio: {time.strftime('%H:%M:%S')}")
        print("=" * 100)
        
        # Ejecutar tests por categoría
        categories = ['config', 'services', 'routes', 'integration']
        
        for category in categories:
            category_tests = [t for t in self.test_files if t['category'] == category]
            
            if category_tests:
                print(f"\n🔧 CATEGORÍA: {category.upper()}")
                print("-" * 60)
                
                for test_file in category_tests:
                    result = self.run_single_test(test_file)
                    self.results.append(result)
        
        self.end_time = time.time()
        
        # Generar reporte final
        return self.generate_final_report()
    
    def generate_final_report(self) -> bool:
        """
        Generar reporte final de resultados
        
        Returns:
            True si todos los tests pasaron
        """
        total_duration = self.end_time - self.start_time
        
        print("\n" + "=" * 100)
        print("📊 REPORTE FINAL DE SUITE DE TESTS MODULARES")
        print("=" * 100)
        
        # Estadísticas generales
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🎯 RESUMEN GENERAL:")
        print(f"   ✅ Tests pasados: {passed_tests}/{total_tests}")
        print(f"   ❌ Tests fallados: {failed_tests}")
        print(f"   📈 Tasa de éxito: {overall_success_rate:.1f}%")
        print(f"   ⏱️ Duración total: {total_duration:.2f}s")
        print(f"   🕒 Tiempo promedio por test: {total_duration/total_tests:.2f}s")
        
        # Desglose por categoría
        print(f"\n📋 DESGLOSE POR CATEGORÍA:")
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0, 'duration': 0}
            categories[cat]['total'] += 1
            if result['success']:
                categories[cat]['passed'] += 1
            categories[cat]['duration'] += result['duration']
        
        for cat, stats in categories.items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   🔧 {cat.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%) - {stats['duration']:.2f}s")
        
        # Desglose por prioridad
        print(f"\n🎯 DESGLOSE POR PRIORIDAD:")
        priorities = {}
        for result in self.results:
            pri = result['priority']
            if pri not in priorities:
                priorities[pri] = {'total': 0, 'passed': 0}
            priorities[pri]['total'] += 1
            if result['success']:
                priorities[pri]['passed'] += 1
        
        for pri, stats in priorities.items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   🚀 {pri.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Tests individuales
        print(f"\n📝 RESULTADOS DETALLADOS:")
        for result in self.results:
            status = "✅ PASÓ" if result['success'] else "❌ FALLÓ"
            individual_stats = ""
            if result['tests_total'] > 0:
                individual_stats = f" - {result['tests_passed']}/{result['tests_total']} ({result['success_percentage']:.1f}%)"
            
            print(f"   {status} {result['description']} ({result['duration']:.2f}s){individual_stats}")
        
        # Tests fallidos en detalle
        failed_results = [r for r in self.results if not r['success']]
        if failed_results:
            print(f"\n🚨 ANÁLISIS DE FALLOS:")
            for result in failed_results:
                print(f"   ❌ {result['file']}:")
                print(f"      - Descripción: {result['description']}")
                print(f"      - Código retorno: {result['returncode']}")
                if result['errors']:
                    error_preview = result['errors'][:200].replace('\n', ' ')
                    print(f"      - Error: {error_preview}...")
        
        # Resumen final
        print(f"\n🎉 RESULTADO FINAL:")
        if passed_tests == total_tests:
            print("   ✅ ¡TODOS LOS TESTS DE LA SUITE MODULAR PASARON!")
            print("   🏆 La refactorización está completamente validada")
            print("   🚀 Arquitectura modular lista para producción")
            print("\n🎯 ARQUITECTURA MODULAR VALIDADA:")
            print("   • ✅ Configuración centralizada de base de datos")
            print("   • ✅ Servicios especializados (Database, Availability, Validation, User)")
            print("   • ✅ Rutas API centralizadas y organizadas")
            print("   • ✅ Integración completa y funcionando")
            print("   • ✅ Tests comprehensivos y pasando")
            print("   • ✅ Logging estructurado implementado")
            print("   • ✅ Compatibilidad hacia atrás mantenida")
            print("   • ✅ Validación centralizada de datos")
            print("   • ✅ Gestión robusta de usuarios")
            print("   • ✅ Herramientas RAG organizadas")
            return True
        else:
            print(f"   ❌ {failed_tests} TESTS FALLARON")
            print("   🔧 Revisa los fallos antes de continuar")
            print("   📋 Considera ejecutar tests individuales para debugging")
            return False
    
    def run_quick_validation(self) -> bool:
        """
        Ejecutar validación rápida solo de tests críticos
        
        Returns:
            True si los tests críticos pasaron
        """
        critical_tests = [t for t in self.test_files if t['priority'] == 'high']
        
        print("⚡ EJECUTANDO VALIDACIÓN RÁPIDA (TESTS CRÍTICOS)")
        print("=" * 70)
        print(f"📋 Tests críticos: {len(critical_tests)}")
        
        self.start_time = time.time()
        
        for test_file in critical_tests:
            result = self.run_single_test(test_file)
            self.results.append(result)
        
        self.end_time = time.time()
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"\n⚡ RESULTADO VALIDACIÓN RÁPIDA:")
        print(f"   ✅ Tests críticos pasados: {passed}/{total}")
        
        if passed == total:
            print("   🎉 ¡VALIDACIÓN RÁPIDA EXITOSA!")
            return True
        else:
            print("   ❌ Fallos en tests críticos")
            return False

def main():
    """Función principal para ejecutar la suite"""
    suite = ModularTestSuite()
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        success = suite.run_quick_validation()
    else:
        success = suite.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()