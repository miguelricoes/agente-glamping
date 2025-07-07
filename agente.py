from flask import Flask, request, jsonify 
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os


from rag_engine import qa_chain

load_dotenv()
app = Flask(__name__)

# LLM base
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Herramienta única: Consultar información con RAG
def call_rag_api(query: str) -> str:
    try:
        result = qa_chain.invoke({"query": query})
        return result
    except Exception as e:
        print(f"Error usando qa_chain:", e)
        return "Lo siento, hubo un error al procesar tu pregunta con el sistema RAG."

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

# Contexto inicial
memory.chat_memory.add_user_message(
    "Actúa como un experto en glamping y responde siempre en español. "
    "Cuando te hagan cualquier pregunta sobre Glamping Brillo de Luna, usa la herramienta 'InformacionGlamping'. "
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

# Endpoint principal
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

# Dialogflow
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    query_text = data.get("queryResult", {}).get("queryText", "")
    try:
        result = agent.invoke({"input": query_text})
        return jsonify({"fulfillmentText": result["output"]})
    except Exception:
        return jsonify({"fulfillmentText": "Lo siento, hubo un error procesando tu solicitud."})

@app.route("/")
def home():
    return "Servidor Flask corriendo con agente RAG para Glamping Brillo de Luna."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
