from flask import Flask, request, jsonify
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os

from rag_engine import qa_chain

load_dotenv()
app = Flask(__name__)

# Twilio Client para envío de mensajes
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# LLM base
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Herramienta: sistema RAG
tools = [
    Tool(
        name="InformacionGlamping",
        func=lambda query: qa_chain.invoke({"query": query}),
        description="Úsalo para responder preguntas sobre precios, servicios, ubicación y horarios de Glamping Brillo de Luna.",
    )
]

# Memoria conversacional
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input"
)

# Mensajes iniciales
memory.chat_memory.add_user_message(
    "Actúa como un experto en glamping y responde siempre en español. "
    "Cuando te hagan cualquier pregunta sobre Glamping Brillo de Luna, usa la herramienta 'InformacionGlamping'."
)
memory.chat_memory.add_ai_message(
    "¡Entendido! Responderé como experto usando la herramienta adecuada."
)

# Agente LangChain
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# Función para enviar mensajes por WhatsApp
def enviar_mensaje_whatsapp(to_number: str, mensaje: str):
    try:
        message = twilio_client.messages.create(
            body=mensaje,
            from_=TWILIO_NUMBER,
            to=to_number
        )
        print(f"Mensaje enviado a {to_number}: SID {message.sid}")
    except Exception as e:
        print(f"Error al enviar mensaje de WhatsApp: {e}")

# Endpoint para recibir mensajes por WhatsApp (Twilio Webhook)
@app.route("/whatsapp_webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    print(f"[{from_number}] Mensaje recibido: '{incoming_msg}'")

    try:
        result = agent.invoke({"input": incoming_msg})
        agent_answer = result.get("output", "Lo siento, no pude obtener una respuesta.")
    except Exception as e:
        print(f"ERROR al invocar agente: {e}")
        agent_answer = "Disculpa, hubo un error procesando tu mensaje."

    # Responder a WhatsApp con TwiML
    resp = MessagingResponse()
    resp.message(agent_answer)
    print(f"[{from_number}] Respuesta enviada: '{agent_answer}'")
    return str(resp)

# Endpoint para enviar mensaje manual (POST JSON)
@app.route("/enviar_mensaje", methods=["POST"])
def enviar_manual():
    data = request.get_json()
    numero = data.get("numero")  # Ejemplo: whatsapp:+573001234567
    mensaje = data.get("mensaje")

    if not numero or not mensaje:
        return jsonify({"error": "Faltan los campos 'numero' o 'mensaje'"}), 400

    enviar_mensaje_whatsapp(numero, mensaje)
    return jsonify({"success": True, "mensaje_enviado": mensaje})

# Endpoint REST de prueba normal
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input")
    if not user_input:
        return jsonify({"error": "Falta el campo 'input'"}), 400
    try:
        result = agent.invoke({"input": user_input})
        return jsonify({"response": result["output"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para Dialogflow
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    try:
        result = agent.invoke({"input": query_text})
        return jsonify({"fulfillmentText": result["output"]})
    except Exception:
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

# Endpoint raíz
@app.route("/")
def home():
    return "Servidor Flask corriendo con agente RAG para Glamping Brillo de Luna."

# Lanzamiento del servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
