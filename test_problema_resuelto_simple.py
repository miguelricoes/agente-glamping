#!/usr/bin/env python3
"""
TEST PROFUNDO SIMPLE - PROBLEMA PRINCIPAL RESUELTO
Sin caracteres especiales para compatibilidad con Windows
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_problema_principal_resuelto():
    """Test profundo para verificar que el problema principal esta completamente resuelto"""
    
    print("=" * 80)
    print("TEST PROFUNDO: VERIFICANDO PROBLEMA PRINCIPAL RESUELTO")
    print("=" * 80)
    print()
    print("PROBLEMA ORIGINAL:")
    print("- Sistema diseñado SOLO para números (1-4)")
    print("- Usuarios escriben palabras ('servicios')")
    print("- Resultado: 'No pude identificar qué opción del menú deseas'")
    print()
    print("SOLUCION IMPLEMENTADA:")
    print("- Expandir validación para incluir palabras clave") 
    print("- Convertir palabras clave a números correspondientes")
    print("- Mantener compatibilidad total con números originales")
    print()
    
    try:
        # PARTE 1: Verificar números originales siguen funcionando
        print("1. VERIFICANDO COMPATIBILIDAD CON NUMEROS ORIGINALES")
        print("-" * 60)
        
        from services.validation_service import ValidationService
        validation_service = ValidationService()
        
        numeros_originales = ["1", "2", "3", "4", "5"]
        numeros_ok = 0
        
        for numero in numeros_originales:
            result = validation_service.is_menu_selection(numero)
            status = "OK" if result else "FAIL"
            print(f"   {status}: Numero '{numero}' -> {result}")
            if result:
                numeros_ok += 1
            assert result == True, f"Numero '{numero}' debe seguir funcionando"
        
        print(f"   RESULTADO: {numeros_ok}/{len(numeros_originales)} numeros funcionan")
        assert numeros_ok == len(numeros_originales), "Todos los numeros deben funcionar"
        
        # PARTE 2: Verificar palabras nuevas funcionan
        print("\n2. VERIFICANDO NUEVAS PALABRAS CLAVE")
        print("-" * 60)
        
        palabras_nuevas = ["domos", "servicios", "disponibilidad", "información", "informacion"]
        palabras_ok = 0
        
        for palabra in palabras_nuevas:
            result = validation_service.is_menu_selection(palabra)
            status = "OK" if result else "FAIL"
            print(f"   {status}: Palabra '{palabra}' -> {result}")
            if result:
                palabras_ok += 1
            assert result == True, f"Palabra '{palabra}' debe ser detectada"
        
        print(f"   RESULTADO: {palabras_ok}/{len(palabras_nuevas)} palabras funcionan")
        assert palabras_ok == len(palabras_nuevas), "Todas las palabras deben funcionar"
        
        # PARTE 3: Verificar conversión de palabras a números
        print("\n3. VERIFICANDO CONVERSION PALABRAS -> NUMEROS")
        print("-" * 60)
        
        from services.conversation_service import convert_keyword_to_menu_number
        
        conversion_map = {
            "domos": "1",
            "servicios": "2", 
            "disponibilidad": "3",
            "información": "4",
            "informacion": "4"
        }
        
        conversiones_ok = 0
        
        for palabra, numero_esperado in conversion_map.items():
            resultado = convert_keyword_to_menu_number(palabra)
            status = "OK" if resultado == numero_esperado else "FAIL"
            print(f"   {status}: '{palabra}' -> '{resultado}' (esperado: '{numero_esperado}')")
            if resultado == numero_esperado:
                conversiones_ok += 1
            assert resultado == numero_esperado, f"'{palabra}' debe convertirse a '{numero_esperado}'"
        
        print(f"   RESULTADO: {conversiones_ok}/{len(conversion_map)} conversiones correctas")
        assert conversiones_ok == len(conversion_map), "Todas las conversiones deben funcionar"
        
        # PARTE 4: Test específico del caso problemático original
        print("\n4. TEST DEL CASO PROBLEMATICO ORIGINAL: 'servicios'")
        print("-" * 60)
        
        user_input = "servicios"
        print(f"   Simulando usuario escribiendo: '{user_input}'")
        
        # Paso 1: Detección
        detection_result = validation_service.is_menu_selection(user_input)
        print(f"   Paso 1 - Deteccion: {detection_result}")
        assert detection_result == True, "'servicios' debe ser detectado"
        
        # Paso 2: Conversión
        conversion_result = convert_keyword_to_menu_number(user_input)
        print(f"   Paso 2 - Conversion: '{user_input}' -> '{conversion_result}'")
        assert conversion_result == "2", "'servicios' debe convertirse a '2'"
        
        # Paso 3: Respuesta sin error
        from routes.whatsapp_routes import handle_fallback_menu_response
        fallback_result = handle_fallback_menu_response(user_input, "none")
        sin_mensaje_error = "No pude identificar" not in fallback_result
        tiene_info_servicios = "SERVICIOS" in fallback_result.upper()
        
        print(f"   Paso 3 - Sin mensaje error: {sin_mensaje_error}")
        print(f"   Paso 3 - Tiene info servicios: {tiene_info_servicios}")
        
        assert sin_mensaje_error, "No debe mostrar mensaje de error"
        assert tiene_info_servicios, "Debe mostrar informacion de servicios"
        
        print("   CASO PROBLEMATICO ORIGINAL: COMPLETAMENTE RESUELTO")
        
        # PARTE 5: Test de equivalencia números vs palabras
        print("\n5. TEST DE EQUIVALENCIA: '2' vs 'servicios'")
        print("-" * 60)
        
        # Respuesta con número
        respuesta_numero = handle_fallback_menu_response("2", "none")
        numero_ok = "SERVICIOS" in respuesta_numero.upper()
        
        # Respuesta con palabra
        respuesta_palabra = handle_fallback_menu_response("servicios", "none")  
        palabra_ok = "SERVICIOS" in respuesta_palabra.upper()
        
        print(f"   Numero '2' produce respuesta servicios: {numero_ok}")
        print(f"   Palabra 'servicios' produce respuesta servicios: {palabra_ok}")
        
        equivalencia = numero_ok and palabra_ok
        print(f"   EQUIVALENCIA CONFIRMADA: {equivalencia}")
        
        assert equivalencia, "'2' y 'servicios' deben producir respuestas equivalentes"
        
        # PARTE 6: Test casos edge del mundo real
        print("\n6. TEST CASOS EDGE DEL MUNDO REAL")
        print("-" * 60)
        
        casos_reales = [
            "servicios",
            "Servicios", 
            " servicios ",
            "los servicios",
            "servicios incluidos",
            "SERVICIOS"
        ]
        
        casos_ok = 0
        
        for caso in casos_reales:
            from services.conversation_service import is_menu_keyword
            
            val_detecta = validation_service.is_menu_selection(caso)
            key_detecta = is_menu_keyword(caso)
            detectado = val_detecta or key_detecta
            
            respuesta = handle_fallback_menu_response(caso, "none")
            sin_error = "No pude identificar" not in respuesta
            
            resultado = detectado and sin_error
            status = "OK" if resultado else "FAIL"
            print(f"   {status}: '{caso}' -> detectado={detectado}, sin_error={sin_error}")
            
            if resultado:
                casos_ok += 1
                
            assert detectado, f"'{caso}' debe ser detectado"
            assert sin_error, f"'{caso}' no debe producir error"
        
        print(f"   RESULTADO: {casos_ok}/{len(casos_reales)} casos edge funcionan")
        assert casos_ok == len(casos_reales), "Todos los casos edge deben funcionar"
        
        # RESUMEN FINAL
        print("\n" + "=" * 80)
        print("RESUMEN DEL TEST PROFUNDO")
        print("=" * 80)
        print()
        print("PROBLEMA PRINCIPAL: COMPLETAMENTE RESUELTO")
        print()
        print("VERIFICACIONES EXITOSAS:")
        print(f"- Compatibilidad numeros originales: {numeros_ok}/{len(numeros_originales)}")
        print(f"- Nuevas palabras clave funcionan: {palabras_ok}/{len(palabras_nuevas)}")
        print(f"- Conversiones correctas: {conversiones_ok}/{len(conversion_map)}")
        print("- Caso problematico 'servicios': RESUELTO") 
        print("- Equivalencia '2' vs 'servicios': CONFIRMADA")
        print(f"- Casos edge del mundo real: {casos_ok}/{len(casos_reales)}")
        print()
        print("TRANSFORMACION DEL SISTEMA:")
        print("ANTES: Solo numeros (1-4) -> Error con palabras")
        print("DESPUES: Numeros + Palabras -> Funciona con ambos")
        print()
        print("ARCHIVOS MODIFICADOS EXITOSAMENTE:")
        print("- services/validation_service.py")
        print("- services/conversation_service.py") 
        print("- routes/whatsapp_routes.py")
        print("- agente_standalone.py")
        print()
        print("RESULTADO FINAL:")
        print("El usuario puede escribir '2' O 'servicios'")
        print("Ambos producen la misma respuesta: informacion de servicios")
        print("Sin errores, sin confusion, funcionamiento perfecto")
        print()
        print("SOLUCION: ROBUSTA, COMPLETA Y VERIFICADA")
        
        return True
        
    except Exception as e:
        print(f"\nERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    
    success = test_problema_principal_resuelto()
    
    print("\n" + "=" * 80)
    if success:
        print("CONCLUSION: EL PROBLEMA PRINCIPAL ESTA COMPLETAMENTE RESUELTO")
        print("El sistema ahora maneja perfectamente numeros Y palabras")
        print("Los usuarios pueden escribir 'servicios' sin problemas")
    else:
        print("CONCLUSION: EL PROBLEMA PRINCIPAL AUN REQUIERE ATENCION")
        print("Revisar los errores arriba para mas detalles")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)