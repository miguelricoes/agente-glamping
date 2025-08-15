#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import uuid

def test_menu_via_api():
    print("=== TEST MENU VIA API ===")
    
    session_id = str(uuid.uuid4())
    
    response = requests.post("http://127.0.0.1:8080/chat", json={
        "input": "Tienes menus con los que me pueda guiar?",
        "session_id": session_id
    }, timeout=20)
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get("response", "")
        
        print("Status: OK")
        print(f"Response length: {len(response_text)} characters")
        
        # Verificar que contiene opciones del menú
        has_menu_options = "1️⃣" in response_text and "2️⃣" in response_text
        has_maria_intro = "María" in response_text
        has_glamping_name = "Brillo de Luna" in response_text
        
        print(f"Contains menu options: {has_menu_options}")
        print(f"Contains María intro: {has_maria_intro}")
        print(f"Contains Glamping name: {has_glamping_name}")
        
        if has_menu_options and has_maria_intro:
            print("RESULTADO: SUCCESS - Menu funcionando correctamente")
            return True
        else:
            print("RESULTADO: FAIL - Menu no detectado")
            return False
    else:
        print(f"ERROR: Status {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_menu_via_api()
    if success:
        print("\nHERRAMIENTA MENU FUNCIONANDO EN API!")
    else:
        print("\nProblema con herramienta menu en API")