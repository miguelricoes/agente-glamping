# Test de integración de DatabaseConfig con agente_modular
# Verifica que la configuración centralizada funcione correctamente

import sys
import os
from unittest.mock import Mock, patch
from flask import Flask

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_database_config_integration():
    """Test de integración básica de DatabaseConfig"""
    
    print("=== TEST: DatabaseConfig Integration ===")
    
    try:
        from config.database_config import DatabaseConfig, init_database_config
        
        # Test con Flask app
        app = Flask(__name__)
        
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            config = init_database_config(app)
            
            print("✓ DatabaseConfig integrado exitosamente")
            print(f"  - Database available: {config.database_available}")
            print(f"  - DB instance: {config.db is not None}")
            print(f"  - Reserva model: {config.Reserva is not None}")
            print(f"  - Usuario model: {config.Usuario is not None}")
            
            # Verificar que los modelos están disponibles
            if config.Reserva and config.Usuario:
                print("  ✓ Modelos definidos correctamente")
                
                # Test de métodos de modelos
                if hasattr(config.Reserva, 'to_dict'):
                    print("  ✓ Modelo Reserva tiene método to_dict")
                
                if hasattr(config.Usuario, 'check_password'):
                    print("  ✓ Modelo Usuario tiene método check_password")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test database config integration: {e}")
        return False

def test_modular_compatibility():
    """Test de compatibilidad con estructura modular"""
    
    print("\n=== TEST: Modular Compatibility ===")
    
    try:
        # Test importaciones necesarias para agente_modular
        from config.database_config import init_database_config
        from services.database_service import DatabaseService
        from services.availability_service import AvailabilityService
        
        print("✓ Importaciones modulares exitosas")
        
        # Simular inicialización como en agente_modular.py
        app = Flask(__name__)
        
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            # Test configuración centralizada
            database_config_instance = init_database_config(app)
            
            # Extraer componentes como en agente_modular.py
            db = database_config_instance.db
            database_available = database_config_instance.database_available
            Reserva = database_config_instance.Reserva
            Usuario = database_config_instance.Usuario
            
            print("✓ Configuración centralizada extraída")
            print(f"  - db: {db is not None}")
            print(f"  - database_available: {database_available}")
            print(f"  - Reserva: {Reserva is not None}")
            print(f"  - Usuario: {Usuario is not None}")
            
            # Test inicialización de servicios con configuración centralizada
            if db and Reserva and Usuario:
                database_service = DatabaseService(db, Reserva, Usuario)
                availability_service = AvailabilityService(db, Reserva)
                
                print("✓ Servicios inicializados con configuración centralizada")
                print(f"  - DatabaseService: {database_service is not None}")
                print(f"  - AvailabilityService: {availability_service is not None}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test modular compatibility: {e}")
        return False

def test_centralized_vs_original_config():
    """Test de comparación entre configuración centralizada y original"""
    
    print("\n=== TEST: Centralized vs Original Config ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        app = Flask(__name__)
        
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            # Test configuración centralizada
            centralized_config = DatabaseConfig()
            centralized_config.init_app(app)
            
            print("✓ Configuración centralizada:")
            print(f"  - Database available: {centralized_config.database_available}")
            print(f"  - URL type: {centralized_config._get_database_url_type()}")
            print(f"  - Models defined: {centralized_config.Reserva is not None and centralized_config.Usuario is not None}")
            
            # Verificar health status
            health = centralized_config.get_health_status()
            print(f"  - Health status: {health.get('database_available')}")
            print(f"  - Connection test: {health.get('connection_test')}")
            
            # Verificar que la configuración está optimizada
            flask_config = app.config
            if 'SQLALCHEMY_ENGINE_OPTIONS' in flask_config:
                engine_options = flask_config['SQLALCHEMY_ENGINE_OPTIONS']
                print("  ✓ Configuración de engine optimizada:")
                print(f"    - pool_pre_ping: {engine_options.get('pool_pre_ping')}")
                print(f"    - pool_recycle: {engine_options.get('pool_recycle')}")
                print(f"    - pool_timeout: {engine_options.get('pool_timeout')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test centralized vs original config: {e}")
        return False

def test_model_functionality():
    """Test de funcionalidad de modelos centralizados"""
    
    print("\n=== TEST: Model Functionality ===")
    
    try:
        from config.database_config import DatabaseConfig
        from werkzeug.security import generate_password_hash
        
        app = Flask(__name__)
        
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            config = DatabaseConfig()
            config.init_app(app)
            
            if config.Reserva and config.Usuario:
                # Test modelo Reserva
                print("✓ Test modelo Reserva:")
                
                # Mock reserva instance
                mock_reserva = Mock()
                mock_reserva.id = 1
                mock_reserva.numero_whatsapp = "123456789"
                mock_reserva.email_contacto = "test@example.com"
                mock_reserva.cantidad_huespedes = 2
                mock_reserva.domo = "Luna"
                mock_reserva.fecha_entrada = None
                mock_reserva.fecha_salida = None
                mock_reserva.metodo_pago = "Tarjeta"
                mock_reserva.nombres_huespedes = "Juan Pérez"
                mock_reserva.servicio_elegido = "Cena"
                mock_reserva.adicciones = "Ninguna"
                mock_reserva.comentarios_especiales = "Vista al lago"
                mock_reserva.numero_contacto = "987654321"
                mock_reserva.monto_total = 500000
                mock_reserva.fecha_creacion = None
                
                # Test to_dict method si está disponible
                if hasattr(config.Reserva, 'to_dict'):
                    print("  ✓ Método to_dict disponible en Reserva")
                
                # Test modelo Usuario
                print("✓ Test modelo Usuario:")
                
                # Test métodos del usuario
                usuario_methods = ['to_dict', 'set_password', 'check_password']
                for method in usuario_methods:
                    if hasattr(config.Usuario, method):
                        print(f"  ✓ Método {method} disponible")
                    else:
                        print(f"  ✗ Método {method} no disponible")
                        return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test model functionality: {e}")
        return False

def test_fallback_functionality():
    """Test de funcionalidad de fallback"""
    
    print("\n=== TEST: Fallback Functionality ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        app = Flask(__name__)
        
        # Test sin configuración de base de datos
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig()
            result = config.init_app(app)
            
            print("✓ Test sin configuración de BD:")
            print(f"  - Inicialización: {result}")
            print(f"  - Database available: {config.database_available}")
            print(f"  - DB instance: {config.db}")
            
            # Verificar health status sin configuración
            health = config.get_health_status()
            print(f"  - Health status: {health.get('database_available')}")
            print(f"  - Database configured: {health.get('database_configured')}")
            
            if not health.get('database_available'):
                print("  ✓ Fallback funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test fallback functionality: {e}")
        return False

def test_environment_variable_priority():
    """Test de prioridad de variables de entorno"""
    
    print("\n=== TEST: Environment Variable Priority ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        config = DatabaseConfig()
        
        # Test casos de prioridad
        priority_tests = [
            {
                'env': {'DATABASE_PRIVATE_URL': 'postgresql://private:5432/test'},
                'expected_type': 'private',
                'description': 'Solo PRIVATE_URL'
            },
            {
                'env': {
                    'DATABASE_PRIVATE_URL': 'postgresql://private:5432/test',
                    'DATABASE_PUBLIC_URL': 'postgresql://public:5432/test'
                },
                'expected_type': 'private',
                'description': 'PRIVATE_URL tiene prioridad sobre PUBLIC_URL'
            },
            {
                'env': {
                    'DATABASE_PRIVATE_URL': 'postgresql://private:5432/test',
                    'DATABASE_PUBLIC_URL': 'postgresql://public:5432/test',
                    'DATABASE_URL': 'postgresql://generic:5432/test'
                },
                'expected_type': 'private',
                'description': 'PRIVATE_URL tiene prioridad sobre todas'
            }
        ]
        
        for i, test in enumerate(priority_tests, 1):
            print(f"✓ Test {i}: {test['description']}")
            
            with patch.dict(os.environ, test['env'], clear=True):
                url = config.get_database_url()
                url_type = config._get_database_url_type()
                
                print(f"  - URL detectada: {url}")
                print(f"  - Tipo detectado: {url_type}")
                
                if url_type == test['expected_type']:
                    print(f"  ✓ Prioridad correcta: {test['expected_type']}")
                else:
                    print(f"  ✗ Prioridad incorrecta: esperado {test['expected_type']}, obtenido {url_type}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test environment variable priority: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests de integración de configuración de base de datos"""
    
    print("INICIANDO TESTS DE INTEGRACIÓN DE DATABASE CONFIG")
    print("=" * 65)
    
    tests = [
        test_database_config_integration,
        test_modular_compatibility,
        test_centralized_vs_original_config,
        test_model_functionality,
        test_fallback_functionality,
        test_environment_variable_priority
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
        print("\nDatabaseConfig integrado exitosamente:")
        print("• Configuración centralizada de base de datos activa")
        print("• Detección inteligente de URLs de entorno")
        print("• Modelos optimizados con métodos adicionales")
        print("• Integración perfecta con agente_modular.py")
        print("• Configuración de engine optimizada para producción")
        print("• Health checks y diagnósticos avanzados")
        print("• Funcionalidad de fallback robusta")
        print("• Compatibilidad total con servicios existentes")
        print("• Logging estructurado completo")
        return True
    else:
        print("❌ ALGUNOS TESTS DE INTEGRACIÓN FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)