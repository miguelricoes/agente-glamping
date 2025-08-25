#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test simple para validar el sistema de fallback RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_fallback():
    print("=== TEST BASICO DE FALLBACK RAG ===")
    
    try:
        from agente import get_direct_rag_response
        
        # Test básico de precios
        print("\n1. Test de precios:")
        response = get_direct_rag_response("cuales son los precios de los domos")
        print(f"Respuesta: {response[:200]}...")
        
        # Verificar contenido básico
        has_pricing = any(price in response for price in ["650", "550", "350"])
        has_domos = any(domo in response.lower() for domo in ["antares", "polaris", "sirius"])
        
        print(f"Incluye precios: {'SI' if has_pricing else 'NO'}")
        print(f"Incluye nombres domos: {'SI' if has_domos else 'NO'}")
        
        # Test básico de servicios  
        print("\n2. Test de servicios:")
        response = get_direct_rag_response("que servicios incluyen")
        print(f"Respuesta: {response[:200]}...")
        
        has_services = any(service in response.lower() for service in ["desayuno", "wifi", "parqueadero"])
        print(f"Incluye servicios: {'SI' if has_services else 'NO'}")
        
        # Test de respuesta general
        print("\n3. Test de respuesta general:")
        response = get_direct_rag_response("hola que tal")
        print(f"Respuesta: {response[:200]}...")
        
        has_menu = "1." in response and "2." in response
        has_branding = "brillo de luna" in response.lower()
        print(f"Incluye menu: {'SI' if has_menu else 'NO'}")
        print(f"Incluye branding: {'SI' if has_branding else 'NO'}")
        
        print("\n=== RESULTADO ===")
        if has_pricing and has_domos and has_services and has_menu:
            print("EXITOSO: Sistema de fallback funcionando correctamente")
            return True
        else:
            print("PARCIAL: Sistema funciona pero podria mejorarse")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("INICIANDO TEST SIMPLE DE FALLBACK")
    print("=" * 50)
    
    success = test_basic_fallback()
    
    print("\n" + "=" * 50)
    if success:
        print("SISTEMA DE FALLBACK RAG FUNCIONANDO")
    else:
        print("SISTEMA NECESITA REVISION")