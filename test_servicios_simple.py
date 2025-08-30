#!/usr/bin/env python3
"""
Test simple para verificar que el fix de 'servicios' funciona
Sin emojis para evitar problemas de encoding en Windows
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_servicios_fix():
    """Test básico para verificar que 'servicios' se maneja correctamente"""
    
    try:
        # Importar la función que fue corregida
        from routes.whatsapp_routes import handle_fallback_menu_response
        
        print("TEST: Verificando fix para 'servicios'")
        
        # Test con "servicios"
        test_message = "servicios"
        result = handle_fallback_menu_response(test_message, "none")
        
        print(f"Input: '{test_message}'")
        print("Output recibido correctamente (contiene respuesta de servicios)")
        
        # Verificar que la respuesta NO es el mensaje de error por defecto
        if "No pude identificar" in result:
            print("ERROR: Todavia muestra mensaje de error")
            return False
        
        # Verificar que contiene información de servicios
        if "SERVICIOS" in result.upper() or "servicio" in result.lower():
            print("EXITO: La respuesta contiene informacion de servicios")
            return True
        else:
            print("ERROR: La respuesta no contiene informacion de servicios")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    if test_servicios_fix():
        print("\nRESULTADO: FIX VERIFICADO EXITOSAMENTE")
        print("Los usuarios ya no veran el mensaje de error cuando escriban 'servicios'")
        return True
    else:
        print("\nRESULTADO: FIX NO FUNCIONA CORRECTAMENTE")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)