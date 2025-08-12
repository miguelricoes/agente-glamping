#!/usr/bin/env python3
"""
Test para validar la funcionalidad de captura de acompañantes en el agente de Glamping
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar funciones del agente
from agente import parse_reservation_details, validate_and_process_reservation_data

class TestAcompanantes:
    """Tests para validar la captura correcta de acompañantes"""
    
    def __init__(self):
        self.test_cases = [
            {
                "name": "Caso 1: Lista de nombres con comas",
                "input": """Luana mora, Carlos smith, YUSEF
Centaury
24/08/2025 hasta el 30/08/2025
Masajes
1 mascota
3203445423
tovar18025@gmail.com""",
                "expected_names": ["Luana mora", "Carlos smith", "YUSEF"],
                "expected_count": 3
            },
            {
                "name": "Caso 2: Acompañantes explícitos",
                "input": """Luana mora
Mis acompañantes son: Carlos smith y YUSEF
Centaury
24/08/2025 hasta el 30/08/2025
Masajes
1 mascota
3203445423
tovar18025@gmail.com""",
                "expected_names": ["Luana mora", "Carlos smith", "YUSEF"],
                "expected_count": 3
            },
            {
                "name": "Caso 3: Número de personas más",
                "input": """Lorena Hurtado y voy con 2 personas mas
Centaury
24/08/2025 hasta el 30/08/2025
Masajes
1 mascota
3203445423
tovar18025@gmail.com""",
                "expected_count": 3,
                "expected_names": ["Lorena Hurtado"]
            },
            {
                "name": "Caso 4: Somos X personas",
                "input": """Juan Pérez
Somos 4 personas en total
Luna
15/09/2025 hasta 18/09/2025
Spa
Sin mascotas
3001234567
juan@email.com""",
                "expected_count": 4,
                "expected_names": ["Juan Pérez"]
            },
            {
                "name": "Caso 5: Solo un nombre",
                "input": """María González
Sol
20/10/2025 hasta 22/10/2025
Cena romántica
Sin mascotas
3009876543
maria@email.com""",
                "expected_names": ["María González"],
                "expected_count": 1
            }
        ]
    
    def run_test_case(self, test_case):
        """Ejecuta un caso de test individual"""
        print(f"\n🧪 {test_case['name']}")
        print("=" * 50)
        
        try:
            # 1. Parsear datos con LLM
            print("📝 Parseando datos con LLM...")
            parsed_data = parse_reservation_details(test_case['input'])
            
            if not parsed_data:
                print("❌ FALLO: parse_reservation_details retornó None")
                return False
            
            print("✅ Parsing exitoso")
            print(f"📊 Datos parseados: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
            
            # 2. Validar y procesar datos
            print("\n🔍 Validando datos...")
            validation_success, processed_data, validation_errors = validate_and_process_reservation_data(
                parsed_data, "whatsapp:+1234567890"
            )
            
            if not validation_success:
                print(f"❌ FALLO en validación: {validation_errors}")
                return False
            
            print("✅ Validación exitosa")
            print(f"📊 Datos procesados: {json.dumps(processed_data, indent=2, ensure_ascii=False)}")
            
            # 3. Verificar resultados esperados
            print("\n🎯 Verificando resultados...")
            
            # Verificar nombres si están especificados
            if 'expected_names' in test_case:
                actual_names = processed_data.get('nombres_huespedes', [])
                expected_names = test_case['expected_names']
                
                if set(actual_names) != set(expected_names):
                    print(f"❌ FALLO en nombres:")
                    print(f"   Esperado: {expected_names}")
                    print(f"   Obtenido: {actual_names}")
                    return False
                print(f"✅ Nombres correctos: {actual_names}")
            
            # Verificar cantidad de huéspedes
            if 'expected_count' in test_case:
                actual_count = processed_data.get('cantidad_huespedes', 0)
                expected_count = test_case['expected_count']
                
                if actual_count != expected_count:
                    print(f"❌ FALLO en cantidad:")
                    print(f"   Esperado: {expected_count} huéspedes")
                    print(f"   Obtenido: {actual_count} huéspedes")
                    return False
                print(f"✅ Cantidad correcta: {actual_count} huéspedes")
            
            # Verificar campos básicos requeridos
            required_fields = ['domo', 'fecha_entrada', 'fecha_salida']
            for field in required_fields:
                if field not in processed_data or processed_data[field] == 'N/A':
                    print(f"❌ FALLO: Campo requerido '{field}' faltante o N/A")
                    return False
            print("✅ Todos los campos requeridos presentes")
            
            print(f"\n🎉 {test_case['name']} - ¡ÉXITO!")
            return True
            
        except Exception as e:
            print(f"❌ ERROR INESPERADO: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Ejecuta todos los casos de test"""
        print("🚀 INICIANDO TESTS DE ACOMPAÑANTES")
        print("=" * 70)
        
        results = []
        for test_case in self.test_cases:
            success = self.run_test_case(test_case)
            results.append({
                'name': test_case['name'],
                'success': success
            })
        
        # Resumen de resultados
        print("\n" + "=" * 70)
        print("📋 RESUMEN DE RESULTADOS")
        print("=" * 70)
        
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        for result in results:
            status = "✅ PASÓ" if result['success'] else "❌ FALLÓ"
            print(f"{status} - {result['name']}")
        
        print(f"\n🎯 RESULTADOS FINALES: {passed}/{total} tests pasaron")
        
        if passed == total:
            print("🎉 ¡TODOS LOS TESTS PASARON! La funcionalidad está correcta.")
            return True
        else:
            print("⚠️  Algunos tests fallaron. Revisar implementación.")
            return False

def main():
    """Función principal para ejecutar los tests"""
    print("🤖 Test de Funcionalidad de Acompañantes - Agente Glamping")
    print("=" * 70)
    
    # Verificar que las funciones del agente estén disponibles
    try:
        from agente import parse_reservation_details, validate_and_process_reservation_data
        print("✅ Funciones del agente importadas correctamente")
    except ImportError as e:
        print(f"❌ ERROR: No se pudieron importar las funciones del agente: {e}")
        print("💡 Asegúrate de que agente.py esté en el mismo directorio")
        return False
    
    # Ejecutar tests
    tester = TestAcompanantes()
    success = tester.run_all_tests()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)