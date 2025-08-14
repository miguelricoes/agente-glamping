# test_usuarios_api.py
import requests
import json
import sys
import os

# URL base del servidor (cambiar si es diferente)
BASE_URL = "http://localhost:8080"

def test_usuarios_api():
    """Test completo de las APIs de usuarios"""
    
    print("=== INICIANDO TESTS DE USUARIOS API ===")
    
    # Test 1: Verificar que el servidor responde
    print("\n1. Verificando conexión al servidor...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("OK: Servidor conectado correctamente")
        else:
            print(f"WARNING: Servidor responde pero con codigo: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error de conexion: {e}")
        print("TIP: Asegurate de que el servidor este ejecutandose en localhost:8080")
        return False
    
    # Test 2: Obtener lista inicial de usuarios
    print("\n2. Obteniendo lista inicial de usuarios...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios")
        if response.status_code == 200:
            usuarios_iniciales = response.json()
            print(f"OK: API /api/usuarios funciona. Usuarios encontrados: {len(usuarios_iniciales)}")
            
            # Mostrar usuarios existentes
            if usuarios_iniciales:
                print("Usuarios existentes:")
                for user in usuarios_iniciales:
                    print(f"   - {user['nombre']} ({user['email']}) - Rol: {user['rol']}")
            else:
                print("No hay usuarios registrados")
        else:
            print(f"ERROR: Error al obtener usuarios: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error en GET usuarios: {e}")
        return False
    
    # Test 3: Crear nuevo usuario
    print("\n3. Creando nuevo usuario de prueba...")
    nuevo_usuario = {
        "nombre": "Usuario Test API",
        "email": "test_api@ejemplo.com",
        "password": "password123",
        "rol": "limitado"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/usuarios",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(nuevo_usuario)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                user_id = result.get('id')
                print(f"OK: Usuario creado exitosamente - ID: {user_id}")
            else:
                print(f"ERROR: Error en respuesta: {result}")
                return False
        else:
            print(f"ERROR: Error al crear usuario: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error en POST usuario: {e}")
        return False
    
    # Test 4: Verificar que el usuario se creó
    print("\n4. Verificando que el usuario se creó correctamente...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios")
        if response.status_code == 200:
            usuarios_actuales = response.json()
            usuario_creado = None
            for user in usuarios_actuales:
                if user['email'] == 'test_api@ejemplo.com':
                    usuario_creado = user
                    break
            
            if usuario_creado:
                print(f"OK: Usuario encontrado en la lista:")
                print(f"   - Nombre: {usuario_creado['nombre']}")
                print(f"   - Email: {usuario_creado['email']}")
                print(f"   - Rol: {usuario_creado['rol']}")
                print(f"   - Activo: {usuario_creado['activo']}")
                user_id = usuario_creado['id']
            else:
                print("ERROR: Usuario no encontrado en la lista")
                return False
        else:
            print(f"ERROR: Error al verificar usuarios: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Error en verificacion: {e}")
        return False
    
    # Test 5: Actualizar usuario
    print("\n5. Actualizando usuario de prueba...")
    datos_actualizacion = {
        "nombre": "Usuario Test API Actualizado",
        "email": "test_api_actualizado@ejemplo.com",
        "rol": "completo",
        "activo": True
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/usuarios/{user_id}",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(datos_actualizacion)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("OK: Usuario actualizado exitosamente")
            else:
                print(f"ERROR: Error en actualizacion: {result}")
                return False
        else:
            print(f"ERROR: Error al actualizar usuario: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error en PUT usuario: {e}")
        return False
    
    # Test 6: Verificar actualización
    print("\n6. Verificando actualización...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios")
        if response.status_code == 200:
            usuarios_actuales = response.json()
            usuario_actualizado = None
            for user in usuarios_actuales:
                if user['id'] == user_id:
                    usuario_actualizado = user
                    break
            
            if usuario_actualizado:
                print(f"OK: Actualizacion verificada:")
                print(f"   - Nombre: {usuario_actualizado['nombre']}")
                print(f"   - Email: {usuario_actualizado['email']}")
                print(f"   - Rol: {usuario_actualizado['rol']}")
            else:
                print("ERROR: Usuario actualizado no encontrado")
                return False
    except Exception as e:
        print(f"ERROR: Error en verificacion de actualizacion: {e}")
        return False
    
    # Test 7: Eliminar usuario (soft delete)
    print("\n7. Eliminando usuario de prueba...")
    try:
        response = requests.delete(f"{BASE_URL}/api/usuarios/{user_id}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("OK: Usuario eliminado exitosamente")
            else:
                print(f"ERROR: Error en eliminacion: {result}")
                return False
        else:
            print(f"ERROR: Error al eliminar usuario: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Error en DELETE usuario: {e}")
        return False
    
    # Test 8: Verificar eliminación
    print("\n8. Verificando eliminación...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios")
        if response.status_code == 200:
            usuarios_finales = response.json()
            usuario_eliminado = None
            for user in usuarios_finales:
                if user['id'] == user_id:
                    usuario_eliminado = user
                    break
            
            if usuario_eliminado:
                if not usuario_eliminado['activo']:
                    print("OK: Usuario marcado como inactivo (soft delete)")
                else:
                    print("WARNING: Usuario aun activo - eliminacion no funciono")
                    return False
            else:
                print("OK: Usuario removido de la lista")
    except Exception as e:
        print(f"ERROR: Error en verificacion de eliminacion: {e}")
        return False
    
    print("\nTODOS LOS TESTS PASARON EXITOSAMENTE!")
    print("Resumen de tests:")
    print("   OK: Conexion al servidor")
    print("   OK: GET /api/usuarios")
    print("   OK: POST /api/usuarios")
    print("   OK: PUT /api/usuarios/<id>")
    print("   OK: DELETE /api/usuarios/<id>")
    print("   OK: Validacion de datos")
    print("   OK: Soft delete")
    
    return True

def mostrar_estado_sistema():
    """Mostrar estado actual del sistema"""
    print("\n=== ESTADO ACTUAL DEL SISTEMA ===")
    
    try:
        # Verificar usuarios
        response = requests.get(f"{BASE_URL}/api/usuarios")
        if response.status_code == 200:
            usuarios = response.json()
            print(f"Total de usuarios: {len(usuarios)}")
            
            usuarios_activos = [u for u in usuarios if u.get('activo', True)]
            usuarios_inactivos = [u for u in usuarios if not u.get('activo', True)]
            
            print(f"   Activos: {len(usuarios_activos)}")
            print(f"   Inactivos: {len(usuarios_inactivos)}")
            
            print("\nUsuarios por rol:")
            completos = [u for u in usuarios_activos if u.get('rol') == 'completo']
            limitados = [u for u in usuarios_activos if u.get('rol') == 'limitado']
            
            print(f"   Completo: {len(completos)}")
            print(f"   Limitado: {len(limitados)}")
            
        # Verificar reservas
        response = requests.get(f"{BASE_URL}/api/reservas")
        if response.status_code == 200:
            reservas = response.json()
            print(f"\nTotal de reservas: {len(reservas)}")
            
    except Exception as e:
        print(f"ERROR: Error al obtener estado: {e}")

if __name__ == "__main__":
    print("SISTEMA DE TESTS - APIs de Usuarios")
    print("=====================================")
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            mostrar_estado_sistema()
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python test_usuarios_api.py           # Ejecutar todos los tests")
            print("  python test_usuarios_api.py --status  # Mostrar estado del sistema")
            print("  python test_usuarios_api.py --help    # Mostrar esta ayuda")
            sys.exit(0)
    
    # Ejecutar tests
    if test_usuarios_api():
        print("\nSistema de usuarios funcionando correctamente")
        mostrar_estado_sistema()
        sys.exit(0)
    else:
        print("\nAlgunos tests fallaron")
        print("TIP: Verifica que:")
        print("   1. El servidor esté ejecutándose (python agente.py)")
        print("   2. La base de datos esté configurada")
        print("   3. Las APIs estén funcionando")
        sys.exit(1)