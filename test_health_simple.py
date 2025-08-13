#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar el endpoint /health sin emojis
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_health_endpoint():
    """Test principal del endpoint /health"""
    
    print("TEST: Verificando endpoint /health")
    print("=" * 50)
    
    try:
        # Importar y verificar variables críticas
        from agente import app, database_available, db, database_url
        
        print("1. Importacion exitosa")
        print(f"   - database_available: {database_available}")
        print(f"   - database_available tipo: {type(database_available)}")
        print(f"   - db inicializado: {db is not None}")
        print(f"   - database_url configurada: {bool(database_url)}")
        
        # Test del endpoint
        with app.test_client() as client:
            print("2. Realizando peticion GET /health")
            response = client.get('/health')
            
            print(f"   - Status code: {response.status_code}")
            
            # Verificar que no es 500 (Internal Server Error)
            if response.status_code == 500:
                print("   ERROR: Aun hay Internal Server Error")
                data = response.get_json()
                if data and 'error' in data:
                    print(f"   Detalle error: {data['error']}")
                return False
            
            # Parsear JSON
            data = response.get_json()
            print("3. Respuesta JSON:")
            print(f"   - status: {data.get('status')}")
            print(f"   - database: {data.get('database')}")
            print(f"   - timestamp: {data.get('timestamp', 'present')}")
            
            # Verificar campos requeridos
            required = ['status', 'timestamp', 'database']
            missing = [f for f in required if f not in data]
            
            if missing:
                print(f"   ERROR: Campos faltantes: {missing}")
                return False
            
            # Verificar coherencia
            if database_available and data['database'] != 'connected':
                print("   ERROR: BD disponible pero status disconnected")
                return False
                
            if not database_available and data['database'] != 'disconnected':
                print("   ERROR: BD no disponible pero status connected")
                return False
            
            print("4. VERIFICACION EXITOSA")
            print("   - No hay Internal Server Error")
            print("   - Todos los campos presentes")
            print("   - Estados coherentes")
            
            return True
            
    except NameError as e:
        if 'database_available' in str(e):
            print("ERROR: Variable database_available no definida")
            return False
        else:
            print(f"ERROR: NameError: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception: {e}")
        return False

def test_original_issue():
    """Verificar que el problema original está solucionado"""
    
    print("\nTEST: Problema original solucionado")
    print("=" * 50)
    
    try:
        from agente import app
        
        with app.test_client() as client:
            response = client.get('/health')
            
            # El problema original era Internal Server Error (500)
            if response.status_code == 500:
                print("FALLO: Aun hay Internal Server Error")
                return False
            
            # Debe ser 200 (healthy) o 503 (degraded)
            if response.status_code not in [200, 503]:
                print(f"FALLO: Codigo inesperado {response.status_code}")
                return False
            
            print(f"EXITO: Endpoint responde con codigo {response.status_code}")
            return True
            
    except Exception as e:
        print(f"FALLO: {e}")
        return False

if __name__ == "__main__":
    print("Ejecutando verificacion del endpoint /health")
    print("Objetivo: Confirmar que el Internal Server Error esta solucionado")
    print()
    
    test1 = test_health_endpoint()
    test2 = test_original_issue()
    
    print("\n" + "=" * 50)
    print("RESUMEN:")
    print(f"Test funcionalidad: {'PASO' if test1 else 'FALLO'}")
    print(f"Test problema original: {'PASO' if test2 else 'FALLO'}")
    
    if test1 and test2:
        print("\nTODOS LOS TESTS PASARON")
        print("Las correcciones funcionan correctamente")
    else:
        print("\nALGUNOS TESTS FALLARON")
        print("Revisar implementacion")