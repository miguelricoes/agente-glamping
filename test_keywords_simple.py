#!/usr/bin/env python3
"""
Test simple para verificar las funciones de keywords sin emojis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_keyword_functions():
    """Test básico para las funciones de keyword"""
    
    try:
        from services.conversation_service import is_menu_keyword, convert_keyword_to_menu_number
        
        print("Test 1: is_menu_keyword('servicios')")
        result = is_menu_keyword("servicios")
        print(f"Result: {result}")
        assert result == True, "servicios should be detected as keyword"
        
        print("Test 2: convert_keyword_to_menu_number('servicios')")
        result = convert_keyword_to_menu_number("servicios")
        print(f"Result: {result}")
        assert result == "2", "servicios should convert to '2'"
        
        print("Test 3: is_menu_keyword('domos')")
        result = is_menu_keyword("domos")
        print(f"Result: {result}")
        assert result == True, "domos should be detected as keyword"
        
        print("Test 4: convert_keyword_to_menu_number('domos')")
        result = convert_keyword_to_menu_number("domos")
        print(f"Result: {result}")
        assert result == "1", "domos should convert to '1'"
        
        print("Test 5: is_menu_keyword('random')")
        result = is_menu_keyword("random")
        print(f"Result: {result}")
        assert result == False, "random should not be detected as keyword"
        
        print("\nTODOS LOS TESTS PASARON!")
        print("Las funciones de keyword funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_keyword_functions()
    if success:
        print("EXITO: Las nuevas funciones de keyword estan listas")
    else:
        print("ERROR: Hay problemas con las funciones de keyword")
    sys.exit(0 if success else 1)