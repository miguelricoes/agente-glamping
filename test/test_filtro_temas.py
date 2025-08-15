#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test del Sistema de Filtrado de Temas
=====================================
Prueba que el agente solo responda temas relacionados con glamping
"""

import requests
import json
import uuid
import re

API_URL = "http://127.0.0.1:8080/chat"

def clean_emojis(text):
    """Remove emojis from text for console display"""
    return re.sub(r'[^\w\s\n\-\*\.,\?¿¡!\(\):á-úÁ-Ú]', '', text)

def test_topic_filter():
    """Test del sistema de filtrado de temas"""
    print("TESTING SISTEMA DE FILTRADO DE TEMAS")
    print("=" * 60)
    
    # Test cases
    tests = [
        {
            "name": "Pregunta sobre glamping (DEBE PASAR)",
            "input": "¿Qué tipos de domos tienen disponibles?",
            "should_be_blocked": False,
            "expected_content": ["domos", "disponibles"]
        },
        {
            "name": "Pregunta sobre reservas (DEBE PASAR)",
            "input": "¿Cómo puedo hacer una reserva para el fin de semana?",
            "should_be_blocked": False,
            "expected_content": ["reserva"]
        },
        {
            "name": "Pregunta sobre deportes (DEBE SER BLOQUEADA)",
            "input": "¿Quién ganó el partido de fútbol ayer?",
            "should_be_blocked": True,
            "expected_content": ["solo puedo ayudarte", "glamping"]
        },
        {
            "name": "Pregunta sobre política (DEBE SER BLOQUEADA)",
            "input": "¿Qué opinas sobre las elecciones?",
            "should_be_blocked": True,
            "expected_content": ["solo puedo ayudarte", "glamping"]
        },
        {
            "name": "Pregunta sobre matemáticas (DEBE SER BLOQUEADA)",
            "input": "¿Cuánto es 2 + 2?",
            "should_be_blocked": True,
            "expected_content": ["solo puedo ayudarte", "glamping"]
        },
        {
            "name": "Saludo (DEBE PASAR - bypass)",
            "input": "hola",
            "should_be_blocked": False,
            "expected_content": ["María", "selecciona"]
        },
        {
            "name": "Número de menú (DEBE PASAR - bypass)",
            "input": "1",
            "should_be_blocked": False,
            "expected_content": ["domos"]
        },
        {
            "name": "Pregunta sobre recetas (DEBE SER BLOQUEADA)",
            "input": "¿Cómo se hace una pizza?",
            "should_be_blocked": True,
            "expected_content": ["solo puedo ayudarte", "glamping"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Input: '{test['input']}'")
        
        try:
            # Usar session ID único para cada test
            session_id = str(uuid.uuid4())
            
            response = requests.post(API_URL, json={
                "input": test["input"],
                "session_id": session_id
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").lower()
                clean_response = clean_emojis(response_text)
                
                print(f"Response: {clean_response[:150]}...")
                
                # Verificar si fue bloqueado correctamente
                was_blocked = "solo puedo ayudarte" in response_text
                
                if test["should_be_blocked"]:
                    
                    # Este mensaje DEBERÍA ser bloqueado
                    if was_blocked:
                        print("OK CORRECTO: Mensaje bloqueado como esperado")
                        passed += 1
                    else:
                        print("ERROR FALLO: Mensaje NO fue bloqueado cuando deberia")
                        failed += 1
                else:
                    # Este mensaje NO debería ser bloqueado
                    if not was_blocked:
                        # Verificar contenido esperado
                        content_found = all(
                            content.lower() in response_text 
                            for content in test["expected_content"]
                        )
                        if content_found:
                            print("OK CORRECTO: Mensaje paso y tiene contenido esperado")
                            passed += 1
                        else:
                            print(f"ERROR FALLO: Mensaje paso pero falta contenido: {test['expected_content']}")
                            failed += 1
                    else:
                        print("ERROR FALLO: Mensaje fue bloqueado cuando NO deberia")
                        failed += 1
                        
            else:
                print(f"ERROR HTTP {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"EXCEPCION: {e}")
            failed += 1
        
        print("-" * 50)
    
    print(f"\nRESULTADOS DEL FILTRADO:")
    print(f"OK Tests exitosos: {passed}")
    print(f"ERROR Tests fallidos: {failed}")
    print(f"Porcentaje de exito: {(passed/(passed+failed)*100):.1f}%")
    
    return passed, failed

if __name__ == "__main__":
    try:
        passed, failed = test_topic_filter()
        if failed == 0:
            print("\nSISTEMA DE FILTRADO FUNCIONANDO PERFECTAMENTE!")
        else:
            print(f"\n{failed} tests fallaron - revisar implementacion")
    except Exception as e:
        print(f"\nError ejecutando tests: {e}")