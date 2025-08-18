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
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string


print("Puerto asignado:", os.environ.get("PORT"))


#Importaciones Paincone

# Importaciones de Pinecone con manejo de errores
try:
    # Import completo (pinecone v3.0+)
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_SERVERLESS_AVAILABLE = True
    print("OK: Pinecone importado con ServerlessSpec")
except ImportError:
    try:
        # Import básico sin ServerlessSpec
        from pinecone import Pinecone
        PINECONE_SERVERLESS_AVAILABLE = False
        print("OK: Pinecone importado sin ServerlessSpec")
    except ImportError:
        #  Import de legacy
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
    
    # Variables funcionalidades específicas)
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

# Inicializar cliente Pinecone con manejo de errores 
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

# Validar que el índice exista con mejor manejo de errores 
if pc:
    try:
        # Obtener lista de índices según la versión de Pinecone
        try:
            
            if hasattr(pc, 'list_indexes') and callable(pc.list_indexes):
                indexes_response = pc.list_indexes()
                if isinstance(indexes_response, dict) and "indexes" in indexes_response:
                    indexes = [index["name"] for index in indexes_response["indexes"]]
                else:
                    # Respuesta directa (lista)
                    indexes = [index.name for index in indexes_response] if hasattr(indexes_response[0], 'name') else [str(index) for index in indexes_response]
            else:
                # Pinecone 
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

# CORS configurado específicamente para el frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",  # Desarrollo Vite
            "http://localhost:4173",  # Preview Vite
            "https://panel-con-react.vercel.app",  # Si despliegas en Vercel
            "https://*.netlify.app",  # Si despliegas en Netlify
            "*"  # Temporal para testing
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuración de la base de datos URL privada
DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL')
DATABASE_URL = os.getenv('DATABASE_URL')


database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL

if DATABASE_PRIVATE_URL:
    print("OK: Usando DATABASE_PRIVATE_URL (sin costos de egress)")
elif DATABASE_PUBLIC_URL:
    print("WARNING: Usando DATABASE_PUBLIC_URL (puede generar costos de egress)")
    print("TIP: Usa DATABASE_PRIVATE_URL para evitar costos")
elif DATABASE_URL:
    print("INFO: Usando DATABASE_URL genérica")

db = None
database_available = False 

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar SQLAlchemy con validación de conexión
    try:
        db = SQLAlchemy(app)
        print("OK: SQLAlchemy inicializado correctamente")

        #Verificar que la conexión funcione realmente
        with app.app_context():
            try:
                db.engine.connect()
                database_available = True  # ← MARCAR COMO DISPONIBLE
                print("OK: Conexion a base de datos verificada exitosamente")
            except Exception as conn_error:
                print(f"ERROR: Error de conexion a BD: {conn_error}")
                database_available = False  # ← MARCAR COMO NO DISPONIBLE

    except Exception as e:
        warning_msg = f"WARNING: Error al inicializar la base de datos: {e}\n[TIP] Funcionalidad de base de datos deshabilitada"
        print(warning_msg)
        db = None
        database_available = False  # ← MARCAR COMO NO DISPONIBLE
else:
    print("WARNING: Ninguna DATABASE_URL configurada - Funcionalidad de base de datos deshabilitada")
    print("TIP: Configura DATABASE_PRIVATE_URL, DATABASE_PUBLIC_URL o DATABASE_URL")
    database_available = False  # ← MARCAR COMO NO DISPONIBLE

# Modelos de datos de reservas y usuarios
Reserva = None # Inicializar como None para evitar errores de referencia
Usuario = None
if db:
    class Reserva(db.Model):
        __tablename__ = 'reservas'
        id = db.Column(db.Integer, primary_key=True)

        # CAMPOS IMPORTANTES 
        numero_whatsapp = db.Column(db.String(50), nullable=False)        
        email_contacto = db.Column(db.String(100), nullable=False)        
        cantidad_huespedes = db.Column(db.Integer, nullable=False)        
        domo = db.Column(db.String(50), nullable=False)                   
        fecha_entrada = db.Column(db.Date, nullable=False)                
        fecha_salida = db.Column(db.Date, nullable=False)                 
        metodo_pago = db.Column(db.String(50), nullable=False, default='Pendiente')  

        # CAMPOS OPCIONALES 
        nombres_huespedes = db.Column(db.String(255))                    
        servicio_elegido = db.Column(db.String(100))                     
        adicciones = db.Column(db.String(255))                           
        comentarios_especiales = db.Column(db.Text)                      
        numero_contacto = db.Column(db.String(50))                       

        
        monto_total = db.Column(db.Numeric(10, 2), default=0.00) # Precio total calculado
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow) # Fecha de creación

        def __repr__(self):
            return f'<Reserva {self.id}: {self.nombres_huespedes or "Usuario"}>'

    # Modelo de Usuario para sistema de autenticación
    class Usuario(db.Model):
        __tablename__ = 'usuarios'
        id = db.Column(db.Integer, primary_key=True)
        nombre = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(100), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)
        temp_password = db.Column(db.String(50))  # NUEVO: Contraseña temporal visible
        rol = db.Column(db.String(20), default='limitado', nullable=False)
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
        creado_por = db.Column(db.String(100), default='juan@example.com')
        activo = db.Column(db.Boolean, default=True)
        ultimo_acceso = db.Column(db.DateTime)
        password_changed = db.Column(db.Boolean, default=False)  # NUEVO: Si cambió contraseña

        def __repr__(self):
            return f'<Usuario {self.id}: {self.nombre} ({self.email})>'

#  FUNCIONES DE GENERACIÓN DE CONTRASEÑAS 
def generate_random_password(length=8):
    """Generar contraseña aleatoria segura"""
    characters = string.ascii_letters + string.digits
    # Evitar caracteres confusos como 0, O, l, I
    characters = characters.replace('0', '').replace('O', '').replace('l', '').replace('I', '')

    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def generate_simple_password():
    """Generar contraseña simple pero segura"""
    # Formato: palabra + número (ej: Mesa2024, Casa5847)
    words = ['Mesa', 'Casa', 'Luna', 'Sol', 'Mar', 'Rio', 'Pan', 'Flor', 'Luz', 'Ave']
    word = random.choice(words)
    number = random.randint(1000, 9999)
    return f"{word}{number}"

# FUNCIONES DE GESTIÓN DE USUARIOS 
def get_all_users(include_passwords=False):
    """Obtener todos los usuarios (con contraseñas solo para admin)"""
    if not db or not Usuario:
        return []

    usuarios = Usuario.query.order_by(Usuario.fecha_creacion.desc()).all()
    result = []

    for u in usuarios:
        user_data = {
            'id': u.id,
            'nombre': u.nombre,
            'email': u.email,
            'rol': u.rol,
            'fecha_creacion': u.fecha_creacion.isoformat() if u.fecha_creacion else None,
            'ultimo_acceso': u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
            'activo': u.activo,
            'password_changed': u.password_changed or False
        }

        # Solo incluir contraseña si se solicita (solo para admin)
        if include_passwords and u.temp_password:
            user_data['temp_password'] = u.temp_password

        result.append(user_data)

    return result

def create_user_function(nombre, email, password=None, rol='limitado'):
    """Crear nuevo usuario con contraseña generada automáticamente"""
    if not db or not Usuario:
        raise Exception("Base de datos no disponible")

    try:
        # Si no se proporciona contraseña, generar una automáticamente
        if not password:
            temp_password = generate_simple_password()
        else:
            temp_password = password

        password_hash = generate_password_hash(temp_password)

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            temp_password=temp_password,  # Guardar contraseña temporal
            rol=rol,
            password_changed=False  # Contraseña generada por admin
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return {
            'id': nuevo_usuario.id,
            'temp_password': temp_password  # Devolver para mostrar al admin
        }
    except Exception as e:
        db.session.rollback()
        raise e

def update_user_function(user_id, nombre, email, rol, activo=True):
    """Actualizar usuario"""
    if not db or not Usuario:
        return False

    try:
        user = Usuario.query.get(user_id)
        if user:
            user.nombre = nombre
            user.email = email
            user.rol = rol
            user.activo = activo
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False

def delete_user_function(user_id):
    """Eliminar usuario (soft delete)"""
    if not db or not Usuario:
        return False

    try:
        user = Usuario.query.get(user_id)
        if user:
            user.activo = False
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False

def validar_campos_importantes_reserva(data):
    """
    Valida que todos los campos importantes estén presentes y sean válidos
    """
    errores = []
    campos_importantes = {
        'numero_whatsapp': 'Teléfono',
        'email_contacto': 'Email',
        'cantidad_huespedes': 'Número de personas',
        'domo': 'Domo seleccionado',
        'fecha_entrada': 'Fecha de entrada',
        'fecha_salida': 'Fecha de salida',
        'metodo_pago': 'Método de pago'
    }

    # Verificar campos obligatorios
    for campo_bd, nombre_amigable in campos_importantes.items():
        if not data.get(campo_bd):
            errores.append(f"Campo importante faltante: {nombre_amigable}")

    # Validaciones específicas
    if data.get('cantidad_huespedes'):
        try:
            personas = int(data['cantidad_huespedes'])
            if personas < 1 or personas > 10:  # Límites del glamping
                errores.append("Número de personas debe estar entre 1 y 10")
        except (ValueError, TypeError):
            errores.append("Número de personas debe ser un número válido")

    if data.get('domo'):
        domos_validos = ['antares', 'polaris', 'sirius', 'centaury']
        if data['domo'].lower() not in domos_validos:
            errores.append(f"Domo debe ser uno de: {', '.join(domos_validos)}")

    if data.get('email_contacto'):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email_contacto']):
            errores.append("Email no tiene formato válido")

    if data.get('fecha_entrada') and data.get('fecha_salida'):
        try:
            from datetime import datetime
            fecha_in = datetime.strptime(data['fecha_entrada'], '%Y-%m-%d').date() if isinstance(data['fecha_entrada'], str) else data['fecha_entrada']
            fecha_out = datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date() if isinstance(data['fecha_salida'], str) else data['fecha_salida']

            if fecha_in >= fecha_out:
                errores.append("Fecha de salida debe ser posterior a la fecha de entrada")

            if fecha_in < datetime.now().date():
                errores.append("Fecha de entrada no puede ser en el pasado")

        except (ValueError, TypeError):
            errores.append("Fechas deben tener formato válido (YYYY-MM-DD)")

    return {
        'valido': len(errores) == 0,
        'errores': errores,
        'campos_faltantes': [campo for campo, _ in campos_importantes.items() if not data.get(campo)]
    }

# Sistema de cálculo de precios para reservas
def calcular_precio_reserva(domo, cantidad_huespedes, fecha_entrada, fecha_salida, servicios_adicionales=None):
    """Calcula el precio total de una reserva basado en domo, huéspedes, días y servicios"""
    
    # Precios base por domo por noche (para pareja)
    precios_domos = {
        'antares': 650000,   
        'polaris': 550000,    
        'sirius': 450000,     
        'centaury': 450000    
    }
    
    # Servicios adicionales disponibles
    precios_servicios = {
        'decoraciones': 60000,      
        'masajes': 90000,           
        'masajes_pareja': 180000,   
        'velero': 150000,           
        'lancha': 80000,            
        'caminata_montecillo': 50000, 
        'caminata_pozo_azul': 70000    
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

# Crear tablas de base de datos y validar conexión 
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

# Directorio de memoria del usuario
MEMORY_DIR = "user_memories_data" # Directorio de archivos de memoria
try:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    print(f"OK: Directorio de memoria creado: {MEMORY_DIR}")
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

# Inicializar LLM de OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    error_msg = "ERROR: OPENAI_API_KEY no configurada\n[TIP] Configura tu API Key de OpenAI"
    print(error_msg)
    raise EnvironmentError(error_msg)

try:
    # En langchain 0.1.0, OpenAI puede estar en diferentes ubicaciones
    import os
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  
    
    # Intentar diferentes imports para compatibilidad con langchain 0.1.0
    llm = None
    try:
        #  Import tradicional (ya importado arriba)
        llm = OpenAI(temperature=0)
        print("OK: LLM OpenAI inicializado con import tradicional")
    except (NameError, ImportError, TypeError) as e:
        try:
            # Import nuevo en langchain 0.1.0
            from langchain_openai import OpenAI as OpenAI_New
            llm = OpenAI_New(temperature=0)
            print("OK: LLM OpenAI inicializado con nuevo import langchain_openai")
        except ImportError:
            try:
                # Import legacy
                from langchain.llms.openai import OpenAI as OpenAI_Legacy
                llm = OpenAI_Legacy(temperature=0)
                print("OK: LLM OpenAI inicializado con import legacy")
            except ImportError:
                #  ChatOpenAI como fallback
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

#  Herramientas RAG para el Agente 

# Funciones wrapper para usar invoke() 
def call_chain_safe(chain_name: str, query: str) -> str:
    """Llama a una cadena QA usando el método invoke() moderno"""
    try:
        if chain_name not in qa_chains or qa_chains[chain_name] is None:
            return "Lo siento, esa información no está disponible en este momento."
        
        chain = qa_chains[chain_name]
        # Usar invoke() 
        result = chain.invoke({"query": query})
        
        # El resultado puede estar en diferentes campos dependiendo de la cadena
        if isinstance(result, dict):
            return result.get("result", result.get("output", str(result)))
        else:
            return str(result)
            
    except Exception as e:
        print(f"ERROR: Error en cadena {chain_name}: {e}")
        return "Disculpa, tuve un problema accediendo a esa información. ¿Podrías reformular tu pregunta?"

# Funciones específicas para archivos originales 
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

def links_imagenes_func(query: str = None) -> str:
    """Función robusta que SIEMPRE devuelve los links"""
    if query is None:
        query = "Enlaces para ver imágenes de los domos"
    
    # Usar RAG para contexto, pero siempre incluir los links
    response = call_chain_safe("links_imagenes", query)
    
    # Crear respuesta que SIEMPRE incluya los links
    links_response = (
        "Aquí tienes los enlaces que necesitas:\n\n"
        "**Para ver imágenes de los domos**: https://www.glampingbrillodeluna.com/domos\n\n"
        "**Página web oficial**: https://www.glampingbrillodeluna.com\n\n"
        "En estos enlaces podrás ver todas las fotos de nuestros hermosos domos geodésicos, "
        "conocer las instalaciones y realizar reservas directamente."
    )
    
    return links_response

# Herramienta para consultar disponibilidades
def consultar_disponibilidades_glamping(consulta_usuario: str) -> str:
    """
    Consulta las disponibilidades de domos 
    """
    try:
        print(f"[AGENTE] Consultando disponibilidades: {consulta_usuario}")

        #  BD disponible
        if not database_available or not db:
            return "Lo siento, no puedo consultar las disponibilidades en este momento. La base de datos no está disponible."

        # Extraer parámetros de la consulta
        parametros = extraer_parametros_consulta(consulta_usuario)
        print(f"📊 [AGENTE] Parámetros extraídos: {parametros}")

        # Si no hay fecha específica, usar próximos 30 días
        if not parametros['fecha_inicio']:
            from datetime import datetime, timedelta
            hoy = datetime.now().date()
            parametros['fecha_inicio'] = hoy.strftime('%Y-%m-%d')
            parametros['fecha_fin'] = (hoy + timedelta(days=30)).strftime('%Y-%m-%d')
        elif not parametros['fecha_fin']:
            from datetime import datetime, timedelta
            fecha_obj = datetime.strptime(parametros['fecha_inicio'], '%Y-%m-%d').date()
            parametros['fecha_fin'] = (fecha_obj + timedelta(days=1)).strftime('%Y-%m-%d')

        # CONSULTAR DIRECTAMENTE LA BD 
        disponibilidades = obtener_disponibilidades_calendario(
            fecha_inicio=parametros['fecha_inicio'],
            fecha_fin=parametros['fecha_fin'],
            domo_especifico=parametros['domo'],
            personas=parametros['personas']
        )

        # Generar respuesta 
        respuesta = generar_respuesta_disponibilidades(disponibilidades, parametros, consulta_usuario)

        print(f"✅ [AGENTE] Respuesta: {respuesta[:100]}...")
        return respuesta

    except Exception as e:
        print(f"ERROR [AGENTE] Error en consulta: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Disculpa, tuve un problema técnico consultando las disponibilidades. Error: {str(e)}"

def obtener_disponibilidades_calendario(fecha_inicio, fecha_fin, domo_especifico=None, personas=None):
    """
    Obtiene disponibilidades consultando directamente la BD
    Misma lógica que usa el calendario del panel de control
    """
    try:
        print(f"🗄️ [BD] Consultando reservas desde {fecha_inicio} hasta {fecha_fin}")

        # Obtener reservas activas en el rango (IGUAL QUE EL CALENDARIO)
        reservas_activas = Reserva.query.filter(
            Reserva.fecha_entrada <= fecha_fin,
            Reserva.fecha_salida >= fecha_inicio
        ).all()

        print(f"📊 [BD] Encontradas {len(reservas_activas)} reservas activas")

        # Información de domos 
        domos_info = {
            'antares': {
                'nombre': 'Antares',
                'capacidad_maxima': 2,
                'precio_base': 650000,
                'descripcion': 'Nido de amor con jacuzzi privado'
            },
            'polaris': {
                'nombre': 'Polaris',
                'capacidad_maxima': 6,
                'precio_base': 550000,
                'descripcion': 'Amplio domo familiar'
            },
            'sirius': {
                'nombre': 'Sirius',
                'capacidad_maxima': 2,
                'precio_base': 450000,
                'descripcion': 'Domo acogedor de un piso'
            },
            'centaury': {
                'nombre': 'Centaury',
                'capacidad_maxima': 2,
                'precio_base': 450000,
                'descripcion': 'Domo íntimo romántico'
            }
        }

        # Calcular disponibilidades día por día.  CALENDARIO
        from datetime import datetime, timedelta
        fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_limite = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        disponibilidades = []
        domos_disponibles_total = []

        while fecha_actual <= fecha_limite:
            # Encontrar qué domos están ocupados este día
            reservas_del_dia = [r for r in reservas_activas
                              if r.fecha_entrada <= fecha_actual < r.fecha_salida]

            domos_ocupados = [r.domo.lower() for r in reservas_del_dia if r.domo]
            domos_disponibles_dia = [domo for domo in domos_info.keys()
                                   if domo not in domos_ocupados]

            # Filtrar por capacidad si se especifica
            if personas:
                domos_disponibles_dia = [
                    domo for domo in domos_disponibles_dia
                    if domos_info[domo]['capacidad_maxima'] >= personas
                ]

            # Filtrar por domo específico si se solicita
            if domo_especifico:
                domo_lower = domo_especifico.lower()
                domos_disponibles_dia = [domo for domo in domos_disponibles_dia
                                       if domo == domo_lower]

            disponibilidades.append({
                'fecha': fecha_actual.strftime('%Y-%m-%d'),
                'fecha_formateada': fecha_actual.strftime('%d de %B de %Y'),
                'domos_disponibles': domos_disponibles_dia,
                'domos_ocupados': domos_ocupados,
                'total_disponibles': len(domos_disponibles_dia)
            })

            # Agregar a disponibles totales
            for domo in domos_disponibles_dia:
                if not any(d['domo'] == domo for d in domos_disponibles_total):
                    domos_disponibles_total.append({
                        'domo': domo,
                        'info': domos_info[domo],
                        'fechas_disponibles': []
                    })

                # Agregar fecha al domo
                for item in domos_disponibles_total:
                    if item['domo'] == domo:
                        item['fechas_disponibles'].append(fecha_actual.strftime('%Y-%m-%d'))

            fecha_actual += timedelta(days=1)

        resultado = {
            'success': True,
            'disponibilidades_por_fecha': disponibilidades,
            'domos_disponibles': domos_disponibles_total,
            'parametros': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'domo_especifico': domo_especifico,
                'personas': personas
            }
        }

        print(f"✅ [BD] Consulta exitosa: {len(domos_disponibles_total)} domos disponibles")
        return resultado

    except Exception as e:
        print(f"ERROR [BD] Error en consulta: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'disponibilidades_por_fecha': [],
            'domos_disponibles': []
        }

def generar_respuesta_disponibilidades(datos, parametros, consulta_original):
    """
    Genera respuesta natural para WhatsApp basada en disponibilidades
    """
    try:
        if not datos.get('success'):
            return f"Lo siento, tuve un problema consultando las disponibilidades: {datos.get('error', 'Error desconocido')}"

        domos_disponibles = datos.get('domos_disponibles', [])
        disponibilidades_por_fecha = datos.get('disponibilidades_por_fecha', [])

        if not domos_disponibles:
            if parametros.get('fecha_inicio'):
                try:
                    fecha_obj = datetime.strptime(parametros['fecha_inicio'], '%Y-%m-%d')
                    fecha_formateada = fecha_obj.strftime('%d de %B de %Y')
                    return f"Lo siento, no tenemos domos disponibles para el {fecha_formateada}. ¿Te gustaría consultar otras fechas? 📅"
                except:
                    return "No encontré domos disponibles para la fecha consultada. ¿Podrías intentar con otras fechas? 📅"
            else:
                return "No encontré domos disponibles para las fechas consultadas. ¿Podrías especificar fechas diferentes? 📅"

        
        respuesta = "¡Excelente! 🎉 "

        # Mencionar fecha específica que haya
        if parametros.get('fecha_inicio') and parametros.get('fecha_fin'):
            try:
                fecha_inicio_obj = datetime.strptime(parametros['fecha_inicio'], '%Y-%m-%d')
                fecha_fin_obj = datetime.strptime(parametros['fecha_fin'], '%Y-%m-%d')

                if fecha_inicio_obj.date() == fecha_fin_obj.date() - timedelta(days=1):
                    # Un solo día
                    fecha_formateada = fecha_inicio_obj.strftime('%d de %B de %Y')
                    respuesta += f"Para el *{fecha_formateada}* "
                else:
                    # Rango de fechas
                    fecha_inicio_str = fecha_inicio_obj.strftime('%d de %B')
                    fecha_fin_str = fecha_fin_obj.strftime('%d de %B de %Y')
                    respuesta += f"Entre el *{fecha_inicio_str}* y *{fecha_fin_str}* "
            except:
                respuesta += "Para las fechas consultadas "

        # Listar domos disponibles
        if len(domos_disponibles) == 1:
            domo = domos_disponibles[0]
            respuesta += f"tenemos disponible el domo *{domo['info']['nombre']}*:\n\n"
            respuesta += f"👥 Capacidad: {domo['info']['capacidad_maxima']} personas\n"
            respuesta += f"💰 Precio: ${domo['info']['precio_base']:,}\n"
            respuesta += f"🏡 {domo['info']['descripcion']}\n\n"
        else:
            respuesta += f"tenemos *{len(domos_disponibles)} domos disponibles*:\n\n"
            for i, domo in enumerate(domos_disponibles, 1):
                respuesta += f"*{i}. {domo['info']['nombre']}*\n"
                respuesta += f"   👥 {domo['info']['capacidad_maxima']} personas - 💰 ${domo['info']['precio_base']:,}\n"
                respuesta += f"   🏡 {domo['info']['descripcion']}\n"
                respuesta += f"   📅 {len(domo['fechas_disponibles'])} fechas disponibles\n\n"

        respuesta += "¿Te gustaría hacer una reserva o necesitas más información sobre algún domo específico? 😊"

        return respuesta

    except Exception as e:
        print(f"ERROR Error generando respuesta: {e}")
        return "Tenemos domos disponibles. ¿Te gustaría hacer una reserva? 😊"


# iniciar el flujo de reserva.
class ReservationRequestTool(BaseTool):
    name: str = "SolicitarDatosReserva"
    description: str = "Útil para iniciar el proceso de recolección de datos de reserva. Úsala cuando el usuario exprese claramente su deseo de hacer una reserva (ej. 'quiero reservar', 'hacer una reserva', 'reservar un domo', 'cómo reservo')."

    def _run(self, query: str = None) -> str:
        # Esta herramienta no procesa la reserva, solo indica que el bot debe pedir los datos.
        return "REQUEST_RESERVATION_DETAILS"

    async def _arun(self, query: str = None) -> str:
        return self._run(query)

def menu_principal_func(query: str = None) -> str:
    """Muestra el menú principal de navegación cuando el usuario lo solicita"""
    return get_welcome_menu()

tools = [
    ReservationRequestTool(), 
    
    Tool(
        name="ConsultarDisponibilidades",
        func=consultar_disponibilidades_glamping,
        description="Útil para consultar disponibilidades de domos, fechas específicas, capacidad y precios. Úsala cuando el usuario pregunte sobre disponibilidad, fechas libres, domos disponibles, si hay espacio para cierta cantidad de personas, o quiera saber qué opciones tiene para hospedarse."
    ),
    
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
        description="Devuelve los precios de los domos. Input: pregunta del usuario, por ejemplo 'precios de los domos para el 12/09'."
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
    ),
    Tool(
        name="LinksImagenesWeb",
        func=links_imagenes_func,
        description="OBLIGATORIO: Usar cuando usuario pida: 'fotos', 'imágenes', 'galería', 'página web', 'sitio web', 'links', 'enlaces', 'ver domos'. SIEMPRE devuelve los links reales de la página web."
    ),
    Tool(
        name="MenuPrincipal",
        func=menu_principal_func,
        description="OBLIGATORIO: Usar cuando usuario pida: 'menú', 'menús', 'opciones', 'guía', 'ayuda', 'navegación', 'qué puedo hacer', 'cómo navegar'. Muestra el menú principal de opciones disponibles."
    )
]

# Manejo de Memoria 
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
        
        # archivo temporal primero 
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(serialized_messages, f, ensure_ascii=False, indent=2)
        
        # temporal es un JSON válido 
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Validar formato
        
        # Mover archivo temporal al destino final
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
            "Eres María, una asistente experta del Glamping Brillo de Luna. "
            "Tienes acceso a información detallada sobre el lugar, sus domos, servicios, políticas y actividades. "
            "Cuentas con una excelente memoria para recordar todo lo conversado, incluso si no está directamente relacionado con el glamping "
            "o si es de carácter personal o emocional. "
            "Responde SIEMPRE en español. "

            "REGLAS IMPORTANTES: "
            "1. SIEMPRE usa las herramientas disponibles para responder preguntas específicas. "
            "2. Si el usuario menciona: 'silla de ruedas', 'movilidad reducida', 'discapacidad', 'accesibilidad', 'limitaciones físicas', 'muletas' o 'adaptaciones', "
            "usa de inmediato la herramienta 'SugerenciasMovilidadReducida' y responde con toda la información que esta te proporcione. "
            "3. Si pregunta sobre precios, usa 'DomosPreciosDetallados'. "
            "4. Si pregunta sobre actividades, usa 'ServiciosExternos'. "
            "5. Si pregunta por fotos, imágenes, galería, página web o enlaces, usa 'LinksImagenesWeb'. "
            "6. Si solicita menú, opciones, guía, ayuda o navegación, usa 'MenuPrincipal'. "
            "7. NUNCA hagas preguntas de seguimiento si ya tienes la información específica de una herramienta. "
            "8. Tu respuesta debe basarse en la información EXACTA de la herramienta, sin agregar información inventada ni preguntas adicionales. "
            "9. Evita respuestas genéricas cuando haya herramientas específicas disponibles. "
            "Tu objetivo es ser útil, clara y precisa, siempre apoyándote en la información de las herramientas."
        )

        assistant_response = (
            "¡Hola! Mi nombre es María y soy la asistente virtual del Glamping Brillo de Luna. "
            "Es un placer saludarte y acompañarte en lo que necesites. "
            "Estoy especializada en brindarte información detallada sobre nuestros domos geodésicos, "
            "servicios exclusivos, experiencias únicas y todo lo necesario para que planifiques una estadía inolvidable. "
            "¿Qué información te gustaría conocer hoy?"
        )

        
        try:
            #  API de langchain 0.1.0
            from langchain.schema import HumanMessage, AIMessage
            memory.chat_memory.add_message(HumanMessage(content=system_message))
            memory.chat_memory.add_message(AIMessage(content=assistant_response))
            print(f"OK: Memoria creada con API nueva para usuario: {user_id}")
        except (ImportError, AttributeError):
            try:
            
                memory.chat_memory.add_user_message(system_message)
                memory.chat_memory.add_ai_message(assistant_response)
                print(f"OK: Memoria creada con API legacy para usuario: {user_id}")
            except AttributeError:
                
                print(f"WARNING:  Creando memoria básica sin mensajes iniciales para usuario: {user_id}")
                
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
    """cargar memoria desde un archivo específico""" 
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
                # API de langchain 
                memory.chat_memory.messages = messages_from_dict(serialized_messages)
            except Exception:
                # Fallback - recrear memoria vacía si falla
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
    
    #   crear memoria nueva si falla algo
    print(f"Creando memoria nueva para usuario: {user_id}")
    memory = _create_fresh_memory(user_id)
    
    # Guardar la memoria nueva
    if save_user_memory(user_id, memory):
        print(f"OK: Memoria nueva guardada para usuario: {user_id}")
    else:
        print(f"WARNING:  No se pudo guardar memoria nueva para usuario: {user_id}")
    
    return memory

# Mantenimiento del sistema de memoria
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
    """Obtiene estadísticas sobre el estado de sistema de memoria"""
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
cleanup_corrupted_memory_files()


# Funciones de validación para datos de reserva
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
    
    # Extraer numeros
    try:
        # Buscar números en el string
        numbers = re.findall(r'\d+', clean_date)
        if len(numbers) == 3:
            # Diferentes combinaciones
            day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
            
            # Determinar el año completo si es de 2 dígitos
            if year < 100:
                if year < 30:
                    year += 2000
                else:
                    year += 1900
            
            #  día/mes/año y mes/día/año
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

# Guardar los datos de reserva. Pinecone 
def save_reservation_to_pinecone(user_phone_number, reservation_data):
    try:
        if not reservation_data or not user_phone_number:
            print(f"WARNING:  Datos de reserva incompletos para Pinecone")
            return False
        
        reserva_text = json.dumps(reservation_data, ensure_ascii=False)
        
        
        embedder = OpenAIEmbeddings()
        vector = embedder.embed_query(reserva_text)
        
        
        pinecone_index.upsert([(user_phone_number, vector, reservation_data)])
        print(f"OK: Reserva guardada en Pinecone para {user_phone_number}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error al guardar en Pinecone para {user_phone_number}: {e}")
        return False

def parse_reservation_details(user_input):
    # Usar LLM para extraer fechas y detalles
    prompt = f"""
    Extrae los siguientes datos de la solicitud de reserva del usuario. Analiza línea por línea.
    
    FORMATO TÍPICO DE ENTRADA:
    Los datos pueden estar en formato de líneas separadas. Analiza todo el texto línea por línea:
    - Nombres de huéspedes: Pueden estar en una línea separados por comas, o en líneas separadas
    - Tipo de domo: Antares, Polaris, Sirius, Centaury
    - Fechas: formato DD/MM/AAAA hasta DD/MM/AAAA o similar
    - Servicios adicionales: masajes, decoraciones, etc.
    - Adiciones especiales: mascotas, etc.
    - Número de teléfono: números de contacto
    - Email: correo electrónico
    - Método de pago: efectivo, transferencia, tarjeta, etc.
    - Comentarios especiales: cualquier observación adicional del usuario
    
    INSTRUCCIONES IMPORTANTES:
    - Los nombres pueden estar en múltiples líneas consecutivas al inicio
    - Identifica el domo por los nombres: Antares, Polaris, Sirius, Centaury
    - Si dice "voy con X personas más", cuenta el solicitante + X acompañantes
    - Si dice "somos X personas", usa ese número total
    - SIEMPRE incluye metodo_pago y comentarios_especiales aunque estén vacíos
    - Si no encuentras método de pago, usa "No especificado"
    - Si no encuentras comentarios, usa "Ninguno"
    - Responde SOLO con JSON válido, sin texto adicional

    EJEMPLO DE ENTRADA:
    "Juan Perez
    Maria Lopez  
    Centaury
    24/08/2025 hasta 30/08/2025
    Masajes
    1 mascota
    3001234567
    correo@email.com
    Efectivo
    Tengo una persona en silla de ruedas"
    
    EJEMPLO DE SALIDA JSON:
    {{
        "nombres_huespedes": ["Juan Perez", "Maria Lopez"],
        "numero_acompanantes": "2",
        "domo": "Centaury",
        "fecha_entrada": "24/08/2025",
        "fecha_salida": "30/08/2025",
        "servicio_elegido": "Masajes",
        "adicciones": "1 mascota",
        "numero_contacto": "3001234567",
        "email_contacto": "correo@email.com",
        "metodo_pago": "Efectivo",
        "comentarios_especiales": "Tengo una persona en silla de ruedas"
    }}

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
    
    # Funcion para llamar al LLM 
    success, response_text, error_msg = call_llm_with_retry(prompt, max_retries=3)
    
    if not success:
        print(f"ERROR: Error al llamar al LLM para parsing: {error_msg}")
        return None
    
    # Usar función robusta para parsear JSON
    json_success, parsed_json, json_error = parse_llm_json_safe(response_text)
    
    if not json_success:
        print(f"ERROR: Error al parsear JSON: {json_error}")
        return None
    
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
            elif field == "metodo_pago":
                parsed_json[field] = "No especificado"
            elif field == "comentarios_especiales":
                parsed_json[field] = "Ninguno"
            else:
                parsed_json[field] = "N/A"
    
    print("OK: Datos de reserva parseados exitosamente")
    return parsed_json

def validate_and_process_reservation_data(parsed_data, from_number) -> tuple[bool, dict, list]:
    """Valida y procesa datos de reserva"""
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
                print(f"INFO: Número de acompañantes especificado: {numero_acompanantes}")
            else:
                processed_data["cantidad_huespedes"] = len(validated_names)
                print(f"INFO: {names_msg}")
        
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
                print(f"INFO: {range_msg}")
        
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
        
        # 6. Procesar método de pago y comentarios especiales (CAMPOS FALTANTES)
        metodo_pago = parsed_data.get("metodo_pago", "No especificado").strip()
        processed_data["metodo_pago"] = metodo_pago if metodo_pago and metodo_pago.lower() not in ["n/a", "na"] else "No especificado"
        
        comentarios = parsed_data.get("comentarios_especiales", "Ninguno").strip()
        processed_data["comentarios_especiales"] = comentarios if comentarios and comentarios.lower() not in ["n/a", "na", "ninguno"] else "Ninguno"
        
        # Determinar si la validación fue exitosa
        success = len(errors) == 0
        return success, processed_data, errors
        
    except Exception as e:
        errors.append(f"Error inesperado en validación: {str(e)}")
        return False, {}, errors

# Funciones de manejo robusto del LLM y agente conversacional

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
        try:
            parsed = json.loads(llm_response)
            return True, parsed, "JSON parseado exitosamente"
        except json.JSONDecodeError:
            pass
        
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
        
        json_pattern_nested = r'\{.*\}'
        match = re.search(json_pattern_nested, llm_response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                print("OK: JSON anidado extraído de respuesta del LLM")
                return True, parsed, "JSON anidado extraído"
            except json.JSONDecodeError:
                pass
        
        cleaned_response = llm_response.replace('\n', '').replace('\r', '').strip()
        try:
            parsed = json.loads(cleaned_response)
            print("OK: JSON parseado después de limpiar")
            return True, parsed, "JSON parseado después de limpieza"
        except json.JSONDecodeError:
            pass
        
        return False, {}, f"No se pudo parsear JSON. Respuesta LLM: '{llm_response[:200]}...'"
        
    except Exception as e:
        return False, {}, f"Error inesperado parseando JSON: {str(e)}"

def initialize_agent_safe(tools, memory, max_retries: int = 3):
    """Inicializa el agente conversacional con manejo de errores"""
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

print("[STARTING] Sistema inicializado - Iniciando rutas Flask...")

# SISTEMA DE MENÚ PRINCIPAL 

def get_welcome_menu():
    return (
        "¡Hola! 👋 Mi nombre es *María* y soy la asistente virtual del *Glamping Brillo de Luna*. "
        "Es un placer saludarte y estar aquí para acompañarte. ✨\n\n"
        "Estoy especializada en brindarte información detallada sobre nuestros hermosos domos geodésicos, "
        "servicios exclusivos y experiencias únicas. 🏕️\n\n"
        "*Selecciona el número de la opción que te interese:*\n\n"
        "1️⃣ *Domos* - Tipos, características y precios\n"
        "2️⃣ *Servicios* - Todo lo que ofrecemos\n" 
        "3️⃣ *Disponibilidad* - Fechas disponibles\n"
        "4️⃣ *Información General* - Ubicación, políticas y más\n\n"
        "También puedes escribir *'reservar'* si ya sabes lo que quieres y deseas hacer una reserva directamente. 📝"
    )

def handle_menu_selection(selection, qa_chains):
    """Maneja la selección del menú principal"""
    selection = selection.strip()
    
    if selection == "1":
        try:
            # Información sobre domos usando múltiples RAG
            domos_info = qa_chains["domos_info"].run("¿Qué tipos de domos tienen y cuáles son sus características?")
            precios_info = qa_chains.get("domos_precios", {}).run("¿Cuáles son los precios de los domos?") if "domos_precios" in qa_chains else ""
            
            response = f"🏠 *INFORMACIÓN DE DOMOS*\n\n{domos_info}"
            if precios_info:
                response += f"\n\n💰 *PRECIOS*\n{precios_info}"
            
            response += "\n\n¿Te gustaría saber algo más específico sobre algún domo? 🤔"
            return response
        except Exception as e:
            return "🏠 *DOMOS DISPONIBLES*\n\nTenemos hermosos domos geodésicos únicos. ¿Te gustaría que te cuente más detalles sobre alguno en particular?"
    
    elif selection == "2":
        try:
            # Información sobre servicios
            servicios_incluidos = qa_chains["servicios_incluidos"].run("¿Qué servicios están incluidos?")
            servicios_adicionales = qa_chains["actividades_adicionales"].run("¿Qué servicios adicionales y actividades ofrecen?")
            
            response = f"🎯 *NUESTROS SERVICIOS*\n\n*SERVICIOS INCLUIDOS:*\n{servicios_incluidos}\n\n*SERVICIOS ADICIONALES:*\n{servicios_adicionales}"
            response += "\n\n¿Hay algún servicio específico que te interese? ✨"
            return response
        except Exception as e:
            return "🎯 *SERVICIOS*\n\nOfrecemos una amplia gama de servicios incluidos y adicionales. ¿Te gustaría saber sobre algo en particular?"
    
    elif selection == "3":
        return {
            "message": (
                "📅 *CONSULTA DE DISPONIBILIDAD*\n\n"
                "Para consultar fechas disponibles, por favor compárteme:\n"
                "• Las fechas que te interesan (formato DD/MM/AAAA)\n"
                "• Número de personas\n"
                "• Tipo de domo preferido (opcional)\n\n"
                "Ejemplo: _'15/09/2024 al 17/09/2024, 2 personas, domo romántico'_"
            ),
            "set_waiting_for_availability": True
        }
    
    elif selection == "4":
        try:
            # Información general del glamping
            ubicacion_info = qa_chains["ubicacion_contacto"].run("¿Dónde están ubicados y cómo contactarlos?")
            concepto_info = qa_chains["concepto_glamping"].run("¿Qué es Glamping Brillo de Luna?")
            politicas_info = qa_chains["politicas_glamping"].run("¿Cuáles son las políticas del glamping?")
            
            response = f"ℹ️ *INFORMACIÓN GENERAL*\n\n*CONCEPTO:*\n{concepto_info}\n\n*UBICACIÓN Y CONTACTO:*\n{ubicacion_info}\n\n*POLÍTICAS:*\n{politicas_info}"
            response += "\n\n¿Hay algo más específico que te gustaría saber? 🌟"
            return response
        except Exception as e:
            return "ℹ️ *INFORMACIÓN GENERAL*\n\nSomos un glamping ubicado en un entorno natural único. ¿Te gustaría saber algo específico?"
    
    else:
        return (
            "🤔 No entendí tu selección. Por favor elige un número del 1 al 4:\n\n"
            "1️⃣ *Domos*\n"
            "2️⃣ *Servicios*\n" 
            "3️⃣ *Disponibilidad*\n"
            "4️⃣ *Información General*\n\n"
            "O escribe *'reservar'* para hacer una reserva."
        )

def is_menu_selection(message):
    """Verifica si el mensaje es una selección válida del menú"""
    return message.strip() in ["1", "2", "3", "4"]

def is_greeting_message(message):
    """Verifica si el mensaje es un saludo inicial"""
    greetings = ['hola', 'holi', 'hello', 'hi', 'buenos días', 'buenas tardes', 'buenas noches', 'buenas', 'saludos']
    return message.lower().strip() in greetings

def handle_availability_request(message):
    """Maneja consultas de disponibilidad cuando el usuario responde después de seleccionar opción 3"""
    try:
        # Usar LLM para extraer fechas y detalles
        prompt = f"""
        Extrae la información de disponibilidad de este mensaje del usuario: "{message}"
        
        Busca:
        - Fechas (formato DD/MM/AAAA o similar)
        - Número de personas
        - Tipo de domo (si lo menciona)
        
        Responde en JSON:
        {{
            "fecha_inicio": "YYYY-MM-DD",
            "fecha_fin": "YYYY-MM-DD", 
            "personas": número,
            "domo_tipo": "tipo o null"
        }}
        
        Si no puedes extraer fechas válidas, responde con: {{"error": "fechas_no_claras"}}
        """
        
        parsing_llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        response_text = parsing_llm.invoke(prompt).content
        try:
            parsed_data = json.loads(response_text)
            
            if "error" in parsed_data:
                return (
                    "🤔 No pude entender las fechas claramente.\n\n"
                    "Por favor, compárteme la información así:\n"
                    "• *Fechas*: DD/MM/AAAA al DD/MM/AAAA\n"
                    "• *Personas*: Número de huéspedes\n"
                    "• *Domo*: Tipo preferido (opcional)\n\n"
                    "*Ejemplo:* _15/12/2024 al 17/12/2024, 2 personas_"
                )
            
            # fechas válidas, consultar disponibilidad
            fecha_inicio = parsed_data.get("fecha_inicio")
            fecha_fin = parsed_data.get("fecha_fin")
            personas = parsed_data.get("personas")
            domo_tipo = parsed_data.get("domo_tipo")
            
            if fecha_inicio and fecha_fin:
                # obtener_disponibilidades_calendario 
                disponibilidades = obtener_disponibilidades_calendario(
                    fecha_inicio, fecha_fin, domo_tipo, personas
                )
                
                if disponibilidades and "disponibilidades_por_dia" in disponibilidades:
                    response = f"📅 *DISPONIBILIDAD para {fecha_inicio} al {fecha_fin}*\n\n"
                    
                    for dia in disponibilidades["disponibilidades_por_dia"]:
                        fecha = dia["fecha_formateada"]
                        domos_disponibles = dia["domos_disponibles"]
                        
                        if domos_disponibles:
                            response += f"✅ *{fecha}*: {', '.join(domos_disponibles)}\n"
                        else:
                            response += f"X *{fecha}*: Sin disponibilidad\n"
                    
                    if disponibilidades.get("domos_disponibles_resumen"):
                        response += "\n🏠 *DOMOS DISPONIBLES EN EL PERÍODO:*\n"
                        for domo_info in disponibilidades["domos_disponibles_resumen"]:
                            domo = domo_info["domo"]
                            info = domo_info["info"]
                            response += f"• *{info['nombre']}*: {info['descripcion']} (${info['precio_base']:,})\n"
                    
                    response += "\n¿Te gustaría hacer una reserva o necesitas más información? 🤔"
                    return response
                else:
                    return f"X No hay disponibilidad para las fechas {fecha_inicio} al {fecha_fin}.\n\n¿Te gustaría consultar otras fechas?"
            
        except json.JSONDecodeError:
            pass
            
    except Exception as e:
        print(f"Error procesando consulta de disponibilidad: {e}")
    
    return (
        "Para consultar disponibilidad, por favor compárteme:\n"
        "• *Fechas*: DD/MM/AAAA al DD/MM/AAAA\n"
        "• *Personas*: Número de huéspedes\n"
        "• *Domo*: Tipo preferido (opcional)\n\n"
        "*Ejemplo:* _15/12/2024 al 17/12/2024, 2 personas, domo romántico_"
    )

#FILTRADO DE TEMAS CONDICIONALES

def is_glamping_related(message):
    """
    Detecta si el mensaje está relacionado con el glamping usando IA
    """
    try:
        # Usar LLM para determinar si la pregunta es sobre glamping
        prompt = f"""
        Analiza este mensaje del usuario y determina si está relacionado con glamping, turismo, alojamiento, reservas o viajes:

        Mensaje: "{message}"

        El mensaje ESTÁ relacionado si habla sobre:
        - Glamping, camping, domos, alojamiento
        - Reservas, disponibilidad, precios, servicios
        - Turismo, viajes, vacaciones, hospedaje
        - Instalaciones, actividades, comida, ubicación
        - Políticas, cancelaciones, mascotas
        - Accesibilidad, movilidad reducida
        - Cualquier pregunta sobre el establecimiento

        El mensaje NO ESTÁ relacionado si habla sobre:
        - Política, deportes, noticias, entretenimiento
        - Tecnología no relacionada con reservas
        - Recetas de cocina, consejos de salud
        - Matemáticas, ciencias, educación
        - Chistes, conversación casual no relacionada
        - Cualquier tema personal no relacionado con viajes

        Responde únicamente:
        - "SI" si está relacionado con glamping/turismo
        - "NO" si no está relacionado

        Respuesta:"""
        
        try:
            filter_llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except NameError:
            # Fallback en caso de que ChatOpenAI no esté disponible
            from langchain_openai import ChatOpenAI
            filter_llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        response_text = filter_llm.invoke(prompt).content.strip().upper()
        
        # Determinar si está relacionado
        is_related = response_text == "SI" or "SI" in response_text
        
        print(f"[FILTRO] Mensaje: '{message[:50]}...' -> Relacionado: {is_related}")
        return is_related
        
    except Exception as e:
        print(f"Error en filtro de temas: {e}")
        # En caso de error, asumimos que está relacionado para no bloquear conversaciones legítimas
        return True

def get_off_topic_response():
    """
    Retorna la respuesta para temas no relacionados con glamping
    """
    return (
        "🏕️ Soy María, la asistente especializada de *Glamping Brillo de Luna*.\n\n"
        "Solo puedo ayudarte con información sobre:\n"
        "• Nuestros domos y servicios\n"
        "• Reservas y disponibilidad\n"
        "• Precios y políticas\n"
        "• Ubicación y actividades\n"
        "• Cualquier consulta relacionada con tu estadía\n\n"
        "*¿Te gustaría saber algo sobre nuestro glamping?*\n\n"
        "Puedes seleccionar una opción:\n"
        "1️⃣ *Domos* - Tipos y características\n"
        "2️⃣ *Servicios* - Todo lo que ofrecemos\n"
        "3️⃣ *Disponibilidad* - Consultar fechas\n"
        "4️⃣ *Información General* - Ubicación y políticas\n\n"
        "O escribir *'reservar'* si deseas hacer una reserva. ✨"
    )

def should_bypass_filter(message):
    """
    Determina si ciertos mensajes deben evitar el filtro
    """
    message_lower = message.lower().strip()
    
    # Mensajes que siempre pasan (saludos, números de menú, etc.)
    bypass_patterns = [
        # Saludos
        'hola', 'hi', 'hello', 'buenos días', 'buenas tardes', 'buenas noches',
        # Comandos de reserva
        'reservar', 'reserva', 'quiero reservar',
        # Respuestas simples
        'si', 'sí', 'no', 'gracias', 'ok',
        # Despedidas
        'adiós', 'chao', 'hasta luego', 'bye'
    ]
    
    # Verificar patrones de bypass
    for pattern in bypass_patterns:
        if pattern in message_lower:
            return True
    
    # Verificar números de menú exactos (solo si es exactamente el número)
    if message_lower.strip() in ['1', '2', '3', '4']:
        return True
    
    return False

# WEBHOOK DE WHATSAPP 

# TEMPORARILY COMMENTED: Moved to routes/whatsapp_routes.py
# Original whatsapp_webhook function commented out to avoid conflicts
# The new modular version is loaded from routes/whatsapp_routes.py
# @app.route("/whatsapp_webhook", methods=["POST"])
# def whatsapp_webhook():
#     # Full function implementation moved to routes/whatsapp_routes.py
#     pass
    
    # Manejar selecciones del menú principal (números 1-4)
    if is_menu_selection(incoming_msg) and user_state["current_flow"] == "none":
        try:
            menu_response = handle_menu_selection(incoming_msg, qa_chains)
            
            # Si la respuesta es un diccionario (opción 3), manejar estado especial
            if isinstance(menu_response, dict):
                message_text = menu_response["message"]
                if menu_response.get("set_waiting_for_availability"):
                    user_state["waiting_for_availability"] = True
                resp.message(message_text)
                
                # Agregar a la memoria
                try:
                    from langchain.schema import HumanMessage, AIMessage
                    memory.chat_memory.add_message(HumanMessage(content=incoming_msg))
                    memory.chat_memory.add_message(AIMessage(content=message_text))
                except (ImportError, AttributeError):
                    try:
                        memory.chat_memory.add_user_message(incoming_msg)
                        memory.chat_memory.add_ai_message(message_text)
                    except:
                        pass
            else:
                # Respuesta normal (string)
                resp.message(menu_response)
                
                # Agregar a la memoria
                try:
                    from langchain.schema import HumanMessage, AIMessage
                    memory.chat_memory.add_message(HumanMessage(content=incoming_msg))
                    memory.chat_memory.add_message(AIMessage(content=menu_response))
                except (ImportError, AttributeError):
                    try:
                        memory.chat_memory.add_user_message(incoming_msg)
                        memory.chat_memory.add_ai_message(menu_response)
                    except:
                        pass
            
            save_user_memory(from_number, memory)
            return str(resp)
        except Exception as e:
            print(f"Error en manejo de menú: {e}")
            resp.message("Disculpa, hubo un error procesando tu selección. ¿Podrías intentar de nuevo?")
            return str(resp)

    # Manejar consultas de disponibilidad cuando el usuario está en modo "esperando disponibilidad"
    if user_state.get("waiting_for_availability", False) and user_state["current_flow"] == "none":
        try:
            availability_response = handle_availability_request(incoming_msg)
            resp.message(availability_response)
            
            # Resetear el estado de espera
            user_state["waiting_for_availability"] = False
            
            # Agregar a la memoria
            try:
                from langchain.schema import HumanMessage, AIMessage
                memory.chat_memory.add_message(HumanMessage(content=incoming_msg))
                memory.chat_memory.add_message(AIMessage(content=availability_response))
            except (ImportError, AttributeError):
                try:
                    memory.chat_memory.add_user_message(incoming_msg)
                    memory.chat_memory.add_ai_message(availability_response)
                except:
                    pass
            
            save_user_memory(from_number, memory)
            return str(resp)
        except Exception as e:
            print(f"Error procesando consulta de disponibilidad: {e}")
            resp.message("Disculpa, hubo un error procesando tu consulta. ¿Podrías intentar de nuevo?")
            user_state["waiting_for_availability"] = False
            return str(resp)

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
            "-Correo electrónico de contacto\n"
            "-Método de pago preferido (efectivo, transferencia, tarjeta)\n"
            "-Comentarios especiales u observaciones adicionales\n\n"
            "Por favor, escribe toda la información en un solo mensaje."
        )
        save_user_memory(from_number, memory)
        return str(resp)
    
    # Si el usuario ya está en el flujo de reserva y está en el paso 1, procesar la solicitud de reserva
    if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
        resp.message("🔄 Procesando tu solicitud de reserva, por favor espera un momento...")
        
        parsed_data = parse_reservation_details(incoming_msg)

        if parsed_data:
        
            validation_success, processed_data, validation_errors = validate_and_process_reservation_data(parsed_data, from_number)
            
            if validation_success:
                # Datos válidos - mostrar confirmación de reserva
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
                
                
        else:
            # Error en el LLM
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

    # Procesamiento normal con el Agente Conversacional si no hay flujo activo
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
            "- Tu correo electrónico de contacto\n"
            "- Método de pago preferido (efectivo, transferencia, tarjeta)\n"
            "- Comentarios especiales u observaciones adicionales\n\n"
            "Por favor, envíame toda esta información en un solo mensaje para procesar tu solicitud."
        )
    else:
        resp.message(agent_answer)
        print(f"[{from_number}] Respuesta: '{agent_answer}'")
    return str(resp)

def detectar_intencion_consulta(user_input: str) -> dict:
    """
    Detecta si el usuario está consultando disponibilidades
    """
    user_input_lower = user_input.lower()

    keywords_disponibilidad = [
        'disponible', 'disponibles', 'disponibilidad',
        'libre', 'libres', 'ocupado', 'ocupados',
        'fechas', 'calendario', 'cuando',
        'hay espacio', 'tienen cupo',
        'que domos', 'cual domo', 'cuales domos',
        'reservar para', 'puedo reservar',
        'esta libre', 'estan libres'
    ]

    keywords_encontradas = [kw for kw in keywords_disponibilidad if kw in user_input_lower]

    return {
        'es_consulta_disponibilidad': len(keywords_encontradas) > 0,
        'confianza': len(keywords_encontradas) / len(keywords_disponibilidad),
        'keywords_detectadas': keywords_encontradas
    }

# ENDPOINT PRINCIPAL PARA CHAT WEB DE WHATSAPP 
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() # Obtener JSON del request
    user_input = data.get("input", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))

    if not user_input: # Verificar si el campo 'input' esta presente
        return jsonify({"error": "Falta el campo 'input'"}), 400 

    if session_id not in user_memories: # Cargar o inicializar memoria del usuario
        user_memories[session_id] = load_user_memory(session_id)
    
    if session_id not in user_states: # Inicializar estado del usuario
        user_states[session_id] = {"current_flow": "none", "reserva_step": 0, "reserva_data": {}, "waiting_for_availability": False}

    memory = user_memories[session_id]
    user_state = user_states[session_id]

    response_output = "Lo siento, no pude procesar tu solicitud en este momento."
    
    #  SISTEMA DE MENÚ PRINCIPAL PARA /chat 
    
    # Verificar si es una memoria nueva (solo tiene mensajes del sistema)
    is_new_conversation = False
    if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
        # Si solo tiene 2 mensajes (system + assistant_response) es conversación nueva
        if len(memory.chat_memory.messages) <= 2:
            is_new_conversation = True
    
    # Si es un saludo en una conversación nueva, mostrar menú de bienvenida
    if is_greeting_message(user_input) and is_new_conversation:
        welcome_message = get_welcome_menu()
        response_output = welcome_message
        
        # Agregar este intercambio a la memoria
        try:
            from langchain.schema import HumanMessage, AIMessage
            memory.chat_memory.add_message(HumanMessage(content=user_input))
            memory.chat_memory.add_message(AIMessage(content=welcome_message))
        except (ImportError, AttributeError):
            try:
                memory.chat_memory.add_user_message(user_input)
                memory.chat_memory.add_ai_message(welcome_message)
            except:
                pass
        
        save_user_memory(session_id, memory)
        
        return jsonify({
            "session_id": session_id,
            "response": response_output,
            "memory": messages_to_dict(memory.chat_memory.messages)
        })
    
    # Manejar selecciones del menú principal (números 1-4)
    if is_menu_selection(user_input) and user_state["current_flow"] == "none":
        try:
            menu_response = handle_menu_selection(user_input, qa_chains)
            
            # Si la respuesta es un diccionario (opción 3), manejar estado especial
            if isinstance(menu_response, dict):
                response_output = menu_response["message"]
                if menu_response.get("set_waiting_for_availability"):
                    user_state["waiting_for_availability"] = True
            else:
                # Respuesta normal (string)
                response_output = menu_response
            
            # Agregar a la memoria
            try:
                from langchain.schema import HumanMessage, AIMessage
                memory.chat_memory.add_message(HumanMessage(content=user_input))
                memory.chat_memory.add_message(AIMessage(content=response_output))
            except (ImportError, AttributeError):
                try:
                    memory.chat_memory.add_user_message(user_input)
                    memory.chat_memory.add_ai_message(response_output)
                except:
                    pass
            
            save_user_memory(session_id, memory)
            
            return jsonify({
                "session_id": session_id,
                "response": response_output,
                "memory": messages_to_dict(memory.chat_memory.messages)
            })
        except Exception as e:
            print(f"Error en manejo de menú en /chat: {e}")
            response_output = "Disculpa, hubo un error procesando tu selección. ¿Podrías intentar de nuevo?"
            
            return jsonify({
                "session_id": session_id,
                "response": response_output,
                "memory": messages_to_dict(memory.chat_memory.messages)
            })

    # Manejar consultas de disponibilidad cuando el usuario está en modo "esperando disponibilidad"
    if user_state.get("waiting_for_availability", False) and user_state["current_flow"] == "none":
        try:
            availability_response = handle_availability_request(user_input)
            response_output = availability_response
            
            # Resetear el estado de espera
            user_state["waiting_for_availability"] = False
            
            # Agregar a la memoria
            try:
                from langchain.schema import HumanMessage, AIMessage
                memory.chat_memory.add_message(HumanMessage(content=user_input))
                memory.chat_memory.add_message(AIMessage(content=availability_response))
            except (ImportError, AttributeError):
                try:
                    memory.chat_memory.add_user_message(user_input)
                    memory.chat_memory.add_ai_message(availability_response)
                except:
                    pass
            
            save_user_memory(session_id, memory)
            
            return jsonify({
                "session_id": session_id,
                "response": response_output,
                "memory": messages_to_dict(memory.chat_memory.messages)
            })
        except Exception as e:
            print(f"Error procesando consulta de disponibilidad en /chat: {e}")
            response_output = "Disculpa, hubo un error procesando tu consulta. ¿Podrías intentar de nuevo?"
            user_state["waiting_for_availability"] = False
            
            return jsonify({
                "session_id": session_id,
                "response": response_output,
                "memory": messages_to_dict(memory.chat_memory.messages)
            })
    
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
            "-Correo electrónico de contacto\n"
            "-Método de pago preferido (efectivo, transferencia, tarjeta)\n"
            "-Comentarios especiales u observaciones adicionales\n\n"
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
        # ==================== FILTRO DE TEMAS PARA /chat ====================
        
        # Verificar si el mensaje está relacionado con glamping (excepto bypass)
        if not should_bypass_filter(user_input):
            if not is_glamping_related(user_input):
                print(f"[FILTRO] Mensaje off-topic bloqueado en /chat: '{user_input}'")
                off_topic_response = get_off_topic_response()
                response_output = off_topic_response
                
                # Agregar a la memoria
                try:
                    from langchain.schema import HumanMessage, AIMessage
                    memory.chat_memory.add_message(HumanMessage(content=user_input))
                    memory.chat_memory.add_message(AIMessage(content=off_topic_response))
                except (ImportError, AttributeError):
                    try:
                        memory.chat_memory.add_user_message(user_input)
                        memory.chat_memory.add_ai_message(off_topic_response)
                    except:
                        pass
                
                save_user_memory(session_id, memory)
                
                return jsonify({
                    "session_id": session_id,
                    "response": response_output,
                    "memory": messages_to_dict(memory.chat_memory.messages)
                })
        
        # Procesamiento normal con el agente robusto si no hay flujo de reserva activo
        
        # Detectar si es consulta de disponibilidad
        intencion = detectar_intencion_consulta(user_input)

        # Preparar el input para el agente
        agent_input = user_input
        
        if intencion['es_consulta_disponibilidad'] and intencion['confianza'] > 0.1:
            # Es muy probable que sea consulta de disponibilidad
            print(f"[CONSULTA] Detectada consulta de disponibilidad: {intencion['keywords_detectadas']}")
            
            # Forzar el uso de la herramienta de disponibilidades
            agent_input = f"""
El usuario está consultando sobre disponibilidades del glamping: "{user_input}"

INSTRUCCIÓN ESPECIAL: Debes usar la herramienta 'consultar_disponibilidades' para responder esta consulta.

Contexto de la consulta:
- Keywords detectadas: {intencion['keywords_detectadas']}
- Confianza: {intencion['confianza']:.2%}

Consulta original del usuario: {user_input}
"""
        
        # Inicializar agente con manejo robusto
        init_success, agent, init_error = initialize_agent_safe(tools, memory, max_retries=3)
        
        if not init_success:
            print(f"ERROR: Error al inicializar agente para {session_id}: {init_error}")
            response_output = "Disculpa, nuestro sistema conversacional está experimentando problemas temporales. Por favor, intenta de nuevo en un momento."
        else:
            # Ejecutar agente con manejo robusto
            run_success, result, run_error = run_agent_safe(agent, agent_input, max_retries=2)
            
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

# Endpoint para obtener todas las reservas Conexion con el frontend
@app.route('/api/reservas', methods=['GET']) # Endpoint para obtener todas las reservas
def get_reservas():
    
    try:
        # Verificar estado de la base de datos
        if not database_available or not db:
            return jsonify({
                'success': False,
                'error': 'Base de datos no disponible',
                'reservas': []
            }), 503
        
        # Obtener todas las reservas ordenadas por fecha de creación
        reservas = Reserva.query.order_by(Reserva.fecha_creacion.desc()).all()
        
        # Formatear datos para el frontend con mapeo correcto
        reservas_data = []
        for reserva in reservas:
            # Procesar servicios - convertir string a array de objetos
            servicios_array = []
            if reserva.servicio_elegido and reserva.servicio_elegido != 'Ninguno':
                # Dividir servicios por comas y crear objetos
                servicios_string = reserva.servicio_elegido
                servicios_lista = [s.strip() for s in servicios_string.split(',') if s.strip()]

                for servicio in servicios_lista:
                    servicios_array.append({
                        'nombre': servicio,
                        'precio': 0,  
                        'descripcion': ''
                    })

            # Calcular monto total (usar monto_total de BD o calcular básico)
            monto_total = 0
            if hasattr(reserva, 'monto_total') and reserva.monto_total:
                monto_total = float(reserva.monto_total)
            else:
                # Precio básico por domo (fallback)
                precios_base = {
                    'antares': 650000,
                    'polaris': 550000,
                    'sirius': 450000,
                    'centaury': 450000
                }
                domo_lower = (reserva.domo or '').lower()
                monto_total = precios_base.get(domo_lower, 450000)

            # Clasificar campos por importancia
            campos_importantes = {
                'numero': reserva.numero_whatsapp,
                'email': reserva.email_contacto,
                'numeroPersonas': reserva.cantidad_huespedes,
                'domo': reserva.domo,
                'fechaEntrada': reserva.fecha_entrada.strftime('%Y-%m-%d') if reserva.fecha_entrada else None,
                'fechaSalida': reserva.fecha_salida.strftime('%Y-%m-%d') if reserva.fecha_salida else None,
                'metodoPago': getattr(reserva, 'metodo_pago', 'Pendiente')
            }

            campos_opcionales = {
                'adicciones': reserva.adicciones or '',
                'servicios': servicios_array,
                'observaciones': getattr(reserva, 'comentarios_especiales', '')
            }

            # Validar campos importantes
            validacion = validar_campos_importantes_reserva({
                'numero_whatsapp': campos_importantes['numero'],
                'email_contacto': campos_importantes['email'],
                'cantidad_huespedes': campos_importantes['numeroPersonas'],
                'domo': campos_importantes['domo'],
                'fecha_entrada': campos_importantes['fechaEntrada'],
                'fecha_salida': campos_importantes['fechaSalida'],
                'metodo_pago': campos_importantes['metodoPago']
            })

            reserva_item = {
                'id': reserva.id,
                'nombre': reserva.nombres_huespedes or f"Usuario {reserva.numero_whatsapp}",

                
                **campos_importantes,

                
                **campos_opcionales,

                # METADATOS
                'montoAPagar': monto_total,
                'fecha_creacion': reserva.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if hasattr(reserva, 'fecha_creacion') and reserva.fecha_creacion else None,
                'estado': 'activa',

                # VALIDACIÓN
                'campos_completos': validacion['valido'],
                'campos_faltantes': validacion['campos_faltantes'],

                # RETROCOMPATIBILIDAD
                'servicio_elegido': reserva.servicio_elegido or 'Ninguno',
                'numero_contacto': reserva.numero_contacto or reserva.numero_whatsapp
            }
            reservas_data.append(reserva_item)
        
        return jsonify({
            'success': True,
            'count': len(reservas_data),
            'reservas': reservas_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error en endpoint GET /api/reservas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'reservas': []
        }), 500

@app.route('/api/reservas/stats', methods=['GET']) # Endpoint para obtener estadísticas de reservas
def get_reservas_stats():
    """
    Endpoint para obtener estadísticas de reservas
    """
    if not db or not Reserva:
        return jsonify({"error": "Base de datos no configurada"}), 500

    try:
        from sqlalchemy import func, extract
        from datetime import datetime, timedelta

        # Estadísticas básicas
        total_reservas = db.session.query(func.count(Reserva.id)).scalar()

        # Reservas por mes actual
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        reservas_mes = db.session.query(func.count(Reserva.id)).filter(
            extract('month', Reserva.fecha_creacion) == mes_actual,
            extract('year', Reserva.fecha_creacion) == año_actual
        ).scalar() if hasattr(Reserva, 'fecha_creacion') else 0

        # Domos más populares
        domos_populares = db.session.query(
            Reserva.domo, func.count(Reserva.id).label('count')
        ).filter(Reserva.domo.isnot(None)).group_by(Reserva.domo).all()

        return jsonify({
            "total_reservas": total_reservas or 0,
            "reservas_mes_actual": reservas_mes or 0,
            "domos_populares": [{"domo": d[0], "cantidad": d[1]} for d in domos_populares],
            "status": "success"
        }), 200

    except Exception as e:
        print(f"ERROR en get_reservas_stats: {e}")
        return jsonify({"error": str(e)}), 500

# ENDPOINT PARA CONSULTAR DISPONIBILIDADES 
def consultar_disponibilidades_interna(fecha_inicio=None, fecha_fin=None, domo=None, personas=None):
    """
    Función interna para consultar disponibilidades sin HTTP
    Reutilizable tanto por la herramienta del agente como por el endpoint REST
    """
    if not database_available or not db:
        return {
            'success': False,
            'error': 'Base de datos no disponible',
            'disponibilidades_por_fecha': {},
            'domos_disponibles': [],
            'mensaje': 'La base de datos no está disponible'
        }

    try:
        # Si no se especifican fechas, usar el próximo mes
        if not fecha_inicio:
            from datetime import datetime, timedelta
            hoy = datetime.now().date()
            fecha_inicio = hoy.strftime('%Y-%m-%d')
            fecha_fin = (hoy + timedelta(days=30)).strftime('%Y-%m-%d')
        elif not fecha_fin:
            from datetime import datetime, timedelta
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = (fecha_inicio_obj + timedelta(days=7)).strftime('%Y-%m-%d')

        # Obtener todas las reservas activas en el rango de fechas
        reservas_activas = Reserva.query.filter(
            Reserva.fecha_entrada <= fecha_fin,
            Reserva.fecha_salida >= fecha_inicio
        ).all()

        # Información de domos disponibles
        domos_info = {
            'antares': {
                'nombre': 'Antares',
                'capacidad_maxima': 2,
                'descripcion': 'Nido de amor con jacuzzi privado',
                'precio_base': 650000,
                'caracteristicas': ['Jacuzzi privado', 'Vista panorámica', 'Ideal para parejas']
            },
            'polaris': {
                'nombre': 'Polaris',
                'capacidad_maxima': 6,
                'descripcion': 'Amplio domo familiar con sofá cama',
                'precio_base': 550000,
                'caracteristicas': ['Sofá cama', 'Espacio amplio', 'Ideal para familias']
            },
            'sirius': {
                'nombre': 'Sirius',
                'capacidad_maxima': 2,
                'descripcion': 'Domo acogedor de un piso',
                'precio_base': 450000,
                'caracteristicas': ['Un piso', 'Acogedor', 'Vista al valle']
            },
            'centaury': {
                'nombre': 'Centaury',
                'capacidad_maxima': 2,
                'descripcion': 'Domo íntimo con ambiente romántico',
                'precio_base': 450000,
                'caracteristicas': ['Ambiente romántico', 'Decoración especial', 'Privacidad']
            }
        }

        # Calcular disponibilidades día por día
        from datetime import datetime, timedelta
        fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_limite = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        disponibilidades_por_fecha = {}
        domos_disponibles_resumen = []
        fechas_completamente_libres = []

        while fecha_actual <= fecha_limite:
            fecha_str = fecha_actual.strftime('%Y-%m-%d')

            # Encontrar reservas que ocupan esta fecha
            reservas_del_dia = [r for r in reservas_activas
                              if r.fecha_entrada <= fecha_actual < r.fecha_salida]

            domos_ocupados = [r.domo.lower() for r in reservas_del_dia if r.domo]
            domos_disponibles = [domo for domo in domos_info.keys() if domo not in domos_ocupados]

            # Filtrar por capacidad si se especifica número de personas
            if personas:
                domos_disponibles = [
                    domo for domo in domos_disponibles
                    if domos_info[domo]['capacidad_maxima'] >= personas
                ]

            # Filtrar por domo específico si se solicita
            if domo:
                domo_lower = domo.lower()
                domos_disponibles = [domo for domo in domos_disponibles if domo == domo_lower]

            disponibilidades_por_fecha[fecha_str] = {
                'fecha': fecha_str,
                'fecha_formateada': fecha_actual.strftime('%A, %d de %B de %Y'),
                'domos_disponibles': domos_disponibles,
                'domos_ocupados': domos_ocupados,
                'total_disponibles': len(domos_disponibles),
                'es_fin_de_semana': fecha_actual.weekday() >= 5,
                'detalles_domos': {
                    domo: domos_info[domo] for domo in domos_disponibles
                }
            }

            # Recopilar información para resumen
            for domo in domos_disponibles:
                if domo not in [d['domo'] for d in domos_disponibles_resumen]:
                    domos_disponibles_resumen.append({
                        'domo': domo,
                        'info': domos_info[domo],
                        'fechas_disponibles': []
                    })

            # Agregar fechas a cada domo disponible
            for item in domos_disponibles_resumen:
                if item['domo'] in domos_disponibles:
                    item['fechas_disponibles'].append(fecha_str)

            # Identificar fechas completamente libres
            if len(domos_disponibles) == len(domos_info):
                fechas_completamente_libres.append(fecha_str)

            fecha_actual += timedelta(days=1)

        return {
            'success': True,
            'disponibilidades_por_fecha': disponibilidades_por_fecha,
            'domos_disponibles': domos_disponibles_resumen,
            'fechas_completamente_libres': fechas_completamente_libres,
            'parametros_busqueda': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'domo_especifico': domo,
                'personas': personas
            },
            'resumen': generar_recomendaciones_disponibilidades(domos_disponibles_resumen),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"ERROR Error en consultar_disponibilidades_interna: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'disponibilidades_por_fecha': {},
            'domos_disponibles': [],
            'mensaje': f'Error técnico: {str(e)}'
        }

@app.route('/api/disponibilidades', methods=['GET']) # Endpoint REST para consultar disponibilidades
def get_disponibilidades():
    
    try:
        # Obtener parámetros
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        domo_especifico = request.args.get('domo')
        personas = request.args.get('personas', type=int)

        # Usar función interna compartida
        resultado = consultar_disponibilidades_interna(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            domo=domo_especifico,
            personas=personas
        )

        return jsonify(resultado), 200

    except Exception as e:
        print(f"ERROR Error en get_disponibilidades: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'disponibilidades_por_fecha': {},
            'domos_disponibles': []
        }), 500


def generar_recomendaciones_disponibilidad(domos_disponibles, fechas_libres, personas, domo_especifico):
    """
    Genera recomendaciones en lenguaje natural para el agente IA
    """
    recomendaciones = []

    if not domos_disponibles:
        return ["No hay disponibilidad en las fechas consultadas. Sugiere fechas alternativas al cliente."]

    # Recomendaciones por número de personas
    if personas:
        if personas <= 2:
            domos_pareja = [d for d in domos_disponibles if d['info']['capacidad_maxima'] == 2]
            if domos_pareja:
                recomendaciones.append(f"Para {personas} persona(s), recomiendo especialmente: {', '.join([d['info']['nombre'] for d in domos_pareja[:2]])}")

        elif personas > 2:
            domos_familiares = [d for d in domos_disponibles if d['info']['capacidad_maxima'] > 2]
            if domos_familiares:
                recomendaciones.append(f"Para {personas} personas, el domo ideal es: {domos_familiares[0]['info']['nombre']} (capacidad: {domos_familiares[0]['info']['capacidad_maxima']})")
            else:
                recomendaciones.append(f"Para {personas} personas, lamentablemente ningún domo tiene capacidad suficiente en estas fechas.")

    # Recomendaciones por fechas
    if fechas_libres:
        if len(fechas_libres) >= 3:
            recomendaciones.append(f"Excelente disponibilidad: {len(fechas_libres)} fechas con todos los domos libres.")
        else:
            recomendaciones.append(f"Disponibilidad limitada: solo {len(fechas_libres)} fechas con plena disponibilidad.")

    # Recomendaciones específicas por domo
    if domo_especifico:
        domo_solicitado = next((d for d in domos_disponibles if d['domo'] == domo_especifico.lower()), None)
        if domo_solicitado:
            recomendaciones.append(f"¡Buenas noticias! El domo {domo_solicitado['info']['nombre']} está disponible en {len(domo_solicitado['fechas_disponibles'])} fechas.")
        else:
            recomendaciones.append(f"El domo {domo_especifico} no está disponible en estas fechas. Ofrece alternativas similares.")

    # Recomendaciones generales
    if len(domos_disponibles) > 0:
        mejor_opcion = max(domos_disponibles, key=lambda x: len(x['fechas_disponibles']))
        recomendaciones.append(f"Mayor disponibilidad: {mejor_opcion['info']['nombre']} ({len(mejor_opcion['fechas_disponibles'])} fechas disponibles)")

    return recomendaciones

@app.route('/api/agente/disponibilidades', methods=['POST']) # Endpoint especializado para consultas del agente IA
def agente_consultar_disponibilidades():
    # Acepta consultas en lenguaje natural y devuelve respuestas estructuradas
    if not database_available or not db:
        return jsonify({
            'respuesta_agente': 'Lo siento, no puedo consultar las disponibilidades en este momento. La base de datos no está disponible.',
            'tiene_disponibilidad': False
        }), 503

    try:
        data = request.get_json()
        consulta_usuario = data.get('consulta', '')

        # Extraer parámetros de la consulta (esto se puede mejorar con NLP)
        parametros_extraidos = extraer_parametros_consulta(consulta_usuario)

        # Realizar consulta de disponibilidades
        query_params = {}
        if parametros_extraidos['fecha_inicio']:
            query_params['fecha_inicio'] = parametros_extraidos['fecha_inicio']
        if parametros_extraidos['fecha_fin']:
            query_params['fecha_fin'] = parametros_extraidos['fecha_fin']
        if parametros_extraidos['domo']:
            query_params['domo'] = parametros_extraidos['domo']
        if parametros_extraidos['personas']:
            query_params['personas'] = parametros_extraidos['personas']

        # Simular llamada interna al endpoint de disponibilidades
        with app.test_request_context(f'/api/disponibilidades', query_string=query_params):
            respuesta_disponibilidades = get_disponibilidades()
            data_disponibilidades = respuesta_disponibilidades[0].get_json()

        if not data_disponibilidades['success']:
            return jsonify({
                'respuesta_agente': 'No pude consultar las disponibilidades. Inténtalo más tarde.',
                'tiene_disponibilidad': False
            }), 500

        # Generar respuesta en lenguaje natural para el agente
        respuesta_natural = generar_respuesta_natural_disponibilidades(
            data_disponibilidades,
            parametros_extraidos,
            consulta_usuario
        )

        return jsonify({
            'respuesta_agente': respuesta_natural,
            'tiene_disponibilidad': len(data_disponibilidades['domos_disponibles']) > 0,
            'datos_tecnicos': data_disponibilidades,
            'parametros_detectados': parametros_extraidos,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        print(f"Error en /api/agente/disponibilidades: {str(e)}")
        return jsonify({
            'respuesta_agente': 'Lo siento, ocurrió un error al consultar las disponibilidades. Por favor inténtalo de nuevo.',
            'tiene_disponibilidad': False,
            'error_tecnico': str(e)
        }), 500


def extraer_parametros_consulta(consulta):
    """
    Extrae parámetros de una consulta en lenguaje natural para disponibilidades
    """
    import re
    from datetime import datetime, timedelta

    parametros = {
        'fecha_inicio': None,
        'fecha_fin': None,
        'domo': None,
        'personas': None
    }

    consulta_lower = consulta.lower()
    print(f"[ANALISIS] Analizando consulta: '{consulta_lower}'")

    # PATRONES DE FECHA MEJORADOS PARA WHATSAPP
    patrones_fecha = [
        # DD/MM/YYYY o DD-MM-YYYY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dmy'),
        # YYYY-MM-DD
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'ymd'),
        # "24 de diciembre del 2025" - NUEVO PATRÓN ESPECÍFICO
        (r'(\d{1,2})\s+de\s+(\w+)\s+del?\s+(\d{4})', 'dmy_texto_con_año'),
        # "24 de diciembre" (sin año)
        (r'(\d{1,2})\s+de\s+(\w+)(?!\s+del?\s+\d)', 'dmy_texto_sin_año'),
        # "diciembre 24, 2025"
        (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', 'mdy_texto'),
    ]

    meses_espanol = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
    }

    # Buscar fechas
    for patron, tipo in patrones_fecha:
        matches = re.findall(patron, consulta_lower)
        if matches:
            try:
                match = matches[0]
                print(f"📅 Fecha encontrada: {match}, tipo: {tipo}")

                if tipo == 'dmy':
                    dia, mes, año = int(match[0]), int(match[1]), int(match[2])
                    fecha_obj = datetime(año, mes, dia).date()
                elif tipo == 'ymd':
                    año, mes, dia = int(match[0]), int(match[1]), int(match[2])
                    fecha_obj = datetime(año, mes, dia).date()
                elif tipo == 'dmy_texto_con_año':
                    dia = int(match[0])
                    mes_nombre = match[1].lower()
                    año = int(match[2])
                    
                    if mes_nombre in meses_espanol:
                        mes = meses_espanol[mes_nombre]
                        fecha_obj = datetime(año, mes, dia).date()
                    else:
                        continue
                elif tipo == 'dmy_texto_sin_año':
                    dia = int(match[0])
                    mes_nombre = match[1].lower()
                    año = datetime.now().year
                    
                    if mes_nombre in meses_espanol:
                        mes = meses_espanol[mes_nombre]
                        # Si la fecha ya pasó este año, usar el próximo año
                        fecha_tentativa = datetime(año, mes, dia).date()
                        if fecha_tentativa < datetime.now().date():
                            año += 1
                        fecha_obj = datetime(año, mes, dia).date()
                    else:
                        continue
                elif tipo == 'mdy_texto':
                    mes_nombre = match[0].lower()
                    dia = int(match[1])
                    año = int(match[2])
                    
                    if mes_nombre in meses_espanol:
                        mes = meses_espanol[mes_nombre]
                        fecha_obj = datetime(año, mes, dia).date()
                    else:
                        continue

                parametros['fecha_inicio'] = fecha_obj.strftime('%Y-%m-%d')
                print(f"✅ Fecha procesada: {parametros['fecha_inicio']}")
                break

            except Exception as e:
                print(f"ERROR Error procesando fecha {match}: {e}")
                continue

    # Detectar domos
    domos_nombres = {
        'antares': ['antares'],
        'polaris': ['polaris'],
        'sirius': ['sirius'],
        'centaury': ['centaury', 'centary']
    }

    for domo, aliases in domos_nombres.items():
        for alias in aliases:
            if alias in consulta_lower:
                parametros['domo'] = domo
                print(f"🏠 Domo detectado: {domo}")
                break

    # Detectar número de personas
    patrones_personas = [
        r'(\d+)\s+persona[s]?',
        r'para\s+(\d+)',
        r'somos\s+(\d+)',
        r'(\d+)\s+huespedes?'
    ]

    for patron in patrones_personas:
        match = re.search(patron, consulta_lower)
        if match:
            parametros['personas'] = int(match.group(1))
            print(f"👥 Personas detectadas: {parametros['personas']}")
            break

    # Si no se especifican fechas, usar los próximos 30 días
    if not parametros['fecha_inicio']:
        hoy = datetime.now().date()
        parametros['fecha_inicio'] = hoy.strftime('%Y-%m-%d')
        parametros['fecha_fin'] = (hoy + timedelta(days=30)).strftime('%Y-%m-%d')

    print(f"📊 Parámetros finales extraídos: {parametros}")
    return parametros


def generar_respuesta_natural_disponibilidades(datos_disponibilidades, parametros_extraidos, consulta_original):
    """
    Genera respuesta natural basada en datos de disponibilidades 
    """
    try:
        if not datos_disponibilidades.get('success'):
            return "Lo siento, no pude consultar las disponibilidades en este momento debido a un problema técnico."

        domos_disponibles = datos_disponibilidades.get('domos_disponibles', [])
        disponibilidades_por_fecha = datos_disponibilidades.get('disponibilidades_por_fecha', {})

        if not domos_disponibles:
            fecha_consultada = parametros_extraidos.get('fecha_inicio')
            if fecha_consultada:
                try:
                    fecha_formateada = datetime.strptime(fecha_consultada, '%Y-%m-%d').strftime('%d de %B de %Y')
                    return f"No tenemos domos disponibles para el {fecha_formateada}. ¿Te gustaría consultar otras fechas?"
                except:
                    return f"No tenemos domos disponibles para la fecha {fecha_consultada}. ¿Te gustaría consultar otras fechas?"
            else:
                return "No encontré domos disponibles para las fechas consultadas. ¿Podrías especificar otras fechas?"

        # Construir respuesta positiva
        respuesta = "¡Excelente! "

        # Si hay fecha específica
        if parametros_extraidos.get('fecha_inicio'):
            try:
                fecha_formateada = datetime.strptime(parametros_extraidos['fecha_inicio'], '%Y-%m-%d').strftime('%d de %B de %Y')
                respuesta += f"Para el {fecha_formateada} "
            except:
                respuesta += "Para la fecha consultada "
        else:
            respuesta += "Tenemos "

        # Listar domos disponibles
        if len(domos_disponibles) == 1:
            domo = domos_disponibles[0]
            respuesta += f"tenemos disponible el domo {domo['info']['nombre']} "
            respuesta += f"(capacidad para {domo['info']['capacidad_maxima']} personas, "
            respuesta += f"precio desde ${domo['info']['precio_base']:,}). "
            respuesta += f"{domo['info']['descripcion']}."
        else:
            respuesta += f"tenemos {len(domos_disponibles)} domos disponibles:\n\n"
            for i, domo in enumerate(domos_disponibles, 1):
                respuesta += f"{i}. *{domo['info']['nombre']}* - "
                respuesta += f"Capacidad: {domo['info']['capacidad_maxima']} personas, "
                respuesta += f"Precio: ${domo['info']['precio_base']:,}\n"
                respuesta += f"   {domo['info']['descripcion']}\n\n"

        # Agregar llamada a la acción
        respuesta += "\n¿Te gustaría hacer una reserva o necesitas más información sobre algún domo específico?"

        return respuesta

    except Exception as e:
        print(f"ERROR Error generando respuesta natural: {e}")
        return "Tenemos domos disponibles. ¿Te gustaría hacer una reserva?"

@app.route('/health', methods=['GET']) # Endpoint de salud mejorado
def health_check():
    """Health check endpoint para monitoreo mejorado"""
    try:
        # Status general de la aplicación
        app_status = 'healthy'

        # Status específico de base de datos
        db_status = 'connected' if database_available else 'disconnected'

        # Información adicional para debugging
        response = {
            'status': app_status,
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status,
            'database_url_configured': bool(database_url),
            'sqlalchemy_initialized': db is not None
        }

        # Si la BD no está disponible, devolver 503 
        if not database_available:
            response['status'] = 'degraded'
            return jsonify(response), 503

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'database': 'unknown'
        }), 500

@app.route('/api/reservas', methods=['POST']) # Endpoint para crear una nueva reserva
def create_reserva():
    """Crear nueva reserva con validación de campos importantes"""
    if not database_available:
        return jsonify({'error': 'Base de datos no disponible'}), 503

    try:
        data = request.get_json()

        # VALIDAR CAMPOS IMPORTANTES PRIMERO
        validacion = validar_campos_importantes_reserva(data)

        if not validacion['valido']:
            return jsonify({
                'success': False,
                'error': 'Campos importantes faltantes o inválidos',
                'errores_detalle': validacion['errores'],
                'campos_faltantes': validacion['campos_faltantes'],
                'requeridos': [
                    'numero_whatsapp (teléfono)',
                    'email_contacto (email)',
                    'cantidad_huespedes (personas)',
                    'domo',
                    'fecha_entrada',
                    'fecha_salida',
                    'metodo_pago'
                ]
            }), 400

        # Si los campos importantes están OK, crear la reserva
        nueva_reserva = Reserva(
            # CAMPOS IMPORTANTES
            numero_whatsapp=data['numero_whatsapp'],
            email_contacto=data['email_contacto'],
            cantidad_huespedes=int(data['cantidad_huespedes']),
            domo=data['domo'],
            fecha_entrada=datetime.strptime(data['fecha_entrada'], '%Y-%m-%d').date(),
            fecha_salida=datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date(),
            metodo_pago=data['metodo_pago'],

            # CAMPOS OPCIONALES (con valores por defecto)
            nombres_huespedes=data.get('nombres_huespedes', ''),
            servicio_elegido=data.get('servicio_elegido', ''),
            adicciones=data.get('adicciones', ''),
            comentarios_especiales=data.get('comentarios_especiales', ''),
            numero_contacto=data.get('numero_contacto', data['numero_whatsapp']),
            monto_total=data.get('monto_total', 0)
        )

        db.session.add(nueva_reserva)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Reserva creada exitosamente',
            'reserva_id': nueva_reserva.id,
            'campos_importantes_completos': True
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservas/<reserva_id>', methods=['PUT']) # Endpoint para actualizar una reserva existente 
def update_reserva(reserva_id):
    """Actualizar reserva existente"""
    if not database_available:
        return jsonify({'error': 'Base de datos no disponible'}), 503

    try:
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

# ENDPOINTS DE USUARIOS
@app.route('/api/usuarios', methods=['GET']) 
def get_usuarios():
    """Obtener lista de usuarios"""
    try:
        # Verificar si se solicitan contraseñas (solo para admin)
        include_passwords = request.args.get('include_passwords', 'false').lower() == 'true'

        usuarios = get_all_users(include_passwords=include_passwords)
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios', methods=['POST'])
def create_user_endpoint():
    """Crear nuevo usuario con contraseña generada"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Datos requeridos'}), 400

        # No requerir contraseña - se genera automáticamente
        result = create_user_function(
            data.get('nombre', ''),
            data.get('email', ''),
            data.get('password'),  # Opcional
            data.get('rol', 'limitado')
        )

        return jsonify({
            'success': True,
            'id': result['id'],
            'temp_password': result['temp_password'],  # Devolver para mostrar
            'message': 'Usuario creado exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
def update_user_endpoint(user_id):
    """Actualizar usuario"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Datos requeridos'}), 400

        success = update_user_function(
            user_id,
            data.get('nombre', ''),
            data.get('email', ''),
            data.get('rol', 'limitado'),
            data.get('activo', True)
        )
        if success:
            return jsonify({'success': True, 'message': 'Usuario actualizado'})
        return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
def delete_user_endpoint(user_id):
    """Eliminar usuario"""
    try:
        success = delete_user_function(user_id)
        if success:
            return jsonify({'success': True, 'message': 'Usuario eliminado'})
        return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# FUNCIÓN DE AUTENTICACIÓN DE USUARIOS
def authenticate_user(email, password):
    if not db or not Usuario:
        return None

    try:
        user = Usuario.query.filter_by(email=email, activo=True).first()
        if user and check_password_hash(user.password_hash, password):
            # Actualizar último acceso
            user.ultimo_acceso = datetime.utcnow()
            db.session.commit()
            return {
                'id': user.id,
                'nombre': user.nombre,
                'email': user.email,
                'rol': user.rol
            }
        return None
    except Exception as e:
        print(f"Error en authenticate_user: {e}")
        return None

# Backend Panel login
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login de usuario con validación de PostgreSQL"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Datos requeridos'}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email y contraseña requeridos'}), 400

        # Autenticar contra PostgreSQL
        user = authenticate_user(email, password)
        if user:
            return jsonify({
                'success': True,
                'user': user,
                'message': 'Login exitoso'
            })

        return jsonify({'error': 'Credenciales inválidas'}), 401

    except Exception as e:
        print(f"Error en login endpoint: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/verify', methods=['GET'])
def verify_user():
    """Verificar que el sistema de usuarios funciona"""
    try:
        if not db or not Usuario:
            return jsonify({'error': 'Base de datos no disponible'}), 500

        total_users = Usuario.query.count()
        return jsonify({
            'total_users': total_users,
            'database_connected': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/<int:user_id>/regenerate-password', methods=['POST'])
def regenerate_password(user_id):
    """Regenerar contraseña para un usuario"""
    try:
        if not db or not Usuario:
            return jsonify({'error': 'Base de datos no disponible'}), 500

        user = Usuario.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Generar nueva contraseña
        new_password = generate_simple_password()
        user.password_hash = generate_password_hash(new_password)
        user.temp_password = new_password
        user.password_changed = False

        db.session.commit()

        return jsonify({
            'success': True,
            'temp_password': new_password,
            'message': 'Contraseña regenerada exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Import and register the modular WhatsApp routes
# This is done after all functions and variables are defined to maintain compatibility
try:
    from routes.whatsapp_routes import register_whatsapp_routes
    
    # Register the new modular WhatsApp routes
    # Pass all dependencies that the extracted route needs
    register_whatsapp_routes(
        app=app,
        db=db,
        user_memories=user_memories,
        user_states=user_states,
        tools=tools,
        qa_chains=qa_chains,
        load_user_memory=load_user_memory,
        save_user_memory=save_user_memory,
        is_greeting_message=is_greeting_message,
        get_welcome_menu=get_welcome_menu,
        is_menu_selection=is_menu_selection,
        handle_menu_selection=handle_menu_selection,
        handle_availability_request=handle_availability_request,
        parse_reservation_details=parse_reservation_details,
        validate_and_process_reservation_data=validate_and_process_reservation_data,
        calcular_precio_reserva=calcular_precio_reserva,
        Reserva=Reserva,
        save_reservation_to_pinecone=save_reservation_to_pinecone,
        initialize_agent_safe=initialize_agent_safe,
        run_agent_safe=run_agent_safe
    )
    print("OK: Módulo WhatsApp routes registrado correctamente")
except ImportError as e:
    print(f"WARNING: No se pudo importar el módulo WhatsApp routes: {e}")
    print("INFO: Usando implementación original en agente.py")

@app.route("/")
def home():
    return "Servidor Flask con Agente RAG y WhatsApp conectado. La memoria del agente ahora es persistente."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)