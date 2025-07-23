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
from firebase_admin import credentials, firestore, auth

# Cargar variables de entorno
load_dotenv()
app = Flask(__name__)

# Directorio para almacenar los archivos de memoria de los usuarios
MEMORY_DIR = "user_memories_data"
os.makedirs(MEMORY_DIR, exist_ok=True)

# Diccionario global para memorias en caché (se carga desde disco si no está aquí)
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
    "INFORMACION_GLAMPING": "HX15408eed7b9138fa4884092d83d97328", # SID de 'submenu_informacion_glamping'
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
firebase_config = None

def initialize_firebase():
    """Initializes the Firebase Admin SDK and Firestore client."""
    global db, app_id, firebase_config

    app_id = os.getenv("APP_ID", "default-app-id")
    firebase_config_str = os.getenv("FIREBASE_CONFIG", "{}")
    
    try:
        firebase_config = json.loads(firebase_config_str)
    except json.JSONDecodeError:
        print("Error decoding FIREBASE_CONFIG. Using empty config.")
        firebase_config = {}

    try:
        if not firebase_admin._apps:
            if 'projectId' in firebase_config and firebase_config['projectId']:
                firebase_admin.initialize_app(options={'projectId': firebase_config['projectId']})
            else:
                print("Firebase project ID not found in config. Initializing without specific project ID.")
                firebase_admin.initialize_app()

        db = firestore.client()
        print("Firestore client initialized successfully.")

        initial_auth_token = os.getenv("INITIAL_AUTH_TOKEN")
        if initial_auth_token:
            try:
                decoded_token = auth.verify_id_token(initial_auth_token)
                print(f"Authenticated with custom token for user: {decoded_token['uid']}")
            except Exception as e:
                print(f"Error verifying custom token: {e}. Proceeding with service account credentials.")
        else:
            print("No initial auth token provided. Operating with service account credentials.")

    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        db = None

def save_reservation_to_firestore(user_phone_number, reservation_data):
    """Saves reservation data to Firestore."""
    if db is None:
        print("Firestore client not initialized. Cannot save reservation.")
        raise Exception("Firestore not available.")

    user_id = user_phone_number.replace("whatsapp:", "")
    collection_path = f"artifacts/{app_id}/users/{user_id}/reservations"
    
    try:
        doc_ref = db.collection(collection_path).document()
        doc_ref.set(reservation_data)
        print(f"Reserva guardada para {user_phone_number} en Firestore con ID: {doc_ref.id}")
        return True
    except Exception as e:
        print(f"Error al guardar reserva en Firestore: {e}")
        raise

# Initialize Firebase when the application starts
initialize_firebase()

# --- Funciones de Persistencia de Memoria ---

def _get_memory_file_path(user_id: str) -> str:
    """Retorna la ruta completa al archivo de memoria de un usuario."""
    return os.path.join(MEMORY_DIR, f"{user_id}.json")

def load_user_memory(user_id: str) -> ConversationBufferMemory:
    """
    Carga la memoria de un usuario desde un archivo JSON.
    Si no existe, inicializa una nueva memoria con mensajes de bienvenida.
    """
    memory_path = _get_memory_file_path(user_id)
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, input_key="input"
    )
    
    if os.path.exists(memory_path):
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                serialized_messages = json.load(f)
                messages = messages_from_dict(serialized_messages)
                memory.chat_memory.messages = messages
            print(f"Memoria cargada desde archivo para el usuario: {user_id}")
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON para el usuario {user_id}: {e}. Se iniciará con memoria vacía.")
        except Exception as e:
            print(f"Error inesperado al cargar memoria para el usuario {user_id}: {e}. Se iniciará con memoria vacía.")
    else:
        print(f"No se encontró archivo de memoria para el usuario {user_id}. Inicializando nueva memoria.")
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
        # Mensaje de bienvenida inicial simple
        memory.chat_memory.add_ai_message(
            "¡Hola! Soy María, tu asistente experta en Glamping Brillo de Luna. "
            "Estoy aquí para ayudarte con cualquier pregunta sobre nuestro glamping, domos, servicios, políticas y actividades. ¿En qué puedo asistirte hoy?"
        )
        save_user_memory(user_id, memory) 

    return memory

def save_user_memory(user_id: str, memory: ConversationBufferMemory):
    """
    Guarda la memoria actual de un usuario en un archivo JSON.
    """
    memory_path = _get_memory_file_path(user_id)
    try:
        serialized_messages = messages_to_dict(memory.chat_memory.messages)
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(serialized_messages, f, ensure_ascii=False, indent=4)
        print(f"Memoria guardada en archivo para el usuario: {user_id}")
    except Exception as e:
        print(f"Error al guardar memoria para el usuario {user_id}: {e}")

# --- Endpoint para WhatsApp Webhook ---
@app.route("/whatsapp_webhook", methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    button_payload = request.values.get('ButtonPayload')
    
    print(f"[{from_number}] Mensaje recibido: '{incoming_msg}' (Payload: '{button_payload}')")

    resp = MessagingResponse()
    agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."

    # Inicializar memoria y estado si es un nuevo usuario
    if from_number not in user_memories:
        user_memories[from_number] = load_user_memory(from_number)
    
    if from_number not in user_states:
        user_states[from_number] = {"first_message_sent": False, "current_flow": "none", "reserva_step": 0, "reserva_data": {}}
            
    memory = user_memories[from_number]
    user_state = user_states[from_number]

    # --- Lógica para manejar el flujo de los menús (prioridad sobre el agente) ---
    if button_payload:
        if button_payload == "Informacion":
            try:
                resp.message().media(f"whatsapp://content/{CONTENT_SIDS['INFORMACION_GLAMPING']}")
                print(f"[{from_number}] Enviando sub-menú de Información Glamping.")
            except Exception as e:
                print(f"Error al enviar plantilla SUBMENU_INFO_GLAMPING: {e}")
                resp.message("Lo siento, no pude cargar la información. Por favor, intenta de nuevo.")
            return str(resp)

        elif button_payload == "Servicios":
            try:
                # Usa la herramienta ServiciosIncluidosGlamping para responder sobre servicios
                result_from_tool = qa_chains["servicios_incluidos"].run("servicios incluidos en Glamping Brillo de Luna")
                agent_answer = result_from_tool
                print(f"[{from_number}] Respuesta de ServiciosIncluidosGlamping: {agent_answer}")
            except Exception as e:
                print(f"Error al ejecutar tool ServiciosIncluidosGlamping: {e}")
                agent_answer = "Disculpa, no pude obtener la información de servicios en este momento."
            
            resp.message(agent_answer)
            return str(resp)

        elif button_payload == "Reservas":
            user_state["current_flow"] = "reserva"
            user_state["reserva_step"] = 1
            user_state["reserva_data"] = {}
            resp.message("¡Excelente! Para tu reserva, por favor, dime el nombre completo de todas las personas que se hospedarán, separadas por comas.")
            return str(resp)

    # --- Lógica para detectar intención de reserva por texto ---
    if user_state["current_flow"] == "none" and ("reserva" in incoming_msg.lower() and ("quiero" in incoming_msg.lower() or "hacer" in incoming_msg.lower() or "reservar" in incoming_msg.lower())):
        user_state["current_flow"] = "reserva"
        user_state["reserva_step"] = 1
        user_state["reserva_data"] = {}
        resp.message("¡Claro! Iniciemos tu reserva. Por favor, dime el nombre completo de todas las personas que se hospedarán, separadas por comas.")
        return str(resp)

    # --- Lógica para el flujo de reserva ---
    if user_state["current_flow"] == "reserva":
        if user_state["reserva_step"] == 1: # Pidiendo nombres de huéspedes
            names_raw = incoming_msg
            names_list = [name.strip() for name in names_raw.replace(' y ', ',').replace(' e ', ',').replace(' & ', ',').split(',') if name.strip()]
            if not names_list:
                resp.message("Por favor, ingresa al menos un nombre. ¿Quiénes se hospedarán?")
                return str(resp)
            user_state["reserva_data"]["nombres_huespedes"] = names_list
            user_state["reserva_data"]["cantidad_huespedes"] = len(names_list)
            user_state["reserva_step"] = 2
            resp.message(f"Entendido. Se hospedarán {len(names_list)} personas. Ahora, ¿qué tipo de domo te gustaría reservar?")
            return str(resp)

        elif user_state["reserva_step"] == 2: # Pidiendo tipo de domo
            user_state["reserva_data"]["domo"] = incoming_msg
            user_state["reserva_step"] = 3
            resp.message("Perfecto. ¿Qué servicio adicional te gustaría elegir? (ej. cena romántica, desayuno especial, etc. o 'ninguno')")
            return str(resp)

        elif user_state["reserva_step"] == 3: # Pidiendo servicio adicional
            user_state["reserva_data"]["servicio_elegido"] = incoming_msg
            user_state["reserva_step"] = 4
            resp.message("Casi terminamos. ¿Cuál sería la fecha de entrada? (Formato DD/MM/AAAA)")
            return str(resp)

        elif user_state["reserva_step"] == 4: # Pidiendo fecha de entrada
            try:
                check_in_date = datetime.strptime(incoming_msg, "%d/%m/%Y").isoformat()
                user_state["reserva_data"]["fecha_entrada"] = check_in_date
                user_state["reserva_step"] = 5
                resp.message("Gracias. Ahora, ¿cuál sería la fecha de salida? (Formato DD/MM/AAAA)")
                return str(resp)
            except ValueError:
                resp.message("Formato de fecha inválido. Por favor, usa DD/MM/AAAA. ¿Cuál es la fecha de entrada?")
                return str(resp)

        elif user_state["reserva_step"] == 5: # Pidiendo fecha de salida
            try:
                check_out_date = datetime.strptime(incoming_msg, "%d/%m/%Y").isoformat()
                if "fecha_entrada" in user_state["reserva_data"]:
                    entrada_dt = datetime.fromisoformat(user_state["reserva_data"]["fecha_entrada"])
                    salida_dt = datetime.fromisoformat(check_out_date)
                    if salida_dt <= entrada_dt:
                        resp.message("La fecha de salida debe ser posterior a la fecha de entrada. Por favor, ingresa una fecha de salida válida.")
                        return str(resp)
                user_state["reserva_data"]["fecha_salida"] = check_out_date
                user_state["reserva_step"] = 6
                resp.message("Entendido. Por favor, ingresa un número de teléfono de contacto para la reserva.")
                return str(resp)
            except ValueError:
                resp.message("Formato de fecha inválido. Por favor, usa DD/MM/AAAA. ¿Cuál es la fecha de salida?")
                return str(resp)

        elif user_state["reserva_step"] == 6: # Pidiendo número de contacto
            user_state["reserva_data"]["numero_contacto"] = incoming_msg
            user_state["reserva_step"] = 7
            resp.message("Gracias. Ahora, por favor, ingresa tu dirección de correo electrónico.")
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
            else:
                resp.message("Reserva cancelada. ¿Hay algo más en lo que pueda ayudarte?")
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
            return str(resp)

    # --- Lógica para el primer saludo o mensajes de texto sin payload de botón ni flujo activo ---
    if not user_state["first_message_sent"] or incoming_msg.lower() in ["hola", "buenas", "holi", "buenos días", "buenas tardes"]:
        try:
            resp.message().media(f"whatsapp://content/{CONTENT_SIDS['MENU_PRINCIPAL']}")
            user_state["first_message_sent"] = True
            print(f"[{from_number}] Enviando menú principal.")
            return str(resp)
        except Exception as e:
            print(f"Error al enviar plantilla MENU_PRINCIPAL: {e}")
            resp.message("¡Hola! Soy tu asistente experto en Glamping Brillo de Luna 🏕️. "
                         "Lo siento, no pude cargar las opciones del menú. ¿En qué puedo ayudarte?")
            return str(resp)

    # Si no es un botón, no es el saludo inicial, y no está en un flujo de reserva, procesa con el agente conversacional
    try:
        custom_agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True
        )
        result = custom_agent.invoke(
            {"input": incoming_msg, "chat_history": memory.load_memory_variables({}).get("chat_history", [])},
            config={"configurable": {"session_id": from_number}}
        )
        agent_answer = result.get("output", agent_answer)
    except Exception as e:
        print(f"ERROR procesando mensaje con agente: {e}")
        agent_answer = "Disculpa, ocurrió un error al procesar tu mensaje con el agente."
    finally:
        save_user_memory(from_number, memory)

    resp.message(agent_answer)
    print(f"[{from_number}] Respuesta: '{agent_answer}'")
    return str(resp)

# --- Endpoint de prueba POST JSON ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input", "").strip()

    session_id = data.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"Nueva sesión generada: {session_id}")

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
        result = agent.invoke({"input": user_input})
        response_output = result["output"]
    except Exception as e:
        print(f"ERROR procesando mensaje para {session_id}: {e}")
        response_output = "Disculpa, ocurrió un error al procesar tu mensaje."
    
    memory.chat_memory.add_user_message(user_input)
    memory.chat_memory.add_ai_message(response_output)
    save_user_memory(session_id, memory)

    messages = memory.chat_memory.messages
    memory_serialized = messages_to_dict(messages)

    return jsonify({
        "session_id": session_id,
        "response": response_output,
        "memory": memory_serialized
    })

# --- Webhook para Dialogflow ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    session_id = data.get("session", "").split('/')[-1] # Obtener session_id de Dialogflow

    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"Nueva sesión generada para Dialogflow: {session_id}")

    if session_id not in user_memories:
        user_memories[session_id] = load_user_memory(session_id)
    
    memory = user_memories[session_id]

    try:
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=False
        )
        result = agent.invoke({"input": query_text})
        
        # Guardar la memoria después de la invocación del agente
        save_user_memory(session_id, memory)
        
        return jsonify({"fulfillmentText": result["output"]})
    except Exception as e:
        print(f"ERROR en webhook de Dialogflow para {session_id}: {e}")
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

# --- Página principal ---
@app.route("/")
def home():
    return "Servidor Flask con Agente RAG, WhatsApp y Firebase conectados. La memoria del agente ahora es persistente y soporta flujos conversacionales."

# --- Iniciar servidor ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)