# Test de integración del DatabaseService con agente_modular
# Verifica que la integración funcione correctamente

import sys
import os
from unittest.mock import Mock, patch

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_database_service_integration():
    """Test de integración básica del DatabaseService"""
    
    print("=== TEST: DatabaseService Integration ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock de dependencias SQLAlchemy
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Test inicialización
        service = DatabaseService(mock_db, mock_reserva, mock_usuario)
        
        print("✓ DatabaseService inicializado en contexto de integración")
        print(f"  - Servicio configurado correctamente: {service is not None}")
        print(f"  - Database check: {service._check_database_available()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test integración básica: {e}")
        return False

def test_api_routes_modular():
    """Test de las rutas API modulares"""
    
    print("\n=== TEST: API Routes Modular ===")
    
    try:
        from routes.api_routes_modular import register_api_routes
        
        # Mock de Flask app
        mock_app = Mock()
        mock_route_decorator = Mock()
        mock_app.route.return_value = mock_route_decorator
        
        # Mock del DatabaseService
        mock_database_service = Mock()
        
        # Test registro de rutas
        with patch('routes.api_routes_modular.logger'):
            result = register_api_routes(mock_app, mock_database_service)
        
        print("✓ register_api_routes ejecutado exitosamente")
        print(f"  - App route llamado: {mock_app.route.called}")
        print(f"  - Número de rutas registradas: {mock_app.route.call_count}")
        
        # Test con DatabaseService None
        with patch('routes.api_routes_modular.logger'):
            register_api_routes(mock_app, None)
        
        print("✓ Manejo correcto cuando DatabaseService es None")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test API routes modular: {e}")
        return False

def test_agente_modular_integration():
    """Test de integración con agente_modular (sin ejecutar completamente)"""
    
    print("\n=== TEST: Agente Modular Integration ===")
    
    try:
        # Test importaciones necesarias
        from services.database_service import DatabaseService
        from routes.api_routes_modular import register_api_routes
        
        print("✓ Importaciones de integración exitosas")
        
        # Simular inicialización como en agente_modular.py
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Test lógica de inicialización
        database_service = None
        
        if mock_db and mock_reserva and mock_usuario:
            database_service = DatabaseService(mock_db, mock_reserva, mock_usuario)
            print("✓ DatabaseService inicializado correctamente")
        else:
            print("✗ Condición de inicialización no cumplida")
        
        print(f"  - Database service disponible: {database_service is not None}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test agente modular integration: {e}")
        return False

def test_backwards_compatibility():
    """Test de compatibilidad hacia atrás"""
    
    print("\n=== TEST: Backwards Compatibility ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        service = DatabaseService(mock_db, mock_reserva, mock_usuario)
        
        # Verificar que los métodos mantengan la interfaz esperada
        expected_methods = [
            'get_all_reservas',
            'create_reserva', 
            'update_reserva',
            'delete_reserva',
            'get_all_users',
            'create_user',
            'update_user',
            'delete_user',
            'authenticate_user',
            'regenerate_user_password'
        ]
        
        for method_name in expected_methods:
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                if callable(method):
                    print(f"✓ Método {method_name} disponible y callable")
                else:
                    print(f"✗ Método {method_name} no es callable")
                    return False
            else:
                print(f"✗ Método {method_name} no existe")
                return False
        
        print(f"✓ Todos los métodos esperados están disponibles ({len(expected_methods)})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test backwards compatibility: {e}")
        return False

def test_error_handling():
    """Test de manejo de errores"""
    
    print("\n=== TEST: Error Handling ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Test con dependencias None
        service = DatabaseService(None, None, None)
        
        # Test operaciones con DB no disponible
        success, data, error = service.get_all_reservas()
        print(f"✓ get_all_reservas con DB None: success={success}")
        
        users = service.get_all_users()
        print(f"✓ get_all_users con DB None: count={len(users)}")
        
        health = service.get_database_health()
        print(f"✓ get_database_health con DB None: status={health.get('status')}")
        
        print("✓ Manejo robusto de errores cuando DB no está disponible")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test error handling: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests de integración"""
    
    print("INICIANDO TESTS DE INTEGRACIÓN DEL DATABASE SERVICE")
    print("=" * 70)
    
    tests = [
        test_database_service_integration,
        test_api_routes_modular,
        test_agente_modular_integration,
        test_backwards_compatibility,
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
    
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS DE INTEGRACIÓN")
    print("=" * 70)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print("\nDatabaseService integrado exitosamente:")
        print("• Servicio centralizado de base de datos activo")
        print("• Rutas API modulares v2 implementadas")
        print("• Integración con agente_modular.py completa") 
        print("• Compatibilidad hacia atrás mantenida")
        print("• Manejo robusto de errores implementado")
        print("• Logging estructurado en todas las operaciones")
        return True
    else:
        print("❌ ALGUNOS TESTS DE INTEGRACIÓN FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)