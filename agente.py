from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
try:
    from langchain_community.llms import OpenAI
except ImportError:
    from langchain.llms import OpenAI
from rag_engine import qa_chains
import uuid
import os
import json
from langchain.tools import BaseTool, Tool
# Importaciones para base de datos con manejo de errores
try:
    from flask_sqlalchemy import SQLAlchemy
    print("OK: Flask-SQLAlchemy importado correctamente")
except ImportError:
    raise ImportError("ERROR: No se pudo importar Flask-SQLAlchemy. Instala: pip install Flask-SQLAlchemy")

from datetime import datetime, date


print("Puerto asignado:", os.environ.get("PORT"))


#Importaciones Paincone

# Importaciones de Pinecone con manejo de errores
try:
    # Opción 1: Import completo (pinecone v3.0+)
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_SERVERLESS_AVAILABLE = True
    print("OK: Pinecone importado con ServerlessSpec")
except ImportError:
    try:
        # Opción 2: Import básico sin ServerlessSpec
        from pinecone import Pinecone
        PINECONE_SERVERLESS_AVAILABLE = False
        print("OK: Pinecone importado sin ServerlessSpec")
    except ImportError:
        # Opción 3: Import legacy
        try:
            import pinecone as pinecone_legacy
            Pinecone = pinecone_legacy
            PINECONE_SERVERLESS_AVAILABLE = False
            print("OK: Pinecone importado con API legacy")
        except ImportError:
            raise ImportError("ERROR: No se pudo importar Pinecone. Instala: pip install pinecone-client")

try:
    from langchain_community.embeddings import OpenAIEmbeddings
except ImportError:
    from langchain.embeddings import OpenAIEmbeddings

# Cargar variables de entorno

load_dotenv()

# Función para validar variables de entorno críticas
def validate_environment_variables():
    """Valida que las variables de entorno críticas estén configuradas"""
    # Variables absolutamente críticas (sin estas no puede funcionar el LLM)
    critical_vars = {
        'OPENAI_API_KEY': 'API Key de OpenAI para LLM',
    }
    
    # Variables opcionales (funcionalidades específicas)
    optional_vars = {
        'DATABASE_URL': 'URL de conexión a PostgreSQL',
        'PINECONE_API_KEY': 'API Key de Pinecone para vectorstore',
        'TWILIO_ACCOUNT_SID': 'Account SID de Twilio',
        'TWILIO_API_KEY_SID': 'API Key SID de Twilio',
        'TWILIO_API_KEY_SECRET': 'API Key Secret de Twilio',
        'TWILIO_PHONE_NUMBER': 'Número de teléfono de Twilio'
    }
    
    # Verificar variables críticas
    missing_critical = []
    for var_name, description in critical_vars.items():
        value = os.getenv(var_name)
        if not value or value.strip() == '':
            missing_critical.append(f"  - {var_name}: {description}")
    
    if missing_critical:
        error_msg = "ERROR: VARIABLES CRÍTICAS FALTANTES:\n" + "\n".join(missing_critical)
        error_msg += "\n\n[TIP] Configura estas variables en tu archivo .env o en Railway"
        print(error_msg)
        raise EnvironmentError(error_msg)
    
    # Verificar variables opcionales (solo advertir)
    missing_optional = []
    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if not value or value.strip() == '':
            missing_optional.append(f"  - {var_name}: {description}")
    
    if missing_optional:
        warning_msg = "WARNING: VARIABLES OPCIONALES FALTANTES (funcionalidad limitada):\n" + "\n".join(missing_optional)
        warning_msg += "\n[TIP] Algunas funciones pueden no estar disponibles"
        print(warning_msg)
    
    print("OK: Variables críticas configuradas correctamente")
    return True

# Validar variables de entorno al inicio
validate_environment_variables()

# Pinecone V3 - Inicialización opcional
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "reservas-glamping-v2")
pc = None
pinecone_index = None

# Inicializar cliente Pinecone con manejo de errores (opcional)
if PINECONE_API_KEY:
    try:
        if hasattr(Pinecone, '__call__'):
            # Pinecone v3.0+ - Clase inicializable
            pc = Pinecone(api_key=PINECONE_API_KEY)
            print("OK: Cliente Pinecone v3.0+ inicializado correctamente")
        else:
            # Pinecone legacy - API estática
            pc = Pinecone
            pc.init(api_key=PINECONE_API_KEY, environment="us-east1-gcp")  # Ajustar environment según tu configuración
            print("OK: Cliente Pinecone legacy inicializado correctamente")
    except Exception as e:
        warning_msg = f"WARNING: Error al inicializar Pinecone: {e}\n[TIP] Funcionalidad Pinecone deshabilitada"
        print(warning_msg)
        pc = None
else:
    print("WARNING: PINECONE_API_KEY no configurada - Funcionalidad Pinecone deshabilitada")

# Validar que el índice exista con mejor manejo de errores (opcional)
if pc:
    try:
        # Obtener lista de índices según la versión de Pinecone
        try:
            # Pinecone v3.0+
            if hasattr(pc, 'list_indexes') and callable(pc.list_indexes):
                indexes_response = pc.list_indexes()
                if isinstance(indexes_response, dict) and "indexes" in indexes_response:
                    indexes = [index["name"] for index in indexes_response["indexes"]]
                else:
                    # Respuesta directa (lista)
                    indexes = [index.name for index in indexes_response] if hasattr(indexes_response[0], 'name') else [str(index) for index in indexes_response]
            else:
                # Pinecone legacy
                indexes = pc.list_indexes()
        except Exception as list_error:
            print(f"WARNING: No se pudo obtener lista de índices: {list_error}")
            indexes = []  # Continuar sin validar
        
        if indexes and PINECONE_INDEX_NAME not in indexes:
            warning_msg = f"WARNING: El índice '{PINECONE_INDEX_NAME}' no existe en Pinecone.\n[TIP] Índices disponibles: {indexes}\n[INFO] Funcionalidad Pinecone deshabilitada"
            print(warning_msg)
            pinecone_index = None
        else:
            # Conectar al índice
            try:
                if hasattr(pc, 'Index'):
                    # Pinecone v3.0+
                    pinecone_index = pc.Index(PINECONE_INDEX_NAME)
                else:
                    # Pinecone legacy
                    pinecone_index = pc.Index(index_name=PINECONE_INDEX_NAME)
                
                print(f"OK: Conectado al índice Pinecone: {PINECONE_INDEX_NAME}")
            except Exception as index_error:
                warning_msg = f"WARNING: Error al conectar con el índice '{PINECONE_INDEX_NAME}': {index_error}\n[INFO] Funcionalidad Pinecone deshabilitada"
                print(warning_msg)
                pinecone_index = None
            
    except Exception as e:
        warning_msg = f"WARNING: Error general con Pinecone: {e}\n[INFO] Funcionalidad Pinecone deshabilitada"
        print(warning_msg)
        pinecone_index = None
else:
    print("INFO: Pinecone no inicializado - Usando solo FAISS local")

# Flask config
app = Flask(__name__)

# Configurar CORS para el panel de control
CORS_ORIGIN = os.getenv('CORS_ORIGIN', 'https://panel-con-react-production.up.railway.app')
CORS(app, origins=[CORS_ORIGIN])

# Configuración de la base de datos opcional con prioridad para URL privada
DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

# Prioridad: PRIVATE > PUBLIC > URL genérica
database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL

if DATABASE_PRIVATE_URL:
    print("OK: Usando DATABASE_PRIVATE_URL (sin costos de egress)")
elif DATABASE_PUBLIC_URL:
    print("WARNING: Usando DATABASE_PUBLIC_URL (puede generar costos de egress)")
    print("TIP: Usa DATABASE_PRIVATE_URL para evitar costos")
elif DATABASE_URL:
    print("INFO: Usando DATABASE_URL genérica")

db = None

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar SQLAlchemy con validación de conexión
    try:
        db = SQLAlchemy(app)
        print("OK: SQLAlchemy inicializado correctamente")
    except Exception as e:
        warning_msg = f"WARNING: Error al inicializar la base de datos: {e}\n[TIP] Funcionalidad de base de datos deshabilitada"
        print(warning_msg)
        db = None
else:
    print("WARNING: Ninguna DATABASE_URL configurada - Funcionalidad de base de datos deshabilitada")
    print("TIP: Configura DATABASE_PRIVATE_URL, DATABASE_PUBLIC_URL o DATABASE_URL")

# Modelo de datos para reservas (solo si hay base de datos)
Reserva = None
if db:
    class Reserva(db.Model):
        __tablename__ = 'reservas'
        id = db.Column(db.Integer, primary_key=True)
        numero_whatsapp = db.Column(db.String(50), nullable=False)
        nombres_huespedes = db.Column(db.String(255), nullable=False)
        cantidad_huespedes = db.Column(db.Integer, nullable=False)
        domo = db.Column(db.String(50))
        fecha_entrada = db.Column(db.Date)
        fecha_salida = db.Column(db.Date)
        servicio_elegido = db.Column(db.String(100))
        adicciones = db.Column(db.String(255))
        numero_contacto = db.Column(db.String(50))
        email_contacto = db.Column(db.String(100))
        # Nuevos campos para funcionalidad completa
        metodo_pago = db.Column(db.String(50), default='Pendiente')
        monto_total = db.Column(db.Numeric(10, 2), default=0.00)
        comentarios_especiales = db.Column(db.Text)
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

        def __repr__(self):
            return f'<Reserva {self.id}: {self.nombres_huespedes}>'

# Sistema de cálculo de precios para reservas
def calcular_precio_reserva(domo, cantidad_huespedes, fecha_entrada, fecha_salida, servicios_adicionales=None):
    """Calcula el precio total de una reserva basado en domo, huéspedes, días y servicios"""
    
    # Precios base por domo por noche (para pareja)
    precios_domos = {
        'antares': 650000,    # Nido de amor con jacuzzi - $650.000/noche
        'polaris': 550000,    # Amplio con sofá cama - $550.000/noche + $100.000 por persona extra
        'sirius': 450000,     # Un piso, pareja - $450.000/noche
        'centaury': 450000    # Similar a Sirius - $450.000/noche
    }
    
    # Servicios adicionales disponibles
    precios_servicios = {
        'decoraciones': 60000,      # Desde $60.000
        'masajes': 90000,           # $90.000 por persona
        'masajes_pareja': 180000,   # Masajes para pareja
        'velero': 150000,           # Estimado para paseo en velero
        'lancha': 80000,            # Estimado para lancha compartida
        'caminata_montecillo': 50000,  # Estimado para caminata guiada
        'caminata_pozo_azul': 70000    # Estimado para caminata más larga
    }
    
    try:
        # Calcular número de noches
        if isinstance(fecha_entrada, str):
            fecha_entrada = datetime.fromisoformat(fecha_entrada).date()
        if isinstance(fecha_salida, str):
            fecha_salida = datetime.fromisoformat(fecha_salida).date()
            
        noches = (fecha_salida - fecha_entrada).days
        if noches <= 0:
            noches = 1  # Mínimo una noche
        
        # Precio base del domo
        domo_key = domo.lower() if domo else 'centaury'
        precio_base_noche = precios_domos.get(domo_key, 450000)
        
        # Costo por huéspedes adicionales (solo para Polaris)
        costo_huespedes_extra = 0
        if domo_key == 'polaris' and cantidad_huespedes > 2:
            personas_extra = cantidad_huespedes - 2
            costo_huespedes_extra = personas_extra * 100000 * noches  # $100.000 por persona extra por noche
        
        # Precio total de estadía
        precio_estadia = (precio_base_noche * noches) + costo_huespedes_extra
        
        # Agregar servicios adicionales
        precio_servicios_total = 0
        if servicios_adicionales:
            servicios_lista = servicios_adicionales.lower().split(',') if isinstance(servicios_adicionales, str) else [servicios_adicionales.lower()]
            
            for servicio in servicios_lista:
                servicio_clean = servicio.strip()
                if 'masaje' in servicio_clean:
                    if cantidad_huespedes >= 2:
                        precio_servicios_total += precios_servicios['masajes_pareja']
                    else:
                        precio_servicios_total += precios_servicios['masajes']
                elif 'decoracion' in servicio_clean:
                    precio_servicios_total += precios_servicios['decoraciones']
                elif 'velero' in servicio_clean:
                    precio_servicios_total += precios_servicios['velero']
                elif 'lancha' in servicio_clean:
                    precio_servicios_total += precios_servicios['lancha']
                elif 'montecillo' in servicio_clean:
                    precio_servicios_total += precios_servicios['caminata_montecillo']
                elif 'pozo' in servicio_clean or 'azul' in servicio_clean:
                    precio_servicios_total += precios_servicios['caminata_pozo_azul']
        
        precio_total = precio_estadia + precio_servicios_total
        
        return {
            'precio_total': precio_total,
            'precio_base_noche': precio_base_noche,
            'noches': noches,
            'precio_estadia': precio_estadia,
            'costo_huespedes_extra': costo_huespedes_extra,
            'precio_servicios': precio_servicios_total,
            'desglose': {
                'domo': f"{domo_key.title()} - ${precio_base_noche:,} x {noches} noche{'s' if noches > 1 else ''}",
                'huespedes_extra': f"${costo_huespedes_extra:,}" if costo_huespedes_extra > 0 else "No aplica",
                'servicios': f"${precio_servicios_total:,}" if precio_servicios_total > 0 else "Ninguno"
            }
        }
        
    except Exception as e:
        print(f"Error calculando precio: {e}")
        return {
            'precio_total': 450000,  # Precio base de emergencia
            'error': str(e)
        }

# Crear tablas de base de datos y validar conexión (opcional)
def initialize_database():
    """Inicializa la base de datos y crea las tablas necesarias"""
    if not db:
        print("INFO: Base de datos no configurada - Saltando inicialización")
        return False
        
    try:
        # Probar conexión a la base de datos
        with app.app_context():
            db.create_all()
            # Hacer una consulta simple para verificar conexión
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
        print("OK: Base de datos inicializada y tablas creadas correctamente")
        return True
    except Exception as e:
        warning_msg = f"WARNING: Error al conectar con la base de datos: {e}\n[TIP] Funcionalidad de base de datos deshabilitada"
        print(warning_msg)
        return False

# Inicializar base de datos si está disponible
db_initialized = initialize_database()

MEMORY_DIR = "user_memories_data"
try:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    # Verificar permisos de escritura
    test_file = os.path.join(MEMORY_DIR, "test_write.tmp")
    with open(test_file, 'w') as f:
        f.write("test")
    os.remove(test_file)
    print(f"OK: Directorio de memoria creado con permisos correctos: {MEMORY_DIR}")
except Exception as e:
    error_msg = f"ERROR: Error al crear directorio de memoria: {e}\n[TIP] Verifica permisos de escritura"
    print(error_msg)
    raise PermissionError(error_msg)

user_memories = {}
user_states = {}

# Configuración de Twilio con validación robusta
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Validar credenciales de Twilio específicamente
def validate_twilio_credentials():
    """Valida que las credenciales de Twilio sean válidas"""
    twilio_vars = {
        'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
        'TWILIO_API_KEY_SID': TWILIO_API_KEY_SID,
        'TWILIO_API_KEY_SECRET': TWILIO_API_KEY_SECRET,
        'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER
    }
    
    missing = [var for var, value in twilio_vars.items() if not value or value.strip() == '']
    if missing:
        error_msg = f"ERROR: Credenciales Twilio faltantes: {missing}\n[TIP] Configura todas las variables de Twilio"
        print(error_msg)
        raise EnvironmentError(error_msg)
    
    return True

# Inicializar cliente Twilio con validación robusta
try:
    validate_twilio_credentials()
    twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, account_sid=TWILIO_ACCOUNT_SID)
    print("OK: Cliente Twilio inicializado correctamente")
except Exception as e:
    error_msg = f"ERROR: Error al inicializar Twilio: {e}\n[TIP] Verifica tus credenciales de Twilio"
    print(error_msg)
    # NO asignamos None - lanzamos la excepción para fallar rápido
    raise ConnectionError(error_msg)

# Inicializar LLM con validación de OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    error_msg = "ERROR: OPENAI_API_KEY no configurada\n[TIP] Configura tu API Key de OpenAI"
    print(error_msg)
    raise EnvironmentError(error_msg)

try:
    # En langchain 0.1.0, OpenAI puede estar en diferentes ubicaciones
    import os
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  # Asegurar que esté en env
    
    # Intentar diferentes imports para compatibilidad con langchain 0.1.0
    llm = None
    try:
        # Opción 1: Import tradicional (ya importado arriba)
        llm = OpenAI(temperature=0)
        print("OK: LLM OpenAI inicializado con import tradicional")
    except (NameError, ImportError, TypeError) as e:
        try:
            # Opción 2: Import nuevo en langchain 0.1.0
            from langchain_openai import OpenAI as OpenAI_New
            llm = OpenAI_New(temperature=0)
            print("OK: LLM OpenAI inicializado con nuevo import langchain_openai")
        except ImportError:
            try:
                # Opción 3: Import legacy
                from langchain.llms.openai import OpenAI as OpenAI_Legacy
                llm = OpenAI_Legacy(temperature=0)
                print("OK: LLM OpenAI inicializado con import legacy")
            except ImportError:
                # Opción 4: ChatOpenAI como fallback
                try:
                    from langchain.chat_models import ChatOpenAI
                    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
                    print("OK: LLM inicializado con ChatOpenAI como fallback")
                except ImportError:
                    try:
                        # Opción 5: ChatOpenAI desde langchain_openai
                        from langchain_openai import ChatOpenAI as ChatOpenAI_New
                        llm = ChatOpenAI_New(temperature=0, model="gpt-3.5-turbo")
                        print("OK: LLM inicializado con ChatOpenAI nuevo")
                    except ImportError:
                        raise ImportError("No se pudo importar ninguna clase OpenAI de LangChain")
    
    if llm is None:
        raise RuntimeError("No se pudo inicializar el LLM")
        
except Exception as e:
    error_msg = f"ERROR: Error al inicializar OpenAI LLM: {e}\n[TIP] Verifica tu OPENAI_API_KEY y versión de langchain"
    print(error_msg)
    raise ConnectionError(error_msg)

# --- Herramientas RAG para el Agente ---

# Funciones wrapper para usar invoke() en lugar del deprecado run()
def call_chain_safe(chain_name: str, query: str) -> str:
    """Llama a una cadena QA usando el método invoke() moderno"""
    try:
        if chain_name not in qa_chains or qa_chains[chain_name] is None:
            return "Lo siento, esa información no está disponible en este momento."
        
        chain = qa_chains[chain_name]
        # Usar invoke() en lugar del deprecado run()
        result = chain.invoke({"query": query})
        
        # El resultado puede estar en diferentes campos dependiendo de la cadena
        if isinstance(result, dict):
            return result.get("result", result.get("output", str(result)))
        else:
            return str(result)
            
    except Exception as e:
        print(f"ERROR: Error en cadena {chain_name}: {e}")
        return "Disculpa, tuve un problema accediendo a esa información. ¿Podrías reformular tu pregunta?"

# Funciones específicas para cada herramienta - Archivos originales
def concepto_glamping_func(query: str) -> str:
    return call_chain_safe("concepto_glamping", query)

def ubicacion_contacto_func(query: str) -> str:
    return call_chain_safe("ubicacion_contacto", query)

def domos_info_func(query: str) -> str:
    return call_chain_safe("domos_info", query)

def servicios_incluidos_func(query: str) -> str:
    return call_chain_safe("servicios_incluidos", query)

def actividades_adicionales_func(query: str) -> str:
    return call_chain_safe("actividades_adicionales", query)

def politicas_glamping_func(query: str) -> str:
    return call_chain_safe("politicas_glamping", query)

def accesibilidad_func(query: str) -> str:
    return call_chain_safe("accesibilidad", query)

def requisitos_reserva_func(query: str) -> str:
    return call_chain_safe("requisitos_reserva", query)

# Funciones específicas para archivos nuevos
def domos_precios_func(query: str) -> str:
    return call_chain_safe("domos_precios", query)

def que_es_brillo_luna_func(query: str) -> str:
    return call_chain_safe("que_es_brillo_luna", query)

def servicios_externos_func(query: str) -> str:
    return call_chain_safe("servicios_externos", query)

def sugerencias_movilidad_reducida_func(query: str) -> str:
    return call_chain_safe("sugerencias_movilidad_reducida", query)

def politicas_privacidad_func(query: str) -> str:
    return call_chain_safe("politicas_privacidad", query)

def politicas_cancelacion_func(query: str) -> str:
    return call_chain_safe("politicas_cancelacion", query)

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
    ReservationRequestTool(), # Herramienta para iniciar reservas
    
    # === HERRAMIENTAS ORIGINALES ===
    Tool(
        name="ConceptoGlamping",
        func=concepto_glamping_func,
        description="Útil para responder preguntas generales sobre el concepto del glamping."
    ),
    Tool(
        name="UbicacionContactoGlamping",
        func=ubicacion_contacto_func,
        description="Información sobre ubicación, contacto, RNT, etc."
    ),
    Tool(
        name="DomosInfoGlamping",
        func=domos_info_func,
        description="Tipos de domos, precios y características básicas."
    ),
    Tool(
        name="ServiciosIncluidosGlamping",
        func=servicios_incluidos_func,
        description="Servicios incluidos como desayuno, WiFi, parqueadero, etc."
    ),
    Tool(
        name="ActividadesServiciosAdicionalesGlamping",
        func=actividades_adicionales_func,
        description="Servicios adicionales y actividades como masajes, paseos, etc."
    ),
    Tool(
        name="PoliticasGlamping",
        func=politicas_glamping_func,
        description="Políticas de cancelación, mascotas, normas del lugar."
    ),
    Tool(
        name="AccesibilidadMovilidadReducidaGlamping",
        func=accesibilidad_func,
        description="Útil cuando el usuario menciona silla de ruedas, discapacidad, movilidad reducida, accesibilidad, o necesidades especiales. Proporciona adaptaciones y recomendaciones para personas con limitaciones de movilidad."
    ),
    Tool(
        name="RequisitosReserva",
        func=requisitos_reserva_func,
        description="Requisitos para que el usuario pueda reservar."
    ),
    
    # === NUEVAS HERRAMIENTAS ===
    Tool(
        name="DomosPreciosDetallados",
        func=domos_precios_func,
        description="USAR CUANDO el usuario pregunte sobre precios, costos, tarifas, cuánto cuesta, valores, presupuesto, o dinero. Proporciona precios exactos de cada domo (Antares, Polaris, Sirius, Centaury), características detalladas, capacidades y tarifas por persona adicional."
    ),
    Tool(
        name="QueEsBrilloDeLuna",
        func=que_es_brillo_luna_func,
        description="Explicación completa sobre qué es Glamping Brillo de Luna, su filosofía y propósito único."
    ),
    Tool(
        name="ServiciosExternos",
        func=servicios_externos_func,
        description="USAR CUANDO el usuario pregunte sobre actividades, qué hacer, turismo, paseos, diversión, entretenimiento, planes, experiencias, o lugares para visitar en Guatavita. Incluye laguna sagrada, jet ski, paseos a caballo, avistamiento de aves, navegación y más."
    ),
    Tool(
        name="SugerenciasMovilidadReducida",
        func=sugerencias_movilidad_reducida_func,
        description="SIEMPRE usar esta herramienta cuando el usuario mencione: 'silla de ruedas', 'amigo en silla de ruedas', 'persona con discapacidad', 'movilidad reducida', 'accesibilidad', 'limitaciones físicas', 'necesidades especiales', 'adaptaciones', 'personas mayores'. Esta herramienta contiene información específica sobre rutas accesibles, equipos de apoyo, medidas de seguridad, personal capacitado y todas las adaptaciones disponibles en Brillo de Luna para personas con movilidad limitada."
    ),
    Tool(
        name="PoliticasPrivacidad",
        func=politicas_privacidad_func,
        description="Políticas de privacidad, manejo de datos personales y protección de información."
    ),
    Tool(
        name="PoliticasCancelacion",
        func=politicas_cancelacion_func,
        description="Políticas específicas de cancelación, términos y condiciones de reserva."
    )
]

# --- Manejo de Memoria ---

def _get_memory_file_path(user_id: str) -> str:
    # Sanitizar user_id para evitar path traversal attacks
    safe_user_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_', '.'))[:50]
    return os.path.join(MEMORY_DIR, f"{safe_user_id}.json")

def _get_backup_memory_file_path(user_id: str) -> str:
    """Obtiene la ruta del archivo de respaldo de memoria"""
    safe_user_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_', '.'))[:50]
    return os.path.join(MEMORY_DIR, f"{safe_user_id}_backup.json")

def save_user_memory(user_id: str, memory: ConversationBufferMemory):
    """Guarda la memoria del usuario con manejo robusto de errores y respaldo automático"""
    memory_path = _get_memory_file_path(user_id)
    backup_path = _get_backup_memory_file_path(user_id)
    temp_path = f"{memory_path}.tmp"
    
    try:
        # Validar que la memoria tenga contenido válido
        if not memory or not hasattr(memory, 'chat_memory') or not hasattr(memory.chat_memory, 'messages'):
            print(f"WARNING:  Memoria inválida para usuario {user_id}, saltando guardado")
            return False
        
        # Serializar los mensajes
        try:
            serialized_messages = messages_to_dict(memory.chat_memory.messages)
        except Exception as e:
            print(f"ERROR: Error al serializar mensajes para usuario {user_id}: {e}")
            return False
        
        # Crear respaldo del archivo existente si existe y es válido
        if os.path.exists(memory_path):
            try:
                # Validar que el archivo actual es un JSON válido antes de hacer backup
                with open(memory_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Solo validar, no usar el contenido
                # Si es válido, crear backup
                import shutil
                shutil.copy2(memory_path, backup_path)
            except (json.JSONDecodeError, IOError) as e:
                print(f"WARNING:  Archivo de memoria actual corrupto para usuario {user_id}: {e}")
                # No creamos backup de archivo corrupto
        
        # Escribir a archivo temporal primero (atomic write)
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(serialized_messages, f, ensure_ascii=False, indent=2)
        
        # Validar que el archivo temporal es un JSON válido
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Validar formato
        
        # Mover archivo temporal al destino final (operación atómica)
        import shutil
        shutil.move(temp_path, memory_path)
        
        print(f"OK: Memoria guardada correctamente para usuario: {user_id}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error inesperado al guardar memoria para usuario {user_id}: {e}")
        # Limpiar archivo temporal si existe
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass
        return False

def _create_fresh_memory(user_id: str) -> ConversationBufferMemory:
    """Crea una memoria nueva con mensajes iniciales para el usuario"""
    try:
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, input_key="input"
        )
        
        # Mensajes iniciales para el contexto del agente
        system_message = (
            "Hola, tu nombre es Maria. Eres una asistente experta en Glamping Brillo de Luna y "
            "tienes acceso a información detallada sobre el lugar, sus domos, sus servicios, políticas y actividades. "
            "También tienes una excelente memoria para recordar todos los detalles de nuestra conversación, "
            "incluso si no son directamente sobre el glamping o si son de índole personal o emocional. "
            "Responde siempre en español. "
            "IMPORTANTE: SIEMPRE usa tus herramientas disponibles para responder preguntas específicas. "
            "Cuando el usuario mencione 'silla de ruedas', 'movilidad reducida', 'discapacidad', 'accesibilidad', 'limitaciones físicas', 'muletas', o 'adaptaciones', "
            "DEBES usar inmediatamente la herramienta SugerenciasMovilidadReducida y responder con TODA la información que la herramienta te proporcione. "
            "NUNCA hagas preguntas de seguimiento cuando ya tienes información específica de una herramienta. "
            "SIEMPRE proporciona la información completa que obtienes de las herramientas. "
            "Cuando pregunten sobre precios, DEBES usar DomosPreciosDetallados. "
            "Cuando pregunten sobre actividades, DEBES usar ServiciosExternos. "
            "No des respuestas genéricas cuando tienes herramientas específicas disponibles. "
            "Tu respuesta debe basarse en la información EXACTA que obtienes de las herramientas, no agregues preguntas adicionales. "
            "Tu objetivo es ser útil, informativa y comprensiva usando SIEMPRE la información específica de tus herramientas."
        )
        
        assistant_response = (
            "¡Hola! Soy María, tu asistente experta en Glamping Brillo de Luna. "
            "Estoy aquí para ayudarte con cualquier pregunta sobre nuestro glamping, domos, servicios, políticas y actividades. ¿En qué puedo asistirte hoy?"
        )
        
        # Intentar métodos compatibles con langchain 0.1.0
        try:
            # Método 1: API nueva de langchain 0.1.0
            from langchain.schema import HumanMessage, AIMessage
            memory.chat_memory.add_message(HumanMessage(content=system_message))
            memory.chat_memory.add_message(AIMessage(content=assistant_response))
            print(f"OK: Memoria creada con API nueva para usuario: {user_id}")
        except (ImportError, AttributeError):
            try:
                # Método 2: API legacy
                memory.chat_memory.add_user_message(system_message)
                memory.chat_memory.add_ai_message(assistant_response)
                print(f"OK: Memoria creada con API legacy para usuario: {user_id}")
            except AttributeError:
                # Método 3: Fallback - memoria básica sin mensajes iniciales
                print(f"WARNING:  Creando memoria básica sin mensajes iniciales para usuario: {user_id}")
                # La memoria se inicializará vacía y se llenará con la primera conversación
        
        return memory
        
    except Exception as e:
        print(f"ERROR: Error creando memoria para usuario {user_id}: {e}")
        # Fallback: memoria mínima
        return ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True, 
            input_key="input"
        )

def _try_load_memory_from_file(file_path: str, user_id: str) -> tuple[bool, ConversationBufferMemory]:
    """Intenta cargar memoria desde un archivo específico"""
    try:
        if not os.path.exists(file_path):
            return False, None
            
        # Verificar que el archivo no esté vacío
        if os.path.getsize(file_path) == 0:
            print(f"WARNING:  Archivo de memoria vacío para usuario {user_id}: {file_path}")
            return False, None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            serialized_messages = json.load(f)
        
        # Validar estructura básica
        if not isinstance(serialized_messages, list):
            print(f"WARNING:  Formato de memoria inválido para usuario {user_id}: esperaba lista")
            return False, None
        
        # Crear memoria y cargar mensajes
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, input_key="input"
        )
        
        try:
            # Intentar cargar mensajes con API compatible
            try:
                # Método 1: API nueva de langchain 0.1.0
                memory.chat_memory.messages = messages_from_dict(serialized_messages)
            except Exception:
                # Método 2: Fallback - recrear memoria vacía si falla
                print(f"WARNING:  No se pudieron cargar mensajes históricos para usuario {user_id}")
                return True, memory  # Retornar memoria vacía pero válida
        except Exception as e:
            print(f"WARNING:  Error al convertir mensajes para usuario {user_id}: {e}")
            return False, None
        
        return True, memory
        
    except json.JSONDecodeError as e:
        print(f"WARNING:  JSON corrupto para usuario {user_id} en {file_path}: {e}")
        return False, None
    except Exception as e:
        print(f"WARNING:  Error al leer archivo de memoria para usuario {user_id}: {e}")
        return False, None

def load_user_memory(user_id: str) -> ConversationBufferMemory:
    """Carga la memoria del usuario con recuperación robusta desde archivo principal y backup"""
    memory_path = _get_memory_file_path(user_id)
    backup_path = _get_backup_memory_file_path(user_id)
    
    # Intento 1: Cargar desde archivo principal
    success, memory = _try_load_memory_from_file(memory_path, user_id)
    if success and memory:
        print(f"OK: Memoria cargada desde archivo principal para usuario: {user_id}")
        return memory
    
    # Intento 2: Cargar desde backup si el archivo principal falló
    if os.path.exists(backup_path):
        print(f"🔄 Intentando recuperar desde backup para usuario: {user_id}")
        success, memory = _try_load_memory_from_file(backup_path, user_id)
        if success and memory:
            print(f"OK: Memoria recuperada desde backup para usuario: {user_id}")
            # Intentar restaurar el archivo principal desde backup
            try:
                import shutil
                shutil.copy2(backup_path, memory_path)
                print(f"🔧 Archivo principal restaurado desde backup para usuario: {user_id}")
            except Exception as e:
                print(f"WARNING:  No se pudo restaurar archivo principal para usuario {user_id}: {e}")
            return memory
    
    # Intento 3: Si todo falló, crear memoria nueva
    print(f"🆕 Creando memoria nueva para usuario: {user_id}")
    memory = _create_fresh_memory(user_id)
    
    # Guardar la memoria nueva
    if save_user_memory(user_id, memory):
        print(f"OK: Memoria nueva guardada para usuario: {user_id}")
    else:
        print(f"WARNING:  No se pudo guardar memoria nueva para usuario: {user_id}")
    
    return memory

# Funciones utilitarias para mantenimiento del sistema de memoria
def cleanup_corrupted_memory_files():
    """Limpia archivos de memoria corruptos y crea logs de problemas encontrados"""
    if not os.path.exists(MEMORY_DIR):
        return
    
    corrupted_files = []
    cleaned_count = 0
    
    try:
        for filename in os.listdir(MEMORY_DIR):
            if filename.endswith('.json') and not filename.endswith('_backup.json'):
                file_path = os.path.join(MEMORY_DIR, filename)
                try:
                    # Intentar validar el JSON
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    corrupted_files.append((filename, str(e)))
                    # Mover archivo corrupto a una carpeta de archivos problemáticos
                    try:
                        corrupted_dir = os.path.join(MEMORY_DIR, 'corrupted')
                        os.makedirs(corrupted_dir, exist_ok=True)
                        corrupted_path = os.path.join(corrupted_dir, f"{filename}.{int(datetime.utcnow().timestamp())}")
                        import shutil
                        shutil.move(file_path, corrupted_path)
                        cleaned_count += 1
                    except Exception as move_error:
                        print(f"WARNING:  No se pudo mover archivo corrupto {filename}: {move_error}")
        
        if corrupted_files:
            print(f"🧹 Limpieza de memoria: {cleaned_count} archivos corruptos movidos")
            for filename, error in corrupted_files[:5]:  # Solo mostrar primeros 5
                print(f"   - {filename}: {error}")
        else:
            print("OK: Todos los archivos de memoria están en buen estado")
            
    except Exception as e:
        print(f"ERROR: Error durante limpieza de archivos de memoria: {e}")

def get_memory_system_health() -> dict:
    """Obtiene estadísticas de salud del sistema de memoria"""
    if not os.path.exists(MEMORY_DIR):
        return {"status": "error", "message": "Directorio de memoria no existe"}
    
    try:
        stats = {
            "status": "healthy",
            "total_files": 0,
            "backup_files": 0,
            "corrupted_files": 0,
            "total_size_mb": 0,
            "oldest_file": None,
            "newest_file": None
        }
        
        oldest_time = None
        newest_time = None
        
        for filename in os.listdir(MEMORY_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(MEMORY_DIR, filename)
                file_stat = os.stat(file_path)
                stats["total_size_mb"] += file_stat.st_size / (1024 * 1024)
                
                # Rastrear archivos más antiguos y nuevos
                if oldest_time is None or file_stat.st_mtime < oldest_time:
                    oldest_time = file_stat.st_mtime
                    stats["oldest_file"] = filename
                if newest_time is None or file_stat.st_mtime > newest_time:
                    newest_time = file_stat.st_mtime
                    stats["newest_file"] = filename
                
                if filename.endswith('_backup.json'):
                    stats["backup_files"] += 1
                else:
                    stats["total_files"] += 1
                    # Verificar si está corrupto
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                    except:
                        stats["corrupted_files"] += 1
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        if stats["corrupted_files"] > 0:
            stats["status"] = "warning"
        
        return stats
        
    except Exception as e:
        return {"status": "error", "message": f"Error al obtener estadísticas: {e}"}

# Ejecutar validaciones de sistema al inicio
print("[VERIFYING] Verificando salud del sistema de memoria...")
cleanup_corrupted_memory_files()
memory_health = get_memory_system_health()
print(f"[STATUS] Estado memoria: {memory_health['status']} | Archivos: {memory_health.get('total_files', 0)} | Tamaño: {memory_health.get('total_size_mb', 0)} MB")


# Funciones de validación robusta para datos de reserva
import re
from datetime import datetime, date, timedelta

def validate_guest_names(names_data) -> tuple[bool, list, str]:
    """Valida y normaliza los nombres de huéspedes"""
    try:
        if not names_data:
            return False, [], "No se proporcionaron nombres de huéspedes"
        
        # Convertir a lista si es string
        if isinstance(names_data, str):
            # Dividir por comas, "y", "&" o saltos de línea
            names_data = re.split(r'[,&\n]|\s+y\s+', names_data)
        
        if not isinstance(names_data, list):
            return False, [], "Formato de nombres inválido"
        
        validated_names = []
        for name in names_data:
            if not name or not isinstance(name, str):
                continue
                
            # Limpiar y normalizar nombre
            clean_name = re.sub(r'[^\w\sáéíóúñü.-]', '', name.strip(), flags=re.IGNORECASE)
            clean_name = ' '.join(clean_name.split())  # Normalizar espacios
            
            # Validar longitud y formato
            if len(clean_name) < 2:
                continue
            if len(clean_name) > 100:
                clean_name = clean_name[:100]
            
            # Verificar que tenga al menos una letra
            if not re.search(r'[a-záéíóúñü]', clean_name, re.IGNORECASE):
                continue
                
            # Capitalizar correctamente
            clean_name = ' '.join(word.capitalize() for word in clean_name.split())
            validated_names.append(clean_name)
        
        if not validated_names:
            return False, [], "No se encontraron nombres válidos"
        
        # Limitar a máximo 10 huéspedes
        if len(validated_names) > 10:
            validated_names = validated_names[:10]
            return True, validated_names, f"Se limitó a 10 huéspedes (máximo permitido)"
        
        return True, validated_names, f"OK: {len(validated_names)} nombre(s) validado(s)"
        
    except Exception as e:
        return False, [], f"Error al validar nombres: {str(e)}"

def parse_flexible_date(date_str: str) -> tuple[bool, date, str]:
    """Parse flexible de fechas que acepta múltiples formatos"""
    if not date_str or not isinstance(date_str, str):
        return False, None, "Fecha no proporcionada"
    
    # Limpiar la fecha
    clean_date = date_str.strip().replace('/', '-').replace('.', '-').replace(' ', '')
    
    # Formatos de fecha soportados
    date_formats = [
        "%Y-%m-%d",      # 2024-12-25
        "%d-%m-%Y",      # 25-12-2024  
        "%m-%d-%Y",      # 12-25-2024
        "%d-%m-%y",      # 25-12-24
        "%m-%d-%y",      # 12-25-24
        "%Y-%d-%m",      # 2024-25-12
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(clean_date, fmt).date()
            
            # Validar que la fecha sea razonable
            today = date.today()
            min_date = today  # No fechas pasadas
            max_date = today + timedelta(days=365)  # Máximo 1 año en el futuro
            
            if parsed_date < min_date:
                return False, None, f"La fecha {parsed_date.strftime('%d/%m/%Y')} ya pasó"
            
            if parsed_date > max_date:
                return False, None, f"La fecha {parsed_date.strftime('%d/%m/%Y')} está muy lejos (máximo 1 año)"
            
            return True, parsed_date, f"OK: Fecha válida: {parsed_date.strftime('%d/%m/%Y')}"
            
        except ValueError:
            continue
    
    # Si ningún formato funcionó, intentar parsing inteligente
    try:
        # Buscar números en el string
        numbers = re.findall(r'\d+', clean_date)
        if len(numbers) == 3:
            # Intentar diferentes combinaciones
            day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
            
            # Determinar el año completo si es de 2 dígitos
            if year < 100:
                if year < 30:
                    year += 2000
                else:
                    year += 1900
            
            # Intentar día/mes/año y mes/día/año
            possible_dates = []
            try:
                if 1 <= day <= 31 and 1 <= month <= 12:
                    possible_dates.append((day, month, year))
            except:
                pass
            try:
                if 1 <= month <= 31 and 1 <= day <= 12:
                    possible_dates.append((month, day, year))
            except:
                pass
            
            for d, m, y in possible_dates:
                try:
                    parsed_date = date(y, m, d)
                    today = date.today()
                    if today <= parsed_date <= today + timedelta(days=365):
                        return True, parsed_date, f"OK: Fecha interpretada: {parsed_date.strftime('%d/%m/%Y')}"
                except ValueError:
                    continue
                    
    except Exception as e:
        pass
    
    return False, None, f"No se pudo interpretar la fecha '{date_str}'. Use formato DD/MM/AAAA"

def validate_date_range(fecha_entrada: date, fecha_salida: date) -> tuple[bool, str]:
    """Valida que el rango de fechas sea lógico"""
    try:
        if not fecha_entrada or not fecha_salida:
            return False, "Fechas de entrada y salida requeridas"
        
        if fecha_salida <= fecha_entrada:
            return False, f"La fecha de salida ({fecha_salida.strftime('%d/%m/%Y')}) debe ser posterior a la de entrada ({fecha_entrada.strftime('%d/%m/%Y')})"
        
        # Calcular duración de estadía
        duration = (fecha_salida - fecha_entrada).days
        
        if duration > 30:
            return False, f"La estadía de {duration} días es muy larga (máximo 30 días)"
        
        return True, f"OK: Estadía de {duration} día(s) válida"
        
    except Exception as e:
        return False, f"Error al validar fechas: {str(e)}"

def validate_contact_info(phone: str, email: str) -> tuple[bool, str, str, list]:
    """Valida información de contacto"""
    errors = []
    clean_phone = phone.strip() if phone else ""
    clean_email = email.strip().lower() if email else ""
    
    # Validar teléfono
    if clean_phone:
        # Limpiar teléfono (solo números, +, espacios, guiones, paréntesis)
        clean_phone = re.sub(r'[^\d+\s()-]', '', clean_phone)
        clean_phone = re.sub(r'\s+', '', clean_phone)  # Quitar espacios
        
        # Debe tener entre 7 y 15 dígitos
        digits_only = re.sub(r'[^\d]', '', clean_phone)
        if len(digits_only) < 7 or len(digits_only) > 15:
            errors.append("Teléfono debe tener entre 7 y 15 dígitos")
    else:
        errors.append("Teléfono requerido")
    
    # Validar email
    if clean_email and clean_email != "n/a":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, clean_email):
            errors.append("Email inválido")
    
    success = len(errors) == 0
    return success, clean_phone, clean_email, errors

#Funcion para guardar los datos de reserva en Pinecone con manejo de errores
def save_reservation_to_pinecone(user_phone_number, reservation_data):
    """Guarda reserva en Pinecone con manejo robusto de errores"""
    try:
        # Validar datos antes de guardar
        if not reservation_data or not user_phone_number:
            print(f"WARNING:  Datos de reserva incompletos para Pinecone")
            return False
        
        # Convierte los datos de reserva a un string para vectorizar
        reserva_text = json.dumps(reservation_data, ensure_ascii=False)
        
        # Obtén el embedding del texto de la reserva
        embedder = OpenAIEmbeddings()
        vector = embedder.embed_query(reserva_text)
        
        # Usa el número de teléfono como ID único
        pinecone_index.upsert([(user_phone_number, vector, reservation_data)])
        print(f"OK: Reserva guardada en Pinecone para {user_phone_number}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error al guardar en Pinecone para {user_phone_number}: {e}")
        return False

def parse_reservation_details(user_input):
    """Parsea detalles de reserva con LLM robusto y manejo de errores"""
    prompt = f"""
    Extrae los siguientes datos de la solicitud de reserva del usuario. Analiza línea por línea.
    
    FORMATO TÍPICO DE ENTRADA:
    Línea 1: Nombres de huéspedes (separados por comas o "y")
    Línea 2: Tipo de domo (Luna, Sol, Centaury, etc.)
    Línea 3: Fechas (formato DD/MM/AAAA hasta DD/MM/AAAA)
    Línea 4: Servicios adicionales
    Línea 5: Adiciones especiales (mascotas, etc.)
    Línea 6: Número de teléfono
    Línea 7: Email
    
    INSTRUCCIONES IMPORTANTES:
    - Los nombres de huéspedes están en la PRIMERA línea
    - El tipo de domo está en una línea SEPARADA (Luna, Sol, Centaury, etc.)
    - Si dice "voy con X personas más", cuenta el solicitante + X acompañantes
    - Si dice "somos X personas", usa ese número total
    - Responde SOLO con JSON válido, sin texto adicional

    Solicitud del usuario: "{user_input}"

    Formato de salida JSON requerido:
    {{
        "nombres_huespedes": ["Nombre Completo 1", "Nombre Completo 2"],
        "numero_acompanantes": "número_total_de_acompañantes_incluyendo_solicitante",
        "domo": "Tipo de Domo",
        "fecha_entrada": "fecha_entrada_del_usuario",
        "fecha_salida": "fecha_salida_del_usuario", 
        "servicio_elegido": "Servicio Adicional",
        "adicciones": "Adicciones (ej. mascota, otro servicio)",
        "numero_contacto": "Numero de Telefono",
        "email_contacto": "Correo Electronico",
        "metodo_pago": "Forma de pago (efectivo, transferencia, tarjeta, etc.)",
        "comentarios_especiales": "Solicitudes especiales o comentarios adicionales"
    }}
    """
    
    # Usar función robusta para llamar al LLM
    success, response_text, error_msg = call_llm_with_retry(prompt, max_retries=3)
    
    if not success:
        print(f"ERROR: Error al llamar al LLM para parsing: {error_msg}")
        return None
    
    # Usar función robusta para parsear JSON
    json_success, parsed_json, json_error = parse_llm_json_safe(response_text)
    
    if not json_success:
        print(f"ERROR: Error al parsear JSON: {json_error}")
        return None
    
    # Validar estructura básica del JSON
    required_fields = ["nombres_huespedes", "domo", "fecha_entrada", "fecha_salida"]
    optional_fields = ["numero_acompanantes", "servicio_elegido", "adicciones", "numero_contacto", "email_contacto", "metodo_pago", "comentarios_especiales"]
    
    missing_fields = [field for field in required_fields if field not in parsed_json]
    
    if missing_fields:
        print(f"WARNING:  JSON incompleto, faltan campos: {missing_fields}")
        # Agregar campos faltantes con valores por defecto
        for field in missing_fields:
            if field == "nombres_huespedes":
                parsed_json[field] = []
            else:
                parsed_json[field] = "N/A"
    
    # Agregar campos opcionales faltantes con valores por defecto
    for field in optional_fields:
        if field not in parsed_json:
            if field == "numero_acompanantes":
                parsed_json[field] = "N/A"
            elif field in ["servicio_elegido", "adicciones"]:
                parsed_json[field] = "ninguno"
            else:
                parsed_json[field] = "N/A"
    
    print("OK: Datos de reserva parseados exitosamente")
    return parsed_json

def validate_and_process_reservation_data(parsed_data, from_number) -> tuple[bool, dict, list]:
    """Valida y procesa datos de reserva usando funciones robustas"""
    errors = []
    processed_data = {}
    
    try:
        # 1. Validar nombres de huéspedes
        names_valid, validated_names, names_msg = validate_guest_names(parsed_data.get("nombres_huespedes", []))
        if not names_valid:
            errors.append(f"Nombres: {names_msg}")
        else:
            processed_data["nombres_huespedes"] = validated_names
            
            # Usar numero_acompanantes si está disponible, sino contar nombres
            numero_acompanantes = parsed_data.get("numero_acompanantes")
            if numero_acompanantes and str(numero_acompanantes).isdigit():
                processed_data["cantidad_huespedes"] = int(numero_acompanantes)
                print(f"ℹ️  Número de acompañantes especificado: {numero_acompanantes}")
            else:
                processed_data["cantidad_huespedes"] = len(validated_names)
                print(f"ℹ️  {names_msg}")
        
        # 2. Validar domo
        domo = parsed_data.get("domo", "").strip()
        if not domo or domo.lower() in ["n/a", "na", "ninguno"]:
            errors.append("Domo: Tipo de domo requerido")
        else:
            processed_data["domo"] = domo
        
        # 3. Validar fechas con parsing flexible
        fecha_entrada_str = parsed_data.get("fecha_entrada", "")
        fecha_salida_str = parsed_data.get("fecha_salida", "")
        
        entrada_valid, fecha_entrada, entrada_msg = parse_flexible_date(fecha_entrada_str)
        salida_valid, fecha_salida, salida_msg = parse_flexible_date(fecha_salida_str)
        
        if not entrada_valid:
            errors.append(f"Fecha entrada: {entrada_msg}")
        if not salida_valid:
            errors.append(f"Fecha salida: {salida_msg}")
        
        if entrada_valid and salida_valid:
            # Validar rango de fechas
            range_valid, range_msg = validate_date_range(fecha_entrada, fecha_salida)
            if not range_valid:
                errors.append(f"Fechas: {range_msg}")
            else:
                processed_data["fecha_entrada"] = fecha_entrada.isoformat()
                processed_data["fecha_salida"] = fecha_salida.isoformat()
                print(f"ℹ️  {range_msg}")
        
        # 4. Validar información de contacto
        phone = parsed_data.get("numero_contacto", "")
        email = parsed_data.get("email_contacto", "")
        
        # Usar número de WhatsApp como fallback para teléfono
        if not phone or phone.lower() in ["n/a", "na"]:
            phone = from_number.replace("whatsapp:", "") if from_number else ""
        
        contact_valid, clean_phone, clean_email, contact_errors = validate_contact_info(phone, email)
        if not contact_valid:
            errors.extend([f"Contacto: {err}" for err in contact_errors])
        else:
            processed_data["numero_contacto"] = clean_phone
            processed_data["email_contacto"] = clean_email if clean_email else "N/A"
        
        # 5. Validar servicios y adiciones (campos opcionales)
        servicio = parsed_data.get("servicio_elegido", "ninguno").strip()
        processed_data["servicio_elegido"] = servicio if servicio and servicio.lower() not in ["n/a", "na"] else "ninguno"
        
        adicciones = parsed_data.get("adicciones", "ninguno").strip()
        processed_data["adicciones"] = adicciones if adicciones and adicciones.lower() not in ["n/a", "na"] else "ninguno"
        
        # Determinar si la validación fue exitosa
        success = len(errors) == 0
        return success, processed_data, errors
        
    except Exception as e:
        errors.append(f"Error inesperado en validación: {str(e)}")
        return False, {}, errors

# Funciones de manejo robusto del LLM y agente conversacional
def test_llm_connection() -> tuple[bool, str]:
    """Prueba la conexión con OpenAI LLM"""
    try:
        # Hacer una consulta simple para probar la conexión
        test_response = llm("Responde solo: 'OK'")
        if test_response and len(test_response.strip()) > 0:
            print("OK: Conexión LLM OpenAI verificada")
            return True, "Conexión exitosa"
        else:
            print("WARNING:  Conexión LLM OpenAI: respuesta vacía")
            return False, "Respuesta vacía del LLM"
    except Exception as e:
        error_msg = f"Error de conexión LLM: {str(e)}"
        print(f"ERROR: {error_msg}")
        return False, error_msg

def call_llm_with_retry(prompt: str, max_retries: int = 3, temperature: float = 0) -> tuple[bool, str, str]:
    """Llama al LLM con reintentos automáticos y manejo de errores"""
    last_error = ""
    
    for attempt in range(max_retries):
        try:
            # Validar prompt
            if not prompt or len(prompt.strip()) == 0:
                return False, "", "Prompt vacío"
            
            # Truncar prompt si es muy largo (límite aproximado de OpenAI)
            if len(prompt) > 3500:
                prompt = prompt[:3500] + "\n[Prompt truncado para evitar límites]"
            
            # Llamar al LLM
            response = llm(prompt)
            
            # Validar respuesta
            if not response:
                last_error = "Respuesta vacía del LLM"
                continue
                
            response = response.strip()
            if len(response) == 0:
                last_error = "Respuesta vacía después de limpiar"
                continue
                
            print(f"OK: LLM respondió exitosamente (intento {attempt + 1})")
            return True, response, "Éxito"
            
        except Exception as e:
            last_error = f"Error en intento {attempt + 1}: {str(e)}"
            print(f"WARNING:  {last_error}")
            
            # Si es error de rate limit, esperar un poco más
            if "rate limit" in str(e).lower():
                import time
                time.sleep(2 ** attempt)  # Backoff exponencial
            
            if attempt < max_retries - 1:
                continue
    
    # Si llegamos aquí, todos los intentos fallaron
    return False, "", last_error

def parse_llm_json_safe(llm_response: str) -> tuple[bool, dict, str]:
    """Parsea JSON del LLM con múltiples estrategias de recuperación"""
    try:
        # Estrategia 1: JSON directo
        try:
            parsed = json.loads(llm_response)
            return True, parsed, "JSON parseado exitosamente"
        except json.JSONDecodeError:
            pass
        
        # Estrategia 2: Buscar JSON entre llaves
        import re
        json_pattern = r'\{[^{}]*\}'
        json_matches = re.findall(json_pattern, llm_response, re.DOTALL)
        
        for match in json_matches:
            try:
                parsed = json.loads(match)
                print("OK: JSON extraído de respuesta del LLM")
                return True, parsed, "JSON extraído exitosamente"
            except json.JSONDecodeError:
                continue
        
        # Estrategia 3: Buscar JSON más complejo (con objetos anidados)
        json_pattern_nested = r'\{.*\}'
        match = re.search(json_pattern_nested, llm_response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                print("OK: JSON anidado extraído de respuesta del LLM")
                return True, parsed, "JSON anidado extraído"
            except json.JSONDecodeError:
                pass
        
        # Estrategia 4: Limpiar y reintentar
        cleaned_response = llm_response.replace('\n', '').replace('\r', '').strip()
        try:
            parsed = json.loads(cleaned_response)
            print("OK: JSON parseado después de limpiar")
            return True, parsed, "JSON parseado después de limpieza"
        except json.JSONDecodeError:
            pass
        
        # Si todo falla, retornar error descriptivo
        return False, {}, f"No se pudo parsear JSON. Respuesta LLM: '{llm_response[:200]}...'"
        
    except Exception as e:
        return False, {}, f"Error inesperado parseando JSON: {str(e)}"

def initialize_agent_safe(tools, memory, max_retries: int = 3):
    """Inicializa el agente conversacional con manejo robusto de errores"""
    last_error = ""
    
    for attempt in range(max_retries):
        try:
            # Usar la API más moderna de LangChain para agentes
            try:
                # Método 1: API nueva con create_conversational_retrieval_agent
                from langchain.agents import create_conversational_retrieval_agent
                agent = create_conversational_retrieval_agent(
                    llm=llm,
                    tools=tools,
                    memory=memory,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3
                )
                print(f"OK: Agente moderno inicializado correctamente (intento {attempt + 1})")
                return True, agent, "Agente moderno inicializado exitosamente"
            except (ImportError, AttributeError):
                # Fallback al método tradicional si el método moderno no está disponible
                agent = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                    memory=memory,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3,
                    early_stopping_method="generate"
                )
                print(f"OK: Agente tradicional inicializado correctamente (intento {attempt + 1})")
                return True, agent, "Agente tradicional inicializado exitosamente"
            
        except Exception as e:
            last_error = f"Error inicializando agente (intento {attempt + 1}): {str(e)}"
            print(f"ERROR: {last_error}")
            
            if attempt < max_retries - 1:
                continue
    
    return False, None, last_error

def run_agent_safe(agent, user_input: str, max_retries: int = 2) -> tuple[bool, str, str]:
    """Ejecuta el agente con manejo robusto de errores"""
    last_error = ""
    
    for attempt in range(max_retries):
        try:
            # Validar input
            if not user_input or len(user_input.strip()) == 0:
                return False, "Entrada vacía", "Input del usuario vacío"
            
            # Truncar input si es muy largo
            if len(user_input) > 1000:
                user_input = user_input[:1000] + " [mensaje truncado]"
            
            # Ejecutar agente con método moderno
            try:
                # Intentar método invoke primero (LangChain 0.1.0+)
                if hasattr(agent, 'invoke'):
                    agent_result = agent.invoke({"input": user_input})
                    # Extraer la respuesta del resultado estructurado
                    if isinstance(agent_result, dict):
                        result = agent_result.get('output', agent_result.get('result', str(agent_result)))
                    else:
                        result = str(agent_result)
                else:
                    # Fallback al método run tradicional
                    result = agent.run(input=user_input)
            except Exception as e:
                # Si falla invoke, intentar run
                result = agent.run(input=user_input)
            
            # Validar resultado
            if not result:
                last_error = "Agente retornó resultado vacío"
                continue
                
            result = str(result).strip()
            if len(result) == 0:
                last_error = "Resultado vacío después de limpiar"
                continue
            
            print(f"OK: Agente ejecutado exitosamente (intento {attempt + 1})")
            return True, result, "Éxito"
            
        except Exception as e:
            last_error = f"Error ejecutando agente (intento {attempt + 1}): {str(e)}"
            print(f"WARNING:  {last_error}")
            
            # Manejar errores específicos
            if "parsing" in str(e).lower():
                # Error de parsing - puede ser temporal
                continue
            elif "rate limit" in str(e).lower():
                # Rate limit - esperar
                import time
                time.sleep(2 ** attempt)
                continue
            elif "timeout" in str(e).lower():
                # Timeout - reintentar con input más corto
                if len(user_input) > 500:
                    user_input = user_input[:500] + " [truncado por timeout]"
                continue
            
            if attempt < max_retries - 1:
                continue
    
    # Si todos los intentos fallaron
    return False, "", last_error


# VALIDACIONES DE SISTEMA AL INICIALIZAR (después de definir todas las funciones)

print("[TESTING] Probando conexión con LLM OpenAI...")
try:
    llm_success, llm_msg = test_llm_connection()
    if llm_success:
        print(f"[STATUS] Estado LLM: OK: {llm_msg}")
    else:
        print(f"[STATUS] Estado LLM: ERROR: {llm_msg}")
        print("WARNING:  El sistema continuará, pero funcionalidad conversacional puede estar limitada")
except Exception as e:
    print(f"ERROR: Error inesperado probando LLM: {e}")
    print("WARNING:  El sistema continuará, pero funcionalidad conversacional puede estar limitada")

print("[STARTING] Sistema inicializado - Iniciando rutas Flask...")

# Rutas Flask para manejo de WhatsApp
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
        resp.message("🔄 Procesando tu solicitud de reserva, por favor espera un momento...")
        
        # Parsear datos con LLM
        parsed_data = parse_reservation_details(incoming_msg)

        if parsed_data:
            # Validar y procesar datos con funciones robustas
            validation_success, processed_data, validation_errors = validate_and_process_reservation_data(parsed_data, from_number)
            
            if validation_success:
                # Datos válidos - mostrar confirmación
                user_state["reserva_data"] = processed_data
                
                # Calcular precio para mostrar en confirmación
                fecha_entrada = datetime.fromisoformat(processed_data['fecha_entrada']).date()
                fecha_salida = datetime.fromisoformat(processed_data['fecha_salida']).date()
                
                calculo_precio = calcular_precio_reserva(
                    domo=processed_data['domo'],
                    cantidad_huespedes=processed_data['cantidad_huespedes'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicios_adicionales=processed_data.get('adicciones', '')
                )
                
                reserva_info = processed_data
                confirmation_msg = (
                    "OK: ¡Perfecto! Aquí está el resumen de tu reserva:\n\n"
                    f"👥 **Huéspedes:** {', '.join(reserva_info['nombres_huespedes'])} ({reserva_info['cantidad_huespedes']} personas)\n"
                    f"🏡 **Domo:** {reserva_info['domo']}\n"
                    f"🍽️ **Servicio:** {reserva_info['servicio_elegido']}\n"
                    f"➕ **Adiciones:** {reserva_info['adicciones']}\n"
                    f"📅 **Entrada:** {datetime.fromisoformat(reserva_info['fecha_entrada']).strftime('%d/%m/%Y')}\n"
                    f"📅 **Salida:** {datetime.fromisoformat(reserva_info['fecha_salida']).strftime('%d/%m/%Y')}\n"
                    f"📞 **Teléfono:** {reserva_info['numero_contacto']}\n"
                    f"📧 **Email:** {reserva_info['email_contacto']}\n"
                    f"💰 **Precio Total:** ${calculo_precio['precio_total']:,} COP\n"
                    f"💳 **Método de Pago:** {reserva_info.get('metodo_pago', 'No especificado')}\n"
                    f"📝 **Comentarios:** {reserva_info.get('comentarios_especiales', 'Ninguno')}\n\n"
                    "❓ **¿Confirmas esta reserva?** (Responde: *Sí* o *No*)"
                )

                resp.message(confirmation_msg)
                user_state["reserva_step"] = 2
                
            else:
                # Errores de validación - dar feedback específico
                error_msg = (
                    "ERROR: **Encontré algunos problemas con la información proporcionada:**\n\n"
                )
                
                for i, error in enumerate(validation_errors, 1):
                    error_msg += f"{i}. {error}\n"
                
                error_msg += (
                    "\n[TIP] **Por favor, envía la información corregida incluyendo:**\n"
                    "• Nombres completos de huéspedes\n"
                    "• Tipo de domo que deseas\n"
                    "• Fechas de entrada y salida (DD/MM/AAAA)\n"
                    "• Servicios adicionales que quieras\n"
                    "• Adiciones especiales (ej. mascota)\n"
                    "• Teléfono de contacto\n"
                    "• Email de contacto\n\n"
                    "✏️ **Escribe toda la información en un solo mensaje.**"
                )
                
                resp.message(error_msg)
                # No resetear el flujo - dar otra oportunidad
                
        else:
            # Error en el parsing del LLM
            resp.message(
                "ERROR: **No pude interpretar tu solicitud de reserva.**\n\n"
                "[TIP] **Por favor, asegúrate de incluir toda la información:**\n"
                "• Nombres completos de huéspedes\n"
                "• Tipo de domo que deseas\n"
                "• Fechas de entrada y salida (DD/MM/AAAA)\n"
                "• Servicios adicionales que quieras\n"
                "• Adiciones especiales (ej. mascota)\n"
                "• Teléfono de contacto\n"
                "• Email de contacto\n\n"
                "✏️ **Ejemplo:** \"Juan Pérez y María González, domo Luna, 25/12/2024 hasta 27/12/2024, cena romántica, sin mascotas, 3001234567, juan@email.com\""
            )
            # No resetear - dar otra oportunidad
        
        save_user_memory(from_number, memory)
        return str(resp)

    if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
        if incoming_msg.lower() in ["si", "sí"]:
            try:
                reservation_data = user_state["reserva_data"]
                
                # Convertir fechas de string a objeto date
                fecha_entrada = datetime.fromisoformat(reservation_data['fecha_entrada']).date()
                fecha_salida = datetime.fromisoformat(reservation_data['fecha_salida']).date()
                
                # Calcular precio total de la reserva
                calculo_precio = calcular_precio_reserva(
                    domo=reservation_data['domo'],
                    cantidad_huespedes=reservation_data['cantidad_huespedes'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicios_adicionales=reservation_data.get('adicciones', '')
                )
                
                # Crear nueva reserva en la base de datos
                nueva_reserva = Reserva(
                    numero_whatsapp=from_number.replace("whatsapp:", ""),
                    nombres_huespedes=', '.join(reservation_data['nombres_huespedes']),
                    cantidad_huespedes=reservation_data['cantidad_huespedes'],
                    domo=reservation_data['domo'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicio_elegido=reservation_data['servicio_elegido'],
                    adicciones=reservation_data['adicciones'],
                    numero_contacto=reservation_data['numero_contacto'],
                    email_contacto=reservation_data['email_contacto'],
                    metodo_pago=reservation_data.get('metodo_pago', 'No especificado'),
                    monto_total=calculo_precio['precio_total'],
                    comentarios_especiales=reservation_data.get('comentarios_especiales', '')
                )
                
                # Guardar en la base de datos con manejo robusto
                try:
                    db.session.add(nueva_reserva)
                    db.session.commit()
                    print(f"OK: Reserva guardada en PostgreSQL - ID: {nueva_reserva.id}")
                    
                    # También guardar en Pinecone
                    pinecone_success = save_reservation_to_pinecone(from_number, reservation_data)
                    
                    success_msg = "🎉 ¡Reserva confirmada y guardada exitosamente!\n\n"
                    success_msg += f"📋 **Número de reserva:** {nueva_reserva.id}\n"
                    success_msg += f"📅 **Fechas:** {datetime.fromisoformat(reservation_data['fecha_entrada']).strftime('%d/%m/%Y')} - {datetime.fromisoformat(reservation_data['fecha_salida']).strftime('%d/%m/%Y')}\n"
                    success_msg += f"👥 **Huéspedes:** {reservation_data['cantidad_huespedes']}\n\n"
                    success_msg += "📞 **Nos pondremos en contacto contigo pronto para coordinar los detalles finales.**\n\n"
                    success_msg += "✨ **¡Gracias por elegir Glamping Brillo de Luna!**"
                    
                    if not pinecone_success:
                        success_msg += "\n\nWARNING: *Nota: La reserva se guardó correctamente, pero hubo un problema menor con el sistema de respaldo.*"
                    
                    resp.message(success_msg)
                    
                except Exception as db_error:
                    db.session.rollback()
                    print(f"ERROR: Error al guardar en base de datos: {db_error}")
                    resp.message(
                        "ERROR: **Lo siento, hubo un error al guardar tu reserva.**\n\n"
                        "🔧 **Nuestro sistema técnico está experimentando problemas temporales.**\n\n"
                        "📞 **Por favor:**\n"
                        "• Intenta de nuevo en unos minutos\n"
                        "• O contáctanos directamente por WhatsApp\n"
                        "• Guarda esta conversación como respaldo\n\n"
                        "[TIP] **Tu información está segura y no se perdió.**"
                    )
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

    # Procesamiento normal con el Agente Conversacional robusto (si no hay flujo activo)
    try:
        # Inicializar agente con manejo robusto
        init_success, custom_agent, init_error = initialize_agent_safe(tools, memory, max_retries=3)
        
        if not init_success:
            print(f"ERROR: Error al inicializar agente: {init_error}")
            agent_answer = "Disculpa, nuestro sistema conversacional está experimentando problemas temporales. Por favor, intenta de nuevo en un momento."
        else:
            # Ejecutar agente con manejo robusto
            run_success, result, run_error = run_agent_safe(custom_agent, incoming_msg, max_retries=2)
            
            if run_success:
                agent_answer = result
            else:
                print(f"ERROR: Error ejecutando agente: {run_error}")
                
                # Fallback inteligente basado en el tipo de error
                if "rate limit" in run_error.lower():
                    agent_answer = "[BUSY] Nuestro sistema está un poco ocupado en este momento. Por favor, intenta de nuevo en unos segundos."
                elif "timeout" in run_error.lower():
                    agent_answer = "[TIMEOUT] Tu mensaje está siendo procesado, pero está tomando más tiempo del esperado. ¿Podrías intentar con un mensaje más corto?"
                elif "parsing" in run_error.lower():
                    agent_answer = "[THINKING] Tuve un problema interpretando tu mensaje. ¿Podrías reformularlo de manera más simple?"
                else:
                    agent_answer = "[PROCESSING] Disculpa, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo o ser más específico en tu consulta?"
        
        # Guardar memoria independientemente del resultado
        save_user_memory(from_number, memory)
        
    except Exception as e:
        print(f"ERROR: Error inesperado en procesamiento conversacional: {e}")
        agent_answer = "🔧 Estamos experimentando problemas técnicos temporales. Por favor, intenta contactarnos de nuevo en unos minutos."

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
            "-Domo que quieras reservar\n"
            "-Fecha que quieras asistir y hasta cuando seria tu estadia (Formato DD/MM/AAAA)\n"
            "-Servicios que quieras incluir\n"
            "-Adicciones (Servicios, mascota etc)\n"
            "-Número de teléfono de contacto\n"
            "-Correo electrónico de contacto\n\n"
            "Por favor, escribe toda la información en un solo mensaje."
        )
    elif user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
        # Parsear datos con LLM
        parsed_data = parse_reservation_details(user_input)
        
        if parsed_data:
            # Validar y procesar datos con funciones robustas
            validation_success, processed_data, validation_errors = validate_and_process_reservation_data(parsed_data, session_id)
            
            if validation_success:
                # Datos válidos - mostrar confirmación
                user_state["reserva_data"] = processed_data
                
                # Calcular precio para mostrar en confirmación
                fecha_entrada = datetime.fromisoformat(processed_data['fecha_entrada']).date()
                fecha_salida = datetime.fromisoformat(processed_data['fecha_salida']).date()
                
                calculo_precio = calcular_precio_reserva(
                    domo=processed_data['domo'],
                    cantidad_huespedes=processed_data['cantidad_huespedes'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicios_adicionales=processed_data.get('adicciones', '')
                )
                
                reserva_info = processed_data
                response_output = (
                    "OK: ¡Perfecto! Aquí está el resumen de tu reserva:\n\n"
                    f"👥 Huéspedes: {', '.join(reserva_info['nombres_huespedes'])} ({reserva_info['cantidad_huespedes']} personas)\n"
                    f"🏡 Domo: {reserva_info['domo']}\n"
                    f"🍽️ Servicio: {reserva_info['servicio_elegido']}\n"
                    f"➕ Adiciones: {reserva_info['adicciones']}\n"
                    f"📅 Entrada: {datetime.fromisoformat(reserva_info['fecha_entrada']).strftime('%d/%m/%Y')}\n"
                    f"📅 Salida: {datetime.fromisoformat(reserva_info['fecha_salida']).strftime('%d/%m/%Y')}\n"
                    f"📞 Teléfono: {reserva_info['numero_contacto']}\n"
                    f"📧 Email: {reserva_info['email_contacto']}\n"
                    f"💰 Precio Total: ${calculo_precio['precio_total']:,} COP\n"
                    f"💳 Método de Pago: {reserva_info.get('metodo_pago', 'No especificado')}\n"
                    f"📝 Comentarios: {reserva_info.get('comentarios_especiales', 'Ninguno')}\n\n"
                    "❓ ¿Confirmas esta reserva? (Responde: Sí o No)"
                )
                user_state["reserva_step"] = 2
                
            else:
                # Errores de validación - dar feedback específico
                response_output = "ERROR: Encontré algunos problemas con la información proporcionada:\n\n"
                
                for i, error in enumerate(validation_errors, 1):
                    response_output += f"{i}. {error}\n"
                
                response_output += (
                    "\n[TIP] Por favor, envía la información corregida incluyendo:\n"
                    "• Nombres completos de huéspedes\n"
                    "• Tipo de domo que deseas\n"
                    "• Fechas de entrada y salida (DD/MM/AAAA)\n"
                    "• Servicios adicionales que quieras\n"
                    "• Adiciones especiales (ej. mascota)\n"
                    "• Teléfono de contacto\n"
                    "• Email de contacto\n\n"
                    "✏️ Escribe toda la información en un solo mensaje."
                )
                # No resetear el flujo - dar otra oportunidad
                
        else:
            # Error en el parsing del LLM
            response_output = (
                "ERROR: No pude interpretar tu solicitud de reserva.\n\n"
                "[TIP] Por favor, asegúrate de incluir toda la información:\n"
                "• Nombres completos de huéspedes\n"
                "• Tipo de domo que deseas\n"
                "• Fechas de entrada y salida (DD/MM/AAAA)\n"
                "• Servicios adicionales que quieras\n"
                "• Adiciones especiales (ej. mascota)\n"
                "• Teléfono de contacto\n"
                "• Email de contacto\n\n"
                "✏️ Ejemplo: \"Juan Pérez y María González, domo Luna, 25/12/2024 hasta 27/12/2024, cena romántica, sin mascotas, 3001234567, juan@email.com\""
            )
            # No resetear - dar otra oportunidad

    elif user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
        if user_input.lower() in ["si", "sí"]:
            try:
                reservation_data = user_state["reserva_data"]
                
                # Convertir fechas de string a objeto date
                fecha_entrada = datetime.fromisoformat(reservation_data['fecha_entrada']).date()
                fecha_salida = datetime.fromisoformat(reservation_data['fecha_salida']).date()
                
                # Calcular precio total de la reserva
                calculo_precio = calcular_precio_reserva(
                    domo=reservation_data['domo'],
                    cantidad_huespedes=reservation_data['cantidad_huespedes'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicios_adicionales=reservation_data.get('adicciones', '')
                )
                
                # Crear nueva reserva en la base de datos
                nueva_reserva = Reserva(
                    numero_whatsapp=session_id,  # En /chat usamos session_id como identificador
                    nombres_huespedes=', '.join(reservation_data['nombres_huespedes']),
                    cantidad_huespedes=reservation_data['cantidad_huespedes'],
                    domo=reservation_data['domo'],
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    servicio_elegido=reservation_data['servicio_elegido'],
                    adicciones=reservation_data['adicciones'],
                    numero_contacto=reservation_data['numero_contacto'],
                    email_contacto=reservation_data['email_contacto'],
                    metodo_pago=reservation_data.get('metodo_pago', 'No especificado'),
                    monto_total=calculo_precio['precio_total'],
                    comentarios_especiales=reservation_data.get('comentarios_especiales', '')
                )
                
                # Guardar en la base de datos con manejo robusto
                try:
                    db.session.add(nueva_reserva)
                    db.session.commit()
                    print(f"OK: Reserva guardada en PostgreSQL - ID: {nueva_reserva.id}")
                    
                    # También guardar en Pinecone
                    pinecone_success = save_reservation_to_pinecone(reservation_data["numero_contacto"], reservation_data)
                    
                    response_output = "🎉 ¡Reserva confirmada y guardada exitosamente!\n\n"
                    response_output += f"📋 Número de reserva: {nueva_reserva.id}\n"
                    response_output += f"📅 Fechas: {datetime.fromisoformat(reservation_data['fecha_entrada']).strftime('%d/%m/%Y')} - {datetime.fromisoformat(reservation_data['fecha_salida']).strftime('%d/%m/%Y')}\n"
                    response_output += f"👥 Huéspedes: {reservation_data['cantidad_huespedes']}\n\n"
                    response_output += "📞 Nos pondremos en contacto contigo pronto para coordinar los detalles finales.\n\n"
                    response_output += "✨ ¡Gracias por elegir Glamping Brillo de Luna!"
                    
                    if not pinecone_success:
                        response_output += "\n\nWARNING: Nota: La reserva se guardó correctamente, pero hubo un problema menor con el sistema de respaldo."
                    
                except Exception as db_error:
                    db.session.rollback()
                    print(f"ERROR: Error al guardar en base de datos: {db_error}")
                    response_output = (
                        "ERROR: Lo siento, hubo un error al guardar tu reserva.\n\n"
                        "🔧 Nuestro sistema técnico está experimentando problemas temporales.\n\n"
                        "📞 Por favor:\n"
                        "• Intenta de nuevo en unos minutos\n"
                        "• O contáctanos directamente\n"
                        "• Guarda esta conversación como respaldo\n\n"
                        "[TIP] Tu información está segura y no se perdió."
                    )
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
        # Procesamiento normal con el agente robusto si no hay flujo de reserva activo
        # Inicializar agente con manejo robusto
        init_success, agent, init_error = initialize_agent_safe(tools, memory, max_retries=3)
        
        if not init_success:
            print(f"ERROR: Error al inicializar agente para {session_id}: {init_error}")
            response_output = "Disculpa, nuestro sistema conversacional está experimentando problemas temporales. Por favor, intenta de nuevo en un momento."
        else:
            # Ejecutar agente con manejo robusto
            run_success, result, run_error = run_agent_safe(agent, user_input, max_retries=2)
            
            if run_success:
                response_output = result
            else:
                print(f"ERROR: Error ejecutando agente para {session_id}: {run_error}")
                
                # Fallback inteligente basado en el tipo de error
                if "rate limit" in run_error.lower():
                    response_output = "[BUSY] Nuestro sistema está un poco ocupado en este momento. Por favor, intenta de nuevo en unos segundos."
                elif "timeout" in run_error.lower():
                    response_output = "[TIMEOUT] Tu mensaje está siendo procesado, pero está tomando más tiempo del esperado. ¿Podrías intentar con un mensaje más corto?"
                elif "parsing" in run_error.lower():
                    response_output = "[THINKING] Tuve un problema interpretando tu mensaje. ¿Podrías reformularlo de manera más simple?"
                else:
                    response_output = "[PROCESSING] Disculpa, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo o ser más específico en tu consulta?"
    
    # Añadir mensajes a la memoria con API compatible
    try:
        # Método 1: API nueva de langchain 0.1.0
        from langchain.schema import HumanMessage, AIMessage
        memory.chat_memory.add_message(HumanMessage(content=user_input))
        memory.chat_memory.add_message(AIMessage(content=response_output))
    except (ImportError, AttributeError):
        try:
            # Método 2: API legacy
            memory.chat_memory.add_user_message(user_input)
            memory.chat_memory.add_ai_message(response_output)
        except AttributeError:
            # Método 3: Fallback - no guardar en memoria si falla
            print(f"WARNING:  No se pudo añadir mensaje a la memoria para sesión: {session_id}")
    
    save_user_memory(session_id, memory)

    return jsonify({
        "session_id": session_id,
        "response": response_output,
        "memory": messages_to_dict(memory.chat_memory.messages)
    })

@app.route('/api/reservas', methods=['GET'])
def get_reservas():
    """Endpoint para obtener todas las reservas para el panel de control"""
    try:
        if not db or not Reserva:
            return jsonify({'error': 'Base de datos no disponible'}), 503
            
        reservas = Reserva.query.order_by(Reserva.fecha_creacion.desc()).all()
        reservas_json = []
        
        for reserva in reservas:
            # Procesar servicios
            servicios = []
            if reserva.servicio_elegido and reserva.servicio_elegido.lower() != 'ninguno':
                servicios = [reserva.servicio_elegido]
            
            # Usar el monto calculado si está disponible, o calcular en tiempo real
            monto_total = 0
            if hasattr(reserva, 'monto_total') and reserva.monto_total:
                monto_total = reserva.monto_total
            elif reserva.domo and reserva.fecha_entrada and reserva.fecha_salida:
                # Calcular precio usando la función de pricing
                calculo_precio = calcular_precio_reserva(
                    domo=reserva.domo,
                    cantidad_huespedes=reserva.cantidad_huespedes,
                    fecha_entrada=reserva.fecha_entrada,
                    fecha_salida=reserva.fecha_salida,
                    servicios_adicionales=reserva.adicciones
                )
                monto_total = calculo_precio['precio_total']
            
            reserva_data = {
                'id': f"RSV-{reserva.id:03d}",
                'nombre': reserva.nombres_huespedes,
                'numero': reserva.numero_whatsapp,
                'email': reserva.email_contacto or 'No proporcionado',
                'numeroPersonas': reserva.cantidad_huespedes,
                'fechaEntrada': reserva.fecha_entrada.isoformat() if reserva.fecha_entrada else None,
                'fechaSalida': reserva.fecha_salida.isoformat() if reserva.fecha_salida else None,
                'domo': reserva.domo or 'No especificado',
                'servicios': servicios,
                'montoAPagar': monto_total,
                'metodoPago': getattr(reserva, 'metodo_pago', 'No especificado') or 'Pendiente',
                'observaciones': reserva.adicciones or '',
                'comentariosEspeciales': getattr(reserva, 'comentarios_especiales', '') or '',
                'fechaCreacion': reserva.fecha_creacion.isoformat()
            }
            reservas_json.append(reserva_data)
            
        return jsonify({
            'success': True,
            'total': len(reservas_json),
            'reservas': reservas_json
        })
        
    except Exception as e:
        print(f"ERROR en /api/reservas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para monitoreo"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if database_available else 'disconnected'
    })

@app.route('/api/reservas', methods=['POST'])
def create_reserva():
    """Crear nueva reserva desde panel admin"""
    if not database_available:
        return jsonify({'error': 'Base de datos no disponible'}), 503

    try:
        data = request.get_json()

        # Calcular precio total si no se proporciona
        monto_total = data.get('montoAPagar', 0)
        if not monto_total and data.get('domo') and data.get('fechaEntrada') and data.get('fechaSalida'):
            calculo_precio = calcular_precio_reserva(
                domo=data['domo'],
                cantidad_huespedes=data['numeroPersonas'],
                fecha_entrada=data['fechaEntrada'],
                fecha_salida=data['fechaSalida'],
                servicios_adicionales=', '.join([s.get('nombre', '') for s in data.get('servicios', [])])
            )
            monto_total = calculo_precio['precio_total']

        nueva_reserva = Reserva(
            numero_whatsapp=data.get('numero', ''),
            nombres_huespedes=data['nombre'],
            cantidad_huespedes=data['numeroPersonas'],
            domo=data['domo'],
            fecha_entrada=datetime.fromisoformat(data['fechaEntrada']).date(),
            fecha_salida=datetime.fromisoformat(data['fechaSalida']).date(),
            servicio_elegido=', '.join([s.get('nombre', '') for s in data.get('servicios', [])]),
            numero_contacto=data.get('numero', ''),
            email_contacto=data.get('email', ''),
            metodo_pago=data.get('metodoPago', 'No especificado'),
            monto_total=monto_total,
            comentarios_especiales=data.get('comentariosEspeciales', '')
        )

        db.session.add(nueva_reserva)
        db.session.commit()

        return jsonify({
            'id': f"RSV-{nueva_reserva.id:03d}",
            'message': 'Reserva creada exitosamente'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservas/<reserva_id>', methods=['PUT'])
def update_reserva(reserva_id):
    """Actualizar reserva existente"""
    if not database_available:
        return jsonify({'error': 'Base de datos no disponible'}), 503

    try:
        # Extraer ID numérico de RSV-XXX
        numeric_id = int(reserva_id.replace('RSV-', ''))
        reserva = Reserva.query.get(numeric_id)

        if not reserva:
            return jsonify({'error': 'Reserva no encontrada'}), 404

        data = request.get_json()

        # Actualizar campos básicos
        reserva.nombres_huespedes = data.get('nombre', reserva.nombres_huespedes)
        reserva.cantidad_huespedes = data.get('numeroPersonas', reserva.cantidad_huespedes)
        reserva.domo = data.get('domo', reserva.domo)
        reserva.email_contacto = data.get('email', reserva.email_contacto)
        reserva.numero_contacto = data.get('numero', reserva.numero_contacto)

        if 'fechaEntrada' in data:
            reserva.fecha_entrada = datetime.fromisoformat(data['fechaEntrada']).date()
        if 'fechaSalida' in data:
            reserva.fecha_salida = datetime.fromisoformat(data['fechaSalida']).date()

        # Actualizar nuevos campos
        if 'metodoPago' in data:
            reserva.metodo_pago = data['metodoPago']
        if 'comentariosEspeciales' in data:
            reserva.comentarios_especiales = data['comentariosEspeciales']
        
        # Actualizar servicios
        if 'servicios' in data:
            reserva.servicio_elegido = ', '.join([s.get('nombre', '') for s in data['servicios']])

        # Recalcular precio si es necesario
        if 'montoAPagar' in data:
            reserva.monto_total = data['montoAPagar']
        elif any(field in data for field in ['domo', 'numeroPersonas', 'fechaEntrada', 'fechaSalida', 'servicios']):
            # Recalcular precio automáticamente si cambiaron datos relevantes
            calculo_precio = calcular_precio_reserva(
                domo=reserva.domo,
                cantidad_huespedes=reserva.cantidad_huespedes,
                fecha_entrada=reserva.fecha_entrada,
                fecha_salida=reserva.fecha_salida,
                servicios_adicionales=reserva.servicio_elegido
            )
            reserva.monto_total = calculo_precio['precio_total']

        db.session.commit()

        return jsonify({'message': 'Reserva actualizada exitosamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservas/<reserva_id>', methods=['DELETE'])
def delete_reserva(reserva_id):
    """Eliminar reserva"""
    if not database_available:
        return jsonify({'error': 'Base de datos no disponible'}), 503

    try:
        # Extraer ID numérico de RSV-XXX
        numeric_id = int(reserva_id.replace('RSV-', ''))
        reserva = Reserva.query.get(numeric_id)

        if not reserva:
            return jsonify({'error': 'Reserva no encontrada'}), 404

        db.session.delete(reserva)
        db.session.commit()

        return jsonify({'message': 'Reserva eliminada exitosamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/")
def home():
    return "Servidor Flask con Agente RAG y WhatsApp conectado. La memoria del agente ahora es persistente."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)