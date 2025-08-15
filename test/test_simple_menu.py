#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Simple del Menu
====================
"""

import requests
import json

# Test directo del saludo
def test_simple():
    try:
        # Test 1: Verificar que el endpoint responde
        import uuid
        session_id = str(uuid.uuid4())
        response = requests.post("http://127.0.0.1:8080/chat", json={
            "input": "hola",
            "session_id": session_id
        }, timeout=10)
        
        print("Status:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print("Response:", data.get("response", ""))
            print("Memory len:", len(data.get("memory", [])))
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_simple()