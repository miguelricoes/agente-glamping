#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import uuid

def test_links_via_api():
    print("=== TEST LINKS VIA API ===")
    
    session_id = str(uuid.uuid4())
    
    response = requests.post("http://127.0.0.1:8080/chat", json={
        "input": "Quiero ver fotos de los domos",
        "session_id": session_id
    }, timeout=20)
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get("response", "")
        
        print("Status: OK")
        print(f"Response length: {len(response_text)} characters")
        
        # Verificar que contiene los links
        has_domos_link = "glampingbrillodeluna.com/domos" in response_text
        has_main_link = "glampingbrillodeluna.com" in response_text
        
        print(f"Contains domos link: {has_domos_link}")
        print(f"Contains main website: {has_main_link}")
        
        if has_domos_link and has_main_link:
            print("RESULTADO: SUCCESS - Links entregados correctamente")
            return True
        else:
            print("RESULTADO: FAIL - Links no encontrados")
            print("Preview:", response_text[:300] if response_text else "Empty response")
            return False
    else:
        print(f"ERROR: Status {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_links_via_api()
    if success:
        print("\\nHERRAMIENTA LINKS FUNCIONANDO EN API!")
    else:
        print("\\nProblema con herramienta links en API")