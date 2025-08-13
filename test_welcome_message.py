# test_welcome_message.py
import os
from dotenv import load_dotenv
load_dotenv()

# Test del mensaje de bienvenida
def test_welcome_message():
    from agente import _create_fresh_memory
    
    print("Testing nuevo mensaje de bienvenida...")
    
    # Crear memoria nueva para usuario de prueba
    memory = _create_fresh_memory('test_welcome_user')
    
    # Verificar que el mensaje contiene las palabras clave esperadas
    if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
        messages = memory.chat_memory.messages
        
        # Buscar el mensaje de María
        maria_message = None
        for message in messages:
            if hasattr(message, 'content') and 'María' in message.content:
                maria_message = message.content
                break
        
        if maria_message:
            print("✅ Mensaje de María encontrado")
            
            # Verificar elementos clave del mensaje
            required_elements = [
                "Mi nombre es María",
                "asistente del Glamping Brillo de Luna",
                "Es un placer saludarte",
                "domos geodésicos", 
                "servicios exclusivos",
                "experiencias únicas",
                "estadía inolvidable",
                "¿En qué puedo ayudarte hoy?"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in maria_message:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ Todos los elementos requeridos están presentes")
                print("\n=== MENSAJE DE BIENVENIDA COMPLETO ===")
                print(maria_message)
                print("=" * 50)
                return True
            else:
                print(f"❌ Elementos faltantes: {missing_elements}")
                return False
        else:
            print("❌ No se encontró mensaje de María")
            return False
    else:
        print("❌ No se pudieron acceder a los mensajes de memoria")
        return False

if __name__ == "__main__":
    success = test_welcome_message()
    if success:
        print("\n🎉 Test EXITOSO: El mensaje de bienvenida está configurado correctamente")
    else:
        print("\n💥 Test FALLIDO: Hay problemas con el mensaje de bienvenida")