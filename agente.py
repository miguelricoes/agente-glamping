from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from rag_engine import qa_chain
import os

# Carga las variables de entorno
load_dotenv()
app = Flask(__name__)

# Credenciales de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")

# Cliente Twilio
try:
    twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, TWILIO_ACCOUNT_SID)
    print("Cliente Twilio cargado correctamente.")
except Exception as e:
    print("Error cargando Twilio:", e)
    twilio_client = None

# LLM de OpenAI
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

# Memoria conversacional
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input"
)

# Contexto inicial
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

# Endpoint para pruebas por JSON
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

# Webhook para Dialogflow
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    try:
        result = agent.invoke({"input": query_text})
        return jsonify({"fulfillmentText": result["output"]})
    except Exception:
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

# Webhook para Twilio WhatsApp
@app.route("/whatsapp_webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    print(f"[{from_number}] Mensaje recibido: '{incoming_msg}'")

    resp = MessagingResponse()
    agent_answer = "Lo siento, no pude responder en este momento."

    try:
        result = agent.invoke(
            {"input": incoming_msg, "chat_history": memory.load_memory_variables({}).get("chat_history", [])},
            config={"configurable": {"session_id": from_number}}
        )
        agent_answer = result.get("output", agent_answer)
    except Exception as e:
        print(f"Error procesando mensaje de WhatsApp: {e}")
        agent_answer = "Ocurrió un error técnico, por favor intenta más tarde."

    resp.message(agent_answer)
    print(f"[{from_number}] Respuesta: '{agent_answer}'")
    return str(resp)

@app.route("/")
def home():
    return "Servidor Flask con Agente RAG y WhatsApp conectado."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
