from flask import Flask, request, jsonify
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import requests

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configurar el modelo LLM (OpenAI)
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

RAG_SERVICE_URL = os.getenv("http://127.0.0.1:8000")

# Función para verificar disponibilidad
def check_availability(date: str) -> str:
    if date.lower() in ["sábado", "domingo"]:
        return "Lo siento, no hay disponibilidad para ese día."
    else:
        return "¡Sí hay disponibilidad para esa fecha!"

# Función para herramienta que llama a la API del RAG
def call_rag_api(query: str) -> str:
    try: 
        response=requests.post(RAG_SERVICE_URL, json={"query": query})
        response.raise_for_status()
        rag_response=response.json()
        return rag_response.get("answer", "No se pudo obtener informacion del sistema RAG")
    except requests.exceptions.RequestException as e:
        print(f"Error al llamar a la API del RAG: {e}")
        return "lo siento, el sistema de informacion RAG no esta disponible en este momento"
    
# Registrar herramienta personalizada
tools = [
    Tool(
        name="VerificarDisponibilidad",
        func=check_availability,
        description="Verifica disponibilidad en una fecha (como 'sábado', 'lunes')"
    ),

    Tool(
        name="InformacionGlamping",
        func=call_rag_api,
        description="Util para responder preguntas generales sobre el glamping Brillo de Luna, coomo capasidad, precios, reglas, check-in/out, servicios o descripciones de los domos. Siempre usa esta herramienta para buscar informacion en los datos del glamping."
    )
]

# Crear memoria conversacional
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="input"
)

# Mensajes iniciales
memory.chat_memory.add_user_message(
    "Quiero que actúes como un experto en glamping y que respondas siempre en español.")
memory.chat_memory.add_ai_message(
    "¡Claro! Estoy listo para responder cualquier pregunta sobre glamping: alojamiento, actividades, precios, ubicación, mascotas, etc.")

# Inicializar agente
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# Endpoint para prueba directa del chatbot
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

# Webhook para integrarse con Dialogflow
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    try:
        result = agent.invoke({"input": query_text})
        return jsonify({
            "fulfillmentText": result["output"]
        })
    except Exception as e:
        return jsonify({
            "fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."
        })

# Endpoint REST para disponibilidad
@app.route("/disponibilidad/<dia>", methods=["GET"])
def disponibilidad(dia):
    if dia.lower() in ["sábado", "domingo"]:
        return jsonify({"disponible": False, "mensaje": "Lo siento, no hay disponibilidad para ese día."})
    else:
        return jsonify({"disponible": True, "mensaje": "¡Sí hay disponibilidad para esa fecha!"})

# Endpoint REST para precios
@app.route("/precios", methods=["GET"])
def precios():
    return jsonify({
        "estándar": "150.000 COP por noche",
        "premium": "250.000 COP por noche",
        "glamping_de_lujo": "350.000 COP por noche"
    })
# Ruta raíz para evitar error 404
@app.route("/")
def home():
    return "¡Servidor Flask para Glamping funcionando correctamente!"


# Iniciar servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
