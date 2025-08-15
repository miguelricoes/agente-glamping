#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar la corrección de parsing de reservas
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_validation():
    """Test básico de validación de reservas"""
    
    print("Test: Verificando corrección de metodo_pago y comentarios_especiales")
    print("=" * 70)
    
    # Datos de prueba (simulando lo que devuelve el LLM)
    parsed_data = {
        'nombres_huespedes': ['Hernesto', 'Jose', 'Claudia', 'Manuel'],
        'numero_acompanantes': '4',
        'domo': 'Centaury',
        'fecha_entrada': '24/08/2025',
        'fecha_salida': '30/08/2025',
        'servicio_elegido': 'Masajes',
        'adicciones': '1 mascota',
        'numero_contacto': '3203445423',
        'email_contacto': 'tovar18025@gmail.com',
        'metodo_pago': 'Efectivo',
        'comentarios_especiales': 'Claudia esta en silla de ruedas'
    }
    
    print("Datos de entrada:")
    print("- metodo_pago:", parsed_data['metodo_pago'])
    print("- comentarios_especiales:", parsed_data['comentarios_especiales'])
    print()
    
    try:
        # Importar función de validación
        from agente import validate_and_process_reservation_data
        
        print("Ejecutando validate_and_process_reservation_data...")
        success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "test_user")
        
        print(f"Success: {success}")
        print(f"Errors: {errors}")
        print()
        
        if not success:
            print("ERROR: La validacion fallo con errores:", errors)
            return False
        
        # Verificar que los campos están presentes
        has_metodo_pago = 'metodo_pago' in processed_data
        has_comentarios = 'comentarios_especiales' in processed_data
        
        print("Verificaciones:")
        print(f"- Campo 'metodo_pago' presente: {has_metodo_pago}")
        print(f"- Campo 'comentarios_especiales' presente: {has_comentarios}")
        
        if has_metodo_pago:
            print(f"- Valor metodo_pago: '{processed_data['metodo_pago']}'")
        
        if has_comentarios:
            print(f"- Valor comentarios_especiales: '{processed_data['comentarios_especiales']}'")
        
        print()
        
        # Verificaciones de éxito
        if not has_metodo_pago:
            print("FALLO: Campo metodo_pago no esta presente")
            return False
            
        if not has_comentarios:
            print("FALLO: Campo comentarios_especiales no esta presente")
            return False
            
        if processed_data['metodo_pago'] != 'Efectivo':
            print(f"FALLO: metodo_pago incorrecto: '{processed_data['metodo_pago']}' (esperado: 'Efectivo')")
            return False
            
        if processed_data['comentarios_especiales'] != 'Claudia esta en silla de ruedas':
            print(f"FALLO: comentarios_especiales incorrecto: '{processed_data['comentarios_especiales']}'")
            return False
        
        print("ÉXITO: Todos los campos se procesaron correctamente")
        return True
        
    except ImportError as e:
        print(f"ERROR: No se pudo importar la función: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Exception durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_valores_por_defecto():
    """Test de valores por defecto cuando faltan campos"""
    
    print("\n" + "=" * 70)
    print("Test: Verificando valores por defecto")
    print("=" * 70)
    
    # Datos sin metodo_pago ni comentarios_especiales
    parsed_data = {
        'nombres_huespedes': ['Juan Perez'],
        'domo': 'Sirius',
        'fecha_entrada': '25/08/2025',
        'fecha_salida': '26/08/2025',
        'numero_contacto': '3001234567',
        'email_contacto': 'juan@email.com'
    }
    
    try:
        from agente import validate_and_process_reservation_data
        
        success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "test_user")
        
        if not success:
            print("ERROR: La validacion fallo:", errors)
            return False
        
        metodo_pago = processed_data.get('metodo_pago', 'CAMPO_FALTANTE')
        comentarios = processed_data.get('comentarios_especiales', 'CAMPO_FALTANTE')
        
        print(f"metodo_pago (por defecto): '{metodo_pago}'")
        print(f"comentarios_especiales (por defecto): '{comentarios}'")
        
        if metodo_pago != 'No especificado':
            print(f"FALLO: Valor por defecto incorrecto para metodo_pago: '{metodo_pago}'")
            return False
            
        if comentarios != 'Ninguno':
            print(f"FALLO: Valor por defecto incorrecto para comentarios: '{comentarios}'")
            return False
        
        print("ÉXITO: Valores por defecto correctos")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Ejecutando tests de verificación...")
    print()
    
    test1_result = test_basic_validation()
    test2_result = test_valores_por_defecto()
    
    print("\n" + "=" * 70)
    print("RESUMEN DE RESULTADOS:")
    print("=" * 70)
    print(f"Test campos completos: {'PASO' if test1_result else 'FALLO'}")
    print(f"Test valores por defecto: {'PASO' if test2_result else 'FALLO'}")
    
    if test1_result and test2_result:
        print("\nTODOS LOS TESTS PASARON - CORRECCIÓN VERIFICADA")
    else:
        print("\nALGUNOS TESTS FALLARON - REVISAR IMPLEMENTACIÓN")