from flask import Flask, request, jsonify
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import requests

load_dotenv()
app = Flask(__name__)

# LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Ruta del servicio RAG
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://127.0.0.1:8000/query")

# Herramienta 1: Verificar disponibilidad
def check_availability(date: str) -> str:
    print(f" Verificando disponibilidad para: {date}")
    if date.lower() in ["sabado", "sábado", "domingo"]:
        return "Lo siento, no hay disponibilidad para ese día."
    return "¡Sí hay disponibilidad para esa fecha!"

# Herramienta 2: Precios
def obtener_precios(_: str) -> str:
    return (
        "Los precios del glamping Brillo de Luna son:\n"
        "- Estándar: 150.000 COP por noche\n"
        "- Premium: 250.000 COP por noche\n"
        "- Glamping de lujo: 350.000 COP por noche"
    )

# Herramienta 3: Llamar al sistema RAG
def call_rag_api(query: str) -> str:
    try:
        response = requests.post(RAG_SERVICE_URL, json={"query": query})
        response.raise_for_status()
        return response.json().get("answer", "No se pudo obtener información del sistema RAG.")
    except Exception as e:
        print(f" Error RAG: {e}")
        return "Lo siento, el sistema RAG no está disponible en este momento."

# Herramientas registradas
tools = [
    Tool(
        name="VerificarDisponibilidad",
        func=check_availability,
        description=(
            "Usa esta herramienta siempre que te pregunten si hay disponibilidad para un día específico, como sábado o domingo. "
            "No respondas tú mismo, siempre consulta esta herramienta."
        )
    ),
    Tool(
        name="PreciosGlamping",
        func=obtener_precios,
        description="Úsala cuando el usuario quiera saber precios, tarifas o cuánto cuesta hospedarse."
    ),
    Tool(
        name="InformacionGlamping",
        func=call_rag_api,
        description="Consulta al sistema RAG sobre temas generales del glamping como servicios, reglas o descripciones."
    )
]

# Memoria conversacional
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input"
)

# Instrucciones al agente (contexto inicial)
memory.chat_memory.add_user_message(
    "Actúa como un experto en glamping y responde siempre en español. "
    "Cuando pregunten por disponibilidad de fechas, usa 'VerificarDisponibilidad'. "
    "Cuando pregunten por precios, tarifas o cuánto cuesta, usa 'PreciosGlamping'. "
    "Cuando la pregunta sea general sobre el glamping, usa 'InformacionGlamping'."
)
memory.chat_memory.add_ai_message(
    "¡Entendido! Usaré las herramientas correctamente y responderé como experto en glamping en español."
)

# Agente
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# ENDPOINT /chat
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

# ENDPOINT webhook para Dialogflow
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    try:
        result = agent.invoke({"input": query_text})
        return jsonify({"fulfillmentText": result["output"]})
    except Exception:
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

# REST para disponibilidad
@app.route("/disponibilidad/<dia>", methods=["GET"])
def disponibilidad(dia):
    if dia.lower() in ["sábado", "domingo"]:
        return jsonify({"disponible": False, "mensaje": "Lo siento, no hay disponibilidad para ese día."})
    return jsonify({"disponible": True, "mensaje": "¡Sí hay disponibilidad para esa fecha!"})

# REST para precios
@app.route("/precios", methods=["GET"])
def precios():
    return jsonify({
        "estándar": "150.000 COP por noche",
        "premium": "250.000 COP por noche",
        "glamping_de_lujo": "350.000 COP por noche"
    })

@app.route("/")
def home():
    return "¡Servidor Flask del agente de Glamping funcionando!"

# Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
