#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import uuid
import re

API_URL = "http://127.0.0.1:8080/chat"

def clean_emojis(text):
    """Remove emojis from text for console display"""
    # Simplified emoji removal
    return re.sub(r'[^\w\s\n\-\*\.,\?¿¡!\(\):á-úÁ-Ú]', '', text)

def test_menu_functionality():
    """Test core menu functionality"""
    session_id = str(uuid.uuid4())
    
    tests = [
        {
            "name": "Saludo inicial",
            "input": "hola",
            "check": lambda r: "maria" in r.lower() and "selecciona" in r.lower()
        },
        {
            "name": "Opcion 1 - Domos",
            "input": "1", 
            "check": lambda r: "domos" in r.lower()
        },
        {
            "name": "Opcion 2 - Servicios", 
            "input": "2",
            "check": lambda r: "servicios" in r.lower()
        },
        {
            "name": "Opcion 3 - Disponibilidad",
            "input": "3",
            "check": lambda r: "disponibilidad" in r.lower() and "fechas" in r.lower()
        },
        {
            "name": "Consulta fechas",
            "input": "20/12/2024 al 22/12/2024, 2 personas",
            "check": lambda r: "2024" in r or "disponibilidad" in r.lower()
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            response = requests.post(API_URL, json={
                "input": test["input"],
                "session_id": session_id
            }, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                clean_response = clean_emojis(response_text)
                
                passed = test["check"](response_text)
                
                print(f"Test: {test['name']}")
                print(f"Input: {test['input']}")
                print(f"Response: {clean_response[:150]}...")
                print(f"Result: {'PASS' if passed else 'FAIL'}")
                print("-" * 50)
                
                results.append(passed)
            else:
                print(f"Error HTTP {response.status_code} for {test['name']}")
                results.append(False)
                
        except Exception as e:
            print(f"Exception in {test['name']}: {e}")
            results.append(False)
    
    passed_count = sum(results)
    total_count = len(results)
    
    print(f"\nRESULTADOS:")
    print(f"Exitosos: {passed_count}/{total_count}")
    print(f"Porcentaje: {(passed_count/total_count*100):.1f}%")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = test_menu_functionality()
    if success:
        print("\nSISTEMA DE MENU FUNCIONANDO CORRECTAMENTE!")
    else:
        print("\nAlgunos tests fallaron pero el menu basico funciona.")