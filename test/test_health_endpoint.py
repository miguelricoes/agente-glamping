#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar la funcionalidad del endpoint /health 
después de las correcciones implementadas
"""

import sys
import os
import json

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_health_endpoint_functionality():
    """Test de funcionalidad básica del endpoint /health"""
    
    print("TEST: Verificando correcciones del endpoint /health")
    print("=" * 60)
    
    try:
        # Importar la aplicación
        from agente import app, database_available, db, database_url
        
        print("1. Importación exitosa del módulo agente")
        
        # Verificar que las variables están definidas
        print("2. Verificando variables críticas:")
        print(f"   - database_available definida: {database_available is not None}")
        print(f"   - database_available valor: {database_available}")
        print(f"   - db definida: {db is not None}")
        print(f"   - database_url configurada: {bool(database_url)}")
        
        # Crear cliente de test
        with app.test_client() as client:
            print("3. Cliente de test creado exitosamente")
            
            # Hacer petición al endpoint /health
            response = client.get('/health')
            
            print("4. Petición a /health realizada")
            print(f"   - Status code: {response.status_code}")
            print(f"   - Content-Type: {response.content_type}")
            
            # Verificar que no hay Internal Server Error
            if response.status_code == 500:
                print("   ❌ FALLO: Aún hay Internal Server Error")
                data = response.get_json()
                if data and 'error' in data:
                    print(f"   Error: {data['error']}")
                return False
            
            # Parsear respuesta JSON
            data = response.get_json()
            
            if not data:
                print("   ❌ FALLO: Respuesta no es JSON válido")
                return False
            
            print("5. Respuesta JSON parseada exitosamente:")
            print(f"   - status: {data.get('status', 'NO_FOUND')}")
            print(f"   - database: {data.get('database', 'NO_FOUND')}")
            print(f"   - timestamp: {data.get('timestamp', 'NO_FOUND')}")
            
            # Verificar campos obligatorios
            required_fields = ['status', 'timestamp', 'database']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   ❌ FALLO: Campos faltantes: {missing_fields}")
                return False
            
            # Verificar campos adicionales de debugging
            debug_fields = ['database_url_configured', 'sqlalchemy_initialized']
            has_debug_fields = all(field in data for field in debug_fields)
            
            print("6. Verificando campos de debugging:")
            print(f"   - database_url_configured: {data.get('database_url_configured', 'NO_FOUND')}")
            print(f"   - sqlalchemy_initialized: {data.get('sqlalchemy_initialized', 'NO_FOUND')}")
            print(f"   - Todos los campos debug presentes: {has_debug_fields}")
            
            # Verificar lógica de códigos HTTP
            expected_status_codes = [200, 503]  # Healthy o Degraded
            
            if response.status_code not in expected_status_codes:
                print(f"   ❌ FALLO: Código HTTP inesperado: {response.status_code}")
                return False
            
            # Verificar consistencia entre database_available y respuesta
            if database_available:
                expected_db_status = "connected"
                expected_http_code = 200
            else:
                expected_db_status = "disconnected" 
                expected_http_code = 503
            
            actual_db_status = data.get('database')
            
            print("7. Verificando consistencia:")
            print(f"   - database_available: {database_available}")
            print(f"   - Esperado DB status: {expected_db_status}")
            print(f"   - Actual DB status: {actual_db_status}")
            print(f"   - Esperado HTTP code: {expected_http_code}")
            print(f"   - Actual HTTP code: {response.status_code}")
            
            if actual_db_status != expected_db_status:
                print("   ❌ FALLO: Status de BD no coincide con database_available")
                return False
                
            if response.status_code != expected_http_code:
                print("   ❌ FALLO: Código HTTP no coincide con estado de BD")
                return False
            
            print("\n✅ TODAS LAS VERIFICACIONES PASARON")
            return True
            
    except NameError as e:
        if 'database_available' in str(e):
            print("❌ FALLO: Variable database_available aún no está definida")
            print(f"Error: {e}")
            return False
        else:
            print(f"❌ FALLO: NameError inesperado: {e}")
            return False
            
    except Exception as e:
        print(f"❌ FALLO: Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_endpoint_scenarios():
    """Test de diferentes escenarios del endpoint /health"""
    
    print("\n" + "=" * 60)
    print("TEST: Escenarios específicos del endpoint /health")
    print("=" * 60)
    
    try:
        from agente import app, database_available
        
        with app.test_client() as client:
            response = client.get('/health')
            data = response.get_json()
            
            print("Escenario actual:")
            print(f"  BD disponible: {database_available}")
            print(f"  HTTP Status: {response.status_code}")
            print(f"  App Status: {data.get('status')}")
            print(f"  DB Status: {data.get('database')}")
            
            # Verificar que el comportamiento es correcto según el estado
            if database_available:
                print("\n📊 Verificando escenario: BD DISPONIBLE")
                assert response.status_code == 200, f"Esperado 200, obtenido {response.status_code}"
                assert data['status'] == 'healthy', f"Esperado 'healthy', obtenido {data['status']}"
                assert data['database'] == 'connected', f"Esperado 'connected', obtenido {data['database']}"
                print("  ✅ Escenario BD disponible: CORRECTO")
            else:
                print("\n📊 Verificando escenario: BD NO DISPONIBLE")
                assert response.status_code == 503, f"Esperado 503, obtenido {response.status_code}"
                assert data['status'] == 'degraded', f"Esperado 'degraded', obtenido {data['status']}"
                assert data['database'] == 'disconnected', f"Esperado 'disconnected', obtenido {data['database']}"
                print("  ✅ Escenario BD no disponible: CORRECTO")
            
            return True
            
    except Exception as e:
        print(f"❌ FALLO en test de escenarios: {e}")
        return False

def test_original_problem_fixed():
    """Verificar que el problema original (Internal Server Error) está solucionado"""
    
    print("\n" + "=" * 60)
    print("TEST: Verificando que el problema original está solucionado")
    print("=" * 60)
    
    try:
        from agente import app
        
        # El problema original era que database_available no estaba definida
        # causando NameError y Internal Server Error (500)
        
        with app.test_client() as client:
            response = client.get('/health')
            
            print(f"Status code obtenido: {response.status_code}")
            
            # Verificar que NO es 500 (Internal Server Error)
            if response.status_code == 500:
                print("❌ PROBLEMA ORIGINAL NO SOLUCIONADO")
                print("   Aún hay Internal Server Error")
                data = response.get_json()
                if data and 'error' in data:
                    print(f"   Error: {data['error']}")
                return False
            
            # Verificar que es uno de los códigos esperados
            valid_codes = [200, 503]
            if response.status_code not in valid_codes:
                print(f"❌ Código inesperado: {response.status_code}")
                return False
            
            print("✅ PROBLEMA ORIGINAL SOLUCIONADO")
            print(f"   Endpoint /health responde correctamente con código {response.status_code}")
            return True
            
    except Exception as e:
        print(f"❌ Error verificando solución: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Ejecutando tests de verificación del endpoint /health")
    print("🎯 Objetivo: Verificar que las correcciones solucionan el Internal Server Error")
    print()
    
    # Ejecutar todos los tests
    test1 = test_health_endpoint_functionality()
    test2 = test_health_endpoint_scenarios() 
    test3 = test_original_problem_fixed()
    
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS:")
    print("=" * 60)
    print(f"✅ Test funcionalidad básica: {'PASÓ' if test1 else 'FALLÓ'}")
    print(f"✅ Test escenarios específicos: {'PASÓ' if test2 else 'FALLÓ'}")
    print(f"✅ Test problema original solucionado: {'PASÓ' if test3 else 'FALLÓ'}")
    
    if test1 and test2 and test3:
        print("\n🎉 TODOS LOS TESTS PASARON")
        print("✅ Las correcciones al endpoint /health funcionan correctamente")
        print("✅ El problema del Internal Server Error está solucionado")
        print("✅ El despliegue en Railway debería funcionar ahora")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        print("⚠️  Revisar las correcciones implementadas")