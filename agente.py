from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from rag_engine import qa_chain
import os

# Cargar variables de entorno
load_dotenv()
app = Flask(__name__)
user_memories = {}  # Diccionario global para memorias por número

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")

try:
    twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, TWILIO_ACCOUNT_SID)
    print("Cliente Twilio cargado correctamente.")
except Exception as e:
    print("Error cargando Twilio:", e)
    twilio_client = None

# LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Herramienta RAG
tools = [
    Tool(
        name="InformacionGlamping",
        func=lambda query: qa_chain.invoke({"query": query}),
        description="Úsalo para responder preguntas sobre precios, servicios, ubicación y horarios de Glamping Brillo de Luna."
    )
]

# --- Endpoint para WhatsApp Webhook ---
@app.route("/whatsapp_webhook", methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    print(f"[{from_number}] Mensaje recibido: '{incoming_msg}'")

    resp = MessagingResponse()
    agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."
    is_first_interaction = False

    # Memoria por usuario
    if from_number not in user_memories:
        user_memories[from_number] = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, input_key="input"
        )
        # Mensaje de bienvenida inicial
        user_memories[from_number].chat_memory.add_user_message(
            "Actúa como un experto en glamping y responde siempre en español. "
            "Cuando te hagan cualquier pregunta sobre Glamping Brillo de Luna, usa la herramienta 'InformacionGlamping'."
        )
        user_memories[from_number].chat_memory.add_ai_message(
            "¡Entendido! Responderé como experto usando la herramienta adecuada."
        )
        is_first_interaction = True

    memory = user_memories[from_number]

    # Bienvenida si es el primer mensaje o saludo
    if is_first_interaction or incoming_msg.lower() in ["hola", "buenas", "holi", "buenos días", "buenas tardes"]:
        resp.message("¡Hola! Soy tu asistente experto en Glamping Brillo de Luna 🏕️. "
                     "Puedo ayudarte con precios, disponibilidad, servicios y más. ¿En qué puedo ayudarte?")
        return str(resp)

    # Crear agente dinámico con la memoria del usuario
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
        print(f"ERROR procesando mensaje: {e}")
        agent_answer = "Disculpa, ocurrió un error al procesar tu mensaje."

    resp.message(agent_answer)
    print(f"[{from_number}] Respuesta: '{agent_answer}'")
    return str(resp)

# Endpoint de prueba POST JSON
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input")
    if not user_input:
        return jsonify({"error": "Falta el campo 'input'"}), 400
    try:
        result = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
            verbose=False
        ).invoke({"input": user_input})
        return jsonify({"response": result["output"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Webhook para Dialogflow
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    try:
        result = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
            verbose=False
        ).invoke({"input": query_text})
        return jsonify({"fulfillmentText": result["output"]})
    except Exception:
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

# Página principal
@app.route("/")
def home():
    return "Servidor Flask con Agente RAG y WhatsApp conectado."

# Iniciar servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
