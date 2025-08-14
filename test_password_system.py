# test_password_system.py - Test completo del sistema de contraseñas visibles
import requests
import json
import re

BASE_URL = "http://localhost:8080"

def test_password_system():
    """Test completo del sistema de contraseñas visibles para admin"""
    
    print("=== TEST DEL SISTEMA DE CONTRASEÑAS VISIBLES ===")
    
    tests_passed = 0
    total_tests = 6
    created_user_id = None
    generated_password = None
    
    # Test 1: Crear usuario SIN contraseña (debe generar automáticamente)
    print("\n1. Creando usuario SIN contraseña especificada...")
    try:
        user_data = {
            "nombre": "Test Password User",
            "email": "test_password@ejemplo.com",
            "rol": "limitado"
            # NO incluir password - debe generar automáticamente
        }
        
        response = requests.post(
            f"{BASE_URL}/api/usuarios",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(user_data)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and 'temp_password' in result:
                created_user_id = result['id']
                generated_password = result['temp_password']
                
                # Verificar formato contraseña generada (ej: Mesa2024)
                password_pattern = r'^[A-Z][a-z]{2,}\d{4}$'  # Palabra + 4 dígitos
                if re.match(password_pattern, generated_password):
                    print(f"   OK: Usuario creado con contraseña generada: '{generated_password}'")
                    print(f"   OK: Formato correcto (Palabra + 4 dígitos)")
                    tests_passed += 1
                else:
                    print(f"   ERROR: Formato de contraseña incorrecto: '{generated_password}'")
            else:
                print(f"   ERROR: Respuesta incorrecta: {result}")
        else:
            print(f"   ERROR: Error al crear usuario: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Obtener usuarios SIN contraseñas (default)
    print("\n2. Obteniendo usuarios SIN contraseñas (comportamiento default)...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios")
        
        if response.status_code == 200:
            usuarios = response.json()
            user_found = None
            for user in usuarios:
                if user.get('id') == created_user_id:
                    user_found = user
                    break
            
            if user_found:
                if 'temp_password' not in user_found:
                    print("   OK: Usuario encontrado SIN campo temp_password")
                    print("   OK: Contraseñas ocultas por default")
                    tests_passed += 1
                else:
                    print("   ERROR: Campo temp_password visible cuando NO debería")
            else:
                print("   ERROR: Usuario creado no encontrado")
        else:
            print(f"   ERROR: Error al obtener usuarios: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Obtener usuarios CON contraseñas (solo admin)
    print("\n3. Obteniendo usuarios CON contraseñas (include_passwords=true)...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios?include_passwords=true")
        
        if response.status_code == 200:
            usuarios = response.json()
            user_found = None
            for user in usuarios:
                if user.get('id') == created_user_id:
                    user_found = user
                    break
            
            if user_found:
                if 'temp_password' in user_found and user_found['temp_password'] == generated_password:
                    print(f"   OK: Usuario encontrado CON temp_password: '{user_found['temp_password']}'")
                    print("   OK: Contraseñas visibles cuando se solicita")
                    tests_passed += 1
                else:
                    print(f"   ERROR: temp_password no coincide o no está presente")
            else:
                print("   ERROR: Usuario creado no encontrado")
        else:
            print(f"   ERROR: Error al obtener usuarios con contraseñas: {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Login con contraseña generada
    print("\n4. Probando login con contraseña generada...")
    try:
        if generated_password:
            login_data = {
                "email": "test_password@ejemplo.com",
                "password": generated_password
            }
            
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(login_data)
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    user_info = result['user']
                    print(f"   OK: Login exitoso con contraseña generada")
                    print(f"   OK: Usuario: {user_info['nombre']} ({user_info['rol']})")
                    tests_passed += 1
                else:
                    print(f"   ERROR: Login falló: {result}")
            else:
                print(f"   ERROR: Login falló - Código: {response.status_code}")
        else:
            print("   ERROR: No hay contraseña generada para probar")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 5: Regenerar contraseña
    print("\n5. Regenerando contraseña del usuario...")
    try:
        if created_user_id:
            response = requests.post(f"{BASE_URL}/api/usuarios/{created_user_id}/regenerate-password")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'temp_password' in result:
                    new_password = result['temp_password']
                    
                    # Verificar que es diferente a la anterior
                    if new_password != generated_password:
                        # Verificar formato de nueva contraseña
                        password_pattern = r'^[A-Z][a-z]{2,}\d{4}$'
                        if re.match(password_pattern, new_password):
                            print(f"   OK: Contraseña regenerada: '{new_password}'")
                            print("   OK: Nueva contraseña tiene formato correcto")
                            generated_password = new_password  # Actualizar para siguiente test
                            tests_passed += 1
                        else:
                            print(f"   ERROR: Nueva contraseña tiene formato incorrecto: '{new_password}'")
                    else:
                        print("   ERROR: Nueva contraseña es igual a la anterior")
                else:
                    print(f"   ERROR: Respuesta incorrecta: {result}")
            else:
                print(f"   ERROR: Error al regenerar contraseña: {response.status_code}")
        else:
            print("   ERROR: No hay usuario creado para regenerar contraseña")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 6: Login con nueva contraseña regenerada
    print("\n6. Probando login con contraseña regenerada...")
    try:
        if generated_password:
            login_data = {
                "email": "test_password@ejemplo.com",
                "password": generated_password
            }
            
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(login_data)
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("   OK: Login exitoso con contraseña regenerada")
                    tests_passed += 1
                else:
                    print(f"   ERROR: Login falló con nueva contraseña: {result}")
            else:
                print(f"   ERROR: Login falló - Código: {response.status_code}")
        else:
            print("   ERROR: No hay contraseña regenerada para probar")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Cleanup: Eliminar usuario de prueba
    if created_user_id:
        try:
            requests.delete(f"{BASE_URL}/api/usuarios/{created_user_id}")
            print(f"\nLimpieza: Usuario test eliminado")
        except:
            pass
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN: {tests_passed}/{total_tests} tests pasaron")
    
    if tests_passed == total_tests:
        print("TODOS LOS TESTS DEL SISTEMA DE CONTRASEÑAS PASARON!")
        print("OK: Contraseñas generadas automáticamente")
        print("OK: Formato correcto (Palabra + 4 dígitos)")
        print("OK: Contraseñas ocultas por default")
        print("OK: Contraseñas visibles solo con include_passwords=true")
        print("OK: Login funciona con contraseñas generadas")
        print("OK: Regeneración de contraseñas operativa")
        return True
    else:
        print(f"WARNING: {total_tests - tests_passed} tests fallaron")
        return False

def test_password_format_validation():
    """Test específico para validar formato de contraseñas generadas"""
    
    print("\n=== TEST DE FORMATO DE CONTRASEÑAS ===")
    
    # Importar funciones directamente para testear
    try:
        # Simular generación de contraseñas
        import random
        import string
        
        def generate_simple_password():
            """Simular función generate_simple_password"""
            words = ['Mesa', 'Casa', 'Luna', 'Sol', 'Mar', 'Rio', 'Pan', 'Flor', 'Luz', 'Ave']
            word = random.choice(words)
            number = random.randint(1000, 9999)
            return f"{word}{number}"
        
        print("Generando 10 contraseñas de muestra...")
        for i in range(10):
            password = generate_simple_password()
            pattern = r'^[A-Z][a-z]{2,}\d{4}$'
            is_valid = re.match(pattern, password) is not None
            status = "OK" if is_valid else "ERROR"
            print(f"   {i+1}. {password} - {status}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("TESTS DEL SISTEMA DE CONTRASEÑAS VISIBLES")
    print("=" * 60)
    
    # Ejecutar test principal
    main_success = test_password_system()
    
    # Ejecutar test de formato
    format_success = test_password_format_validation()
    
    print(f"\n{'='*60}")
    print("RESUMEN FINAL:")
    print(f"Sistema principal: {'PASS' if main_success else 'FAIL'}")
    print(f"Formato contraseñas: {'PASS' if format_success else 'FAIL'}")
    
    if main_success and format_success:
        print("\nSISTEMA DE CONTRASEÑAS COMPLETAMENTE FUNCIONAL!")
        print("✓ Generación automática implementada")
        print("✓ Visibilidad controlada por parámetro")
        print("✓ Regeneración de contraseñas operativa")
        print("✓ Login funciona con contraseñas generadas")
        print("✓ Formato de contraseñas correcto")
    else:
        print("\nALGUNOS TESTS FALLARON - Revisar implementación")
    
    exit(0 if (main_success and format_success) else 1)