#!/usr/bin/env python3
"""
Test simple para validar la funcionalidad de captura de acompañantes
"""

import sys
import os
import json

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_parsing():
    """Test básico del parsing de acompañantes"""
    
    # Importar funciones del agente
    try:
        from agente import parse_reservation_details
        print("OK: Funciones importadas correctamente")
    except ImportError as e:
        print(f"ERROR: No se pudieron importar las funciones: {e}")
        return False
    
    # Caso de test simple
    test_input = """Luana mora, Carlos smith, YUSEF
Centaury
24/08/2025 hasta el 30/08/2025
Masajes
1 mascota
3203445423
tovar18025@gmail.com"""

    print("INICIANDO TEST DE PARSING...")
    print("Input de test:")
    print(test_input)
    print("-" * 50)
    
    try:
        # Parsear datos
        result = parse_reservation_details(test_input)
        
        if result:
            print("EXITO: Parsing completado")
            print("Resultado:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Verificar campos esperados
            expected_fields = ["nombres_huespedes", "numero_acompanantes", "domo", "fecha_entrada", "fecha_salida"]
            missing = [field for field in expected_fields if field not in result]
            
            if missing:
                print(f"ADVERTENCIA: Campos faltantes: {missing}")
            else:
                print("OK: Todos los campos esperados presentes")
            
            # Verificar nombres
            nombres = result.get("nombres_huespedes", [])
            print(f"Nombres extraidos: {nombres}")
            print(f"Numero de acompañantes: {result.get('numero_acompanantes', 'N/A')}")
            
            return True
        else:
            print("ERROR: parse_reservation_details retorno None")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== TEST SIMPLE DE ACOMPAÑANTES ===")
    success = test_parsing()
    print(f"\nRESULTADO: {'EXITO' if success else 'FALLO'}")
    sys.exit(0 if success else 1)