#!/usr/bin/env python3
"""
Test completo del flujo de disponibilidades mejorado (sin emojis)
Verifica todas las mejoras implementadas
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path para importar el módulo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar funciones del agente
from agente import (
    extraer_parametros_consulta,
    consultar_disponibilidades_interna,
    generar_respuesta_natural_disponibilidades,
    consultar_disponibilidades_glamping
)

class TestDisponibilidadesMejorado:
    """Suite de tests para el flujo de disponibilidades mejorado"""
    
    def test_parser_fechas_espanol(self):
        """1. Procesar fechas en español: '24 de diciembre del 2025'"""
        print("\nTest 1: Parser de fechas en español")
        
        # Test fechas en español
        consultas_fechas = [
            "24 de diciembre del 2025",
            "15 de agosto de 2025", 
            "3 de enero",
            "25/12/2024",
            "2025-08-15",
            "¿Qué domos están disponibles el 24 de diciembre del 2025?"
        ]
        
        for consulta in consultas_fechas:
            print(f"Probando: '{consulta}'")
            parametros = extraer_parametros_consulta(consulta)
            
            # Verificar que se extrajo una fecha
            assert parametros['fecha_inicio'] is not None, f"No se extrajo fecha de: {consulta}"
            
            # Verificar formato YYYY-MM-DD
            fecha = parametros['fecha_inicio']
            assert len(fecha) == 10, f"Formato de fecha incorrecto: {fecha}"
            assert fecha[4] == '-' and fecha[7] == '-', f"Formato de fecha incorrecto: {fecha}"
            
            print(f"OK - Fecha extraída: {fecha}")
    
    def test_parser_domos_y_personas(self):
        """Test extracción de domos y número de personas"""
        print("\nTest: Parser de domos y personas")
        
        consultas = [
            ("¿Está disponible Antares para 2 personas?", "antares", 2),
            ("Polaris para 4 huespedes", "polaris", 4),
            ("somos 6 y queremos sirius", "sirius", 6),
            ("centaury para una pareja", "centaury", None)
        ]
        
        for consulta, domo_esperado, personas_esperado in consultas:
            print(f"Probando: '{consulta}'")
            parametros = extraer_parametros_consulta(consulta)
            
            if domo_esperado:
                assert parametros['domo'] == domo_esperado, f"Domo incorrecto: {parametros['domo']}"
                print(f"OK - Domo detectado: {parametros['domo']}")
                
            if personas_esperado:
                assert parametros['personas'] == personas_esperado, f"Personas incorrectas: {parametros['personas']}"
                print(f"OK - Personas detectadas: {parametros['personas']}")

    @patch('agente.database_available', True)
    @patch('agente.db')
    @patch('agente.Reserva')
    def test_consulta_disponibilidades_sin_errores(self, mock_reserva, mock_db):
        """2. Consultar disponibilidades sin errores HTTP"""
        print("\nTest 2: Consulta disponibilidades sin errores HTTP")
        
        # Mock de reservas vacías
        mock_reserva.query.filter.return_value.all.return_value = []
        
        # Test parámetros básicos
        resultado = consultar_disponibilidades_interna(
            fecha_inicio="2025-12-24",
            fecha_fin="2025-12-25",
            domo=None,
            personas=2
        )
        
        print(f"Resultado keys: {list(resultado.keys())}")
        
        # Verificaciones
        assert resultado['success'] == True, "La consulta debe ser exitosa"
        assert 'disponibilidades_por_fecha' in resultado, "Debe incluir disponibilidades por fecha"
        assert 'domos_disponibles' in resultado, "Debe incluir domos disponibles"
        assert 'parametros_busqueda' in resultado, "Debe incluir parámetros de búsqueda"
        
        print("OK - Consulta exitosa sin errores HTTP")

    @patch('agente.database_available', True)
    @patch('agente.db')
    @patch('agente.Reserva')
    def test_respuesta_informacion_especifica(self, mock_reserva, mock_db):
        """3. Responder con información específica y útil"""
        print("\nTest 3: Respuesta con información específica")
        
        # Mock de reservas vacías (todos los domos disponibles)
        mock_reserva.query.filter.return_value.all.return_value = []
        
        # Simular consulta completa
        parametros = {
            'fecha_inicio': '2025-12-24',
            'fecha_fin': None,
            'domo': None,
            'personas': 2
        }
        
        datos_disponibilidades = consultar_disponibilidades_interna(
            fecha_inicio=parametros['fecha_inicio'],
            fecha_fin=parametros['fecha_fin'],
            domo=parametros['domo'],
            personas=parametros['personas']
        )
        
        respuesta = generar_respuesta_natural_disponibilidades(
            datos_disponibilidades,
            parametros,
            "¿Qué domos están disponibles para 2 personas el 24 de diciembre?"
        )
        
        print(f"Respuesta generada: {respuesta[:100]}...")
        
        # Verificaciones de contenido específico
        assert "¡Excelente!" in respuesta, "Debe incluir saludo positivo"
        assert any(domo in respuesta.lower() for domo in ['antares', 'polaris', 'sirius', 'centaury']), "Debe mencionar domos"
        assert "$" in respuesta, "Debe incluir precios"
        assert "reserva" in respuesta.lower(), "Debe incluir llamada a la acción"
        
        print("OK - Respuesta contiene información específica y útil")

    def test_multiples_formatos_fecha(self):
        """4. Manejar múltiples formatos de fecha"""
        print("\nTest 4: Múltiples formatos de fecha")
        
        formatos_fecha = [
            "24/12/2025",           # DD/MM/YYYY
            "24-12-2025",           # DD-MM-YYYY  
            "2025-12-24",           # YYYY-MM-DD
            "24 de diciembre del 2025",  # DD de MMMM del YYYY
            "15 de agosto",         # DD de MMMM (año actual)
            "3 de enero de 2026"    # DD de MMMM de YYYY
        ]
        
        for formato in formatos_fecha:
            print(f"Probando formato: '{formato}'")
            consulta = f"¿Disponibilidad para {formato}?"
            parametros = extraer_parametros_consulta(consulta)
            
            # Verificar que se extrajo fecha
            assert parametros['fecha_inicio'] is not None, f"No se procesó formato: {formato}"
            
            # Verificar formato normalizado
            fecha = parametros['fecha_inicio']
            partes = fecha.split('-')
            assert len(partes) == 3, f"Fecha mal formateada: {fecha}"
            assert len(partes[0]) == 4, f"Año incorrecto: {fecha}"
            assert 1 <= int(partes[1]) <= 12, f"Mes incorrecto: {fecha}"
            assert 1 <= int(partes[2]) <= 31, f"Día incorrecto: {fecha}"
            
            print(f"OK - Formato procesado correctamente: {fecha}")

    @patch('agente.database_available', True)
    @patch('agente.db')
    @patch('agente.Reserva')
    def test_detalles_domos_disponibles(self, mock_reserva, mock_db):
        """5. Proporcionar detalles de domos disponibles"""
        print("\nTest 5: Detalles de domos disponibles")
        
        # Mock de reservas que ocupan algunos domos
        reserva_mock = Mock()
        reserva_mock.domo = "Antares"
        reserva_mock.fecha_entrada = datetime(2025, 12, 24).date()
        reserva_mock.fecha_salida = datetime(2025, 12, 25).date()
        
        mock_reserva.query.filter.return_value.all.return_value = [reserva_mock]
        
        resultado = consultar_disponibilidades_interna(
            fecha_inicio="2025-12-24",
            fecha_fin="2025-12-24",
            domo=None,
            personas=None
        )
        
        print(f"Domos disponibles: {len(resultado['domos_disponibles'])}")
        
        # Verificaciones de detalles
        assert resultado['success'] == True, "Consulta debe ser exitosa"
        
        domos_disponibles = resultado['domos_disponibles']
        assert len(domos_disponibles) >= 1, "Debe haber al menos un domo disponible"
        
        # Verificar estructura de datos de domo
        if domos_disponibles:
            domo = domos_disponibles[0]
            assert 'domo' in domo, "Debe incluir nombre del domo"
            assert 'info' in domo, "Debe incluir información del domo"
            assert 'fechas_disponibles' in domo, "Debe incluir fechas disponibles"
            
            info = domo['info']
            assert 'nombre' in info, "Debe incluir nombre del domo"
            assert 'capacidad_maxima' in info, "Debe incluir capacidad máxima"
            assert 'precio_base' in info, "Debe incluir precio base"
            assert 'descripcion' in info, "Debe incluir descripción"
            
            print(f"OK - Domo: {info['nombre']}, Capacidad: {info['capacidad_maxima']}, Precio: ${info['precio_base']:,}")

    def test_flujo_completo_integracion(self):
        """Test de integración completo del flujo"""
        print("\nTest: Flujo completo de integración")
        
        consultas_test = [
            "¿Está disponible Antares el 24 de diciembre del 2025?",
            "Necesito domo para 4 personas el 15 de agosto",
            "¿Qué domos tienen el 31/12/2024?",
            "Polaris para 2 personas el 2025-06-15"
        ]
        
        for consulta in consultas_test:
            print(f"\nProbando consulta completa: '{consulta}'")
            
            # 1. Extraer parámetros
            parametros = extraer_parametros_consulta(consulta)
            print(f"   Parámetros: {parametros}")
            
            # 2. Verificar extracción básica
            assert parametros['fecha_inicio'] is not None, "Debe extraer fecha"
            
            # 3. Test con mock para evitar dependencias de DB
            with patch('agente.database_available', True), \
                 patch('agente.db'), \
                 patch('agente.Reserva') as mock_reserva:
                
                mock_reserva.query.filter.return_value.all.return_value = []
                
                # 4. Consultar disponibilidades
                datos = consultar_disponibilidades_interna(
                    fecha_inicio=parametros['fecha_inicio'],
                    fecha_fin=parametros['fecha_fin'],
                    domo=parametros['domo'],
                    personas=parametros['personas']
                )
                
                assert datos['success'] == True, "Consulta debe ser exitosa"
                
                # 5. Generar respuesta natural
                respuesta = generar_respuesta_natural_disponibilidades(
                    datos, parametros, consulta
                )
                
                assert len(respuesta) > 20, "Respuesta debe tener contenido"
                assert "error" not in respuesta.lower(), "No debe contener mensajes de error"
                
                print(f"   OK - Respuesta: {respuesta[:80]}...")

def run_tests():
    """Ejecuta todos los tests"""
    print("INICIANDO TESTS DEL FLUJO DE DISPONIBILIDADES MEJORADO")
    print("=" * 60)
    
    # Crear instancia de tests
    test_instance = TestDisponibilidadesMejorado()
    
    tests = [
        ("Parser fechas español", test_instance.test_parser_fechas_espanol),
        ("Parser domos y personas", test_instance.test_parser_domos_y_personas),
        ("Consulta sin errores HTTP", test_instance.test_consulta_disponibilidades_sin_errores),
        ("Respuesta información específica", test_instance.test_respuesta_informacion_especifica),
        ("Múltiples formatos fecha", test_instance.test_multiples_formatos_fecha),
        ("Detalles domos disponibles", test_instance.test_detalles_domos_disponibles),
        ("Flujo completo integración", test_instance.test_flujo_completo_integracion)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n[EJECUTANDO] {test_name}")
            test_func()
            print(f"[EXITO] {test_name}")
            passed += 1
        except Exception as e:
            print(f"[ERROR] {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESUMEN DE TESTS:")
    print(f"✓ Tests exitosos: {passed}")
    print(f"✗ Tests fallidos: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("\nTODOS LOS TESTS PASARON EXITOSAMENTE")
        print("El flujo de disponibilidades funciona correctamente")
        print("Las mejoras implementadas están operativas")
        return True
    else:
        print(f"\n{failed} tests fallaron. Revisar errores arriba.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)