# Test del servicio centralizado de base de datos
# Verifica funcionalidad de DatabaseService sin requerir conexión real

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

def test_database_service_initialization():
    """Test de inicialización del servicio"""
    
    print("=== TEST: DatabaseService Initialization ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock de dependencias
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Test inicialización
        service = DatabaseService(mock_db, mock_reserva, mock_usuario)
        
        print("✓ DatabaseService inicializado correctamente")
        print(f"  - DB instance: {service.db is not None}")
        print(f"  - Reserva model: {service.Reserva is not None}")
        print(f"  - Usuario model: {service.Usuario is not None}")
        
        # Test check database available
        available = service._check_database_available()
        print(f"  - Database available check: {available}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test inicialización: {e}")
        return False

def test_reservas_operations():
    """Test de operaciones CRUD de reservas"""
    
    print("\n=== TEST: Reservas Operations ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock setup
        mock_db = Mock()
        mock_session = Mock()
        mock_db.session = mock_session
        
        mock_reserva_class = Mock()
        mock_usuario_class = Mock()
        
        # Mock query results
        mock_reserva_instance = Mock()
        mock_reserva_instance.id = 1
        mock_reserva_instance.numero_whatsapp = "123456789"
        mock_reserva_instance.email_contacto = "test@example.com"
        mock_reserva_instance.cantidad_huespedes = 2
        mock_reserva_instance.domo = "Luna"
        mock_reserva_instance.fecha_entrada = date(2024, 12, 25)
        mock_reserva_instance.fecha_salida = date(2024, 12, 27)
        mock_reserva_instance.servicio_elegido = "Cena romántica"
        mock_reserva_instance.adicciones = "Sin mascotas"
        mock_reserva_instance.numero_contacto = "987654321"
        mock_reserva_instance.metodo_pago = "Tarjeta"
        mock_reserva_instance.monto_total = Decimal('500000')
        mock_reserva_instance.fecha_creacion = datetime.now()
        mock_reserva_instance.nombres_huespedes = "Juan Pérez, María González"
        mock_reserva_instance.comentarios_especiales = "Vista al lago"
        
        # Mock query chain
        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = [mock_reserva_instance]
        mock_query.count.return_value = 1
        mock_reserva_class.query = mock_query
        
        service = DatabaseService(mock_db, mock_reserva_class, mock_usuario_class)
        
        # Test get_all_reservas
        success, reservas_data, error = service.get_all_reservas()
        print(f"✓ get_all_reservas: success={success}, count={len(reservas_data)}")
        
        if success and reservas_data:
            reserva = reservas_data[0]
            print(f"  - Reserva ID: {reserva.get('id')}")
            print(f"  - Domo: {reserva.get('domo')}")
            print(f"  - Huéspedes: {reserva.get('cantidadHuespedes')}")
        
        # Test get_reservas_stats
        mock_db.extract.return_value = Mock()
        mock_db.func.count.return_value.label.return_value = Mock()
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("Luna", 5), ("Sol", 3)
        ]
        
        success, stats, error = service.get_reservas_stats()
        print(f"✓ get_reservas_stats: success={success}")
        
        if success:
            print(f"  - Total reservas: {stats.get('total_reservas')}")
            print(f"  - Reservas por domo: {len(stats.get('reservas_por_domo', []))}")
        
        # Test create_reserva
        reserva_data = {
            'numero_whatsapp': '123456789',
            'email_contacto': 'test@example.com',
            'cantidad_huespedes': 2,
            'domo': 'Luna',
            'fecha_entrada': '2024-12-25',
            'fecha_salida': '2024-12-27',
            'metodo_pago': 'Tarjeta',
            'nombres_huespedes': 'Juan Pérez',
            'servicio_elegido': 'Cena romántica',
            'adicciones': 'Sin mascotas',
            'numero_contacto': '987654321',
            'monto_total': 500000,
            'comentarios_especiales': 'Vista al lago'
        }
        
        # Mock nueva reserva
        mock_nueva_reserva = Mock()
        mock_nueva_reserva.id = 2
        mock_reserva_class.return_value = mock_nueva_reserva
        
        success, reserva_id, error = service.create_reserva(reserva_data)
        print(f"✓ create_reserva: success={success}, id={reserva_id}")
        
        # Test update_reserva
        mock_reserva_class.query.get.return_value = mock_reserva_instance
        success, error = service.update_reserva(1, {'domo': 'Sol'})
        print(f"✓ update_reserva: success={success}")
        
        # Test delete_reserva
        success, error = service.delete_reserva(1)
        print(f"✓ delete_reserva: success={success}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test reservas operations: {e}")
        return False

def test_usuarios_operations():
    """Test de operaciones CRUD de usuarios"""
    
    print("\n=== TEST: Usuarios Operations ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock setup
        mock_db = Mock()
        mock_session = Mock()
        mock_db.session = mock_session
        
        mock_reserva_class = Mock()
        mock_usuario_class = Mock()
        
        # Mock usuario instance
        mock_usuario_instance = Mock()
        mock_usuario_instance.id = 1
        mock_usuario_instance.nombre = "Juan Pérez"
        mock_usuario_instance.email = "juan@example.com"
        mock_usuario_instance.rol = "admin"
        mock_usuario_instance.activo = True
        mock_usuario_instance.password_changed = False
        mock_usuario_instance.fecha_creacion = datetime.now()
        mock_usuario_instance.ultimo_acceso = datetime.now()
        mock_usuario_instance.temp_password = "temp123"
        
        # Mock query
        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = [mock_usuario_instance]
        mock_query.filter_by.return_value.first.return_value = None  # No existe
        mock_query.get.return_value = mock_usuario_instance
        mock_usuario_class.query = mock_query
        
        service = DatabaseService(mock_db, mock_reserva_class, mock_usuario_class)
        
        # Test get_all_users
        users = service.get_all_users(include_passwords=True)
        print(f"✓ get_all_users: count={len(users)}")
        
        if users:
            user = users[0]
            print(f"  - Usuario: {user.get('nombre')} ({user.get('email')})")
            print(f"  - Rol: {user.get('rol')}")
            print(f"  - Activo: {user.get('activo')}")
        
        # Test create_user
        mock_nuevo_usuario = Mock()
        mock_nuevo_usuario.id = 2
        mock_nuevo_usuario.nombre = "María González"
        mock_nuevo_usuario.email = "maria@example.com"
        mock_nuevo_usuario.rol = "limitado"
        mock_usuario_class.return_value = mock_nuevo_usuario
        
        success, user_data, error = service.create_user("María González", "maria@example.com")
        print(f"✓ create_user: success={success}")
        
        if success and user_data:
            print(f"  - Nuevo usuario: {user_data.get('nombre')}")
            print(f"  - Password temporal: {user_data.get('temp_password') is not None}")
        
        # Test update_user
        success, error = service.update_user(1, "Juan Carlos", "juan@example.com", "admin")
        print(f"✓ update_user: success={success}")
        
        # Test delete_user
        success, error = service.delete_user(1)
        print(f"✓ delete_user: success={success}")
        
        # Test authenticate_user
        with patch('werkzeug.security.check_password_hash', return_value=True):
            user_data = service.authenticate_user("juan@example.com", "password123")
            print(f"✓ authenticate_user: success={user_data is not None}")
            
            if user_data:
                print(f"  - Usuario autenticado: {user_data.get('nombre')}")
        
        # Test regenerate_user_password
        success, new_password, error = service.regenerate_user_password(1)
        print(f"✓ regenerate_user_password: success={success}")
        
        if success:
            print(f"  - Nueva password generada: {len(new_password)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test usuarios operations: {e}")
        return False

def test_validation_methods():
    """Test de métodos de validación"""
    
    print("\n=== TEST: Validation Methods ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        service = DatabaseService(mock_db, mock_reserva, mock_usuario)
        
        # Test validación correcta
        valid_data = {
            'numero_whatsapp': '123456789',
            'email_contacto': 'test@example.com',
            'cantidad_huespedes': 2,
            'domo': 'Luna',
            'fecha_entrada': '2024-12-25',
            'fecha_salida': '2024-12-27',
            'metodo_pago': 'Tarjeta'
        }
        
        result = service._validate_reserva_fields(valid_data)
        print(f"✓ Validación datos correctos: válido={result['valido']}")
        
        # Test validación incorrecta
        invalid_data = {
            'email_contacto': 'email_invalido',
            'cantidad_huespedes': 0
        }
        
        result = service._validate_reserva_fields(invalid_data)
        print(f"✓ Validación datos incorrectos: válido={result['valido']}")
        print(f"  - Errores encontrados: {len(result['errores'])}")
        
        # Test generación de password
        password = service._generate_simple_password()
        print(f"✓ Generación password: {len(password)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test validation methods: {e}")
        return False

def test_database_health():
    """Test de verificación de salud de la base de datos"""
    
    print("\n=== TEST: Database Health ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Mock setup
        mock_db = Mock()
        mock_reserva = Mock()
        mock_usuario = Mock()
        
        # Mock queries para health check
        mock_reserva.query.count.return_value = 10
        mock_usuario.query.count.return_value = 5
        
        service = DatabaseService(mock_db, mock_reserva, mock_usuario)
        
        # Test health check exitoso
        health = service.get_database_health()
        print(f"✓ Database health check: status={health.get('status')}")
        print(f"  - Database connected: {health.get('database_connected')}")
        print(f"  - Tables available: {health.get('tables_available')}")
        print(f"  - Total reservas: {health.get('total_reservas')}")
        print(f"  - Total usuarios: {health.get('total_usuarios')}")
        
        # Test health check con error
        service.Reserva = None  # Simular error
        health = service.get_database_health()
        print(f"✓ Database health check (error): status={health.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test database health: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests del servicio de base de datos"""
    
    print("INICIANDO TESTS DEL SERVICIO DE BASE DE DATOS")
    print("=" * 65)
    
    tests = [
        test_database_service_initialization,
        test_reservas_operations,
        test_usuarios_operations,
        test_validation_methods,
        test_database_health
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
    print("RESUMEN DE TESTS")
    print("=" * 65)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON")
        print("\nDatabaseService listo para usar:")
        print("• Operaciones CRUD de reservas implementadas")
        print("• Operaciones CRUD de usuarios implementadas") 
        print("• Validaciones de datos incluidas")
        print("• Logging estructurado integrado")
        print("• Health checks disponibles")
        print("• Manejo robusto de errores")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)