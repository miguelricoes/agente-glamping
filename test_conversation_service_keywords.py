#!/usr/bin/env python3
"""
Test para verificar que las nuevas funciones de keywords en conversation_service funcionan
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_menu_keyword_functions():
    """Test las nuevas funciones de detección y conversión de keywords"""
    
    try:
        # Importar las nuevas funciones
        from services.conversation_service import is_menu_keyword, convert_keyword_to_menu_number
        
        print("=== TEST: Funciones de Menu Keywords ===")
        
        # Test 1: is_menu_keyword
        test_cases_keyword = [
            ("servicios", True),
            ("domos", True),
            ("disponibilidad", True),
            ("información", True),
            ("informacion", True),
            ("general", True),
            ("hola", False),
            ("random text", False),
        ]
        
        print("\n1. Testing is_menu_keyword:")
        for message, expected in test_cases_keyword:
            result = is_menu_keyword(message)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{message}' -> {result} (expected: {expected})")
            assert result == expected, f"Failed for '{message}'"
        
        # Test 2: convert_keyword_to_menu_number
        test_cases_convert = [
            ("servicios", "2"),
            ("domos", "1"),
            ("disponibilidad", "3"),
            ("información", "4"),
            ("informacion", "4"),
            ("general", "4"),
            ("random text", "random text"),  # Should return original if no match
            ("1", "1"),  # Numbers should return as-is
        ]
        
        print("\n2. Testing convert_keyword_to_menu_number:")
        for message, expected in test_cases_convert:
            result = convert_keyword_to_menu_number(message)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{message}' -> '{result}' (expected: '{expected}')")
            assert result == expected, f"Failed for '{message}'"
        
        print("\n🎉 TODAS las funciones de keyword funcionan correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_servicios_keyword_specifically():
    """Test específico para verificar que 'servicios' funciona"""
    
    try:
        from services.conversation_service import is_menu_keyword, convert_keyword_to_menu_number
        
        print("\n=== TEST ESPECÍFICO: 'servicios' keyword ===")
        
        # Test diferentes variantes de servicios
        servicios_variants = ["servicios", "Servicios", "SERVICIOS", " servicios ", "los servicios"]
        
        for variant in servicios_variants:
            is_keyword = is_menu_keyword(variant)
            converted = convert_keyword_to_menu_number(variant)
            
            print(f"Variant: '{variant}'")
            print(f"  is_menu_keyword: {is_keyword}")
            print(f"  convert_to_number: '{converted}'")
            
            # Verificaciones
            assert is_keyword == True, f"'{variant}' should be detected as keyword"
            assert converted == "2", f"'{variant}' should convert to '2'"
            print(f"  ✅ PASSED")
            
        print("\n🎯 ESPECÍFICO para 'servicios': TODAS LAS VARIANTES FUNCIONAN!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR en test específico: {e}")
        return False

def main():
    """Función principal para ejecutar todos los tests"""
    try:
        print("EJECUTANDO TESTS PARA NUEVAS FUNCIONES DE KEYWORDS")
        print("=" * 60)
        
        # Test 1: Funciones básicas
        success1 = test_menu_keyword_functions()
        
        # Test 2: Test específico para servicios
        success2 = test_servicios_keyword_specifically()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎯 RESUMEN: TODOS LOS TESTS PASARON EXITOSAMENTE")
            print("✅ Las funciones is_menu_keyword() y convert_keyword_to_menu_number() funcionan correctamente")
            print("✅ 'servicios' será detectado como keyword válido")
            print("✅ 'servicios' será convertido al número '2' para procesamiento")
            print("✅ El sistema ahora maneja keywords además de números")
            return True
        else:
            print("\n❌ ALGUNOS TESTS FALLARON")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR EJECUTANDO TESTS: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)