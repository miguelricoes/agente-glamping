#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test para verificar que la corrección del agente funciona
"""

from agente import tools, llm, initialize_agent_safe, _create_fresh_memory

def test_fix():
    """Verificar que el agente responda correctamente"""
    print("=== Verificación de la Corrección ===\n")
    
    # Crear memoria con el nuevo prompt
    memory = _create_fresh_memory("test-fix-user")
    
    # Inicializar agente
    success, agent, error = initialize_agent_safe(tools, memory, max_retries=1)
    if not success:
        print(f"ERROR: {error}")
        return
    
    # Test con consulta de silla de ruedas
    print("Probando consulta: 'Quiero llevar a una amiga en muletas. ¿Alguna recomendación?'")
    
    try:
        if hasattr(agent, 'invoke'):
            result = agent.invoke({"input": "Quiero llevar a una amiga en muletas. ¿Alguna recomendación?"})
            if isinstance(result, dict):
                response = result.get('output', result.get('result', str(result)))
            else:
                response = str(result)
        else:
            response = agent.run(input="Quiero llevar a una amiga en muletas. ¿Alguna recomendación?")
        
        print(f"\nRespuesta del agente:\n{response}\n")
        
        # Verificar si la respuesta contiene información específica
        keywords = ['rutas alternativas', 'adaptaciones', 'sillas adaptadas', 'personal capacitado', 'superficie', 'informar con anticipación']
        found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
        
        if found_keywords:
            print(f"✅ CORRECCIÓN EXITOSA - La respuesta incluye información específica:")
            for kw in found_keywords:
                print(f"   - {kw}")
        else:
            print("❌ PROBLEMA PERSISTE - La respuesta sigue siendo genérica")
            
        # Verificar si sigue haciendo preguntas de seguimiento
        if "¿" in response and ("costo" in response.lower() or "adicional" in response.lower()):
            print("❌ PROBLEMA PERSISTE - Sigue haciendo preguntas de seguimiento")
        else:
            print("✅ CORRECCIÓN EXITOSA - No hace preguntas de seguimiento innecesarias")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fix()