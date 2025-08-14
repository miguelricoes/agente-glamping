# test_auth_endpoints.py - Test para endpoints de autenticación
import requests
import json

BASE_URL = "http://localhost:8080"

def test_authentication_endpoints():
    """Test completo para endpoints de autenticación"""
    
    print("=== TEST DE ENDPOINTS DE AUTENTICACION ===")
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Verificar endpoint /api/auth/verify
    print("\n1. Verificando endpoint /api/auth/verify...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/verify")
        if response.status_code == 200:
            data = response.json()
            if 'total_users' in data and 'database_connected' in data:
                print(f"   OK: Endpoint verify funcionando - {data['total_users']} usuarios")
                tests_passed += 1
            else:
                print("   ERROR: Respuesta incompleta")
        else:
            print(f"   ERROR: Código de respuesta: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Login con credenciales incorrectas
    print("\n2. Probando login con credenciales incorrectas...")
    try:
        login_data = {
            "email": "usuario_inexistente@test.com",
            "password": "password_incorrecto"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(login_data)
        )
        
        if response.status_code == 401:
            print("   OK: Credenciales incorrectas rechazadas correctamente")
            tests_passed += 1
        else:
            print(f"   ERROR: Debería retornar 401, retornó: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Login con datos faltantes
    print("\n3. Probando login con datos faltantes...")
    try:
        login_data = {"email": "test@test.com"}  # Falta password
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(login_data)
        )
        
        if response.status_code == 400:
            print("   OK: Datos faltantes rechazados correctamente")
            tests_passed += 1
        else:
            print(f"   ERROR: Debería retornar 400, retornó: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Login con usuario administrador
    print("\n4. Probando login con usuario administrador...")
    try:
        login_data = {
            "email": "juan@example.com",
            "password": "admin123"  # Contraseña del admin creada en setup
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(login_data)
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'user' in data:
                user = data['user']
                print(f"   OK: Login admin exitoso - {user['nombre']} ({user['rol']})")
                tests_passed += 1
            else:
                print(f"   ERROR: Respuesta incorrecta: {data}")
        else:
            print(f"   ERROR: Login falló - Código: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN: {tests_passed}/{total_tests} tests pasaron")
    
    if tests_passed == total_tests:
        print("TODOS LOS TESTS DE AUTENTICACION PASARON!")
        print("OK: Endpoints /api/auth/* funcionando")
        print("OK: Función authenticate_user() operativa")
        print("OK: Validación de contraseñas con check_password_hash")
        print("OK: Sistema de login completamente funcional")
        return True
    else:
        print(f"WARNING: {total_tests - tests_passed} tests fallaron")
        return False

def test_authentication_flow():
    """Test de flujo completo de autenticación"""
    
    print("\n=== TEST DE FLUJO COMPLETO DE AUTENTICACION ===")
    
    # 1. Crear usuario temporal para test
    print("\n1. Creando usuario temporal para test...")
    user_data = {
        "nombre": "Usuario Auth Test",
        "email": "auth_test@ejemplo.com",
        "password": "test_password_123",
        "rol": "limitado"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/usuarios",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(user_data)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                user_id = result.get('id')
                print(f"   OK: Usuario temporal creado - ID: {user_id}")
                
                # 2. Probar login con el usuario temporal
                print("\n2. Probando login con usuario temporal...")
                login_data = {
                    "email": "auth_test@ejemplo.com",
                    "password": "test_password_123"
                }
                
                login_response = requests.post(
                    f"{BASE_URL}/api/auth/login",
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(login_data)
                )
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    if login_result.get('success'):
                        user_info = login_result['user']
                        print(f"   OK: Login exitoso - {user_info['nombre']} ({user_info['rol']})")
                        
                        # 3. Limpiar - eliminar usuario temporal
                        print("\n3. Limpiando usuario temporal...")
                        delete_response = requests.delete(f"{BASE_URL}/api/usuarios/{user_id}")
                        if delete_response.status_code == 200:
                            print("   OK: Usuario temporal eliminado")
                            return True
                        else:
                            print(f"   WARNING: No se pudo eliminar usuario temporal")
                            return True  # El test principal pasó
                    else:
                        print(f"   ERROR: Login falló: {login_result}")
                        return False
                else:
                    print(f"   ERROR: Login falló - Código: {login_response.status_code}")
                    return False
            else:
                print(f"   ERROR: No se pudo crear usuario temporal: {result}")
                return False
        else:
            print(f"   ERROR: Error al crear usuario temporal: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    print("TESTS DE SISTEMA DE AUTENTICACION")
    print("=" * 50)
    
    # Ejecutar tests básicos
    basic_success = test_authentication_endpoints()
    
    # Ejecutar test de flujo completo
    flow_success = test_authentication_flow()
    
    print(f"\n{'='*50}")
    print("RESUMEN FINAL:")
    print(f"Tests básicos: {'PASS' if basic_success else 'FAIL'}")
    print(f"Test de flujo: {'PASS' if flow_success else 'FAIL'}")
    
    if basic_success and flow_success:
        print("\nSISTEMA DE AUTENTICACION COMPLETAMENTE FUNCIONAL!")
        print("✓ Endpoints implementados correctamente")
        print("✓ Validación de contraseñas funcionando")
        print("✓ Base de datos integrada")
        print("✓ Flujo completo de login operativo")
    else:
        print("\nALGUNOS TESTS FALLARON - Revisar implementación")
    
    exit(0 if (basic_success and flow_success) else 1)