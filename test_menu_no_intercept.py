#!/usr/bin/env python3
"""
Test para verificar que menu ya NO intercepta "servicios"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.validation_service import ValidationService

def test_menu_no_intercept():
    """Test que menu ya no intercepte servicios"""
    
    validation_service = ValidationService()
    
    test_cases = [
        ("servicios", False, "Consulta general - debe ir a topic fallback"),
        ("que servicios incluyen", False, "Consulta específica - debe ir a topic fallback"),
        ("servicios incluidos", True, "Opción específica de menú - debe ir a menu"),
        ("servicios combinados", True, "Opción específica de menú - debe ir a menu"),
        ("opcion 4", True, "Opción numérica - debe ir a menu"),
        ("4", True, "Número - debe ir a menu")
    ]
    
    print("TESTING MENU INTERCEPTION FIX")
    print("=" * 50)
    
    for message, should_intercept, description in test_cases:
        is_menu = validation_service.is_menu_selection(message)
        
        print(f"\nTEST: '{message}'")
        print(f"EXPECTED: {'Menu intercept' if should_intercept else 'Topic fallback'}")
        print(f"ACTUAL: {'Menu intercept' if is_menu else 'Topic fallback'}")
        
        if is_menu == should_intercept:
            print("RESULTADO: ✓ CORRECTO")
        else:
            print("RESULTADO: ✗ ERROR")
        
        print(f"DESCRIPCION: {description}")

if __name__ == "__main__":
    test_menu_no_intercept()