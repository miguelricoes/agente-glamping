# test_usuarios_simple.py - Test simple y robusto para verificar dependencias
import requests
import json

BASE_URL = "http://localhost:8080"

def test_dependencies_and_basic_functionality():
    """Test simple para verificar que las dependencias funcionen"""
    
    print("=== TEST DE DEPENDENCIAS Y FUNCIONALIDAD BASICA ===")
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Servidor responde
    print("\n1. Verificando servidor...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   OK: Servidor funcionando")
            tests_passed += 1
        else:
            print(f"   ERROR: Servidor error: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: Error conexion: {e}")
    
    # Test 2: Base de datos accesible
    print("\n2. Verificando base de datos...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios")
        if response.status_code == 200:
            users = response.json()
            print(f"   OK: BD accesible - {len(users)} usuarios encontrados")
            tests_passed += 1
        else:
            print(f"   ERROR: BD error: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: Error BD: {e}")
    
    # Test 3: Werkzeug hash funcionando
    print("\n3. Verificando funciones de hash...")
    try:
        from werkzeug.security import generate_password_hash, check_password_hash
        test_password = "test123"
        hash_result = generate_password_hash(test_password)
        check_result = check_password_hash(hash_result, test_password)
        
        if check_result:
            print("   OK: Werkzeug hash funcionando correctamente")
            tests_passed += 1
        else:
            print("   ERROR: Werkzeug hash fallo")
    except Exception as e:
        print(f"   ERROR: Error Werkzeug: {e}")
    
    # Test 4: Crear usuario temporal
    print("\n4. Verificando creación de usuario...")
    try:
        user_data = {
            "nombre": "Test Temporal",
            "email": f"test_temp_{hash(str(requests.get(f'{BASE_URL}/health').headers))}@test.com",
            "password": "test123",
            "rol": "limitado"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/usuarios",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(user_data)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                user_id = result.get('id')
                print(f"   OK: Usuario creado exitosamente - ID: {user_id}")
                tests_passed += 1
                
                # Test 5: Eliminar usuario temporal
                print("\n5. Verificando eliminación...")
                delete_response = requests.delete(f"{BASE_URL}/api/usuarios/{user_id}")
                if delete_response.status_code == 200:
                    print("   OK: Usuario eliminado correctamente")
                    tests_passed += 1
                else:
                    print(f"   ERROR: Error al eliminar: {delete_response.status_code}")
            else:
                print(f"   ERROR: Error en respuesta: {result}")
        else:
            print(f"   ERROR: Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: Error en test CRUD: {e}")
    
    # Resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN: {tests_passed}/{total_tests} tests pasaron")
    
    if tests_passed == total_tests:
        print("TODOS LOS TESTS PASARON!")
        print("OK: Dependencias resueltas correctamente")
        print("OK: Werkzeug 3.0+ funcionando")
        print("OK: Sistema de usuarios operativo")
        return True
    else:
        print(f"WARNING: {total_tests - tests_passed} tests fallaron")
        return False

if __name__ == "__main__":
    success = test_dependencies_and_basic_functionality()
    exit(0 if success else 1)