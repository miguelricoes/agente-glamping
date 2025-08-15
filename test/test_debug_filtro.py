#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test directo de la función de filtrado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agente import is_glamping_related, should_bypass_filter

def test_filter_function():
    test_cases = [
        ("¿Quién ganó el partido de fútbol ayer?", False, "Deportes"),
        ("¿Qué tipos de domos tienen?", True, "Glamping"),
        ("¿Cómo se hace una pizza?", False, "Recetas"),
        ("¿Cuánto es 2 + 2?", False, "Matemáticas"),
        ("hola", True, "Saludo - bypass"),
        ("1", True, "Menú - bypass")
    ]
    
    print("TESTING FUNCIÓN DE FILTRADO DIRECTA")
    print("=" * 50)
    
    for message, expected, categoria in test_cases:
        print(f"\nTest: {categoria}")
        print(f"Mensaje: '{message}'")
        
        # Verificar bypass
        bypass = should_bypass_filter(message)
        print(f"Bypass: {bypass}")
        
        if bypass:
            result = True  # Los bypass siempre pasan
        else:
            result = is_glamping_related(message)
        
        print(f"Resultado: {result}")
        print(f"Esperado: {expected}")
        print(f"Status: {'PASS' if result == expected else 'FAIL'}")
        print("-" * 30)

if __name__ == "__main__":
    test_filter_function()