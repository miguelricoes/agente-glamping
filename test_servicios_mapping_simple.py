#!/usr/bin/env python3
"""
TEST SIMPLE: VERIFICAR MAPEO CORRECTO DE 'SERVICIOS'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_servicios_mapping_correcto():
    """Test para verificar que 'servicios' mapea correctamente"""
    
    print("TEST: VERIFICANDO MAPEO CORRECTO DE 'SERVICIOS'")
    print("=" * 60)
    print()
    print("NUEVO MAPEO ESPERADO:")
    print("1. Domos")
    print("2. Servicios") 
    print("3. Disponibilidad")
    print("4. Informacion General")
    print()
    
    try:
        # TEST 1: ValidationService
        print("1. TESTING ValidationService...")
        from services.validation_service import ValidationService
        validation_service = ValidationService()
        
        servicios_detected = validation_service.is_menu_selection("servicios")
        print(f"   ValidationService detecta 'servicios': {servicios_detected}")
        assert servicios_detected == True, "ValidationService debe detectar 'servicios'"
        
        # TEST 2: ConversationService
        print("\n2. TESTING ConversationService...")
        from services.conversation_service import convert_keyword_to_menu_number, is_menu_keyword
        
        servicios_is_keyword = is_menu_keyword("servicios")
        servicios_converted = convert_keyword_to_menu_number("servicios")
        
        print(f"   is_menu_keyword('servicios'): {servicios_is_keyword}")
        print(f"   convert_keyword_to_menu_number('servicios'): '{servicios_converted}'")
        
        assert servicios_is_keyword == True, "'servicios' debe ser detectado como keyword"
        assert servicios_converted == "2", "'servicios' debe convertirse a '2'"
        
        # TEST 3: WhatsApp Routes Fallback
        print("\n3. TESTING WhatsApp Routes...")
        from routes.whatsapp_routes import handle_fallback_menu_response
        
        respuesta = handle_fallback_menu_response("servicios", "none")
        sin_error = "No pude identificar" not in respuesta
        tiene_servicios = "SERVICIOS" in respuesta.upper()
        
        print(f"   Fallback maneja 'servicios' sin error: {sin_error}")
        print(f"   Respuesta contiene info servicios: {tiene_servicios}")
        
        assert sin_error == True, "No debe haber mensaje de error"
        assert tiene_servicios == True, "Debe contener informacion de servicios"
        
        # TEST 4: Test de otros keywords también
        print("\n4. TESTING otros keywords...")
        
        otros_tests = [
            ("domos", "1"),
            ("disponibilidad", "3"),
            ("informacion", "4")
        ]
        
        otros_ok = 0
        for palabra, opcion_esperada in otros_tests:
            detected = is_menu_keyword(palabra)
            converted = convert_keyword_to_menu_number(palabra)
            
            if detected and converted == opcion_esperada:
                otros_ok += 1
                print(f"   OK: '{palabra}' -> '{converted}'")
            else:
                print(f"   FAIL: '{palabra}' -> detected={detected}, converted='{converted}'")
            
            assert detected, f"'{palabra}' debe ser detectada"
            assert converted == opcion_esperada, f"'{palabra}' debe convertirse a '{opcion_esperada}'"
        
        print(f"   Otros keywords: {otros_ok}/{len(otros_tests)} correctos")
        
        # TEST 5: Test del problema original resuelto
        print("\n5. TESTING problema original...")
        
        print("   ANTES: Usuario escribe 'servicios' -> Error")
        print("   DESPUES:")
        
        # Simular flujo completo
        user_input = "servicios"
        
        # Paso 1: Sistema detecta
        paso1 = validation_service.is_menu_selection(user_input)
        print(f"   - Sistema detecta '{user_input}': {paso1}")
        
        # Paso 2: Sistema convierte
        paso2 = convert_keyword_to_menu_number(user_input)
        print(f"   - Sistema convierte a: '{paso2}'")
        
        # Paso 3: Sistema responde
        paso3_respuesta = handle_fallback_menu_response(user_input, "none")
        paso3_ok = "SERVICIOS" in paso3_respuesta.upper() and "No pude identificar" not in paso3_respuesta
        print(f"   - Sistema responde correctamente: {paso3_ok}")
        
        flujo_completo = paso1 and paso2 == "2" and paso3_ok
        print(f"   FLUJO COMPLETO FUNCIONA: {flujo_completo}")
        
        assert flujo_completo, "El flujo completo debe funcionar"
        
        print("\n" + "=" * 60)
        print("RESULTADO: MAPEO DE 'SERVICIOS' COMPLETAMENTE CORREGIDO")
        print()
        print("VERIFICACIONES EXITOSAS:")
        print("- ValidationService detecta 'servicios'")
        print("- ConversationService convierte 'servicios' -> '2'")
        print("- WhatsApp fallback maneja 'servicios' sin error")
        print("- Otros keywords también funcionan correctamente")
        print("- Flujo completo usuario -> respuesta funciona")
        print()
        print("MAPEO FINAL CORRECTO:")
        print("'servicios' -> Opcion 2 (Servicios incluidos)")
        print()
        print("PROBLEMA ORIGINAL: COMPLETAMENTE RESUELTO")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_servicios_mapping_correcto()
    
    if success:
        print("\nCONCLUSION:")
        print("EL MAPEO DE 'SERVICIOS' ESTA COMPLETAMENTE CORREGIDO")
        print("Sistema reorganizado y funcionando perfectamente")
    else:
        print("\nPROBLEMAS DETECTADOS EN EL MAPEO")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)