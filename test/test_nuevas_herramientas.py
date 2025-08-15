#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de las nuevas herramientas RAG del agente
"""

from rag_engine import qa_chains

def test_nuevas_herramientas():
    """Prueba las nuevas cadenas QA del sistema RAG"""
    print("=== Test de las Nuevas Herramientas RAG ===\n")
    
    # Test de cadenas disponibles
    print("Cadenas QA disponibles:")
    total_chains = len(qa_chains)
    working_chains = sum(1 for chain in qa_chains.values() if chain is not None)
    
    for chain_name, chain in qa_chains.items():
        status = "OK" if chain else "ERROR"
        print(f"  - {chain_name}: {status}")
    
    print(f"\nEstado: {working_chains}/{total_chains} cadenas funcionando\n")
    
    # Test de consultas para las nuevas herramientas
    nuevas_consultas = [
        ("domos_precios", "¿Cuánto cuesta el Domo Antares?"),
        ("que_es_brillo_luna", "¿Qué es Glamping Brillo de Luna?"),
        ("servicios_externos", "¿Qué actividades hay en Guatavita?"),
        ("sugerencias_movilidad_reducida", "¿Qué adaptaciones tienen para personas con movilidad reducida?"),
        ("politicas_privacidad", "¿Cómo manejan la privacidad de los datos?"),
        ("politicas_cancelacion", "¿Cuáles son las políticas de cancelación?")
    ]
    
    print("=== TESTING NUEVAS HERRAMIENTAS ===\n")
    
    for chain_name, query in nuevas_consultas:
        print(f"Probando {chain_name}: {query}")
        try:
            if chain_name in qa_chains and qa_chains[chain_name]:
                # Usar invoke en lugar de run
                result = qa_chains[chain_name].invoke({"query": query})
                
                # Extraer la respuesta del resultado
                if isinstance(result, dict):
                    response = result.get("result", result.get("output", str(result)))
                else:
                    response = str(result)
                    
                print(f"OK Respuesta: {response[:150]}...")
            else:
                print(f"ERROR Cadena no disponible: {chain_name}")
        except Exception as e:
            print(f"ERROR: {e}")
        print("-" * 60)

if __name__ == "__main__":
    test_nuevas_herramientas()