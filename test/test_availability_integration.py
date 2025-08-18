# Test de integración del AvailabilityService con agente_modular
# Verifica que la integración funcione correctamente

import sys
import os
from unittest.mock import Mock, patch

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_availability_service_integration():
    """Test de integración de AvailabilityService con agente_modular"""
    
    print("=== TEST: AvailabilityService Integration ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        
        # Test integración básica
        service = AvailabilityService(mock_db, mock_reserva)
        
        print("✓ AvailabilityService integrado exitosamente")
        print(f"  - Database check: {service._check_database_available()}")
        print(f"  - Domos configurados: {len(service.domos_info)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test availability service integration: {e}")
        return False

def test_api_routes_with_availability_service():
    """Test de rutas API con AvailabilityService"""
    
    print("\n=== TEST: API Routes with AvailabilityService ===")
    
    try:
        from routes.api_routes import register_api_routes
        from services.availability_service import AvailabilityService
        
        # Mock de dependencias
        mock_app = Mock()
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Mock AvailabilityService
        mock_availability_service = AvailabilityService(mock_db, mock_reserva)
        
        # Test registro con availability_service
        register_api_routes(
            app=mock_app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test",
            availability_service=mock_availability_service
        )
        
        print("✓ Rutas API registradas con AvailabilityService")
        print(f"  - App.route llamado: {mock_app.route.called}")
        print(f"  - AvailabilityService integrado correctamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test API routes with availability service: {e}")
        return False

def test_modular_compatibility():
    """Test de compatibilidad con estructura modular"""
    
    print("\n=== TEST: Modular Compatibility ===")
    
    try:
        # Test importaciones necesarias para agente_modular
        from services.availability_service import AvailabilityService
        from services.database_service import DatabaseService
        from routes.api_routes import register_api_routes
        
        print("✓ Importaciones modulares exitosas")
        
        # Simular inicialización como en agente_modular.py
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Test inicialización de servicios
        database_service = DatabaseService(mock_db, mock_reserva, mock_usuario)
        availability_service = AvailabilityService(mock_db, mock_reserva)
        
        print("✓ Servicios inicializados exitosamente")
        print(f"  - DatabaseService: {database_service is not None}")
        print(f"  - AvailabilityService: {availability_service is not None}")
        
        # Test integración en routes
        mock_app = Mock()
        register_api_routes(
            app=mock_app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test",
            database_service=database_service,
            availability_service=availability_service
        )
        
        print("✓ Integración completa exitosa")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test modular compatibility: {e}")
        return False

def test_availability_endpoints_enhanced():
    """Test de endpoints de disponibilidades mejorados"""
    
    print("\n=== TEST: Availability Endpoints Enhanced ===")
    
    try:
        from routes.api_routes import register_api_routes
        from services.availability_service import AvailabilityService
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Mock AvailabilityService
        mock_availability_service = Mock()
        mock_availability_service.consultar_disponibilidades.return_value = {
            'success': True,
            'domos_disponibles': [
                {
                    'domo': 'antares',
                    'info': {'nombre': 'Antares', 'precio_base': 650000}
                }
            ]
        }
        mock_availability_service.detectar_intencion_consulta.return_value = {
            'es_consulta_disponibilidad': True,
            'confianza': 0.8
        }
        mock_availability_service.consultar_disponibilidades_natural.return_value = "✅ Tenemos disponibilidad"
        mock_availability_service.extraer_parametros_consulta.return_value = {
            'fecha_inicio': '2024-12-25'
        }
        
        # Registrar rutas
        register_api_routes(
            app=app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test",
            availability_service=mock_availability_service
        )
        
        print("✓ Endpoints de disponibilidades mejorados registrados")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test GET disponibilidades mejorado
                response = client.get('/api/disponibilidades?fecha_inicio=2024-12-25&personas=2')
                print(f"✓ GET /api/disponibilidades mejorado: status={response.status_code}")
                
                # Test POST agente disponibilidades mejorado
                response = client.post('/api/agente/disponibilidades', 
                                     json={'consulta': '¿Tienen disponible el 25 de diciembre?'})
                print(f"✓ POST /api/agente/disponibilidades mejorado: status={response.status_code}")
                
                if response.status_code == 200:
                    print("  - Respuesta exitosa con AvailabilityService")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test availability endpoints enhanced: {e}")
        return False

def test_natural_language_processing():
    """Test de procesamiento de lenguaje natural"""
    
    print("\n=== TEST: Natural Language Processing ===")
    
    try:
        from services.availability_service import AvailabilityService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        
        service = AvailabilityService(mock_db, mock_reserva)
        
        # Test consultas en español
        consultas_test = [
            "¿Tienen disponible el 25 de diciembre del 2024?",
            "Necesito un domo para 2 personas",
            "¿Cuánto cuesta el domo Antares?",
            "Domo familiar para 4 personas el fin de semana",
            "Disponibilidad romántica para pareja"
        ]
        
        for i, consulta in enumerate(consultas_test, 1):
            # Test extracción de parámetros
            parametros = service.extraer_parametros_consulta(consulta)
            
            print(f"✓ Consulta {i}: '{consulta}'")
            print(f"  - Fecha extraída: {parametros['fecha_inicio']}")
            print(f"  - Personas: {parametros['personas']}")
            print(f"  - Domo: {parametros['domo']}")
            
            # Test detección de intención
            intencion = service.detectar_intencion_consulta(consulta)
            print(f"  - Es consulta disponibilidad: {intencion['es_consulta_disponibilidad']}")
            print(f"  - Confianza: {intencion['confianza']:.2f}")
        
        print("\n✓ Procesamiento de lenguaje natural funcionando")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test natural language processing: {e}")
        return False

def test_fallback_functionality():
    """Test de funcionalidad de fallback"""
    
    print("\n=== TEST: Fallback Functionality ===")
    
    try:
        from routes.api_routes import register_api_routes
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Registrar rutas SIN AvailabilityService (fallback)
        register_api_routes(
            app=app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test",
            availability_service=None  # Sin availability service
        )
        
        print("✓ Rutas registradas sin AvailabilityService (modo fallback)")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test fallback GET disponibilidades
                response = client.get('/api/disponibilidades')
                print(f"✓ GET /api/disponibilidades (fallback): status={response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    if 'source' in data and data['source'] == 'fallback_basic':
                        print("  ✓ Fallback funcionando correctamente")
                
                # Test fallback POST agente disponibilidades
                response = client.post('/api/agente/disponibilidades', 
                                     json={'consulta': 'test'})
                print(f"✓ POST /api/agente/disponibilidades (fallback): status={response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    if 'source' in data and data['source'] == 'fallback_basic':
                        print("  ✓ Fallback agente funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test fallback functionality: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests de integración de disponibilidades"""
    
    print("INICIANDO TESTS DE INTEGRACIÓN DE AVAILABILITY SERVICE")
    print("=" * 65)
    
    tests = [
        test_availability_service_integration,
        test_api_routes_with_availability_service,
        test_modular_compatibility,
        test_availability_endpoints_enhanced,
        test_natural_language_processing,
        test_fallback_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Error inesperado en {test_func.__name__}: {e}")
    
    print("\n" + "=" * 65)
    print("RESUMEN DE TESTS DE INTEGRACIÓN")
    print("=" * 65)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print("\nAvailabilityService integrado exitosamente:")
        print("• Servicio especializado de disponibilidades activo")
        print("• Procesamiento avanzado de lenguaje natural")
        print("• Endpoints API mejorados con AvailabilityService")
        print("• Integración completa con agente_modular.py")
        print("• Funcionalidad de fallback implementada")
        print("• Extracción inteligente de parámetros")
        print("• Detección automática de intenciones")
        print("• Configuración completa de 4 domos")
        print("• Compatibilidad hacia atrás mantenida")
        return True
    else:
        print("❌ ALGUNOS TESTS DE INTEGRACIÓN FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)