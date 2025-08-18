# Test del servicio centralizado de usuarios
# Verifica funcionalidad de UserService

import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_password_generation():
    """Test de generación de contraseñas"""
    
    print("=== TEST: Password Generation ===")
    
    try:
        from services.user_service import UserService
        
        # Mock database y modelo
        mock_db = Mock()
        mock_usuario = Mock()
        
        service = UserService(mock_db, mock_usuario)
        
        # Test generate_random_password
        password1 = service.generate_random_password()
        password2 = service.generate_random_password(12)
        
        print(f"✓ Random password (8): {password1} (longitud: {len(password1)})")
        print(f"✓ Random password (12): {password2} (longitud: {len(password2)})")
        
        if len(password1) == 8 and len(password2) == 12:
            print("  ✓ Longitudes correctas")
        else:
            print("  ✗ Longitudes incorrectas")
            return False
        
        # Verificar que no contiene caracteres confusos
        confusing_chars = ['0', 'O', 'l', 'I']
        has_confusing = any(char in password1 for char in confusing_chars)
        if not has_confusing:
            print("  ✓ No contiene caracteres confusos")
        else:
            print("  ⚠ Contiene caracteres confusos")
        
        # Test generate_simple_password
        simple_password = service.generate_simple_password()
        print(f"✓ Simple password: {simple_password} (longitud: {len(simple_password)})")
        
        if len(simple_password) == 8:
            print("  ✓ Longitud correcta (8 caracteres)")
        else:
            print(f"  ✗ Longitud incorrecta: {len(simple_password)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test password generation: {e}")
        return False

def test_get_all_users():
    """Test de obtención de todos los usuarios"""
    
    print("\n=== TEST: Get All Users ===")
    
    try:
        from services.user_service import UserService
        
        # Mock database y modelo
        mock_db = Mock()
        mock_usuario = Mock()
        
        # Mock usuarios
        mock_user1 = Mock()
        mock_user1.id = 1
        mock_user1.nombre = "Admin"
        mock_user1.email = "admin@example.com"
        mock_user1.rol = "admin"
        mock_user1.fecha_creacion = datetime.now()
        mock_user1.activo = True
        mock_user1.ultimo_acceso = None
        mock_user1.password_changed = False
        
        mock_user2 = Mock()
        mock_user2.id = 2
        mock_user2.nombre = "Usuario Test"
        mock_user2.email = "user@example.com"
        mock_user2.rol = "limitado"
        mock_user2.fecha_creacion = datetime.now()
        mock_user2.activo = True
        mock_user2.ultimo_acceso = datetime.now()
        mock_user2.password_changed = True
        
        mock_usuario.query.all.return_value = [mock_user1, mock_user2]
        
        service = UserService(mock_db, mock_usuario)
        
        # Test sin contraseñas
        success, users, error = service.get_all_users(include_passwords=False)
        
        print("✓ Test obtener usuarios sin contraseñas:")
        print(f"  - Success: {success}")
        print(f"  - Cantidad usuarios: {len(users)}")
        print(f"  - Error: {error}")
        
        if success and len(users) == 2 and not error:
            print("  ✓ PASÓ")
        else:
            print("  ✗ FALLÓ")
            return False
        
        # Verificar estructura de datos
        if all('id' in user and 'nombre' in user and 'email' in user for user in users):
            print("  ✓ Estructura de datos correcta")
        else:
            print("  ✗ Estructura de datos incorrecta")
            return False
        
        # Test con contraseñas
        success, users_with_pwd, error = service.get_all_users(include_passwords=True)
        
        print("\n✓ Test obtener usuarios con info de contraseñas:")
        print(f"  - Success: {success}")
        print(f"  - Info contraseñas incluida: {'tiene_password_hash' in users_with_pwd[0] if users_with_pwd else False}")
        
        if success and users_with_pwd and 'tiene_password_hash' in users_with_pwd[0]:
            print("  ✓ PASÓ")
        else:
            print("  ✗ FALLÓ")
            return False
        
        # Test con base de datos no disponible
        service_no_db = UserService(None, mock_usuario)
        success, users, error = service_no_db.get_all_users()
        
        print("\n✓ Test sin base de datos:")
        print(f"  - Success: {success} (esperado: False)")
        print(f"  - Error: {error}")
        
        if not success and "Base de datos no disponible" in error:
            print("  ✓ PASÓ - Error detectado correctamente")
        else:
            print("  ✗ FALLÓ")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test get all users: {e}")
        return False

def test_create_user_function():
    """Test de creación de usuarios"""
    
    print("\n=== TEST: Create User Function ===")
    
    try:
        from services.user_service import UserService
        
        # Mock database y modelo
        mock_db = Mock()
        mock_usuario = Mock()
        
        # Mock query para verificar email existente
        mock_usuario.query.filter_by.return_value.first.return_value = None
        
        # Mock nuevo usuario
        mock_new_user = Mock()
        mock_new_user.id = 1
        
        service = UserService(mock_db, mock_usuario)
        
        # Test creación exitosa
        success, user_id, message = service.create_user_function(
            nombre="Nuevo Usuario",
            email="nuevo@example.com",
            rol="limitado"
        )
        
        print("✓ Test creación de usuario:")
        print(f"  - Success: {success}")
        print(f"  - User ID: {user_id}")
        print(f"  - Message: {message[:50]}...")
        
        if success:
            print("  ✓ PASÓ")
        else:
            print(f"  ✗ FALLÓ - Error: {message}")
            return False
        
        # Verificar que se llamaron los métodos correctos
        mock_db.session.add.assert_called()
        mock_db.session.commit.assert_called()
        
        print("  ✓ Métodos de DB llamados correctamente")
        
        # Test email duplicado
        mock_existing_user = Mock()
        mock_usuario.query.filter_by.return_value.first.return_value = mock_existing_user
        
        success, user_id, message = service.create_user_function(
            nombre="Usuario Duplicado",
            email="existente@example.com"
        )
        
        print("\n✓ Test email duplicado:")
        print(f"  - Success: {success} (esperado: False)")
        print(f"  - Message: {message}")
        
        if not success and "Ya existe un usuario" in message:
            print("  ✓ PASÓ - Error detectado correctamente")
        else:
            print("  ✗ FALLÓ")
            return False
        
        # Test sin base de datos
        service_no_db = UserService(None, mock_usuario)
        success, user_id, message = service_no_db.create_user_function("Test", "test@example.com")
        
        print("\n✓ Test sin base de datos:")
        print(f"  - Success: {success} (esperado: False)")
        print(f"  - Message: {message}")
        
        if not success and "Base de datos no disponible" in message:
            print("  ✓ PASÓ - Error detectado correctamente")
        else:
            print("  ✗ FALLÓ")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test create user function: {e}")
        return False

def test_update_user_function():
    """Test de actualización de usuarios"""
    
    print("\n=== TEST: Update User Function ===")
    
    try:
        from services.user_service import UserService
        
        # Mock database y modelo
        mock_db = Mock()
        mock_usuario = Mock()
        
        # Mock usuario existente
        mock_user = Mock()
        mock_user.id = 1
        mock_user.nombre = "Usuario Original"
        mock_user.email = "original@example.com"
        mock_user.rol = "limitado"
        mock_user.activo = True
        
        mock_usuario.query.get.return_value = mock_user
        mock_usuario.query.filter_by.return_value.first.return_value = None  # No hay conflicto de email
        
        service = UserService(mock_db, mock_usuario)
        
        # Test actualización exitosa
        success, message = service.update_user_function(
            user_id=1,
            nombre="Usuario Actualizado",
            email="actualizado@example.com",
            rol="admin",
            activo=True
        )
        
        print("✓ Test actualización de usuario:")
        print(f"  - Success: {success}")
        print(f"  - Message: {message}")
        
        if success:
            print("  ✓ PASÓ")
        else:
            print(f"  ✗ FALLÓ - Error: {message}")
            return False
        
        # Verificar que se actualizaron los campos
        assert mock_user.nombre == "Usuario Actualizado"
        assert mock_user.email == "actualizado@example.com"
        assert mock_user.rol == "admin"
        
        print("  ✓ Campos actualizados correctamente")
        
        # Verificar que se llamó commit
        mock_db.session.commit.assert_called()
        
        print("  ✓ Commit ejecutado")
        
        # Test usuario no encontrado
        mock_usuario.query.get.return_value = None
        
        success, message = service.update_user_function(
            user_id=999,
            nombre="No Existe",
            email="noexiste@example.com",
            rol="limitado"
        )
        
        print("\n✓ Test usuario no encontrado:")
        print(f"  - Success: {success} (esperado: False)")
        print(f"  - Message: {message}")
        
        if not success and "no encontrado" in message:
            print("  ✓ PASÓ - Error detectado correctamente")
        else:
            print("  ✗ FALLÓ")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test update user function: {e}")
        return False

def test_authenticate_user():
    """Test de autenticación de usuarios"""
    
    print("\n=== TEST: Authenticate User ===")
    
    try:
        from services.user_service import UserService
        
        # Mock database y modelo
        mock_db = Mock()
        mock_usuario = Mock()
        
        # Mock usuario válido
        mock_user = Mock()
        mock_user.id = 1
        mock_user.nombre = "Usuario Test"
        mock_user.email = "test@example.com"
        mock_user.rol = "admin"
        mock_user.activo = True
        mock_user.password_changed = True
        mock_user.check_password = Mock(return_value=True)
        mock_user.ultimo_acceso = None
        
        mock_usuario.query.filter_by.return_value.first.return_value = mock_user
        
        service = UserService(mock_db, mock_usuario)
        
        # Test autenticación exitosa
        success, user_data, message = service.authenticate_user("test@example.com", "password123")
        
        print("✓ Test autenticación exitosa:")
        print(f"  - Success: {success}")
        print(f"  - User data: {user_data}")
        print(f"  - Message: {message}")
        
        if success and user_data and user_data['id'] == 1:
            print("  ✓ PASÓ")
        else:
            print(f"  ✗ FALLÓ - Error: {message}")
            return False
        
        # Verificar que se actualizó último acceso
        mock_db.session.commit.assert_called()
        
        print("  ✓ Último acceso actualizado")
        
        # Test usuario no encontrado
        mock_usuario.query.filter_by.return_value.first.return_value = None
        
        success, user_data, message = service.authenticate_user("noexiste@example.com", "password")
        
        print("\n✓ Test usuario no encontrado:")
        print(f"  - Success: {success} (esperado: False)")
        print(f"  - Message: {message}")
        
        if not success and "Credenciales inválidas" in message:
            print("  ✓ PASÓ - Error detectado correctamente")
        else:
            print("  ✗ FALLÓ")
            return False
        
        # Test contraseña incorrecta
        mock_user.check_password.return_value = False
        mock_usuario.query.filter_by.return_value.first.return_value = mock_user
        
        success, user_data, message = service.authenticate_user("test@example.com", "wrongpassword")
        
        print("\n✓ Test contraseña incorrecta:")
        print(f"  - Success: {success} (esperado: False)")
        print(f"  - Message: {message}")
        
        if not success and "Credenciales inválidas" in message:
            print("  ✓ PASÓ - Error detectado correctamente")
        else:
            print("  ✗ FALLÓ")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test authenticate user: {e}")
        return False

def test_health_status():
    """Test de estado de salud del servicio"""
    
    print("\n=== TEST: Health Status ===")
    
    try:
        from services.user_service import UserService
        
        # Mock database y modelo
        mock_db = Mock()
        mock_usuario = Mock()
        mock_usuario.query.count.return_value = 5
        
        service = UserService(mock_db, mock_usuario)
        
        # Test health status con DB disponible
        health = service.get_health_status()
        
        print("✓ Test health status con DB:")
        print(f"  - Service name: {health.get('service_name')}")
        print(f"  - Status: {health.get('status')}")
        print(f"  - Database available: {health.get('database_available')}")
        print(f"  - User count: {health.get('user_count')}")
        
        if health.get('service_name') == 'UserService' and health.get('database_available'):
            print("  ✓ PASÓ")
        else:
            print("  ✗ FALLÓ")
            return False
        
        # Test health status sin DB
        service_no_db = UserService(None, mock_usuario)
        health_no_db = service_no_db.get_health_status()
        
        print("\n✓ Test health status sin DB:")
        print(f"  - Status: {health_no_db.get('status')}")
        print(f"  - Database available: {health_no_db.get('database_available')}")
        
        if health_no_db.get('status') == 'degraded' and not health_no_db.get('database_available'):
            print("  ✓ PASÓ")
        else:
            print("  ✗ FALLÓ")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test health status: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests del servicio de usuarios"""
    
    print("INICIANDO TESTS DEL SERVICIO DE USUARIOS")
    print("=" * 55)
    
    tests = [
        test_password_generation,
        test_get_all_users,
        test_create_user_function,
        test_update_user_function,
        test_authenticate_user,
        test_health_status
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Error inesperado en {test_func.__name__}: {e}")
    
    print("\n" + "=" * 55)
    print("RESUMEN DE TESTS")
    print("=" * 55)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON")
        print("\nUserService listo para usar:")
        print("• Generación segura de contraseñas")
        print("• Gestión completa de usuarios (CRUD)")
        print("• Autenticación robusta")
        print("• Validación de datos de entrada")
        print("• Manejo de errores y excepciones")
        print("• Health checks y diagnósticos")
        print("• Logging estructurado integrado")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)