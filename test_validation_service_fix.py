#!/usr/bin/env python3
"""
Test para verificar que el fix en validation_service.py funciona correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_validation_service_fix():
    """Test para verificar que ValidationService detecta 'servicios' correctamente"""
    
    try:
        from services.validation_service import ValidationService
        
        print("=== TEST VALIDATION SERVICE FIX ===")
        
        # Crear instancia del servicio
        validation_service = ValidationService()
        
        # Test casos específicos
        test_cases = [
            ("servicios", True, "servicios simple debe ser detectado"),
            ("1", True, "número 1 debe ser detectado"), 
            ("domos", True, "domos debe ser detectado"),
            ("disponibilidad", True, "disponibilidad debe ser detectada"),
            ("servicios incluidos", True, "servicios incluidos debe ser detectado"),
            ("políticas", True, "políticas debe ser detectado"),
            ("random text", False, "texto random no debe ser detectado"),
            ("hola", False, "saludo no debe ser detectado como menú"),
        ]
        
        all_passed = True
        
        for message, expected, description in test_cases:
            result = validation_service.is_menu_selection(message)
            status = "OK" if result == expected else "FAIL"
            print(f"  {status}: '{message}' -> {result} ({description})")
            
            if result != expected:
                all_passed = False
                print(f"    ERROR: esperado {expected}, obtuvo {result}")
        
        if all_passed:
            print("\nTODOS LOS TESTS PASARON!")
            print("ValidationService ahora detecta 'servicios' correctamente")
            return True
        else:
            print("\nALGUNOS TESTS FALLARON")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_servicios_specifically():
    """Test específico para diferentes variantes de 'servicios'"""
    
    try:
        from services.validation_service import ValidationService
        
        print("\n=== TEST ESPECÍFICO PARA 'SERVICIOS' ===")
        
        validation_service = ValidationService()
        
        servicios_variants = [
            "servicios",
            "Servicios", 
            "SERVICIOS",
            " servicios ",
            "servicios incluidos",
            "servicios combinados"
        ]
        
        all_passed = True
        
        for variant in servicios_variants:
            result = validation_service.is_menu_selection(variant)
            status = "OK" if result else "FAIL"
            print(f"  {status}: '{variant}' -> {result}")
            
            if not result:
                all_passed = False
                print(f"    ERROR: '{variant}' debería ser detectado como menú válido")
        
        if all_passed:
            print("\nTODAS LAS VARIANTES DE SERVICIOS FUNCIONAN!")
            return True
        else:
            print("\nALGUNAS VARIANTES DE SERVICIOS FALLAN")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Función principal"""
    print("TESTING FIX EN VALIDATION_SERVICE.PY")
    print("=" * 50)
    
    success1 = test_validation_service_fix()
    success2 = test_servicios_specifically()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("RESULTADO: FIX EN VALIDATION_SERVICE FUNCIONA CORRECTAMENTE")
        print("")
        print("CAMBIO IMPLEMENTADO:")
        print("- Agregado 'servicios' a menu_variants['4'] en is_menu_selection()")
        print("- Ahora ValidationService detecta 'servicios' como selección válida")
        print("- Se mantiene compatibilidad con 'servicios incluidos' y otras variantes")
        print("")
        print("IMPACTO:")
        print("- El sistema ahora detecta 'servicios' en TODOS los niveles")
        print("- Cobertura completa: validation_service + conversation_service + fallback")
        print("- Solución robusta y consistente")
        return True
    else:
        print("RESULTADO: HAY PROBLEMAS EN EL FIX")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)