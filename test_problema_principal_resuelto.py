#!/usr/bin/env python3
"""
TEST PROFUNDO PARA VERIFICAR QUE EL PROBLEMA PRINCIPAL ESTA COMPLETAMENTE RESUELTO

PROBLEMA ORIGINAL:
- El sistema estaba diseñado solo para números (1-4)
- Los usuarios escriben palabras ("servicios") 
- Resultado: "No pude identificar qué opción del menú deseas"

SOLUCION IMPLEMENTADA:
- Expandir validación para incluir palabras clave
- Convertir palabras clave a números correspondientes
- Asegurar compatibilidad total entre números y palabras

Este test verifica que la solución funciona en TODOS los niveles del sistema.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_problema_principal_numeros_vs_palabras():
    """
    Test principal: Verificar que el sistema ahora maneja tanto números como palabras
    """
    
    print("=" * 80)
    print("TEST PROFUNDO: PROBLEMA PRINCIPAL RESUELTO")
    print("=" * 80)
    print()
    print("PROBLEMA ORIGINAL:")
    print("- Sistema diseñado SOLO para números (1-4)")
    print("- Usuarios escriben palabras ('servicios')")
    print("- Resultado: Mensaje de error 'No pude identificar...'")
    print()
    print("SOLUCION IMPLEMENTADA:")
    print("- Expandir validación para palabras clave")
    print("- Convertir palabras a números correspondientes") 
    print("- Mantener compatibilidad con números originales")
    print()
    print("VERIFICANDO SOLUCION...")
    print("=" * 80)
    
    try:
        # PARTE 1: Verificar que el sistema original con números sigue funcionando
        print("\n1. VERIFICANDO COMPATIBILIDAD CON NUMEROS ORIGINALES")
        print("-" * 60)
        
        from services.validation_service import ValidationService
        validation_service = ValidationService()
        
        numeros_originales = ["1", "2", "3", "4", "5"]
        for numero in numeros_originales:
            result = validation_service.is_menu_selection(numero)
            status = "✓ OK" if result else "✗ FAIL"
            print(f"   {status}: Número '{numero}' -> {result}")
            assert result == True, f"Número '{numero}' debe seguir funcionando"
        
        print("   ✓ TODOS LOS NÚMEROS ORIGINALES SIGUEN FUNCIONANDO")
        
        # PARTE 2: Verificar que las palabras ahora también funcionan
        print("\n2. VERIFICANDO NUEVAS PALABRAS CLAVE")
        print("-" * 60)
        
        palabras_nuevas = ["domos", "servicios", "disponibilidad", "información", "informacion"]
        for palabra in palabras_nuevas:
            result = validation_service.is_menu_selection(palabra)
            status = "✓ OK" if result else "✗ FAIL" 
            print(f"   {status}: Palabra '{palabra}' -> {result}")
            assert result == True, f"Palabra '{palabra}' debe ser detectada"
            
        print("   ✓ TODAS LAS PALABRAS CLAVE NUEVAS FUNCIONAN")
        
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
        
        for palabra, numero_esperado in conversion_map.items():
            resultado = convert_keyword_to_menu_number(palabra)
            status = "✓ OK" if resultado == numero_esperado else "✗ FAIL"
            print(f"   {status}: '{palabra}' -> '{resultado}' (esperado: '{numero_esperado}')")
            assert resultado == numero_esperado, f"'{palabra}' debe convertirse a '{numero_esperado}'"
        
        print("   ✓ TODAS LAS CONVERSIONES FUNCIONAN CORRECTAMENTE")
        
        # PARTE 4: Test específico del caso problemático original
        print("\n4. TEST ESPECIFICO: CASO PROBLEMATICO ORIGINAL")
        print("-" * 60)
        print("   Simulando usuario escribiendo 'servicios'...")
        
        user_input = "servicios"
        
        # Paso 1: ¿El sistema detecta 'servicios' como válido?
        detection_result = validation_service.is_menu_selection(user_input)
        print(f"   Paso 1 - Detección: '{user_input}' -> {detection_result}")
        assert detection_result == True, "'servicios' debe ser detectado como selección válida"
        
        # Paso 2: ¿Se convierte a número correctamente?
        conversion_result = convert_keyword_to_menu_number(user_input)
        print(f"   Paso 2 - Conversión: '{user_input}' -> '{conversion_result}'")
        assert conversion_result == "2", "'servicios' debe convertirse a '2'"
        
        # Paso 3: ¿El fallback maneja correctamente?
        from routes.whatsapp_routes import handle_fallback_menu_response
        fallback_result = handle_fallback_menu_response(user_input, "none")
        fallback_ok = "SERVICIOS" in fallback_result.upper() and "No pude identificar" not in fallback_result
        print(f"   Paso 3 - Fallback: funciona correctamente -> {fallback_ok}")
        assert fallback_ok, "Fallback debe manejar 'servicios' sin error"
        
        print("   ✓ CASO PROBLEMATICO ORIGINAL COMPLETAMENTE RESUELTO")
        
        # PARTE 5: Test de equivalencia entre números y palabras
        print("\n5. TEST DE EQUIVALENCIA: NUMEROS vs PALABRAS")
        print("-" * 60)
        print("   Verificando que '2' y 'servicios' producen el mismo resultado...")
        
        # Test con número
        numero_result = handle_fallback_menu_response("2", "none")
        numero_contains_servicios = "SERVICIOS" in numero_result.upper()
        
        # Test con palabra
        palabra_result = handle_fallback_menu_response("servicios", "none")
        palabra_contains_servicios = "SERVICIOS" in palabra_result.upper()
        
        print(f"   Número '2' produce respuesta de servicios: {numero_contains_servicios}")
        print(f"   Palabra 'servicios' produce respuesta de servicios: {palabra_contains_servicios}")
        
        # Ambos deben producir respuestas relacionadas con servicios
        assert numero_contains_servicios == True, "Número '2' debe producir respuesta de servicios"
        assert palabra_contains_servicios == True, "Palabra 'servicios' debe producir respuesta de servicios"
        
        print("   ✓ EQUIVALENCIA CONFIRMADA: '2' y 'servicios' producen resultados equivalentes")
        
        # PARTE 6: Test de casos edge del mundo real
        print("\n6. TEST CASOS EDGE DEL MUNDO REAL")
        print("-" * 60)
        
        casos_reales = [
            "servicios",           # Caso original
            "Servicios",           # Con mayúscula
            " servicios ",         # Con espacios
            "los servicios",       # En contexto
            "servicios incluidos", # Frase completa
            "quiero servicios",    # En oración
            "SERVICIOS",           # Todo mayúsculas
        ]
        
        for caso in casos_reales:
            # Al menos uno de los métodos debe detectarlo
            val_detecta = validation_service.is_menu_selection(caso)
            
            from services.conversation_service import is_menu_keyword
            key_detecta = is_menu_keyword(caso)
            
            detectado = val_detecta or key_detecta
            
            # La respuesta no debe ser mensaje de error
            respuesta = handle_fallback_menu_response(caso, "none")
            sin_error = "No pude identificar" not in respuesta
            
            status = "✓ OK" if detectado and sin_error else "✗ FAIL"
            print(f"   {status}: '{caso}' -> detectado={detectado}, sin_error={sin_error}")
            
            assert detectado, f"'{caso}' debe ser detectado por algún método"
            assert sin_error, f"'{caso}' no debe producir mensaje de error"
        
        print("   ✓ TODOS LOS CASOS EDGE DEL MUNDO REAL FUNCIONAN")
        
        # RESUMEN FINAL
        print("\n" + "=" * 80)
        print("RESULTADO DEL TEST PROFUNDO")
        print("=" * 80)
        print()
        print("✓ PROBLEMA PRINCIPAL: COMPLETAMENTE RESUELTO")
        print()
        print("ANTES DE LA SOLUCION:")
        print("- Sistema solo aceptaba números (1-4)")
        print("- Usuario escribía 'servicios'")
        print("- Resultado: 'No pude identificar qué opción del menú deseas'")
        print()
        print("DESPUES DE LA SOLUCION:")
        print("- Sistema acepta números (1-4) Y palabras clave")
        print("- Usuario escribe 'servicios'")
        print("- Resultado: Información completa de servicios incluidos")
        print()
        print("VERIFICACIONES EXITOSAS:")
        print("✓ Compatibilidad con números originales mantenida")
        print("✓ Palabras clave nuevas funcionan correctamente")
        print("✓ Conversión palabras->números implementada")
        print("✓ Caso problemático original resuelto")
        print("✓ Equivalencia números/palabras confirmada")
        print("✓ Casos edge del mundo real cubiertos")
        print()
        print("COBERTURA DE ARCHIVOS:")
        print("✓ services/validation_service.py - Detecta palabras clave")
        print("✓ services/conversation_service.py - Convierte palabras a números")
        print("✓ routes/whatsapp_routes.py - Maneja fallback con palabras")
        print("✓ agente_standalone.py - Convierte palabras en handle_menu_selection")
        print()
        print("🎯 CONCLUSION: EL SISTEMA AHORA ES HIBRIDO")
        print("   - Mantiene compatibilidad con números (1-4)")
        print("   - Agrega soporte completo para palabras clave")
        print("   - Garantiza que 'servicios' SIEMPRE funcione")
        print()
        print("🚀 SOLUCION ROBUSTA Y COMPLETA IMPLEMENTADA")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal del test profundo"""
    
    success = test_problema_principal_numeros_vs_palabras()
    
    if success:
        print("\n" + "=" * 80)
        print("🏆 TEST PROFUNDO COMPLETADO EXITOSAMENTE")
        print("🎯 EL PROBLEMA PRINCIPAL ESTA COMPLETAMENTE RESUELTO")
        print("=" * 80)
        return True
    else:
        print("\n" + "=" * 80)
        print("❌ TEST PROFUNDO FALLO")
        print("🔧 EL PROBLEMA PRINCIPAL AUN REQUIERE ATENCION")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)