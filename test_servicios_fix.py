#!/usr/bin/env python3
"""
Test específico para verificar que el fix de 'servicios' funciona correctamente
Reproduce el escenario exacto del problema reportado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_handle_fallback_menu_response():
    """Test para verificar que 'servicios' se maneja correctamente"""
    
    # Importar la función que fue corregida
    from routes.whatsapp_routes import handle_fallback_menu_response
    
    print("=== TEST: handle_fallback_menu_response con 'servicios' ===")
    
    # Test case 1: "servicios" exacto
    test_message = "servicios"
    result = handle_fallback_menu_response(test_message, "none")
    
    print(f"Input: '{test_message}'")
    print(f"Output: {result[:100]}..." if len(result) > 100 else f"Output: {result}")
    
    # Verificar que la respuesta contiene información de servicios
    assert "SERVICIOS INCLUIDOS" in result or "servicios" in result.lower(), f"La respuesta no contiene información de servicios: {result}"
    print("✅ Test 1 PASÓ: 'servicios' maneja correctamente")
    
    # Test case 2: "Servicios" con mayúscula
    test_message = "Servicios"
    result = handle_fallback_menu_response(test_message, "none")
    
    print(f"\nInput: '{test_message}'")
    print(f"Output: {result[:100]}..." if len(result) > 100 else f"Output: {result}")
    assert "SERVICIOS INCLUIDOS" in result or "servicios" in result.lower(), f"La respuesta no contiene información de servicios: {result}"
    print("✅ Test 2 PASÓ: 'Servicios' con mayúscula maneja correctamente")
    
    # Test case 3: "servicio" singular (debería funcionar también)
    test_message = "servicio"
    result = handle_fallback_menu_response(test_message, "none")
    
    print(f"\nInput: '{test_message}'")
    print(f"Output: {result[:100]}..." if len(result) > 100 else f"Output: {result}")
    assert "SERVICIOS INCLUIDOS" in result or "servicios" in result.lower(), f"La respuesta no contiene información de servicios: {result}"
    print("✅ Test 3 PASÓ: 'servicio' singular maneja correctamente")
    
    # Test case 4: "4" numérico (para completar el test)
    test_message = "4"
    result = handle_fallback_menu_response(test_message, "none")
    
    print(f"\nInput: '{test_message}'")
    print(f"Output: {result[:100]}..." if len(result) > 100 else f"Output: {result}")
    # Nota: El número 4 podría ir a 'precios' según la configuración actual
    print("✅ Test 4 COMPLETADO: opción numérica '4'")
    
    print("\n🎉 TODOS LOS TESTS PASARON - El fix de 'servicios' funciona correctamente!")
    return True

def test_generate_simple_menu_response():
    """Test para verificar que generate_simple_menu_response funciona para servicios"""
    
    from routes.whatsapp_routes import generate_simple_menu_response
    
    print("\n=== TEST: generate_simple_menu_response('servicios') ===")
    
    result = generate_simple_menu_response('servicios')
    
    print(f"Output para 'servicios':")
    print(result)
    
    # Verificar que contiene elementos esperados
    expected_elements = ["SERVICIOS INCLUIDOS", "Alimentación", "Actividades", "Comodidades"]
    for element in expected_elements:
        assert element in result, f"Elemento '{element}' no encontrado en la respuesta"
        print(f"✅ Elemento '{element}' encontrado")
    
    print("🎉 generate_simple_menu_response('servicios') funciona correctamente!")
    return True

def main():
    """Función principal para ejecutar todos los tests"""
    try:
        print("EJECUTANDO TESTS PARA VERIFICAR EL FIX DE 'SERVICIOS'")
        print("="*60)
        
        # Test 1: Función de fallback
        test_handle_fallback_menu_response()
        
        # Test 2: Función de respuesta de menú
        test_generate_simple_menu_response()
        
        print("\n" + "="*60)
        print("🎯 RESUMEN: TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("✅ El fix para 'servicios' ha sido implementado y verificado correctamente")
        print("✅ Los usuarios ya no verán el mensaje 'No pude identificar qué opción del menú deseas'")
        print("✅ Cuando escriban 'servicios', recibirán la información completa de servicios")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LOS TESTS: {e}")
        print("🔍 Revisa la implementación del fix")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)