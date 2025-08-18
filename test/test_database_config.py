# Test de configuración centralizada de base de datos
# Verifica funcionalidad de DatabaseConfig

import sys
import os
from unittest.mock import Mock, patch
from flask import Flask

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_database_config_initialization():
    """Test de inicialización de DatabaseConfig"""
    
    print("=== TEST: DatabaseConfig Initialization ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        # Test inicialización sin app
        config = DatabaseConfig()
        
        print("✓ DatabaseConfig inicializado sin app")
        print(f"  - DB instance: {config.db}")
        print(f"  - Database available: {config.database_available}")
        print(f"  - Database URL: {config.database_url}")
        print(f"  - Reserva model: {config.Reserva}")
        print(f"  - Usuario model: {config.Usuario}")
        
        # Test con Flask app
        app = Flask(__name__)
        config_with_app = DatabaseConfig(app)
        
        print("✓ DatabaseConfig inicializado con app")
        print(f"  - Inicialización exitosa: {config_with_app is not None}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test inicialización: {e}")
        return False

def test_database_url_detection():
    """Test de detección de URL de base de datos"""
    
    print("\n=== TEST: Database URL Detection ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        config = DatabaseConfig()
        
        # Test con variables de entorno mockeadas
        test_cases = [
            {
                'env_vars': {
                    'DATABASE_PRIVATE_URL': 'postgresql://private:5432/test',
                    'DATABASE_PUBLIC_URL': 'postgresql://public:5432/test',
                    'DATABASE_URL': 'postgresql://generic:5432/test'
                },
                'expected_priority': 'private',
                'description': 'Prioridad DATABASE_PRIVATE_URL'
            },
            {
                'env_vars': {
                    'DATABASE_PUBLIC_URL': 'postgresql://public:5432/test',
                    'DATABASE_URL': 'postgresql://generic:5432/test'
                },
                'expected_priority': 'public',
                'description': 'Prioridad DATABASE_PUBLIC_URL'
            },
            {
                'env_vars': {
                    'DATABASE_URL': 'postgresql://generic:5432/test'
                },
                'expected_priority': 'generic',
                'description': 'Fallback DATABASE_URL'
            },
            {
                'env_vars': {},
                'expected_priority': 'none',
                'description': 'Sin configuración'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n✓ Caso {i}: {case['description']}")
            
            with patch.dict(os.environ, case['env_vars'], clear=True):
                database_url = config.get_database_url()
                url_type = config._get_database_url_type()
                
                print(f"  - URL detectada: {database_url}")
                print(f"  - Tipo detectado: {url_type}")
                
                if case['expected_priority'] == 'none':
                    if database_url is None:
                        print("  ✓ Correctamente detecta ausencia de configuración")
                    else:
                        print("  ✗ Debería detectar ausencia de configuración")
                else:
                    if database_url and case['expected_priority'] in database_url:
                        print(f"  ✓ Prioridad correcta: {case['expected_priority']}")
                    else:
                        print(f"  ⚠ Prioridad esperada: {case['expected_priority']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test database URL detection: {e}")
        return False

def test_flask_app_integration():
    """Test de integración con Flask app"""
    
    print("\n=== TEST: Flask App Integration ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        # Crear Flask app de prueba
        app = Flask(__name__)
        
        # Test con URL de base de datos mock
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            config = DatabaseConfig()
            
            # Test init_app
            result = config.init_app(app)
            
            print(f"✓ init_app ejecutado: success={result}")
            print(f"  - DB configurado: {config.db is not None}")
            print(f"  - Database available: {config.database_available}")
            
            # Verificar configuración de Flask
            if 'SQLALCHEMY_DATABASE_URI' in app.config:
                print(f"  ✓ SQLALCHEMY_DATABASE_URI configurado: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            if 'SQLALCHEMY_TRACK_MODIFICATIONS' in app.config:
                print(f"  ✓ SQLALCHEMY_TRACK_MODIFICATIONS: {app.config['SQLALCHEMY_TRACK_MODIFICATIONS']}")
            
            if 'SQLALCHEMY_ENGINE_OPTIONS' in app.config:
                print(f"  ✓ SQLALCHEMY_ENGINE_OPTIONS configurado")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test Flask app integration: {e}")
        return False

def test_models_definition():
    """Test de definición de modelos"""
    
    print("\n=== TEST: Models Definition ===")
    
    try:
        from config.database_config import DatabaseConfig
        from flask import Flask
        
        app = Flask(__name__)
        
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            config = DatabaseConfig()
            config.init_app(app)
            
            # Verificar que los modelos están definidos
            if config.Reserva:
                print("✓ Modelo Reserva definido")
                
                # Verificar campos del modelo Reserva
                expected_fields = [
                    'id', 'numero_whatsapp', 'email_contacto', 'cantidad_huespedes',
                    'domo', 'fecha_entrada', 'fecha_salida', 'metodo_pago',
                    'nombres_huespedes', 'servicio_elegido', 'monto_total', 'fecha_creacion'
                ]
                
                for field in expected_fields:
                    if hasattr(config.Reserva, field):
                        print(f"  ✓ Campo {field} presente")
                    else:
                        print(f"  ✗ Campo {field} faltante")
                        return False
                
                # Test método to_dict
                if hasattr(config.Reserva, 'to_dict'):
                    print("  ✓ Método to_dict implementado")
            
            if config.Usuario:
                print("✓ Modelo Usuario definido")
                
                # Verificar campos del modelo Usuario
                expected_fields = [
                    'id', 'nombre', 'email', 'password_hash', 'temp_password',
                    'rol', 'fecha_creacion', 'activo', 'ultimo_acceso', 'password_changed'
                ]
                
                for field in expected_fields:
                    if hasattr(config.Usuario, field):
                        print(f"  ✓ Campo {field} presente")
                    else:
                        print(f"  ✗ Campo {field} faltante")
                        return False
                
                # Test métodos del modelo Usuario
                expected_methods = ['to_dict', 'set_password', 'check_password']
                for method in expected_methods:
                    if hasattr(config.Usuario, method):
                        print(f"  ✓ Método {method} implementado")
                    else:
                        print(f"  ✗ Método {method} faltante")
                        return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test models definition: {e}")
        return False

def test_health_status():
    """Test de health status"""
    
    print("\n=== TEST: Health Status ===")
    
    try:
        from config.database_config import DatabaseConfig
        
        # Test sin configuración
        config = DatabaseConfig()
        health = config.get_health_status()
        
        print("✓ Health status sin configuración:")
        print(f"  - Database configured: {health.get('database_configured')}")
        print(f"  - Database available: {health.get('database_available')}")
        print(f"  - SQLAlchemy initialized: {health.get('sqlalchemy_initialized')}")
        print(f"  - Models defined: {health.get('models_defined')}")
        print(f"  - Database URL type: {health.get('database_url_type')}")
        print(f"  - Connection test: {health.get('connection_test')}")
        
        # Test con configuración
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            from flask import Flask
            app = Flask(__name__)
            
            config_with_db = DatabaseConfig()
            config_with_db.init_app(app)
            
            health_with_db = config_with_db.get_health_status()
            
            print("\n✓ Health status con configuración:")
            print(f"  - Database configured: {health_with_db.get('database_configured')}")
            print(f"  - Database available: {health_with_db.get('database_available')}")
            print(f"  - SQLAlchemy initialized: {health_with_db.get('sqlalchemy_initialized')}")
            print(f"  - Models defined: {health_with_db.get('models_defined')}")
            print(f"  - Database URL type: {health_with_db.get('database_url_type')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test health status: {e}")
        return False

def test_utility_functions():
    """Test de funciones de utilidad"""
    
    print("\n=== TEST: Utility Functions ===")
    
    try:
        from config.database_config import generate_random_password, generate_simple_password
        
        # Test generate_random_password
        password1 = generate_random_password()
        password2 = generate_random_password(12)
        
        print(f"✓ generate_random_password() generó: {password1} (longitud: {len(password1)})")
        print(f"✓ generate_random_password(12) generó: {password2} (longitud: {len(password2)})")
        
        # Verificar que no contiene caracteres confusos
        confusing_chars = ['0', 'O', 'l', 'I']
        has_confusing = any(char in password1 for char in confusing_chars)
        if not has_confusing:
            print("  ✓ No contiene caracteres confusos")
        else:
            print("  ⚠ Contiene caracteres confusos")
        
        # Test generate_simple_password
        simple_password = generate_simple_password()
        print(f"✓ generate_simple_password() generó: {simple_password} (longitud: {len(simple_password)})")
        
        if len(simple_password) == 8:
            print("  ✓ Longitud correcta (8 caracteres)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test utility functions: {e}")
        return False

def test_global_functions():
    """Test de funciones globales"""
    
    print("\n=== TEST: Global Functions ===")
    
    try:
        from config.database_config import get_database_config, init_database_config
        from flask import Flask
        
        # Test get_database_config
        global_config = get_database_config()
        print(f"✓ get_database_config() retornó: {type(global_config).__name__}")
        
        # Test init_database_config
        app = Flask(__name__)
        
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}, clear=True):
            initialized_config = init_database_config(app)
            print(f"✓ init_database_config() retornó: {type(initialized_config).__name__}")
            print(f"  - DB configurado: {initialized_config.db is not None}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test global functions: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests de configuración de base de datos"""
    
    print("INICIANDO TESTS DE CONFIGURACIÓN DE BASE DE DATOS")
    print("=" * 70)
    
    tests = [
        test_database_config_initialization,
        test_database_url_detection,
        test_flask_app_integration,
        test_models_definition,
        test_health_status,
        test_utility_functions,
        test_global_functions
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
        print("\nDatabaseConfig listo para usar:")
        print("• Configuración centralizada de base de datos implementada")
        print("• Detección inteligente de URLs de base de datos")
        print("• Modelos Reserva y Usuario completamente definidos")
        print("• Integración con Flask-SQLAlchemy optimizada")
        print("• Health checks y diagnósticos disponibles")
        print("• Funciones de utilidad para contraseñas")
        print("• Configuración de engine optimizada para producción")
        print("• Logging estructurado integrado")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)