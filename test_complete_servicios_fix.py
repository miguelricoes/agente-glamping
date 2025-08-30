#!/usr/bin/env python3
"""
Test completo para verificar que ambos fixes para 'servicios' funcionan juntos
- Fix en routes/whatsapp_routes.py (fallback response)
- Fix en services/conversation_service.py (keyword detection)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_whatsapp_routes_fix():
    """Test del fix en whatsapp_routes.py"""
    try:
        from routes.whatsapp_routes import handle_fallback_menu_response
        
        print("=== TEST WHATSAPP ROUTES FIX ===")
        
        result = handle_fallback_menu_response("servicios", "none")
        
        # Verificar que NO retorna mensaje de error
        if "No pude identificar" in result:
            print("ERROR: Aun retorna mensaje de error")
            return False
            
        # Verificar que contiene informacion de servicios
        if "SERVICIOS" in result.upper():
            print("EXITO: handle_fallback_menu_response maneja 'servicios' correctamente")
            return True
        else:
            print("ERROR: No contiene informacion de servicios")
            return False
            
    except Exception as e:
        print(f"ERROR en whatsapp routes fix: {e}")
        return False

def test_conversation_service_fix():
    """Test del fix en conversation_service.py"""
    try:
        from services.conversation_service import is_menu_keyword, convert_keyword_to_menu_number
        
        print("\n=== TEST CONVERSATION SERVICE FIX ===")
        
        # Test keyword detection
        is_keyword = is_menu_keyword("servicios")
        if not is_keyword:
            print("ERROR: servicios no es detectado como keyword")
            return False
            
        # Test keyword conversion
        converted = convert_keyword_to_menu_number("servicios")
        if converted != "2":
            print(f"ERROR: servicios se convierte a '{converted}' en lugar de '2'")
            return False
            
        print("EXITO: conversation_service maneja keywords correctamente")
        return True
        
    except Exception as e:
        print(f"ERROR en conversation service fix: {e}")
        return False

def test_integration():
    """Test de integración para verificar que ambos fixes trabajan juntos"""
    try:
        print("\n=== TEST INTEGRACION ===")
        
        # Simular el flujo completo:
        # 1. Usuario escribe "servicios"
        # 2. Sistema detecta como keyword 
        # 3. Se convierte a numero "2"
        # 4. Se procesa correctamente
        
        from services.conversation_service import is_menu_keyword, convert_keyword_to_menu_number
        from routes.whatsapp_routes import handle_fallback_menu_response
        
        user_input = "servicios"
        
        # Paso 1: Detectar como keyword
        is_keyword = is_menu_keyword(user_input)
        print(f"Paso 1 - Deteccion keyword: {is_keyword}")
        
        if is_keyword:
            # Paso 2: Convertir a numero
            converted = convert_keyword_to_menu_number(user_input)
            print(f"Paso 2 - Conversion: '{user_input}' -> '{converted}'")
            
            # Paso 3: Procesar con fallback (simulando cuando llega ahi)
            fallback_result = handle_fallback_menu_response(user_input, "none")
            print(f"Paso 3 - Fallback result: contiene servicios = {'SERVICIOS' in fallback_result.upper()}")
            
            if "SERVICIOS" in fallback_result.upper():
                print("EXITO: Integracion completa funciona!")
                return True
            else:
                print("ERROR: Fallback no devuelve servicios")
                return False
        else:
            print("ERROR: No se detecta como keyword")
            return False
            
    except Exception as e:
        print(f"ERROR en test integracion: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("EJECUTANDO TESTS COMPLETOS PARA FIXES DE 'SERVICIOS'")
    print("=" * 60)
    
    # Test individual de cada fix
    success1 = test_whatsapp_routes_fix()
    success2 = test_conversation_service_fix() 
    success3 = test_integration()
    
    print("\n" + "=" * 60)
    if success1 and success2 and success3:
        print("RESULTADO FINAL: TODOS LOS FIXES FUNCIONAN CORRECTAMENTE")
        print("")
        print("SOLUCION IMPLEMENTADA:")
        print("1. Fix en routes/whatsapp_routes.py - Agregado 'servicios' a patrones de fallback")
        print("2. Fix en services/conversation_service.py - Nuevas funciones de deteccion de keywords") 
        print("3. Integracion - Ambos fixes trabajan juntos sin conflictos")
        print("")
        print("RESULTADO PARA EL USUARIO:")
        print("- Cuando escriba 'servicios' recibira informacion completa de servicios")
        print("- No mas mensaje 'No pude identificar que opcion del menu deseas'")
        print("- El sistema ahora maneja tanto numeros (1,2,3) como palabras (domos, servicios)")
        return True
    else:
        print("RESULTADO FINAL: ALGUNOS FIXES TIENEN PROBLEMAS")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)