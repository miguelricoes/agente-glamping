#!/usr/bin/env python3
"""
Test simple para verificar que la conversión de keywords funciona en fallback
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fallback_conversion():
    """Test básico para verificar conversión en fallback"""
    
    try:
        from services.conversation_service import convert_keyword_to_menu_number, is_menu_keyword
        
        print("Test fallback conversion:")
        
        # Test servicios
        user_message = "servicios" 
        is_keyword = is_menu_keyword(user_message)
        converted = convert_keyword_to_menu_number(user_message)
        
        print(f"Input: '{user_message}'")
        print(f"Is keyword: {is_keyword}")
        print(f"Converted: '{converted}'")
        
        assert is_keyword == True, "servicios should be keyword"
        assert converted == "2", f"servicios should convert to '2', got '{converted}'"
        
        print("SUCCESS: Fallback conversion works!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    if test_fallback_conversion():
        print("\nRESULTADO: FIX ADICIONAL FUNCIONA CORRECTAMENTE")
        print("El path de fallback ahora también convierte keywords a números")
        return True
    else:
        print("\nERROR: Fix adicional tiene problemas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)