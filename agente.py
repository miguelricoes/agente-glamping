from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from langchain_openai import ChatOpenAI
from rag_engine import qa_chains
import uuid
import os
import json

# --- Configuración inicial ---

load_dotenv()
app = Flask(__name__)

MEMORY_DIR = "user_memories_data"
os.makedirs(MEMORY_DIR, exist_ok=True)

user_memories = {}
user_agents = {}

# --- Configuración de Twilio ---

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")

try:
    twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, account_sid=TWILIO_ACCOUNT_SID)
    print("Cliente Twilio cargado correctamente.")
except Exception as e:
    print("Error cargando Twilio:", e)
    twilio_client = None

# --- Configuración del LLM ---

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# --- Herramientas RAG para el Agente ---

tools = [
    Tool(
        name="ConceptoGlamping",
        func=qa_chains["concepto_glamping"].run,
        description="Útil para responder preguntas generales sobre el concepto del glamping."
    ),
    Tool(
        name="UbicacionContactoGlamping",
        func=qa_chains["ubicacion_contacto"].run,
        description="Información sobre ubicación, contacto, RNT, etc."
    ),
    Tool(
        name="DomosInfoGlamping",
        func=qa_chains["domos_info"].run,
        description="Tipos de domos, precios y características."
    ),
    Tool(
        name="ServiciosIncluidosGlamping",
        func=qa_chains["servicios_incluidos"].run,
        description="Servicios incluidos como desayuno, WiFi, parqueadero, etc."
    ),
    Tool(
        name="ActividadesServiciosAdicionalesGlamping",
        func=qa_chains["actividades_adicionales"].run,
        description="Servicios adicionales y actividades como masajes, paseos, etc."
    ),
    Tool(
        name="PoliticasGlamping",
        func=qa_chains["politicas_glamping"].run,
        description="Políticas de cancelación, mascotas, normas del lugar."
    ),
    Tool(
        name="AccesibilidadMovilidadReducidaGlamping",
        func=qa_chains["accesibilidad"].run,
        description="Adaptaciones y recomendaciones para personas con movilidad reducida."
    )
]

# --- Manejo de Memoria ---

def _get_memory_file_path(user_id: str) -> str:
    return os.path.join(MEMORY_DIR, f"{user_id}.json")

def load_user_memory(user_id: str) -> ConversationBufferMemory:
    memory_path = _get_memory_file_path(user_id)
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, input_key="input"
    )

    if os.path.exists(memory_path):
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                serialized_messages = json.load(f)
                memory.chat_memory.messages = messages_from_dict(serialized_messages)
            print(f"Memoria cargada desde archivo para el usuario: {user_id}")
        except Exception as e:
            print(f"Error al cargar memoria para el usuario {user_id}: {e}")
    else:
        print(f"No se encontró archivo de memoria para el usuario {user_id}. Inicializando nueva memoria.")
        memory.chat_memory.add_user_message(
            "Hola, tu nombre es Maria. Eres una asistente experta en Glamping Brillo de Luna..."
        )
        memory.chat_memory.add_ai_message(
            "¡Hola! Soy María, tu asistente experta en Glamping Brillo de Luna..."
        )
        save_user_memory(user_id, memory)

    return memory

def save_user_memory(user_id: str, memory: ConversationBufferMemory):
    memory_path = _get_memory_file_path(user_id)
    try:
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(messages_to_dict(memory.chat_memory.messages), f, ensure_ascii=False, indent=4)
        print(f"Memoria guardada para el usuario: {user_id}")
    except Exception as e:
        print(f"Error al guardar memoria para el usuario {user_id}: {e}")

# --- Webhook WhatsApp ---

@app.route("/whatsapp_webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    print(f"[{from_number}] Mensaje recibido: '{incoming_msg}'")

    resp = MessagingResponse()
    agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."

    if from_number not in user_memories:
        user_memories[from_number] = load_user_memory(from_number)

    memory = user_memories[from_number]

    try:
        custom_agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True
        )
        result = custom_agent.invoke({"input": incoming_msg})
        agent_answer = result.get("output", agent_answer)
    except Exception as e:
        print(f"ERROR procesando mensaje para {from_number}: {e}")
        agent_answer = "Disculpa, ocurrió un error al procesar tu mensaje."
    finally:
        save_user_memory(from_number, memory)

    resp.message(agent_answer)
    print(f"[{from_number}] Respuesta: '{agent_answer}'")
    return str(resp)

# --- Endpoint de prueba desde frontend o Postman ---

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))

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

    return jsonify({
        "session_id": session_id,
        "response": response_output,
        "memory": messages_to_dict(memory.chat_memory.messages)
    })

# --- Webhook para Dialogflow ---

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")

    try:
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
            verbose=False
        )
        result = agent.invoke({"input": query_text})
        return jsonify({"fulfillmentText": result["output"]})
    except Exception as e:
        print(f"ERROR en webhook de Dialogflow: {e}")
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

# --- Página de inicio ---

@app.route("/")
def home():
    return "Servidor Flask con Agente RAG y WhatsApp conectado. La memoria del agente ahora es persistente."

# --- Iniciar servidor ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
