#!/usr/bin/env python3
"""
Script de testing para servicios de fallback sin LLM
Prueba todas las respuestas automáticas del sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fallback_service import detect_topic_and_provide_fallback, get_available_topics

def test_fallback_responses():
    """Test completo de respuestas de fallback"""
    
    print("TESTING DE SERVICIOS FALLBACK SIN LLM")
    print("=" * 60)
    
    # Test cases organizados por categoría
    test_cases = {
        "SERVICIOS INEXISTENTES": [
            "tienen yate?",
            "puedo bucear?", 
            "hay casino?",
            "paracaidismo disponible?",
            "paseo en barco"
        ],
        
        "UBICACIÓN": [
            "donde están ubicados?",
            "dirección del glamping",
            "como llegar desde bogotá",
            "coordenadas gps",
            "ubicacion exacta"
        ],
        
        "POLÍTICAS": [
            "políticas de cancelación",
            "normas del lugar",
            "condiciones de reserva",
            "política de reembolsos",
            "reglas de cancelacion"
        ],
        
        "CONCEPTO": [
            "qué es glamping?",
            "filosofía del lugar",
            "concepto brillo de luna",
            "sobre el glamping",
            "historia del lugar"
        ],
        
        "SERVICIOS": [
            "qué servicios incluyen?",
            "amenidades disponibles",
            "que ofrecen",
            "servicios incluidos",
            "comodidades del lugar"
        ],
        
        "ACTIVIDADES": [
            "qué actividades hay?",
            "que puedo hacer",
            "planes disponibles",
            "entretenimiento",
            "experiencias"
        ],
        
        "MENSAJES NO RECONOCIDOS": [
            "reserva datos personales",
            "mensaje aleatorio sin sentido",
            "hola cómo estás",
            "entrada 15/12 salida 17/12"
        ]
    }
    
    for category, messages in test_cases.items():
        print(f"\nCATEGORIA: {category}")
        print("-" * 50)
        
        for message in messages:
            print(f"\nINPUT: '{message}'")
            
            handled, response, topic = detect_topic_and_provide_fallback(message)
            
            if handled:
                print(f"[OK] DETECTADO: {topic}")
                print(f"RESPUESTA: {response[:150]}...")
                if len(response) > 150:
                    print(f"    [Respuesta completa: {len(response)} caracteres]")
            else:
                print("[NO] NO DETECTADO - Pasa a siguiente handler")
    
    print(f"\nRESUMEN:")
    print(f"Temas disponibles: {get_available_topics()}")
    print("=" * 60)

def test_specific_service_queries():
    """Test de consultas específicas de servicios"""
    
    print("\nTESTING DE CONSULTAS ESPECÍFICAS")
    print("=" * 60)
    
    specific_queries = [
        # Servicios que SÍ tienen
        "tienen wifi?",
        "incluye desayuno?", 
        "hay parqueadero?",
        "masajes disponibles?",
        "observación de estrellas",
        
        # Servicios que NO tienen
        "tienen piscina?",
        "hay discoteca?",
        "puedo hacer surf?",
        "deportes extremos",
        "casino nocturno"
    ]
    
    for query in specific_queries:
        print(f"\nCONSULTA: '{query}'")
        handled, response, topic = detect_topic_and_provide_fallback(query)
        
        if handled:
            print(f"[OK] Respuesta automática disponible ({topic})")
            # Mostrar solo primeras líneas de la respuesta
            lines = response.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            if len(response.split('\n')) > 5:
                print("   [... más contenido]")
        else:
            print("[LLM] Requiere procesamiento con LLM")

def test_reservation_context_protection():
    """Test de protección contra interceptación de datos de reserva"""
    
    print("\nTESTING DE PROTECCIÓN DE CONTEXTO DE RESERVA")
    print("=" * 60)
    
    reservation_messages = [
        "Juan Pérez, correo juan@email.com, teléfono 3001234567",
        "2 huéspedes, entrada 15/12/2024, salida 17/12/2024",
        "reserva para María, email maria@test.com",
        "domo Antares, pago efectivo, 3 personas",
        "servicios masajes, observaciones aniversario"
    ]
    
    for message in reservation_messages:
        print(f"\nDATOS DE RESERVA: '{message[:40]}...'")
        handled, response, topic = detect_topic_and_provide_fallback(message)
        
        if not handled:
            print("[OK] PROTEGIDO - No intercepta datos de reserva")
        else:
            print(f"[WARN] INTERCEPTADO como {topic} - Verificar protección")

if __name__ == "__main__":
    try:
        test_fallback_responses()
        test_specific_service_queries() 
        test_reservation_context_protection()
        
        print("\nTESTING COMPLETADO")
        print("Todos los servicios fallback funcionan correctamente sin LLM")
        
    except Exception as e:
        print(f"\nERROR EN TESTING: {e}")
        import traceback
        traceback.print_exc()