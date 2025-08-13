# test_whatsapp_greeting.py
import os
from dotenv import load_dotenv
load_dotenv()

def test_whatsapp_greeting():
    """Test del mensaje de bienvenida en WhatsApp webhook"""
    
    print("=== TEST DE MENSAJE DE BIENVENIDA WHATSAPP ===")
    
    # Importar después de cargar env
    from agente import app
    
    # Simular webhook de WhatsApp con "Hola"
    with app.test_client() as client:
        response = client.post('/whatsapp_webhook', data={
            'Body': 'Hola',
            'From': 'whatsapp:+573001234567'  # Número de prueba
        })
        
        if response.status_code == 200:
            response_text = response.get_data(as_text=True)
            print(f"Respuesta del webhook (código {response.status_code}):")
            print("=" * 60)
            print(response_text)
            print("=" * 60)
            
            # Verificar que la respuesta contiene el mensaje de María
            if "Mi nombre es María" in response_text and "Glamping Brillo de Luna" in response_text:
                print("✅ ÉXITO: El mensaje de bienvenida de María se está enviando correctamente")
                return True
            else:
                print("❌ FALLO: La respuesta no contiene el mensaje de bienvenida completo")
                return False
        else:
            print(f"❌ ERROR: El webhook falló con código {response.status_code}")
            print(response.get_data(as_text=True))
            return False

def test_chat_api_greeting():
    """Test del mensaje de bienvenida en endpoint /chat"""
    
    print("\n=== TEST DE MENSAJE DE BIENVENIDA CHAT API ===")
    
    from agente import app
    
    # Simular API call con "Hola"
    with app.test_client() as client:
        response = client.post('/chat', 
            json={'input': 'Hola', 'session_id': 'test_chat_session'},
            content_type='application/json')
        
        if response.status_code == 200:
            data = response.get_json()
            response_msg = data.get('response', '')
            
            print(f"Respuesta del chat API (código {response.status_code}):")
            print("=" * 60)
            print(response_msg)
            print("=" * 60)
            
            # Verificar que la respuesta contiene el mensaje de María
            if "Mi nombre es María" in response_msg and "Glamping Brillo de Luna" in response_msg:
                print("✅ ÉXITO: El mensaje de bienvenida de María funciona en chat API")
                return True
            else:
                print("❌ FALLO: La respuesta del chat API no contiene el mensaje completo")
                return False
        else:
            print(f"❌ ERROR: El chat API falló con código {response.status_code}")
            print(response.get_data(as_text=True))
            return False

if __name__ == "__main__":
    print("Iniciando tests del mensaje de bienvenida...")
    
    # Test 1: WhatsApp webhook
    whatsapp_success = test_whatsapp_greeting()
    
    # Test 2: Chat API
    chat_success = test_chat_api_greeting()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS:")
    print(f"WhatsApp Webhook: {'✅ PASÓ' if whatsapp_success else '❌ FALLÓ'}")
    print(f"Chat API: {'✅ PASÓ' if chat_success else '❌ FALLÓ'}")
    
    if whatsapp_success and chat_success:
        print("\n🎉 TODOS LOS TESTS PASARON!")
        print("El mensaje de bienvenida de María funciona correctamente.")
    else:
        print("\n💥 ALGUNOS TESTS FALLARON")
        print("Revisar la configuración del mensaje de bienvenida.")