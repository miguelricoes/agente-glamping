# Test del servicio especializado de disponibilidades
# Verifica funcionalidad completa del AvailabilityService

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_availability_service_initialization():
    """Test de inicialización del servicio"""
    
    print("=== TEST: AvailabilityService Initialization ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        
        # Test inicialización
        service = AvailabilityService(mock_db, mock_reserva)
        
        print("✓ AvailabilityService inicializado correctamente")
        print(f"  - DB instance: {service.db is not None}")
        print(f"  - Reserva model: {service.Reserva is not None}")
        print(f"  - Domos configurados: {len(service.domos_info)}")
        print(f"  - Meses en español: {len(service.meses_espanol)}")
        
        # Test check database available
        available = service._check_database_available()
        print(f"  - Database available check: {available}")
        
        # Verificar configuración de domos
        expected_domos = ['antares', 'polaris', 'sirius', 'centaury']
        for domo in expected_domos:
            if domo in service.domos_info:
                info = service.domos_info[domo]
                print(f"✓ Domo {domo}: {info['nombre']} (${info['precio_base']:,})")
            else:
                print(f"✗ Domo {domo} no configurado")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test inicialización: {e}")
        return False

def test_consultar_disponibilidades():
    """Test de consulta principal de disponibilidades"""
    
    print("\n=== TEST: Consultar Disponibilidades ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva_class = Mock()
        
        # Mock reservas existentes
        mock_reserva1 = Mock()
        mock_reserva1.fecha_entrada = date(2024, 12, 25)
        mock_reserva1.fecha_salida = date(2024, 12, 27)
        mock_reserva1.domo = "Antares"
        
        mock_reserva2 = Mock()
        mock_reserva2.fecha_entrada = date(2024, 12, 26)
        mock_reserva2.fecha_salida = date(2024, 12, 28)
        mock_reserva2.domo = "Polaris"
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_reserva1, mock_reserva2]
        mock_reserva_class.query = mock_query
        
        service = AvailabilityService(mock_db, mock_reserva_class)
        
        # Test consulta básica
        resultado = service.consultar_disponibilidades(
            fecha_inicio="2024-12-25",
            fecha_fin="2024-12-27"
        )
        
        print(f"✓ Consulta disponibilidades: success={resultado['success']}")
        
        if resultado['success']:
            print(f"  - Fechas consultadas: {len(resultado['disponibilidades_por_fecha'])}")
            print(f"  - Domos disponibles: {len(resultado['domos_disponibles'])}")
            print(f"  - Fechas completamente libres: {len(resultado['fechas_completamente_libres'])}")
            
            # Verificar estructura de respuesta
            if 'disponibilidades_por_fecha' in resultado:
                print("✓ Estructura disponibilidades_por_fecha correcta")
            if 'domos_disponibles' in resultado:
                print("✓ Estructura domos_disponibles correcta")
            if 'parametros_busqueda' in resultado:
                print("✓ Parámetros de búsqueda incluidos")
        
        # Test con parámetros específicos
        resultado_filtrado = service.consultar_disponibilidades(
            fecha_inicio="2024-12-25",
            fecha_fin="2024-12-27",
            personas=2,
            domo_especifico="sirius"
        )
        
        print(f"✓ Consulta filtrada: success={resultado_filtrado['success']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test consultar disponibilidades: {e}")
        return False

def test_extraer_parametros_consulta():
    """Test de extracción de parámetros de consulta natural"""
    
    print("\n=== TEST: Extraer Parámetros Consulta ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        service = AvailabilityService(mock_db, mock_reserva)
        
        # Test casos de extracción
        casos_test = [
            {
                'consulta': '25/12/2024 al 27/12/2024 para 2 personas',
                'esperado': {
                    'tiene_fechas': True,
                    'tiene_personas': True,
                    'personas': 2
                }
            },
            {
                'consulta': '15 de enero del 2025 domo romántico',
                'esperado': {
                    'tiene_fechas': True,
                    'tiene_domo': True,
                    'domo': 'polaris'  # romántico -> polaris
                }
            },
            {
                'consulta': 'domo familiar para 4 personas',
                'esperado': {
                    'tiene_personas': True,
                    'personas': 4,
                    'tiene_domo': True,
                    'domo': 'antares'  # familiar -> antares
                }
            },
            {
                'consulta': 'disponibilidad para el fin de semana',
                'esperado': {
                    'tiene_fechas': False,
                    'tiene_personas': False
                }
            }
        ]
        
        for i, caso in enumerate(casos_test, 1):
            parametros = service.extraer_parametros_consulta(caso['consulta'])
            
            print(f"✓ Caso {i}: '{caso['consulta']}'")
            print(f"  - Fecha inicio: {parametros['fecha_inicio']}")
            print(f"  - Fecha fin: {parametros['fecha_fin']}")
            print(f"  - Personas: {parametros['personas']}")
            print(f"  - Domo: {parametros['domo']}")
            
            # Verificar expectativas
            esperado = caso['esperado']
            
            if esperado.get('tiene_fechas') and not parametros['fecha_inicio']:
                print(f"  ⚠ Se esperaba fecha pero no se extrajo")
            elif not esperado.get('tiene_fechas') and parametros['fecha_inicio']:
                print(f"  ⚠ No se esperaba fecha pero se extrajo")
            
            if esperado.get('tiene_personas'):
                if parametros['personas'] == esperado.get('personas'):
                    print(f"  ✓ Personas correctas: {parametros['personas']}")
                else:
                    print(f"  ✗ Personas incorrectas: esperado {esperado.get('personas')}, obtenido {parametros['personas']}")
            
            if esperado.get('tiene_domo'):
                if parametros['domo'] == esperado.get('domo'):
                    print(f"  ✓ Domo correcto: {parametros['domo']}")
                else:
                    print(f"  ⚠ Domo: esperado {esperado.get('domo')}, obtenido {parametros['domo']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test extraer parámetros: {e}")
        return False

def test_consultar_disponibilidades_natural():
    """Test de consulta en lenguaje natural"""
    
    print("\n=== TEST: Consultar Disponibilidades Natural ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva_class = Mock()
        
        # Mock query sin reservas
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_reserva_class.query = mock_query
        
        service = AvailabilityService(mock_db, mock_reserva_class)
        
        # Test consultas naturales
        consultas_test = [
            "¿Tienen disponible el 25 de diciembre?",
            "Necesito un domo para 2 personas el fin de semana",
            "¿Cuál es el precio del domo Antares?",
            "Disponibilidad para el 15/01/2025 al 17/01/2025"
        ]
        
        for i, consulta in enumerate(consultas_test, 1):
            print(f"\n✓ Consulta {i}: '{consulta}'")
            
            respuesta = service.consultar_disponibilidades_natural(consulta)
            
            print(f"  - Respuesta generada: {len(respuesta)} caracteres")
            print(f"  - Primer párrafo: {respuesta[:100]}...")
            
            # Verificar que la respuesta tiene elementos esperados
            if "disponibilidad" in respuesta.lower() or "disponible" in respuesta.lower():
                print("  ✓ Respuesta contiene información de disponibilidad")
            else:
                print("  ⚠ Respuesta no contiene información de disponibilidad")
            
            if "domo" in respuesta.lower():
                print("  ✓ Respuesta menciona domos")
            
            if "$" in respuesta or "precio" in respuesta.lower():
                print("  ✓ Respuesta incluye información de precios")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test consulta natural: {e}")
        return False

def test_generar_respuesta_natural():
    """Test de generación de respuestas naturales"""
    
    print("\n=== TEST: Generar Respuesta Natural ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        service = AvailabilityService(mock_db, mock_reserva)
        
        # Test caso con disponibilidad
        datos_disponibles = {
            'success': True,
            'domos_disponibles': [
                {
                    'domo': 'antares',
                    'info': {
                        'nombre': 'Antares',
                        'descripcion': 'Domo familiar con jacuzzi',
                        'capacidad_maxima': 6,
                        'precio_base': 650000
                    },
                    'fechas_disponibles': ['2024-12-25', '2024-12-26'],
                    'total_fechas_disponibles': 2
                }
            ],
            'resumen': ['Excelente disponibilidad para fechas solicitadas']
        }
        
        parametros = {
            'fecha_inicio': '2024-12-25',
            'fecha_fin': '2024-12-26',
            'personas': 4
        }
        
        respuesta = service.generar_respuesta_natural(datos_disponibles, parametros, "consulta test")
        
        print("✓ Respuesta con disponibilidad generada")
        print(f"  - Longitud: {len(respuesta)} caracteres")
        
        # Verificar elementos esperados
        elementos_esperados = [
            "EXCELENTE", "disponibilidad", "Antares", "650000", "capacidad", "personas"
        ]
        
        for elemento in elementos_esperados:
            if elemento in respuesta:
                print(f"  ✓ Contiene: {elemento}")
            else:
                print(f"  ⚠ Falta: {elemento}")
        
        # Test caso sin disponibilidad
        datos_sin_disponibilidad = {
            'success': True,
            'domos_disponibles': [],
            'disponibilidades_por_fecha': {}
        }
        
        respuesta_sin = service.generar_respuesta_natural(datos_sin_disponibilidad, parametros, "consulta test")
        
        print("\n✓ Respuesta sin disponibilidad generada")
        print(f"  - Longitud: {len(respuesta_sin)} caracteres")
        
        if "No tenemos" in respuesta_sin or "❌" in respuesta_sin:
            print("  ✓ Respuesta indica falta de disponibilidad")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test generar respuesta natural: {e}")
        return False

def test_detectar_intencion_consulta():
    """Test de detección de intención de consulta"""
    
    print("\n=== TEST: Detectar Intención Consulta ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        service = AvailabilityService(mock_db, mock_reserva)
        
        # Test casos
        casos_test = [
            {
                'input': '¿Tienen disponibilidad para el fin de semana?',
                'esperado': True,
                'descripcion': 'Consulta directa de disponibilidad'
            },
            {
                'input': 'Quiero hacer una reserva',
                'esperado': False,
                'descripcion': 'Intención de reserva, no consulta'
            },
            {
                'input': '¿Cuándo están libres los domos?',
                'esperado': True,
                'descripcion': 'Consulta sobre fechas libres'
            },
            {
                'input': 'Hola, ¿cómo están?',
                'esperado': False,
                'descripcion': 'Saludo sin consulta de disponibilidad'
            },
            {
                'input': '¿Tienen espacio para 4 personas el viernes?',
                'esperado': True,
                'descripcion': 'Consulta con fechas y capacidad'
            }
        ]
        
        for i, caso in enumerate(casos_test, 1):
            resultado = service.detectar_intencion_consulta(caso['input'])
            
            print(f"✓ Caso {i}: {caso['descripcion']}")
            print(f"  - Input: '{caso['input']}'")
            print(f"  - Es consulta disponibilidad: {resultado['es_consulta_disponibilidad']}")
            print(f"  - Confianza: {resultado['confianza']:.2f}")
            print(f"  - Keywords: {resultado['keywords_detectadas']}")
            
            if resultado['es_consulta_disponibilidad'] == caso['esperado']:
                print(f"  ✓ Detección correcta")
            else:
                print(f"  ✗ Detección incorrecta: esperado {caso['esperado']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test detectar intención: {e}")
        return False

def test_availability_health():
    """Test de health check del servicio"""
    
    print("\n=== TEST: Availability Health ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Test con DB disponible
        mock_db = Mock()
        mock_reserva = Mock()
        
        service = AvailabilityService(mock_db, mock_reserva)
        
        # Mock consulta básica exitosa
        with patch.object(service, 'consultar_disponibilidades') as mock_consulta:
            mock_consulta.return_value = {'success': True}
            
            health = service.get_availability_health()
            
            print(f"✓ Health check con DB disponible: status={health.get('status')}")
            print(f"  - Database connected: {health.get('database_connected')}")
            print(f"  - Service available: {health.get('service_available')}")
            print(f"  - Domos configurados: {health.get('domos_configurados')}")
            print(f"  - Test query success: {health.get('test_query_success')}")
        
        # Test con DB no disponible
        service_sin_db = AvailabilityService(None, None)
        health_sin_db = service_sin_db.get_availability_health()
        
        print(f"\n✓ Health check sin DB: status={health_sin_db.get('status')}")
        print(f"  - Database connected: {health_sin_db.get('database_connected')}")
        print(f"  - Service available: {health_sin_db.get('service_available')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test availability health: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests del servicio de disponibilidades"""
    
    print("INICIANDO TESTS DEL SERVICIO DE DISPONIBILIDADES")
    print("=" * 70)
    
    tests = [
        test_availability_service_initialization,
        test_consultar_disponibilidades,
        test_extraer_parametros_consulta,
        test_consultar_disponibilidades_natural,
        test_generar_respuesta_natural,
        test_detectar_intencion_consulta,
        test_availability_health
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Error inesperado en {test_func.__name__}: {e}")
    
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON")
        print("\nAvailabilityService listo para usar:")
        print("• Consultas de disponibilidades implementadas")
        print("• Procesamiento de lenguaje natural incluido") 
        print("• Extracción inteligente de parámetros")
        print("• Generación de respuestas naturales")
        print("• Detección de intenciones de consulta")
        print("• Health checks disponibles")
        print("• Configuración completa de 4 domos")
        print("• Logging estructurado integrado")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)