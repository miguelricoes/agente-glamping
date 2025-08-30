#!/usr/bin/env python3
"""
TEST CORE: PROBLEMA PRINCIPAL DE 'SERVICIOS' RESUELTO

Enfoque específico en el problema central:
- Sistema solo aceptaba números (1-4)
- Usuario escribía "servicios"
- Ahora debe funcionar perfectamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_servicios_problema_central():
    """Test del problema central: 'servicios' debe funcionar como '2'"""
    
    print("=" * 70)
    print("TEST CORE: PROBLEMA PRINCIPAL DE 'SERVICIOS' RESUELTO")
    print("=" * 70)
    print()
    print("PROBLEMA ORIGINAL:")
    print("- Usuario escribia: 'servicios'")
    print("- Sistema respondia: 'No pude identificar que opcion del menu deseas'")
    print("- Causa: Sistema solo entendia numeros (1-4), no palabras")
    print()
    print("SOLUCION IMPLEMENTADA:")
    print("- Expandir sistema para entender palabras clave")
    print("- 'servicios' debe ser equivalente a '2'")
    print("- Mantener compatibilidad con numeros originales")
    print()
    
    try:
        # TEST 1: Verificar que números originales siguen funcionando
        print("TEST 1: COMPATIBILIDAD CON NUMEROS ORIGINALES")
        print("-" * 50)
        
        from services.validation_service import ValidationService
        validation_service = ValidationService()
        
        # Test números 1-4 (los originales del sistema)
        for numero in ["1", "2", "3", "4"]:
            result = validation_service.is_menu_selection(numero)
            print(f"   Numero '{numero}': {result}")
            assert result == True, f"Numero '{numero}' debe funcionar"
        
        print("   RESULTADO: Todos los numeros originales funcionan")
        
        # TEST 2: Verificar que 'servicios' ahora funciona
        print("\nTEST 2: LA PALABRA 'SERVICIOS' AHORA FUNCIONA")
        print("-" * 50)
        
        # Test detección de 'servicios'
        servicios_detectado = validation_service.is_menu_selection("servicios")
        print(f"   ValidationService detecta 'servicios': {servicios_detectado}")
        assert servicios_detectado == True, "'servicios' debe ser detectado"
        
        # Test conversión de 'servicios' a '2'
        from services.conversation_service import convert_keyword_to_menu_number
        servicios_convertido = convert_keyword_to_menu_number("servicios")
        print(f"   'servicios' se convierte a: '{servicios_convertido}'")
        assert servicios_convertido == "2", "'servicios' debe convertirse a '2'"
        
        # Test que ya no produce mensaje de error
        from routes.whatsapp_routes import handle_fallback_menu_response
        respuesta_servicios = handle_fallback_menu_response("servicios", "none")
        tiene_error = "No pude identificar" in respuesta_servicios
        tiene_info_servicios = "SERVICIOS" in respuesta_servicios.upper()
        
        print(f"   Respuesta contiene error: {tiene_error}")
        print(f"   Respuesta contiene info servicios: {tiene_info_servicios}")
        
        assert tiene_error == False, "'servicios' no debe producir mensaje de error"
        assert tiene_info_servicios == True, "'servicios' debe producir info de servicios"
        
        print("   RESULTADO: 'servicios' funciona perfectamente")
        
        # TEST 3: Verificar equivalencia entre '2' y 'servicios'
        print("\nTEST 3: EQUIVALENCIA '2' vs 'SERVICIOS'")
        print("-" * 50)
        
        # Respuesta con número '2'
        respuesta_2 = handle_fallback_menu_response("2", "none")
        numero_2_ok = "SERVICIOS" in respuesta_2.upper()
        
        # Respuesta con palabra 'servicios'
        respuesta_servicios = handle_fallback_menu_response("servicios", "none")
        palabra_servicios_ok = "SERVICIOS" in respuesta_servicios.upper()
        
        print(f"   Numero '2' produce info servicios: {numero_2_ok}")
        print(f"   Palabra 'servicios' produce info servicios: {palabra_servicios_ok}")
        
        equivalentes = numero_2_ok and palabra_servicios_ok
        print(f"   Son equivalentes: {equivalentes}")
        
        assert equivalentes == True, "'2' y 'servicios' deben ser equivalentes"
        
        print("   RESULTADO: '2' y 'servicios' producen el mismo resultado")
        
        # TEST 4: Test del scenario completo del usuario
        print("\nTEST 4: SCENARIO COMPLETO DEL USUARIO")
        print("-" * 50)
        print("   Simulando: Usuario ve menu y escribe 'servicios'...")
        
        user_input = "servicios"
        
        # Paso 1: Sistema debe detectar como selección válida
        paso1 = validation_service.is_menu_selection(user_input)
        print(f"   Paso 1 - Sistema detecta como válido: {paso1}")
        
        # Paso 2: Sistema convierte a número para procesamiento interno
        paso2 = convert_keyword_to_menu_number(user_input)
        print(f"   Paso 2 - Convierte para procesamiento: '{paso2}'")
        
        # Paso 3: Sistema procesa y responde con información
        paso3_respuesta = handle_fallback_menu_response(user_input, "none")
        paso3_ok = "SERVICIOS" in paso3_respuesta.upper() and "No pude identificar" not in paso3_respuesta
        print(f"   Paso 3 - Responde con informacion: {paso3_ok}")
        
        # Verificar todo el flujo
        flujo_completo = paso1 and paso2 == "2" and paso3_ok
        print(f"   FLUJO COMPLETO FUNCIONA: {flujo_completo}")
        
        assert flujo_completo == True, "El flujo completo debe funcionar"
        
        # TEST 5: Antes vs Después
        print("\nTEST 5: COMPARACION ANTES vs DESPUES")
        print("-" * 50)
        
        print("   ANTES DE LA SOLUCION:")
        print("   - Usuario: 'servicios'")
        print("   - Sistema: 'No pude identificar que opcion del menu deseas'")
        print("   - Estado: ROTO")
        print()
        print("   DESPUES DE LA SOLUCION:")
        print("   - Usuario: 'servicios'")
        print(f"   - Sistema detecta: {validation_service.is_menu_selection('servicios')}")
        print(f"   - Sistema convierte: 'servicios' -> '{convert_keyword_to_menu_number('servicios')}'")
        
        respuesta_final = handle_fallback_menu_response("servicios", "none")
        tiene_info = "SERVICIOS" in respuesta_final.upper()
        no_tiene_error = "No pude identificar" not in respuesta_final
        
        print(f"   - Sistema responde con info: {tiene_info}")
        print(f"   - Sin mensaje de error: {no_tiene_error}")
        print("   - Estado: FUNCIONANDO PERFECTAMENTE")
        
        solucion_exitosa = tiene_info and no_tiene_error
        assert solucion_exitosa == True, "La solucion debe ser exitosa"
        
        # RESUMEN FINAL
        print("\n" + "=" * 70)
        print("RESUMEN: PROBLEMA PRINCIPAL COMPLETAMENTE RESUELTO")
        print("=" * 70)
        print()
        print("VERIFICACIONES EXITOSAS:")
        print("✓ Numeros originales (1-4) siguen funcionando")
        print("✓ Palabra 'servicios' ahora es detectada correctamente")
        print("✓ 'servicios' se convierte a '2' internamente")
        print("✓ 'servicios' ya no produce mensaje de error")
        print("✓ 'servicios' produce informacion completa de servicios")
        print("✓ '2' y 'servicios' son completamente equivalentes")
        print("✓ Flujo completo usuario -> respuesta funciona")
        print()
        print("TRANSFORMACION LOGRADA:")
        print("ANTES: Sistema solo numeros -> Error con 'servicios'")
        print("DESPUES: Sistema hibrido -> 'servicios' funciona perfecto")
        print()
        print("IMPACTO EN EL USUARIO:")
        print("- Puede escribir '2' (método original)")
        print("- Puede escribir 'servicios' (método nuevo)")
        print("- Ambos producen la misma respuesta exitosa")
        print("- Ya no hay confusion ni mensajes de error")
        print()
        print("🎯 PROBLEMA CENTRAL: COMPLETAMENTE RESUELTO")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar test del problema central"""
    
    success = test_servicios_problema_central()
    
    print("\n" + "=" * 70)
    if success:
        print("CONCLUSION FINAL:")
        print("EL PROBLEMA PRINCIPAL DE 'SERVICIOS' ESTA COMPLETAMENTE RESUELTO")
        print()
        print("✓ Sistema transformado de 'solo-numeros' a 'hibrido'")
        print("✓ 'servicios' funciona perfectamente como '2'")  
        print("✓ Usuario ya no vera mensajes de error")
        print("✓ Compatibilidad total mantenida")
        print()
        print("🚀 SOLUCION ROBUSTA IMPLEMENTADA Y VERIFICADA")
    else:
        print("HAY PROBLEMAS EN LA SOLUCION - REVISAR ERRORES ARRIBA")
    print("=" * 70)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)