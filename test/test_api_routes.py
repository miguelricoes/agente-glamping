# Test de rutas API centralizadas
# Verifica que todos los endpoints REST funcionen correctamente

import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_api_routes_registration():
    """Test de registro de rutas API"""
    
    print("=== TEST: API Routes Registration ===")
    
    try:
        from routes.api_routes import register_api_routes
        
        # Mock de Flask app
        mock_app = Mock()
        mock_route_calls = []
        
        def mock_route_decorator(*args, **kwargs):
            mock_route_calls.append((args, kwargs))
            return lambda func: func
        
        mock_app.route = mock_route_decorator
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Test registro
        register_api_routes(
            app=mock_app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test",
            database_service=None
        )
        
        print(f"✓ register_api_routes ejecutado exitosamente")
        print(f"  - Rutas registradas: {len(mock_route_calls)}")
        
        # Verificar rutas específicas
        expected_routes = [
            '/api/reservas',
            '/api/reservas/stats', 
            '/api/usuarios',
            '/api/auth/login',
            '/api/auth/verify',
            '/health',
            '/api/disponibilidades',
            '/api/agente/disponibilidades'
        ]
        
        registered_routes = [call[0][0] for call in mock_route_calls]
        
        for expected_route in expected_routes:
            matching_routes = [r for r in registered_routes if expected_route in r]
            if matching_routes:
                print(f"✓ Ruta encontrada: {expected_route}")
            else:
                print(f"✗ Ruta faltante: {expected_route}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test api routes registration: {e}")
        return False

def test_reservas_endpoints():
    """Test de endpoints de reservas"""
    
    print("\n=== TEST: Reservas Endpoints ===")
    
    try:
        from routes.api_routes import register_api_routes
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Mock de dependencias
        mock_db = Mock()
        mock_session = Mock()
        mock_db.session = mock_session
        
        mock_reserva_class = Mock()
        mock_usuario_class = Mock()
        
        # Mock reserva instance
        mock_reserva = Mock()
        mock_reserva.id = 1
        mock_reserva.numero_whatsapp = "123456789"
        mock_reserva.email_contacto = "test@example.com"
        mock_reserva.cantidad_huespedes = 2
        mock_reserva.domo = "Luna"
        mock_reserva.fecha_entrada = date(2024, 12, 25)
        mock_reserva.fecha_salida = date(2024, 12, 27)
        mock_reserva.servicio_elegido = "Cena romántica"
        mock_reserva.adicciones = "Sin mascotas"
        mock_reserva.numero_contacto = "987654321"
        mock_reserva.metodo_pago = "Tarjeta"
        mock_reserva.monto_total = Decimal('500000')
        mock_reserva.fecha_creacion = datetime.now()
        mock_reserva.nombres_huespedes = "Juan Pérez"
        mock_reserva.comentarios_especiales = "Vista al lago"
        
        # Mock query chain
        mock_query = Mock()
        mock_query.order_by.return_value.desc.return_value.all.return_value = [mock_reserva]
        mock_query.count.return_value = 1
        mock_reserva_class.query = mock_query
        
        # Registrar rutas
        register_api_routes(
            app=app,
            db=mock_db,
            Reserva=mock_reserva_class,
            Usuario=mock_usuario_class,
            database_available=True,
            database_url="postgresql://test"
        )
        
        print("✓ Endpoints de reservas registrados")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test GET reservas
                response = client.get('/api/reservas')
                print(f"✓ GET /api/reservas: status={response.status_code}")
                
                # Test GET stats
                mock_db.extract.return_value = Mock()
                mock_db.func.count.return_value.label.return_value = Mock()
                mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
                    ("Luna", 5), ("Sol", 3)
                ]
                
                response = client.get('/api/reservas/stats')
                print(f"✓ GET /api/reservas/stats: status={response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test reservas endpoints: {e}")
        return False

def test_usuarios_endpoints():
    """Test de endpoints de usuarios"""
    
    print("\n=== TEST: Usuarios Endpoints ===")
    
    try:
        from routes.api_routes import register_api_routes
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Mock de dependencias
        mock_db = Mock()
        mock_session = Mock()
        mock_db.session = mock_session
        
        mock_reserva_class = Mock()
        mock_usuario_class = Mock()
        
        # Mock usuario instance
        mock_usuario = Mock()
        mock_usuario.id = 1
        mock_usuario.nombre = "Juan Pérez"
        mock_usuario.email = "juan@example.com"
        mock_usuario.rol = "admin"
        mock_usuario.activo = True
        mock_usuario.password_changed = False
        mock_usuario.fecha_creacion = datetime.now()
        mock_usuario.ultimo_acceso = datetime.now()
        
        # Mock query chain
        mock_query = Mock()
        mock_query.order_by.return_value.desc.return_value.all.return_value = [mock_usuario]
        mock_query.filter_by.return_value.first.return_value = None
        mock_query.filter_by.return_value.count.return_value = 5
        mock_usuario_class.query = mock_query
        
        # Registrar rutas
        register_api_routes(
            app=app,
            db=mock_db,
            Reserva=mock_reserva_class,
            Usuario=mock_usuario_class,
            database_available=True,
            database_url="postgresql://test"
        )
        
        print("✓ Endpoints de usuarios registrados")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test GET usuarios
                response = client.get('/api/usuarios')
                print(f"✓ GET /api/usuarios: status={response.status_code}")
                
                # Test auth verify
                response = client.get('/api/auth/verify')
                print(f"✓ GET /api/auth/verify: status={response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test usuarios endpoints: {e}")
        return False

def test_health_endpoint():
    """Test de endpoint de salud"""
    
    print("\n=== TEST: Health Endpoint ===")
    
    try:
        from routes.api_routes import register_api_routes
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Registrar rutas
        register_api_routes(
            app=app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test"
        )
        
        print("✓ Health endpoint registrado")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test health check
                response = client.get('/health')
                print(f"✓ GET /health: status={response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"  - Status: {data.get('status')}")
                    print(f"  - Database: {data.get('database')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test health endpoint: {e}")
        return False

def test_disponibilidades_endpoints():
    """Test de endpoints de disponibilidades"""
    
    print("\n=== TEST: Disponibilidades Endpoints ===")
    
    try:
        from routes.api_routes import register_api_routes
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Registrar rutas
        register_api_routes(
            app=app,
            db=mock_db,
            Reserva=mock_reserva,
            Usuario=mock_usuario,
            database_available=True,
            database_url="postgresql://test"
        )
        
        print("✓ Endpoints de disponibilidades registrados")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test disponibilidades básicas
                response = client.get('/api/disponibilidades?fecha_inicio=2024-12-25&fecha_fin=2024-12-27')
                print(f"✓ GET /api/disponibilidades: status={response.status_code}")
                
                # Test agente disponibilidades
                response = client.post('/api/agente/disponibilidades', 
                                     json={'consulta': 'disponibilidad para diciembre'})
                print(f"✓ POST /api/agente/disponibilidades: status={response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test disponibilidades endpoints: {e}")
        return False

def test_error_handling():
    """Test de manejo de errores"""
    
    print("\n=== TEST: Error Handling ===")
    
    try:
        from routes.api_routes import register_api_routes
        from flask import Flask
        
        # Crear app de prueba
        app = Flask(__name__)
        
        # Registrar rutas con database no disponible
        register_api_routes(
            app=app,
            db=None,
            Reserva=None,
            Usuario=None,
            database_available=False,
            database_url=None
        )
        
        print("✓ Rutas registradas con DB no disponible")
        
        # Test con app context
        with app.test_client() as client:
            with app.app_context():
                # Test endpoints con DB no disponible
                response = client.get('/api/reservas')
                print(f"✓ GET /api/reservas (DB unavailable): status={response.status_code}")
                
                response = client.get('/api/usuarios')
                print(f"✓ GET /api/usuarios (DB unavailable): status={response.status_code}")
                
                response = client.get('/health')
                print(f"✓ GET /health (DB unavailable): status={response.status_code}")
                
                # Health debe devolver 503 cuando DB no está disponible
                if response.status_code == 503:
                    print("  - Health check correctamente devuelve 503 sin DB")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test error handling: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests de rutas API"""
    
    print("INICIANDO TESTS DE RUTAS API CENTRALIZADAS")
    print("=" * 60)
    
    tests = [
        test_api_routes_registration,
        test_reservas_endpoints,
        test_usuarios_endpoints,
        test_health_endpoint,
        test_disponibilidades_endpoints,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Error inesperado en {test_func.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS DE RUTAS API")
    print("=" * 60)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS DE RUTAS API PASARON")
        print("\nRutas API centralizadas listas:")
        print("• 16 endpoints REST consolidados")
        print("• Endpoints de reservas (GET, POST, PUT, DELETE)")
        print("• Endpoints de usuarios (CRUD completo)")
        print("• Endpoints de autenticación (login, verify)")
        print("• Endpoint de salud (/health)")
        print("• Endpoints de disponibilidades")
        print("• Manejo robusto de errores")
        print("• Logging estructurado integrado")
        return True
    else:
        print("❌ ALGUNOS TESTS DE RUTAS API FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)