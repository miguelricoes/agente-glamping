from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from langchain_openai import ChatOpenAI
from rag_engine import qa_chains # Asegúrate que este import sea correcto y apunte a tu rag_engine.py
import uuid
import os
import json
from datetime import datetime

# Firebase Admin SDK imports
import firebase_admin
from firebase_admin import credentials, firestore

# Cargar variables de entorno
load_dotenv()
app = Flask(__name__)

# Diccionario global para memorias en caché (se carga desde Firestore)
user_memories = {}
# Diccionario global para gestionar estados en flujos conversacionales (e.g., reservas)
user_states = {}

# --- Configuración de Twilio ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER") # Asegúrate de tener esta variable en .env

try:
    twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, account_sid=TWILIO_ACCOUNT_SID)
    print("Cliente Twilio cargado correctamente.")
except Exception as e:
    print(f"Error cargando Twilio: {e}")
    twilio_client = None

# Diccionario para los Content SIDs de tus plantillas de Twilio
# ¡Asegúrate de que estos SIDs coincidan exactamente con los de tu Twilio Console!
CONTENT_SIDS = {
    "MENU_PRINCIPAL": "HXe45a0e0ad8054578b1a55c017ed8a88c", # SID de 'menu_principal'
    "INFORMACION_GLAMPING": "HX15408eed7b9138fa484092d83d97328", # SID de 'submenu_informacion_glamping'
    # Agrega aquí los SIDs para el resto de tus menús cuando los crees:
    # "SUBMENU_DOMOS": "HX...",
    # "SUBMENU_RESERVAS": "HX...", # Si tienes una plantilla para iniciar reservas
    # "SUBMENU_PQRS": "HX...",
}

# --- Configuración del LLM ---
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# --- Herramientas para el Agente (RAG) ---
# Cada Tool está vinculada a una cadena QA específica de rag_engine.py
tools = [
    Tool(
        name="ConceptoGlamping",
        func=qa_chains["concepto_glamping"].run,
        description="Útil para responder preguntas generales sobre qué es Glamping Brillo de Luna, su concepto, filosofía, y la definición de glamping."
    ),
    Tool(
        name="UbicacionContactoGlamping",
        func=qa_chains["ubicacion_contacto"].run,
        description="Útil para responder preguntas sobre la ubicación del glamping, cómo llegar, su dirección, número de teléfono, correo electrónico, horario de atención y Registro Nacional de Turismo (RNT)."
    ),
    Tool(
        name="DomosInfoGlamping",
        func=qa_chains["domos_info"].run,
        description="Útil para responder preguntas sobre los tipos de domos disponibles (Antares, Polaris, Sirius, Centaury), sus descripciones, capacidades, características principales (ej. jacuzzi, malla catamarán, cocineta) y precios por noche."
    ),
    Tool(
        name="ServiciosIncluidosGlamping",
        func=qa_chains["servicios_incluidos"].run,
        description="Útil para responder preguntas sobre los servicios y comodidades que están INCLUIDOS en la tarifa base de cada domo, como desayuno, WiFi, parqueadero, fogata, zona BBQ, aseo, y comodidades de cama y baño."
    ),
    Tool(
        name="ActividadesServiciosAdicionalesGlamping",
        func=qa_chains["actividades_adicionales"].run,
        description="Útil para responder preguntas sobre servicios OPCIONALES con costo adicional (ej. decoraciones, masajes), actividades propias del glamping (ej. diseño de domos, jacuzzis específicos), y experiencias o actividades turísticas en Guatavita (ej. laguna, paseos en velero, caminatas, cabalgatas, jet ski, avistamiento de aves, casa al revés)."
    ),
    Tool(
        name="PoliticasGlamping",
        func=qa_chains["politicas_glamping"].run,
        description="Útil para responder preguntas sobre las políticas de reserva, cancelación, cambios de fecha, políticas de mascotas, reglas de la casa y medidas de seguridad y responsabilidad del Glamping Brillo de Luna."
    ),
    Tool(
        name="AccesibilidadMovilidadReducidaGlamping",
        func=qa_chains["accesibilidad"].run,
        description="Útil para responder preguntas sobre las medidas de seguridad y comodidad, adaptaciones para actividades (caminatas, paseos en velero, cabalgatas) y consejos para familias con personas con movilidad reducida en Glamping Brillo de Luna."
    )
]

# Global Firestore client and app_id
db = None
app_id = None

def initialize_firebase():
    """Initializes the Firebase Admin SDK and Firestore client using service account credentials."""
    global db, app_id

    app_id = os.getenv("APP_ID", "default-app-id")
    firebase_config_str = os.getenv("FIREBASE_CONFIG", "") # Usar cadena vacía por defecto

    if not firebase_config_str:
        print("FIREBASE_CONFIG variable de entorno no encontrada. Firebase no se inicializará completamente.")
        db = None
        return # Salir si no hay config para evitar errores

    try:
        # Cargar el JSON completo de la cuenta de servicio
        service_account_info = json.loads(firebase_config_str)
        
        # **CLAVE AQUÍ: Usar credentials.Certificate**
        cred = credentials.Certificate(service_account_info)
        
        if not firebase_admin._apps: # Verifica si ya está inicializado para evitar errores
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado correctamente con credenciales.")
        else:
            print("Firebase Admin SDK ya estaba inicializado.")

        db = firestore.client()
        print("Firestore client initialized successfully.")

    except json.JSONDecodeError as e:
        print(f"Error decodificando FIREBASE_CONFIG: {e}. Asegúrate de que es un JSON válido del archivo de clave de servicio.")
        db = None
    except Exception as e:
        print(f"Error general al inicializar Firebase: {e}")
        db = None

def save_reservation_to_firestore(user_phone_number, reservation_data):
    """Saves reservation data to Firestore."""
    if db is None:
        print("Firestore client not initialized. Cannot save reservation.")
        raise Exception("Firestore not available.")

    user_id = user_phone_number.replace("whatsapp:", "")
    # Es buena práctica tener una subcolección por usuario para sus reservas
    # Usamos artifacts/app_id para categorizar dentro de un proyecto Firebase
    collection_path = f"artifacts/{app_id}/users/{user_id}/reservations"
    
    try:
        doc_ref = db.collection(collection_path).document() # Crea un nuevo documento con ID automático
        reservation_data["timestamp"] = firestore.SERVER_TIMESTAMP # Añade un timestamp del servidor
        doc_ref.set(reservation_data)
        print(f"Reserva guardada para {user_phone_number} en Firestore con ID: {doc_ref.id}")
        return True
    except Exception as e:
        print(f"Error al guardar reserva en Firestore: {e}")
        raise # Re-lanzar la excepción para que el llamador pueda manejarla

# Initialize Firebase when the application starts
initialize_firebase()

# --- Funciones de Persistencia de Memoria con Firestore ---

def load_user_memory(user_id: str) -> ConversationBufferMemory:
    """
    Carga la memoria de un usuario desde Firestore.
    Si no existe, inicializa una nueva memoria con mensajes de bienvenida.
    """
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, input_key="input"
    )
    
    if db: # Asegúrate de que db esté inicializado
        user_doc_id = user_id.replace('whatsapp:', '') # Limpia el user_id para usarlo como ID de documento en Firestore
        # Ruta de la colección para memorias: artifacts/{app_id}/user_memories/{user_doc_id}
        doc_ref = db.collection(f"artifacts/{app_id}/user_memories").document(user_doc_id)
        doc = doc_ref.get()

        if doc.exists:
            try:
                serialized_messages = doc.to_dict().get("chat_history", [])
                messages = messages_from_dict(serialized_messages)
                memory.chat_memory.messages = messages
                print(f"Memoria cargada desde Firestore para el usuario: {user_id}")
            except Exception as e:
                print(f"Error al cargar memoria de Firestore para {user_id}: {e}. Se iniciará con memoria vacía.")
        else:
            print(f"No se encontró memoria en Firestore para {user_id}. Inicializando nueva.")
            # Prompt de sistema para memoria y conversación natural
            memory.chat_memory.add_user_message(
                "Hola, tu nombre es Maria. Eres una asistente experta en Glamping Brillo de Luna y "
                "tienes acceso a información detallada sobre el lugar, sus domos, sus servicios, políticas y actividades. "
                "También tienes una excelente memoria para recordar *todos los detalles* de nuestra conversación, "
                "incluso si no son directamente sobre el glamping o si son de índole personal o emocional. "
                "Responde siempre en español. "
                "Usa tus herramientas de información de Glamping para responder preguntas específicas sobre cualquier aspecto del lugar. "
                "Recuerda siempre el contexto de la conversación para responder de manera coherente y empática, "
                "incluso si la información no es directamente relevante para las herramientas o el Glamping. "
                "Si se te pregunta sobre algo que ya mencionaste, reitéralo de forma natural sin sonar repetitivo. "
                "Tu objetivo es ser útil, informativa y comprensiva en todo momento."
            )
            # El mensaje de bienvenida inicial se manejará en el webhook, no aquí.
            # save_user_memory(user_id, memory) # No guardar aquí, se guarda al final del webhook

    else:
        print("Firestore no está disponible. Inicializando memoria vacía (no persistente) para este ciclo.")
        # Aquí puedes dejar un mensaje de bienvenida por defecto si Firestore falla
        memory.chat_memory.add_user_message("Hola")
        memory.chat_memory.add_ai_message("¡Hola! Soy María. Parece que tengo problemas para acceder a mi memoria. ¿En qué puedo ayudarte hoy?")

    return memory

def save_user_memory(user_id: str, memory: ConversationBufferMemory):
    """
    Guarda la memoria actual de un usuario en Firestore.
    """
    if db: # Asegúrate de que db esté inicializado
        user_doc_id = user_id.replace('whatsapp:', '') # Limpia el user_id
        # Ruta de la colección para memorias: artifacts/{app_id}/user_memories/{user_doc_id}
        doc_ref = db.collection(f"artifacts/{app_id}/user_memories").document(user_doc_id)
        
        try:
            serialized_messages = messages_to_dict(memory.chat_memory.messages)
            memory_data = {"chat_history": serialized_messages}
            doc_ref.set(memory_data) # set() sobrescribe, update() fusiona
            print(f"Memoria guardada en Firestore para el usuario: {user_id}")
        except Exception as e:
            print(f"Error al guardar memoria en Firestore para el usuario {user_id}: {e}")
    else:
        print("Firestore no está disponible. Memoria NO guardada.")


# --- Endpoint para WhatsApp Webhook ---
@app.route("/whatsapp_webhook", methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    button_payload = request.values.get('ButtonPayload')
    
    print(f"DEBUG: [Webhook recibido] From: {from_number}, Mensaje: '{incoming_msg}', Payload: '{button_payload}'")

    resp = MessagingResponse()
    agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."

    # Cargar memoria del usuario o inicializarla.
    # user_memories es un caché local para esta ejecución del proceso, pero la fuente es Firestore.
    if from_number not in user_memories:
        user_memories[from_number] = load_user_memory(from_number)
    
    # Inicializar estado del usuario si es la primera vez en la sesión del servidor
    if from_number not in user_states:
        user_states[from_number] = {"first_message_sent_to_this_session": False, "current_flow": "none", "reserva_step": 0, "reserva_data": {}}
             
    memory = user_memories[from_number]
    user_state = user_states[from_number]

    # --- Lógica para el primer saludo o mensajes de texto que deben activar el menú principal ---
    # Esto se activa si es el primer mensaje para esta instancia del servidor O si es un saludo explícito.
    if not user_state["first_message_sent_to_this_session"] or incoming_msg.lower() in ["hola", "buenas", "holi", "buenos días", "buenas tardes", "menú", "menu principal"]:
        try:
            resp.message().media(f"whatsapp://content/{CONTENT_SIDS['MENU_PRINCIPAL']}")
            user_state["first_message_sent_to_this_session"] = True # Marca que ya se envió el menú para esta sesión
            print(f"[{from_number}] Enviando menú principal (primer saludo/saludo explícito).")
            # No guardamos memoria aquí porque el mensaje del usuario aún no ha sido procesado por el agente.
            return str(resp)
        except Exception as e:
            print(f"Error al enviar plantilla MENU_PRINCIPAL: {e}")
            resp.message("¡Hola! Soy tu asistente experto en Glamping Brillo de Luna 🏕️. "
                         "Lo siento, no pude cargar las opciones del menú. ¿En qué puedo ayudarte?")
            return str(resp)

    # --- Lógica para manejar el flujo de los menús por botón (prioridad sobre el agente) ---
    if button_payload:
        print(f"DEBUG: Botón presionado con payload: {button_payload}")
        if button_payload == "Informacion":
            try:
                resp.message().media(f"whatsapp://content/{CONTENT_SIDS['INFORMACION_GLAMPING']}")
                print(f"[{from_number}] Enviando sub-menú de Información Glamping (via plantilla).")
            except Exception as e:
                print(f"Error al enviar plantilla INFORMACION_GLAMPING: {e}")
                resp.message("Lo siento, no pude cargar la información. Por favor, intenta de nuevo.")
            return str(resp)

        elif button_payload == "Servicios":
            try:
                # Usa la herramienta ServiciosIncluidosGlamping para responder sobre servicios
                print(f"DEBUG: Procesando payload 'Servicios' con tool ServiciosIncluidosGlamping.")
                result_from_tool = qa_chains["servicios_incluidos"].run("servicios incluidos en Glamping Brillo de Luna")
                agent_answer = result_from_tool
                print(f"[{from_number}] Respuesta de ServiciosIncluidosGlamping: {agent_answer}")
            except Exception as e:
                print(f"Error al ejecutar tool ServiciosIncluidosGlamping: {e}")
                agent_answer = "Disculpa, no pude obtener la información de servicios en este momento."
            
            resp.message(agent_answer)
            save_user_memory(from_number, memory) # Guarda la memoria después de responder al botón
            return str(resp)

        elif button_payload == "Reservas":
            print(f"DEBUG: Iniciando flujo de reserva por botón.")
            user_state["current_flow"] = "reserva"
            user_state["reserva_step"] = 1
            user_state["reserva_data"] = {}
            resp.message("¡Excelente! Para tu reserva, por favor, dime el nombre completo de todas las personas que se hospedarán, separadas por comas.")
            save_user_memory(from_number, memory) # Guarda la memoria al iniciar el flujo
            return str(resp)

    # --- Lógica para detectar intención de reserva por texto (si no hay flujo activo) ---
    if user_state["current_flow"] == "none" and \
       ("reserva" in incoming_msg.lower() and ("quiero" in incoming_msg.lower() or "hacer" in incoming_msg.lower() or "reservar" in incoming_msg.lower())):
        print(f"DEBUG: Iniciando flujo de reserva por texto: '{incoming_msg}'")
        user_state["current_flow"] = "reserva"
        user_state["reserva_step"] = 1
        user_state["reserva_data"] = {}
        resp.message("¡Claro! Iniciemos tu reserva. Por favor, dime el nombre completo de todas las personas que se hospedarán, separadas por comas.")
        save_user_memory(from_number, memory) # Guarda la memoria al iniciar el flujo
        return str(resp)

    # --- Flujo de reserva paso a paso ---
    if user_state["current_flow"] == "reserva":
        print(f"DEBUG: Continuando flujo de reserva, paso: {user_state['reserva_step']}")
        # ... (Tu lógica de pasos de reserva existente, con save_user_memory en cada paso) ...
        if user_state["reserva_step"] == 1: # Pidiendo nombres de huéspedes
            names_raw = incoming_msg
            names_list = [name.strip() for name in names_raw.replace(' y ', ',').replace(' e ', ',').replace(' & ', ',').split(',') if name.strip()]
            if not names_list:
                resp.message("Por favor, ingresa al menos un nombre. ¿Quiénes se hospedarán?")
                save_user_memory(from_number, memory)
                return str(resp)
            user_state["reserva_data"]["nombres_huespedes"] = names_list
            user_state["reserva_data"]["cantidad_huespedes"] = len(names_list)
            user_state["reserva_step"] = 2
            resp.message(f"Entendido. Se hospedarán {len(names_list)} personas. Ahora, ¿qué tipo de domo te gustaría reservar?")
            save_user_memory(from_number, memory)
            return str(resp)

        elif user_state["reserva_step"] == 2: # Pidiendo tipo de domo
            user_state["reserva_data"]["domo"] = incoming_msg
            user_state["reserva_step"] = 3
            resp.message("Perfecto. ¿Qué servicio adicional te gustaría elegir? (ej. cena romántica, desayuno especial, etc. o 'ninguno')")
            save_user_memory(from_number, memory)
            return str(resp)

        elif user_state["reserva_step"] == 3: # Pidiendo servicio adicional
            user_state["reserva_data"]["servicio_elegido"] = incoming_msg
            user_state["reserva_step"] = 4
            resp.message("Casi terminamos. ¿Cuál sería la fecha de entrada? (Formato DD/MM/AAAA)")
            save_user_memory(from_number, memory)
            return str(resp)

        elif user_state["reserva_step"] == 4: # Pidiendo fecha de entrada
            try:
                check_in_date = datetime.strptime(incoming_msg, "%d/%m/%Y").isoformat()
                user_state["reserva_data"]["fecha_entrada"] = check_in_date
                user_state["reserva_step"] = 5
                resp.message("Gracias. Ahora, ¿cuál sería la fecha de salida? (Formato DD/MM/AAAA)")
                save_user_memory(from_number, memory)
                return str(resp)
            except ValueError:
                resp.message("Formato de fecha inválido. Por favor, usa DD/MM/AAAA. ¿Cuál es la fecha de entrada?")
                save_user_memory(from_number, memory)
                return str(resp)

        elif user_state["reserva_step"] == 5: # Pidiendo fecha de salida
            try:
                check_out_date = datetime.strptime(incoming_msg, "%d/%m/%Y").isoformat()
                if "fecha_entrada" in user_state["reserva_data"]:
                    entrada_dt = datetime.fromisoformat(user_state["reserva_data"]["fecha_entrada"])
                    salida_dt = datetime.fromisoformat(check_out_date)
                    if salida_dt <= entrada_dt:
                        resp.message("La fecha de salida debe ser posterior a la fecha de entrada. Por favor, ingresa una fecha de salida válida.")
                        save_user_memory(from_number, memory)
                        return str(resp)
                user_state["reserva_data"]["fecha_salida"] = check_out_date
                user_state["reserva_step"] = 6
                resp.message("Entendido. Por favor, ingresa un número de teléfono de contacto para la reserva.")
                save_user_memory(from_number, memory)
                return str(resp)
            except ValueError:
                resp.message("Formato de fecha inválido. Por favor, usa DD/MM/AAAA. ¿Cuál es la fecha de salida?")
                save_user_memory(from_number, memory)
                return str(resp)

        elif user_state["reserva_step"] == 6: # Pidiendo número de contacto
            user_state["reserva_data"]["numero_contacto"] = incoming_msg
            user_state["reserva_step"] = 7
            resp.message("Gracias. Ahora, por favor, ingresa tu dirección de correo electrónico.")
            save_user_memory(from_number, memory)
            return str(resp)

        elif user_state["reserva_step"] == 7: # Pidiendo email
            user_state["reserva_data"]["email_contacto"] = incoming_msg
            user_state["reserva_step"] = 8
            
            reserva_info = user_state["reserva_data"]
            confirmation_msg = (
                "¡Listo! Aquí está el resumen de tu reserva:\n"
                f"Huéspedes: {', '.join(reserva_info['nombres_huespedes'])} ({reserva_info['cantidad_huespedes']} personas)\n"
                f"Domo: {reserva_info['domo']}\n"
                f"Servicio: {reserva_info['servicio_elegido']}\n"
                f"Entrada: {datetime.fromisoformat(reserva_info['fecha_entrada']).strftime('%d/%m/%Y')}\n"
                f"Salida: {datetime.fromisoformat(reserva_info['fecha_salida']).strftime('%d/%m/%Y')}\n"
                f"Teléfono: {reserva_info['numero_contacto']}\n"
                f"Email: {reserva_info['email_contacto']}\n\n"
                "¿Confirmas esta reserva? (Sí/No)"
            )
            resp.message(confirmation_msg)
            save_user_memory(from_number, memory)
            return str(resp)

        elif user_state["reserva_step"] == 8: # Confirmar reserva
            if incoming_msg.lower() in ["si", "sí"]:
                try:
                    reservation_data = user_state["reserva_data"]
                    save_reservation_to_firestore(from_number, reservation_data)
                    resp.message("¡Reserva confirmada y guardada! Nos pondremos en contacto contigo pronto para los detalles finales. ¡Gracias por elegir Glamping Brillo de Luna!")
                except Exception as e:
                    print(f"Error al guardar reserva en Firestore: {e}")
                    resp.message("Lo siento, hubo un error al guardar tu reserva. Por favor, intenta de nuevo más tarde.")
                finally:
                    user_state["current_flow"] = "none"
                    user_state["reserva_step"] = 0
                    user_state["reserva_data"] = {}
                    save_user_memory(from_number, memory) # Guardar memoria después de finalizar el flujo
            else:
                resp.message("Reserva cancelada. ¿Hay algo más en lo que pueda ayudarte?")
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
                save_user_memory(from_number, memory) # Guardar memoria después de finalizar el flujo
            return str(resp)
    
    # --- Procesamiento con el Agente Conversacional (si no hay flujo activo) ---
    # Si no está en un flujo de reserva, el mensaje se pasa al agente conversacional.
    print(f"DEBUG: Procesando mensaje con el agente RAG: '{incoming_msg}'")
    try:
        custom_agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True
        )
        # Asegúrate de que 'chat_history' se pasa correctamente al invocar el agente
        result = custom_agent.invoke(
            {"input": incoming_msg, "chat_history": memory.load_memory_variables({}).get("chat_history", [])},
            config={"configurable": {"session_id": from_number}}
        )
        agent_answer = result.get("output", agent_answer)
    except Exception as e:
        print(f"ERROR procesando mensaje con agente: {e}")
        agent_answer = "Disculpa, ocurrió un error al procesar tu mensaje con el agente."
    finally:
        # Guarda la memoria después de que el agente la actualice
        save_user_memory(from_number, memory)

    resp.message(agent_answer)
    print(f"[{from_number}] Respuesta final del agente: '{agent_answer}'")
    return str(resp)

# --- Endpoint de prueba POST JSON (para probar el agente directamente) ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input", "").strip()

    session_id = data.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"Nueva sesión generada para /chat: {session_id}")

    if not user_input:
        return jsonify({"error": "Falta el campo 'input'"}), 400

    if session_id not in user_memories:
        user_memories[session_id] = load_user_memory(session_id)
    
    memory = user_memories[session_id]

    response_output = "Lo siento, no pude procesar tu solicitud en este momento."
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )
    try:
        result = agent.invoke({"input": user_input, "chat_history": memory.load_memory_variables({}).get("chat_history", [])})
        response_output = result["output"]
    except Exception as e:
        print(f"ERROR procesando mensaje para {session_id} en /chat: {e}")
        response_output = "Disculpa, ocurrió un error al procesar tu mensaje."
    
    # La memoria ya se actualiza dentro de la invocación del agente, solo necesitamos guardarla.
    save_user_memory(session_id, memory)

    messages = memory.chat_memory.messages
    memory_serialized = messages_to_dict(messages)

    return jsonify({
        "session_id": session_id,
        "response": response_output,
        "memory": memory_serialized
    })

# --- Página principal (para verificar que el servidor está corriendo) ---
@app.route("/")
def home():
    return "Servidor Flask con Agente RAG, WhatsApp y Firebase conectados. La memoria del agente ahora es persistente con Firestore."

# --- Iniciar servidor ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)