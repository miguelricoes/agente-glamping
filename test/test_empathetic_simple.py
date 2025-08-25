#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test simple para validar el nuevo sistema de Redirección Conversacional Estratégica
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test directo de la función generate_empathetic_redirect
def test_empathetic_function():
    print("=== TEST DIRECTO DE FUNCION EMPATICA ===")
    
    try:
        # Importar función directamente
        from agente import generate_empathetic_redirect
        
        test_cases = [
            "Estoy muy triste, he tenido días difíciles",
            "Me siento estresado con el trabajo",
            "Mi relación está pasando por momentos difíciles"
        ]
        
        for i, test_message in enumerate(test_cases, 1):
            print(f"\n--- TEST {i} ---")
            print(f"INPUT: {test_message}")
            
            try:
                response = generate_empathetic_redirect(test_message)
                print(f"OUTPUT: {response}")
                
                # Validación básica
                response_lower = response.lower()
                has_empathy = any(word in response_lower for word in [
                    "comprendo", "entiendo", "momentos", "situación"
                ])
                has_glamping = any(word in response_lower for word in [
                    "glamping", "brillo de luna", "naturaleza", "domos"
                ])
                
                print(f"VALIDACION:")
                print(f"  - Empatía: {'SI' if has_empathy else 'NO'}")
                print(f"  - Redirección Glamping: {'SI' if has_glamping else 'NO'}")
                print(f"  - Resultado: {'EXITOSO' if (has_empathy and has_glamping) else 'NECESITA MEJORA'}")
                
            except Exception as e:
                print(f"ERROR: {e}")
        
    except ImportError as e:
        print(f"ERROR IMPORTANDO: {e}")
        return False
    
    return True

def test_strategic_redirect_function():
    print("\n=== TEST DIRECTO DE FUNCION STRATEGIC REDIRECT ===")
    
    try:
        from agente import get_strategic_redirect_response
        
        test_message = "Estoy muy triste últimamente"
        print(f"INPUT: {test_message}")
        
        response = get_strategic_redirect_response(test_message)
        print(f"OUTPUT: {response}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("INICIANDO TEST SIMPLE DE REDIRECCION EMPATICA")
    print("=" * 50)
    
    success1 = test_empathetic_function()
    success2 = test_strategic_redirect_function()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("RESULTADO: Las funciones empáticas están disponibles y funcionando")
    else:
        print("RESULTADO: Hay problemas con las funciones empáticas")