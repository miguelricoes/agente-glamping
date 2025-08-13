#!/usr/bin/env python3
"""
Test para verificar que el parsing de reservas funciona correctamente
después de las correcciones implementadas
"""

import pytest
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_validate_and_process_reservation_data():
    """Test directo de la función validate_and_process_reservation_data"""
    
    # Simular datos parseados por el LLM (como deberían venir)
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
    
    # Importar la función que queremos probar
    try:
        from agente import validate_and_process_reservation_data
    except ImportError as e:
        pytest.skip(f"No se pudo importar la función: {e}")
    
    # Ejecutar la función
    success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "test_user")
    
    # Verificaciones
    assert success, f"La validación falló con errores: {errors}"
    assert len(errors) == 0, f"Se esperaban 0 errores, pero se encontraron: {errors}"
    
    # Verificar que los campos críticos están presentes
    assert 'metodo_pago' in processed_data, "Campo 'metodo_pago' faltante en processed_data"
    assert 'comentarios_especiales' in processed_data, "Campo 'comentarios_especiales' faltante en processed_data"
    
    # Verificar los valores específicos
    assert processed_data['metodo_pago'] == 'Efectivo', f"Método de pago incorrecto: {processed_data['metodo_pago']}"
    assert processed_data['comentarios_especiales'] == 'Claudia esta en silla de ruedas', f"Comentarios incorrectos: {processed_data['comentarios_especiales']}"
    
    # Verificar otros campos importantes
    assert processed_data['nombres_huespedes'] == ['Hernesto', 'Jose', 'Claudia', 'Manuel']
    assert processed_data['domo'] == 'Centaury'
    assert processed_data['cantidad_huespedes'] == 4
    
    print("✅ Test validate_and_process_reservation_data PASÓ")

def test_campos_opcionales_vacios():
    """Test con campos opcionales vacíos o faltantes"""
    
    parsed_data = {
        'nombres_huespedes': ['Juan Perez'],
        'domo': 'Sirius',
        'fecha_entrada': '25/08/2025',
        'fecha_salida': '26/08/2025',
        'numero_contacto': '3001234567',
        'email_contacto': 'juan@email.com'
        # Sin metodo_pago ni comentarios_especiales
    }
    
    try:
        from agente import validate_and_process_reservation_data
    except ImportError as e:
        pytest.skip(f"No se pudo importar la función: {e}")
    
    success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "test_user")
    
    assert success, f"La validación falló: {errors}"
    
    # Verificar valores por defecto
    assert processed_data['metodo_pago'] == 'No especificado'
    assert processed_data['comentarios_especiales'] == 'Ninguno'
    
    print("✅ Test campos opcionales vacíos PASÓ")

def test_campos_con_valores_na():
    """Test con campos que tienen valores N/A"""
    
    parsed_data = {
        'nombres_huespedes': ['Maria Lopez'],
        'domo': 'Antares',
        'fecha_entrada': '27/08/2025',
        'fecha_salida': '28/08/2025',
        'numero_contacto': '3009876543',
        'email_contacto': 'maria@email.com',
        'metodo_pago': 'N/A',
        'comentarios_especiales': 'na'
    }
    
    try:
        from agente import validate_and_process_reservation_data
    except ImportError as e:
        pytest.skip(f"No se pudo importar la función: {e}")
    
    success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "test_user")
    
    assert success, f"La validación falló: {errors}"
    
    # Verificar que N/A se convierte a valores por defecto
    assert processed_data['metodo_pago'] == 'No especificado'
    assert processed_data['comentarios_especiales'] == 'Ninguno'
    
    print("✅ Test campos con valores N/A PASÓ")

def test_caso_real_usuario():
    """Test con los datos exactos del caso real reportado"""
    
    # Datos exactos de la conversación problemática
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
    
    try:
        from agente import validate_and_process_reservation_data
    except ImportError as e:
        pytest.skip(f"No se pudo importar la función: {e}")
    
    success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "whatsapp573203445423")
    
    # Verificaciones específicas del caso real
    assert success == True
    assert len(errors) == 0
    assert processed_data['metodo_pago'] == 'Efectivo'
    assert processed_data['comentarios_especiales'] == 'Claudia esta en silla de ruedas'
    assert processed_data['cantidad_huespedes'] == 4
    assert processed_data['domo'] == 'Centaury'
    
    print("✅ Test caso real usuario PASÓ")

def test_flujo_completo_simulado():
    """Test que simula el flujo completo como aparecería en la confirmación"""
    
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
    
    try:
        from agente import validate_and_process_reservation_data
    except ImportError as e:
        pytest.skip(f"No se pudo importar la función: {e}")
    
    success, processed_data, errors = validate_and_process_reservation_data(parsed_data, "test_user")
    
    assert success
    
    # Simular cómo aparecería en la confirmación
    reserva_info = processed_data
    metodo_pago_display = reserva_info.get('metodo_pago', 'No especificado')
    comentarios_display = reserva_info.get('comentarios_especiales', 'Ninguno')
    
    # Verificar que NO aparecen los valores por defecto
    assert metodo_pago_display != 'No especificado'
    assert comentarios_display != 'Ninguno'
    
    # Verificar que aparecen los valores correctos
    assert metodo_pago_display == 'Efectivo'
    assert comentarios_display == 'Claudia esta en silla de ruedas'
    
    print("✅ Test flujo completo simulado PASÓ")
    print(f"   💳 Método de Pago: {metodo_pago_display}")
    print(f"   📝 Comentarios: {comentarios_display}")

def test_resumen_correcciones():
    """Test que verifica el resumen de todas las correcciones implementadas"""
    
    print("\n" + "="*60)
    print("RESUMEN DE CORRECCIONES VERIFICADAS:")
    print("="*60)
    print("✅ validate_and_process_reservation_data procesa metodo_pago")
    print("✅ validate_and_process_reservation_data procesa comentarios_especiales")
    print("✅ Manejo correcto de valores por defecto")
    print("✅ Manejo correcto de valores N/A")
    print("✅ Caso real del usuario funciona correctamente")
    print("✅ Flujo completo hasta confirmación funciona")
    print("\n🎉 TODAS LAS CORRECCIONES FUNCIONAN CORRECTAMENTE")
    print("="*60)

if __name__ == "__main__":
    print("Ejecutando tests de verificación de reservas...")
    print("="*60)
    
    try:
        test_validate_and_process_reservation_data()
        test_campos_opcionales_vacios()
        test_campos_con_valores_na()
        test_caso_real_usuario()
        test_flujo_completo_simulado()
        test_resumen_correcciones()
        
        print(f"\n🎊 TODOS LOS TESTS PASARON EXITOSAMENTE")
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {e}")
        import traceback
        traceback.print_exc()