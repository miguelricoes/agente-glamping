#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test simple del sistema RAG para verificar que funciona correctamente
"""

from rag_engine import qa_chains

def test_rag_chains():
    """Prueba las cadenas QA del sistema RAG"""
    print("=== Test del Sistema RAG ===\n")
    
    # Test de cadenas disponibles
    print("Cadenas QA disponibles:")
    for chain_name, chain in qa_chains.items():
        status = "OK" if chain else "ERROR"
        print(f"  - {chain_name}: {status}")
    print()
    
    # Test de consultas
    test_queries = [
        ("concepto_glamping", "¿Qué es el glamping?"),
        ("domos_info", "¿Qué tipos de domos tienen?"),
        ("ubicacion_contacto", "¿Dónde están ubicados?"),
        ("servicios_incluidos", "¿Qué servicios incluyen?"),
        ("politicas_glamping", "¿Cuáles son las políticas?")
    ]
    
    for chain_name, query in test_queries:
        print(f"Probando {chain_name}: {query}")
        try:
            if chain_name in qa_chains and qa_chains[chain_name]:
                response = qa_chains[chain_name].run(query)
                print(f"OK Respuesta: {response[:100]}...")
            else:
                print(f"ERROR Cadena no disponible: {chain_name}")
        except Exception as e:
            print(f"ERROR Error: {e}")
        print()

if __name__ == "__main__":
    test_rag_chains()