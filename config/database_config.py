# Configuración centralizada de base de datos - Extrae configuración de BD de agente.py
# Centraliza configuración, modelos y inicialización de SQLAlchemy

import os
from datetime import datetime
from flask import Flask
from utils.logger import get_logger, log_startup

# Importaciones para base de datos con manejo de errores
try:
    from flask_sqlalchemy import SQLAlchemy
except ImportError:
    raise ImportError("ERROR: No se pudo importar Flask-SQLAlchemy. Instala: pip install Flask-SQLAlchemy")

from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

# Inicializar logger para este módulo
logger = get_logger(__name__)

class DatabaseConfig:
    """
    Configuración centralizada de base de datos
    Maneja inicialización, configuración y modelos de SQLAlchemy
    """
    
    def __init__(self, app: Flask = None):
        """
        Inicializar configuración de base de datos
        
        Args:
            app: Instancia de Flask (opcional)
        """
        self.db = None
        self.database_available = False
        self.database_url = None
        self.Reserva = None
        self.Usuario = None
        
        if app:
            self.init_app(app)
        
        logger.info("Configuración de base de datos inicializada",
                   extra={"phase": "startup", "component": "database_config"})
    
    def get_database_url(self) -> str:
        """
        Obtener URL de base de datos desde variables de entorno
        Prioriza DATABASE_PRIVATE_URL > DATABASE_PUBLIC_URL > DATABASE_URL
        Detecta entorno local y evita URLs internas de Railway
        
        Returns:
            URL de base de datos o None si no está configurada
        """
        # Configuración prioritaria para Railway/producción
        DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
        DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL')
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL
        
        # Verificar si estamos en entorno local y la URL es interna de Railway
        if database_url and "railway.internal" in database_url:
            logger.warning("Detectada URL interna de Railway en entorno local - Deshabilitando BD", 
                         extra={"phase": "startup"})
            return None
        
        # Logging de configuración seleccionada
        if DATABASE_PRIVATE_URL:
            log_startup(logger, "Usando DATABASE_PRIVATE_URL (sin costos de egress)", "SUCCESS", "")
        elif DATABASE_PUBLIC_URL:
            logger.warning("Usando DATABASE_PUBLIC_URL (puede generar costos de egress)", 
                         extra={"phase": "startup"})
            print("TIP: Usa DATABASE_PRIVATE_URL para evitar costos")
        elif DATABASE_URL:
            logger.info("Usando DATABASE_URL genérica", extra={"phase": "startup"})
        else:
            logger.warning("Ninguna DATABASE_URL configurada - Funcionalidad de base de datos deshabilitada", 
                         extra={"phase": "startup"})
            print("TIP: Configura DATABASE_PRIVATE_URL, DATABASE_PUBLIC_URL o DATABASE_URL")
        
        return database_url
    
    def init_app(self, app: Flask) -> bool:
        """
        Inicializar configuración de base de datos para la aplicación Flask
        
        Args:
            app: Instancia de Flask
            
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        try:
            # Obtener URL de base de datos
            self.database_url = self.get_database_url()
            
            if not self.database_url:
                self.database_available = False
                return False
            
            # Configurar Flask-SQLAlchemy
            app.config['SQLALCHEMY_DATABASE_URI'] = self.database_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_pre_ping': True,  # Verificar conexiones antes de usar
                'pool_recycle': 300,    # Reciclar conexiones cada 5 minutos
                'pool_timeout': 20,     # Timeout de conexión
                'max_overflow': 0       # No crear conexiones adicionales
            }
            
            # Inicializar SQLAlchemy
            self.db = SQLAlchemy(app)
            log_startup(logger, "SQLAlchemy inicializado correctamente", "SUCCESS", "")
            
            # Verificar conexión
            with app.app_context():
                try:
                    self.db.engine.connect()
                    self.database_available = True
                    log_startup(logger, "Conexión a base de datos verificada exitosamente", "SUCCESS", "")
                except Exception as conn_error:
                    logger.error(f"Error de conexión a BD: {conn_error}", extra={"phase": "startup"})
                    self.database_available = False
                    return False
            
            # Definir modelos después de la inicialización exitosa
            self._define_models()
            
            return True
            
        except Exception as e:
            warning_msg = f"WARNING: Error al inicializar la base de datos: {e}\n[TIP] Funcionalidad de base de datos deshabilitada"
            print(warning_msg)
            logger.error(f"Error inicializando base de datos: {e}", extra={"phase": "startup"})
            self.db = None
            self.database_available = False
            return False
    
    def _define_models(self):
        """Definir modelos de base de datos"""
        if not self.db:
            return
        
        # Modelo de Reserva
        class Reserva(self.db.Model):
            __tablename__ = 'reservas'
            id = self.db.Column(self.db.Integer, primary_key=True)

            # CAMPOS IMPORTANTES 
            numero_whatsapp = self.db.Column(self.db.String(50), nullable=False, index=True)        
            email_contacto = self.db.Column(self.db.String(100), nullable=False, index=True)        
            cantidad_huespedes = self.db.Column(self.db.Integer, nullable=False)        
            domo = self.db.Column(self.db.String(50), nullable=False, index=True)                   
            fecha_entrada = self.db.Column(self.db.Date, nullable=False, index=True)                
            fecha_salida = self.db.Column(self.db.Date, nullable=False, index=True)                 
            metodo_pago = self.db.Column(self.db.String(50), nullable=False, default='Pendiente')

            # CAMPOS OPCIONALES 
            nombres_huespedes = self.db.Column(self.db.String(255))                    
            servicio_elegido = self.db.Column(self.db.String(100))                     
            adicciones = self.db.Column(self.db.String(255))                           
            comentarios_especiales = self.db.Column(self.db.Text)                      
            numero_contacto = self.db.Column(self.db.String(50))

            # CAMPOS CALCULADOS
            monto_total = self.db.Column(self.db.Numeric(10, 2), default=0.00)
            fecha_creacion = self.db.Column(self.db.DateTime, default=datetime.utcnow, index=True)
            
            # CONSTRAINTS PARA PREVENIR RACE CONDITIONS
            __table_args__ = (
                # Prevenir reservas duplicadas exactas (mismo usuario, fechas y domo)
                self.db.UniqueConstraint(
                    'numero_whatsapp', 'domo', 'fecha_entrada', 'fecha_salida',
                    name='uq_reserva_usuario_domo_fechas'
                ),
                # Índice compuesto para consultas de disponibilidad (optimización + constraint)
                self.db.Index(
                    'idx_disponibilidad_domo_fechas',
                    'domo', 'fecha_entrada', 'fecha_salida'
                ),
                # Índice para búsquedas por usuario
                self.db.Index(
                    'idx_reservas_usuario_fecha',
                    'numero_whatsapp', 'fecha_creacion'
                ),
                # CHECK constraints para validación de datos
                self.db.CheckConstraint(
                    'cantidad_huespedes > 0 AND cantidad_huespedes <= 20',
                    name='chk_cantidad_huespedes_valida'
                ),
                self.db.CheckConstraint(
                    'fecha_salida > fecha_entrada',
                    name='chk_fechas_validas'
                ),
                self.db.CheckConstraint(
                    'monto_total >= 0',
                    name='chk_monto_no_negativo'
                )
            )

            def __repr__(self):
                return f'<Reserva {self.id}: {self.nombres_huespedes or "Usuario"}>'
            
            def to_dict(self):
                """Convertir reserva a diccionario para JSON"""
                return {
                    'id': self.id,
                    'numero_whatsapp': self.numero_whatsapp,
                    'email_contacto': self.email_contacto,
                    'cantidad_huespedes': self.cantidad_huespedes,
                    'domo': self.domo,
                    'fecha_entrada': self.fecha_entrada.isoformat() if self.fecha_entrada else None,
                    'fecha_salida': self.fecha_salida.isoformat() if self.fecha_salida else None,
                    'metodo_pago': self.metodo_pago,
                    'nombres_huespedes': self.nombres_huespedes,
                    'servicio_elegido': self.servicio_elegido,
                    'adicciones': self.adicciones,
                    'comentarios_especiales': self.comentarios_especiales,
                    'numero_contacto': self.numero_contacto,
                    'monto_total': float(self.monto_total) if self.monto_total else 0.0,
                    'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
                }

        # Modelo de Usuario
        class Usuario(self.db.Model):
            __tablename__ = 'usuarios'
            id = self.db.Column(self.db.Integer, primary_key=True)
            nombre = self.db.Column(self.db.String(100), nullable=False)
            email = self.db.Column(self.db.String(100), unique=True, nullable=False, index=True)
            password_hash = self.db.Column(self.db.String(255), nullable=False)
            temp_password = self.db.Column(self.db.String(50))
            rol = self.db.Column(self.db.String(20), default='limitado', nullable=False, index=True)
            fecha_creacion = self.db.Column(self.db.DateTime, default=datetime.utcnow, index=True)
            creado_por = self.db.Column(self.db.String(100), default='system')
            activo = self.db.Column(self.db.Boolean, default=True, index=True)
            ultimo_acceso = self.db.Column(self.db.DateTime, index=True)
            password_changed = self.db.Column(self.db.Boolean, default=False)
            
            # CONSTRAINTS PARA INTEGRIDAD Y SEGURIDAD
            __table_args__ = (
                # Índice para búsquedas de usuarios activos
                self.db.Index(
                    'idx_usuarios_activos',
                    'activo', 'fecha_creacion'
                ),
                # Índice para autenticación rápida
                self.db.Index(
                    'idx_usuarios_auth',
                    'email', 'activo'
                ),
                # CHECK constraints para validación
                self.db.CheckConstraint(
                    "rol IN ('admin', 'limitado')",
                    name='chk_rol_valido'
                ),
                self.db.CheckConstraint(
                    "email LIKE '%@%'",
                    name='chk_email_formato'
                ),
                self.db.CheckConstraint(
                    "LENGTH(nombre) >= 2",
                    name='chk_nombre_longitud_minima'
                )
            )

            def __repr__(self):
                return f'<Usuario {self.id}: {self.nombre} ({self.email})>'
            
            def to_dict(self, include_password=False):
                """Convertir usuario a diccionario para JSON"""
                user_dict = {
                    'id': self.id,
                    'nombre': self.nombre,
                    'email': self.email,
                    'rol': self.rol,
                    'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
                    'creado_por': self.creado_por,
                    'activo': self.activo,
                    'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
                    'password_changed': self.password_changed or False
                }
                
                # Solo incluir contraseña temporal si se solicita (para admin)
                if include_password and hasattr(self, 'temp_password') and self.temp_password:
                    user_dict['temp_password'] = self.temp_password
                
                return user_dict
            
            def set_password(self, password: str):
                """Establecer contraseña hasheada"""
                self.password_hash = generate_password_hash(password)
            
            def check_password(self, password: str) -> bool:
                """Verificar contraseña"""
                # Verificar contra password_hash (principal)
                if self.password_hash and check_password_hash(self.password_hash, password):
                    return True
                # Verificar contra temp_password (respaldo)
                elif hasattr(self, 'temp_password') and self.temp_password == password:
                    return True
                return False

        # Asignar modelos a la instancia
        self.Reserva = Reserva
        self.Usuario = Usuario
        
        logger.info("Modelos de base de datos definidos exitosamente",
                   extra={"phase": "startup", "component": "database_models"})
    
    def create_tables(self, app: Flask = None):
        """
        Crear todas las tablas en la base de datos
        
        Args:
            app: Instancia de Flask (opcional)
        """
        if not self.db or not self.database_available:
            logger.warning("Base de datos no disponible para crear tablas")
            return False
        
        try:
            if app:
                with app.app_context():
                    self.db.create_all()
            else:
                self.db.create_all()
            
            logger.info("Tablas de base de datos creadas exitosamente",
                       extra={"phase": "startup", "component": "database_tables"})
            return True
            
        except Exception as e:
            logger.error(f"Error creando tablas: {e}", extra={"phase": "startup"})
            return False
    
    def get_health_status(self) -> dict:
        """
        Obtener estado de salud de la configuración de base de datos
        
        Returns:
            Diccionario con información de salud
        """
        try:
            health_info = {
                "database_configured": self.database_url is not None,
                "database_available": self.database_available,
                "sqlalchemy_initialized": self.db is not None,
                "models_defined": self.Reserva is not None and self.Usuario is not None,
                "database_url_type": self._get_database_url_type(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test de conexión si está disponible
            if self.db and self.database_available:
                try:
                    with self.db.engine.connect() as connection:
                        result = connection.execute("SELECT 1")
                        health_info["connection_test"] = "success"
                except Exception as e:
                    health_info["connection_test"] = f"failed: {str(e)}"
            else:
                health_info["connection_test"] = "not_available"
            
            return health_info
            
        except Exception as e:
            return {
                "database_configured": False,
                "database_available": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_database_url_type(self) -> str:
        """Obtener tipo de URL de base de datos configurada"""
        if os.getenv('DATABASE_PRIVATE_URL'):
            return "private"
        elif os.getenv('DATABASE_PUBLIC_URL'):
            return "public"
        elif os.getenv('DATABASE_URL'):
            return "generic"
        else:
            return "none"

# Funciones de utilidad para generación de contraseñas
def generate_random_password(length=8) -> str:
    """
    Generar contraseña aleatoria segura
    
    Args:
        length: Longitud de la contraseña
        
    Returns:
        Contraseña generada
    """
    characters = string.ascii_letters + string.digits
    # Evitar caracteres confusos como 0, O, l, I
    characters = characters.replace('0', '').replace('O', '').replace('l', '').replace('I', '')
    
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def generate_simple_password() -> str:
    """
    Generar contraseña simple para usuarios
    
    Returns:
        Contraseña simple de 8 caracteres
    """
    return generate_random_password(8)

# Instancia global de configuración (se inicializa en agente_modular.py)
database_config = DatabaseConfig()

def get_database_config() -> DatabaseConfig:
    """
    Obtener instancia de configuración de base de datos
    
    Returns:
        Instancia de DatabaseConfig
    """
    return database_config

def init_database_config(app: Flask) -> DatabaseConfig:
    """
    Inicializar configuración de base de datos con aplicación Flask
    
    Args:
        app: Instancia de Flask
        
    Returns:
        Instancia configurada de DatabaseConfig
    """
    global database_config
    
    if not database_config.db:
        database_config.init_app(app)
    
    return database_config