#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de debugging del agente conversacional
"""

from agente import tools, llm, initialize_agent_safe, _create_fresh_memory

def test_agent_debug():
    """Prueba debug del agente para ver qué está pasando"""
    print("=== Debug del Agente Conversacional ===\n")
    
    # Crear memoria
    print("1. Creando memoria...")
    memory = _create_fresh_memory("debug-user")
    print(f"Memoria creada: {type(memory)}")
    
    # Inicializar agente
    print("\n2. Inicializando agente...")
    success, agent, error = initialize_agent_safe(tools, memory, max_retries=1)
    print(f"Inicialización exitosa: {success}")
    print(f"Tipo de agente: {type(agent) if success else 'N/A'}")
    if not success:
        print(f"Error: {error}")
        return
    
    # Probar herramientas directamente
    print(f"\n3. Herramientas disponibles: {len(tools)}")
    for i, tool in enumerate(tools):
        print(f"   {i+1}. {tool.name}: {tool.description[:60]}...")
    
    # Test directo de herramienta
    print("\n4. Probando herramienta directamente...")
    sugerencias_tool = None
    for tool in tools:
        if "SugerenciasMovilidadReducida" in tool.name:
            sugerencias_tool = tool
            break
    
    if sugerencias_tool:
        try:
            direct_result = sugerencias_tool.func("Mi amigo está en silla de ruedas")
            print(f"Resultado directo: {direct_result[:200]}...")
        except Exception as e:
            print(f"Error herramienta directa: {e}")
    
    # Test del agente
    print("\n5. Probando agente conversacional...")
    test_input = "Mi amigo está en silla de ruedas, ¿es recomendable llevarlo al glamping?"
    
    try:
        # Diferentes métodos según el tipo de agente
        if hasattr(agent, 'invoke'):
            result = agent.invoke({"input": test_input})
        elif hasattr(agent, 'run'):
            result = agent.run(test_input)
        elif callable(agent):
            result = agent(test_input)
        else:
            print(f"Tipo de agente desconocido: {type(agent)}")
            print(f"Métodos disponibles: {[method for method in dir(agent) if not method.startswith('_')]}")
            return
            
        print(f"Resultado del agente: {result}")
        
    except Exception as e:
        print(f"Error ejecutando agente: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_debug()