from flask import Flask, Response, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType # Eliminamos 'Tool' de aquí
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from langchain_openai import ChatOpenAI
from rag_engine import qa_chains
from twilio.twiml.messaging_response import MessagingResponse
import uuid
import os
import json
from datetime import datetime
from langchain.tools import BaseTool, Tool # Importamos BaseTool y Tool


#Importaciones Paincone

from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
# Cargar variables de entorno
load_dotenv()

# Pinecone (versión nueva - 3.x)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "reservas-glamping-v2")

# Inicializar cliente Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Conectar al índice existente (asegúrate que ya está creado)
try:
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    print(f"✅ Índice '{PINECONE_INDEX_NAME}' conectado correctamente.")
except Exception as e:
    raise RuntimeError(f"❌ Error al conectar con el índice '{PINECONE_INDEX_NAME}': {e}")

# Flask config
app = Flask(__name__)

MEMORY_DIR = "user_memories_data"
os.makedirs(MEMORY_DIR, exist_ok=True)

user_memories = {}
user_states = {}

# Twilio config
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

try:
    twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, account_sid=TWILIO_ACCOUNT_SID)
    print("📞 Cliente Twilio cargado correctamente.")
except Exception as e:
    print(f"❌ Error cargando Twilio: {e}")
    twilio_client = None

# LLM (OpenAI)
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)
# --- Herramientas RAG para el Agente ---

# Esta clase de Herramienta para solicitar datos de reserva es un buen enfoque.
# El agente la "llama" y luego tu código Flask interpreta la respuesta
# "REQUEST_RESERVATION_DETAILS" para iniciar el flujo.
class ReservationRequestTool(BaseTool):
    name: str = "SolicitarDatosReserva"
    description: str = "Útil para iniciar el proceso de recolección de datos de reserva. Úsala cuando el usuario exprese claramente su deseo de hacer una reserva (ej. 'quiero reservar', 'hacer una reserva', 'reservar un domo', 'cómo reservo')."

    def _run(self, query: str = None) -> str:
        # Esta herramienta no procesa la reserva, solo indica que el bot debe pedir los datos.
        return "REQUEST_RESERVATION_DETAILS"

    async def _arun(self, query: str = None) -> str:
        return self._run(query)

tools = [
    ReservationRequestTool(), # Ahora se instancia correctamente
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
    ),
    Tool(
        name="RequisitosReserva",
        func=qa_chains["requisitos_reserva"].run,
        description="Requisitos para que el usuario pueda reservar."
    )
]

# --- Manejo de Memoria ---

def _get_memory_file_path(user_id: str) -> str:
    return os.path.join(MEMORY_DIR, f"{user_id}.json")

def save_user_memory(user_id: str, memory: ConversationBufferMemory):
    memory_path = _get_memory_file_path(user_id)
    with open(memory_path, 'w', encoding='utf-8') as f:
        json.dump(messages_to_dict(memory.chat_memory.messages), f, ensure_ascii=False, indent=2)
    print(f"Memoria guardada en archivo para el usuario: {user_id}")

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
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON para el usuario {user_id}: {e}. Se iniciará con memoria vacía.")
        except Exception as e:
            print(f"Error inesperado al cargar memoria para el usuario {user_id}: {e}. Se iniciará con memoria vacía.")
    else:
        print(f"No se encontró archivo de memoria para el usuario {user_id}. Inicializando nueva memoria.")
        memory.chat_memory.add_user_message(
            "Hola, tu nombre es Maria. Eres una asistente experta en Glamping Brillo de Luna y "
            "tienes acceso a información detallada sobre el lugar, sus domos, sus servicios, políticas y actividades. "
            "También tienes una excelente memoria para recordar todos los detalles de nuestra conversación, "
            "incluso si no son directamente sobre el glamping o si son de índole personal o emocional. "
            "Responde siempre en español. "
            "Usa tus herramientas de información de Glamping para responder preguntas específicas sobre cualquier aspecto del lugar. "
            "Recuerda siempre el contexto de la conversación para responder de manera coherente y empática, "
            "incluso si la información no es directamente relevante para las herramientas o el Glamping. "
            "Si se te pregunta sobre algo que ya mencionaste, reitéralo de forma natural sin sonar repetitivo. "
            "Tu objetivo es ser útil, informativa y comprensiva en todo momento."
        )
        memory.chat_memory.add_ai_message(
            "¡Hola! Soy María, tu asistente experta en Glamping Brillo de Luna. "
            "Estoy aquí para ayudarte con cualquier pregunta sobre nuestro glamping, domos, servicios, políticas y actividades. ¿En qué puedo asistirte hoy?"
        )
        save_user_memory(user_id, memory)

    return memory

# ...existing code...
def save_reservation_data(user_phone_number, reservation_data):
    print(f"Datos de reserva para {user_phone_number}: {json.dumps(reservation_data, indent=2)}")
    print("La reserva se ha procesado, pero no se ha guardado en una base de datos persistente.")
    return True

#Funcion para guardar los datos de reserva en Pinecone
def save_reservation_to_pinecone(user_phone_number, reservation_data):
    # Convierte los datos de reserva a un string para vectorizar
    reserva_text = json.dumps(reservation_data, ensure_ascii=False)
    # Obtén el embedding del texto de la reserva
    embedder = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vector = embedder.embed_query(reserva_text)
    # Usa el número de teléfono como ID único
    pinecone_index.upsert([(user_phone_number, vector, reservation_data)])
    print(f"Reserva guardada en Pinecone para {user_phone_number}")

def parse_reservation_details(user_input):
    prompt = f"""
    Extrae los siguientes datos de la solicitud de reserva del usuario. Si un dato no se proporciona, usa 'N/A'.
    El nombre completo de los huéspedes debe ser una lista de strings.
    Las fechas deben estar en formato YYYY-MM-DD. Si el usuario da DD/MM/AAAA, conviértelo.
    Si el usuario no especifica un servicio adicional o adiciones, usa "ninguno".

    Solicitud del usuario: "{user_input}"

    Formato de salida JSON esperado:
    {{
        "nombres_huespedes": ["Nombre Completo 1", "Nombre Completo 2"],
        "domo": "Tipo de Domo",
        "fecha_entrada": "YYYY-MM-DD",
        "fecha_salida": "YYYY-MM-DD",
        "servicio_elegido": "Servicio Adicional",
        "adicciones": "Adicciones (ej. mascota, otro servicio)",
        "numero_contacto": "Numero de Telefono",
        "email_contacto": "Correo Electronico"
    }}
    """
    try:
        parsing_llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        response_text = parsing_llm.invoke(prompt).content
        parsed_json = json.loads(response_text)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON de la respuesta del LLM para parsing: {response_text}. Error: {e}")
        return None
    except Exception as e:
        print(f"Error al llamar al LLM para parsing: {e}")
        return None

@app.route("/whatsapp_webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    button_payload = request.values.get('ButtonPayload') 

    print(f"[{from_number}] Mensaje recibido: '{incoming_msg}' (Payload: '{button_payload}')")

    resp = MessagingResponse()
    agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."

    if from_number not in user_memories:
        user_memories[from_number] = load_user_memory(from_number)
    
    if from_number not in user_states:
        user_states[from_number] = {"current_flow": "none", "reserva_step": 0, "reserva_data": {}}
            
    memory = user_memories[from_number]
    user_state = user_states[from_number]

    # Lógica de flujo de reserva (detecta intención o continúa flujo existente)
    if user_state["current_flow"] == "none" and \
       (("reserva" in incoming_msg.lower() and ("quiero" in incoming_msg.lower() or "hacer" in incoming_msg.lower() or "reservar" in incoming_msg.lower())) or \
        (button_payload and "reserva" in button_payload.lower())):
        
        user_state["current_flow"] = "reserva"
        user_state["reserva_step"] = 1
        user_state["reserva_data"] = {}
        
        resp.message(
            "¡Claro! Dame los siguientes datos:\n"
            "-Tu nombre completo y de tus acompañantes\n"
            "-Domo que quieras\n"
            "-Fecha que quieras asistir y hasta cuando seria tu estadia (Formato DD/MM/AAAA)\n"
            "-Servicios que quieras incluir\n"
            "-Adicciones (Servicios, mascota etc)\n"
            "-Número de teléfono de contacto\n"
            "-Correo electrónico de contacto\n\n"
            "Por favor, escribe toda la información en un solo mensaje."
        )
        save_user_memory(from_number, memory)
        return str(resp)

    if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
        resp.message("Procesando tu solicitud de reserva, por favor espera un momento...")
        parsed_data = parse_reservation_details(incoming_msg)

        if parsed_data:
            try:
                names_list = [name.strip() for name in parsed_data.get("nombres_huespedes", []) if name.strip()]
                if not names_list:
                    raise ValueError("Nombres de huéspedes no proporcionados.")
                
                fecha_entrada_str = parsed_data.get("fecha_entrada")
                fecha_salida_str = parsed_data.get("fecha_salida")

                fecha_entrada_dt = datetime.strptime(fecha_entrada_str, "%Y-%m-%d")
                fecha_salida_dt = datetime.strptime(fecha_salida_str, "%Y-%m-%d")

                if fecha_salida_dt <= fecha_entrada_dt:
                    raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")

                user_state["reserva_data"] = {
                    "nombres_huespedes": names_list,
                    "cantidad_huespedes": len(names_list),
                    "domo": parsed_data.get("domo", "N/A"),
                    "fecha_entrada": fecha_entrada_dt.isoformat(),
                    "fecha_salida": fecha_salida_dt.isoformat(),
                    "servicio_elegido": parsed_data.get("servicio_elegido", "ninguno"),
                    "adicciones": parsed_data.get("adicciones", "ninguno"),
                    "numero_contacto": parsed_data.get("numero_contacto", from_number.replace("whatsapp:", "")),
                    "email_contacto": parsed_data.get("email_contacto", "N/A")
                }

                reserva_info = user_state["reserva_data"]
                confirmation_msg = (
                    "¡Listo! Aquí está el resumen de tu reserva:\n"
                    f"Huéspedes: {', '.join(reserva_info['nombres_huespedes'])} ({reserva_info['cantidad_huespedes']} personas)\n"
                    f"Domo: {reserva_info['domo']}\n"
                    f"Servicio: {reserva_info['servicio_elegido']}\n"
                    f"Adiciones: {reserva_info['adicciones']}\n"
                    f"Entrada: {datetime.fromisoformat(reserva_info['fecha_entrada']).strftime('%d/%m/%Y')}\n"
                    f"Salida: {datetime.fromisoformat(reserva_info['fecha_salida']).strftime('%d/%m/%Y')}\n"
                    f"Teléfono: {reserva_info['numero_contacto']}\n"
                    f"Email: {reserva_info['email_contacto']}\n\n"
                    "¿Confirmas esta reserva? (Sí/No)"
                )

                
                resp.message(confirmation_msg)
                user_state["reserva_step"] = 2
                
            except (ValueError, KeyError) as e:
                resp.message(f"Lo siento, no pude entender todos los detalles de tu reserva. Por favor, asegúrate de incluir:\n"
                             "-Nombres completos de huéspedes\n"
                             "-Domo\n"
                             "-Fechas de entrada y salida (DD/MM/AAAA)\n"
                             "-Servicios que quieras incluir\n"
                             "-Adiciones (ej. mascota)\n"
                             f"Error: {e}. Por favor, intenta de nuevo con toda la información.")
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
            except Exception as e:
                print(f"Error inesperado al procesar reserva: {e}")
                resp.message("Hubo un error inesperado al procesar tu reserva. Por favor, intenta de nuevo.")
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
        else:
            resp.message("No pude extraer los datos de tu reserva. Por favor, asegúrate de incluir toda la información solicitada en un solo mensaje.")
            user_state["current_flow"] = "none"
            user_state["reserva_step"] = 0
            user_state["reserva_data"] = {}
        
        save_user_memory(from_number, memory)
        return str(resp)

    if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
        if incoming_msg.lower() in ["si", "sí"]:
            try:
                reservation_data = user_state["reserva_data"]
                save_reservation_data(from_number, reservation_data)
                save_reservation_to_pinecone(from_number, reservation_data)
                resp.message("¡Reserva confirmada y procesada! Nos pondremos en contacto contigo pronto para los detalles finales. ¡Gracias por elegir Glamping Brillo de Luna!")
            except Exception as e:
                print(f"Error al procesar la reserva: {e}")
                resp.message("Lo siento, hubo un error al procesar tu reserva. Por favor, intenta de nuevo más tarde.")
            finally:
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
        else:
            resp.message("Reserva cancelada. ¿Hay algo más en lo que pueda ayudarte?")
            user_state["current_flow"] = "none"
            user_state["reserva_step"] = 0
            user_state["reserva_data"] = {}
        save_user_memory(from_number, memory)
        return str(resp)

    # Procesamiento normal con el Agente Conversacional (si no hay flujo activo)
    try:
        custom_agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )
        try:
            result = custom_agent.invoke(
                {"input": incoming_msg, "chat_history": memory.load_memory_variables({}).get("chat_history", [])},
                config={"configurable": {"session_id": from_number}}
            )
            if isinstance(result, dict) and "output" in result:
                agent_answer = result["output"]
            else:
                raise ValueError("El agente no devolvió un campo 'output'.")
        except Exception as e:
            print(f"ERROR procesando mensaje con agente: {e}")
            agent_answer = "Disculpa, ocurrió un error al procesar tu mensaje con el agente."
        finally:
            save_user_memory(from_number, memory)
    except Exception as e:
        print(f"Error inesperado al inicializar el agente: {e}")
        agent_answer = "Disculpa, ocurrió un error inesperado al procesar tu mensaje."

    # Si el agente decide iniciar el flujo de reserva (a través de la herramienta)
    if agent_answer == "REQUEST_RESERVATION_DETAILS":
        resp.message(
            "¡Claro! Para tu reserva, necesito los siguientes datos:\n"
            "- Tu nombre completo y el de tus acompañantes\n"
            "- Tipo de domo que te gustaría reservar\n"
            "- Fecha de entrada y fecha de salida (Formato DD/MM/AAAA)\n"
            "- Servicios adicionales que quieras incluir (ej. cena romántica, masajes)\n"
            "- Cualquier adición especial (ej. mascota, decoración específica)\n"
            "- Tu número de teléfono de contacto\n"
            "- Tu correo electrónico de contacto\n\n"
            "Por favor, envíame toda esta información en un solo mensaje para procesar tu solicitud."
        )
    else:
        resp.message(agent_answer)
        print(f"[{from_number}] Respuesta: '{agent_answer}'")
    return str(resp)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))

    if not user_input:
        return jsonify({"error": "Falta el campo 'input'"}), 400

    if session_id not in user_memories:
        user_memories[session_id] = load_user_memory(session_id)
    
    if session_id not in user_states:
        user_states[session_id] = {"current_flow": "none", "reserva_step": 0, "reserva_data": {}}

    memory = user_memories[session_id]
    user_state = user_states[session_id]

    response_output = "Lo siento, no pude procesar tu solicitud en este momento."
    
    # Lógica de flujo de reserva para el endpoint /chat
    if user_state["current_flow"] == "none" and \
       ("reserva" in user_input.lower() and ("quiero" in user_input.lower() or "hacer" in user_input.lower() or "reservar" in user_input.lower())):
        user_state["current_flow"] = "reserva"
        user_state["reserva_step"] = 1
        user_state["reserva_data"] = {}
        response_output = (
            "¡Claro! Dame los siguientes datos:\n"
            "-Tu nombre completo y de tus acompañantes\n"
            "-Domo que quieras\n"
            "-Fecha que quieras asistir y hasta cuando seria tu estadia (Formato DD/MM/AAAA)\n"
            "-Servicios que quieras incluir\n"
            "-Adicciones (Servicios, mascota etc)\n"
            "-Número de teléfono de contacto\n"
            "-Correo electrónico de contacto\n\n"
            "Por favor, escribe toda la información en un solo mensaje."
        )
    elif user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
        parsed_data = parse_reservation_details(user_input)
        if parsed_data:
            try:
                names_list = [name.strip() for name in parsed_data.get("nombres_huespedes", []) if name.strip()]
                if not names_list:
                    raise ValueError("Nombres de huéspedes no proporcionados.")
                
                fecha_entrada_str = parsed_data.get("fecha_entrada")
                fecha_salida_str = parsed_data.get("fecha_salida")

                fecha_entrada_dt = datetime.strptime(fecha_entrada_str, "%Y-%m-%d")
                fecha_salida_dt = datetime.strptime(fecha_salida_str, "%Y-%m-%d")

                if fecha_salida_dt <= fecha_entrada_dt:
                    raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")

                user_state["reserva_data"] = {
                    "nombres_huespedes": names_list,
                    "cantidad_huespedes": len(names_list),
                    "domo": parsed_data.get("domo", "N/A"),
                    "fecha_entrada": fecha_entrada_dt.isoformat(),
                    "fecha_salida": fecha_salida_dt.isoformat(),
                    "servicio_elegido": parsed_data.get("servicio_elegido", "ninguno"),
                    "adicciones": parsed_data.get("adicciones", "ninguno"),
                    "numero_contacto": parsed_data.get("numero_contacto", session_id),
                    "email_contacto": parsed_data.get("email_contacto", "N/A")
                }

                reserva_info = user_state["reserva_data"]
                response_output = (
                    "¡Listo! Aquí está el resumen de tu reserva:\n"
                    f"Huéspedes: {', '.join(reserva_info['nombres_huespedes'])} ({reserva_info['cantidad_huespedes']} personas)\n"
                    f"Domo: {reserva_info['domo']}\n"
                    f"Servicio: {reserva_info['servicio_elegido']}\n"
                    f"Adiciones: {reserva_info['adicciones']}\n"
                    f"Entrada: {datetime.fromisoformat(reserva_info['fecha_entrada']).strftime('%d/%m/%Y')}\n"
                    f"Salida: {datetime.fromisoformat(reserva_info['fecha_salida']).strftime('%d/%m/%Y')}\n"
                    f"Teléfono: {reserva_info['numero_contacto']}\n"
                    f"Email: {reserva_info['email_contacto']}\n\n"
                    "¿Confirmas esta reserva? (Sí/No)"
                )
                user_state["reserva_step"] = 2

            except (ValueError, KeyError) as e:
                response_output = (f"Lo siento, no pude entender todos los detalles de tu reserva. Por favor, asegúrate de incluir:\n"
                                   "-Nombres completos de huéspedes\n"
                                   "-Domo\n"
                                   "-Fechas de entrada y salida (DD/MM/AAAA)\n"
                                   "-Servicios que quieras incluir\n"
                                   "-Adiciones (ej. mascota)\n"
                                   f"Error: {e}. Por favor, intenta de nuevo con toda la información.")
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
            except Exception as e:
                print(f"Error inesperado al procesar reserva en /chat: {e}")
                response_output = "Hubo un error inesperado al procesar tu reserva. Por favor, intenta de nuevo."
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
        else:
            response_output = "No pude extraer los datos de tu reserva. Por favor, asegúrate de incluir toda la información solicitada en un solo mensaje."
            user_state["current_flow"] = "none"
            user_state["reserva_step"] = 0
            user_state["reserva_data"] = {}

    elif user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
        if user_input.lower() in ["si", "sí"]:
            try:
                reservation_data = user_state["reserva_data"]
                save_reservation_data(session_id, reservation_data)
                save_reservation_to_pinecone(reservation_data["numero_contacto"], reservation_data)
                response_output = "¡Reserva confirmada y procesada! Nos pondremos en contacto contigo pronto para los detalles finales. ¡Gracias por elegir Glamping Brillo de Luna!"
            except Exception as e:
                print(f"Error al procesar la reserva en /chat: {e}")
                response_output = "Lo siento, hubo un error al procesar tu reserva. Por favor, intenta de nuevo más tarde."
            finally:
                user_state["current_flow"] = "none"
                user_state["reserva_step"] = 0
                user_state["reserva_data"] = {}
        else:
            response_output = "Reserva cancelada. ¿Hay algo más en lo que pueda ayudarte?"
            user_state["current_flow"] = "none"
            user_state["reserva_step"] = 0
            user_state["reserva_data"] = {}
    else:
        # Procesamiento normal con el agente si no hay flujo de reserva activo
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
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

@app.route("/")
def home():
    return "Servidor Flask con Agente RAG y WhatsApp conectado. La memoria del agente ahora es persistente."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)