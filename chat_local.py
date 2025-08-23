#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chat Local para Glamping Brillo de Luna
Interfaz de chat local para pruebas utilizando la arquitectura modular existente
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# AGREGAR: Cargar variables de entorno para desarrollo
load_dotenv('.env.local')  # Primero .env.local
load_dotenv()             # Luego .env principal

# Importar servicios necesarios
from services.conversation_service import process_chat_conversation
from services.llm_service import get_llm_service
from services.database_service import DatabaseService
from services.user_service import UserService
from services.validation_service import ValidationService
from services.reservation_service import ReservationService
from services.rag_tools_service import get_rag_tools_service
from services.availability_service import AvailabilityService
from services.memory_service import create_memory_directory
from services.personality_service import get_personality_service
from services.import_resolver import get_import_resolver

# Configuración
from config.database_config import init_database_config

# Utilidades
from utils.logger import get_logger

# Configurar logger
logger = get_logger(__name__)

# AGREGAR: Verificación y configuración de fallback
def setup_local_environment():
    """Configurar entorno para desarrollo local"""
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("⚠️  OPENAI_API_KEY no configurada")
        print("💡 Opciones:")
        print("1. Crear archivo .env.local con OPENAI_API_KEY=tu_key")
        print("2. Export OPENAI_API_KEY=tu_key")
        print("3. Continuar con modo fallback (funcionalidad limitada)")

        choice = input("¿Continuar sin API key? (y/n): ").lower()
        if choice != 'y':
            print("❌ Configuración cancelada")
            exit(1)
        else:
            print("✅ Continuando en modo fallback")
            os.environ['USE_FALLBACK_MODE'] = 'true'
    else:
        print(f"✅ OPENAI_API_KEY configurada: {api_key[:10]}...")

    return True

# AGREGAR: Llamar la función al inicio
setup_local_environment()

class ChatLocal:
    """Interfaz de chat local para pruebas del agente Glamping Brillo de Luna"""
    
    def __init__(self):
        """Inicializar chat local"""
        self.session_id = str(uuid.uuid4())
        self.user_memories = {}
        self.user_states = {}
        self.services_initialized = False
        
        # Servicios (diccionario modular)
        self.services = {}
        
        # Configuraciones
        self.database_config = None
        
        # Servicios individuales (compatibilidad)
        self.llm_service = None
        self.database_service = None
        self.user_service = None
        self.validation_service = None
        self.reservation_service = None
        self.availability_service = None
        self.personality_service = None
        
        # Tools y QA chains
        self.tools = []
        self.qa_chains = {}
        
        print("🌟 Glamping Brillo de Luna - Chat Local")
        print("=" * 50)
        
    def initialize_services(self):
        """Inicializar servicios para chat local (sin Flask app)"""
        try:
            logger.info("Inicializando servicios para chat local",
                       extra={"component": "chat_local", "action": "init_services"})

            # INICIALIZAR servicios básicos que no requieren Flask app
            self.services['validation'] = ValidationService()
            logger.info("✅ ValidationService inicializado")

            # INICIALIZAR LLM service (crítico para chat)
            if self.llm_service and self.llm_service.llm:
                logger.info("✅ LLMService disponible")
            else:
                logger.warning("⚠️  LLMService no disponible - funcionalidad limitada")

            # INTENTAR configuración de BD ligera (opcional para chat local)
            try:
                self.database_config = self._setup_lightweight_database()
                if self.database_config and self.database_config.database_available:
                    # Solo si BD está realmente disponible
                    self.services['database'] = DatabaseService(
                        self.database_config.db,
                        self.database_config.Reserva,
                        self.database_config.Usuario
                    )
                    self.services['reservation'] = ReservationService(
                        self.database_config.db,
                        self.database_config.Reserva
                    )
                    self.services['availability'] = AvailabilityService(
                        self.database_config.db,
                        self.database_config.Reserva
                    )
                    logger.info("✅ Servicios de BD inicializados")
                else:
                    logger.info("ℹ️  BD no disponible - usando modo solo-chat")
            except Exception as db_error:
                logger.warning(f"⚠️  BD no disponible: {db_error} - Continuando sin BD")

            # INICIALIZAR servicios RAG
            if self.llm_service and self.llm_service.qa_chains:
                from services.rag_tools_service import get_rag_tools_service
                self.services['rag_tools'] = get_rag_tools_service(self.llm_service.qa_chains)
                logger.info("✅ RAG tools inicializadas")
            else:
                logger.warning("⚠️  RAG tools no disponibles")

            # INICIALIZAR sistema de memoria
            memory_initialized = self.initialize_memory()
            if memory_initialized:
                logger.info("✅ Sistema de memoria inicializado")
            else:
                logger.warning("⚠️  Sistema de memoria no inicializado")

            # CREAR herramientas para el agente
            self.tools = self.create_tools()
            if self.tools:
                logger.info(f"✅ {len(self.tools)} herramientas creadas")
            else:
                logger.warning("⚠️  No se pudieron crear herramientas")

            successful_services = len(self.services)
            logger.info(f"✅ Servicios inicializados: {successful_services}",
                       extra={"component": "chat_local", "services_count": successful_services})

            return successful_services > 0

        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {e}",
                        extra={"component": "chat_local"})
            return False

    def _setup_lightweight_database(self):
        """Configurar BD ligera opcional para chat local"""
        try:
            # IMPORTAR sin crear app Flask
            from config.database_config import DatabaseConfig

            # CREAR configuración ligera
            db_config = DatabaseConfig()

            # VERIFICAR si hay URL de BD configurada
            database_url = db_config.get_database_url()
            if not database_url:
                logger.info("ℹ️  No hay URL de BD - Funcionando sin persistencia")
                return None

            # CREAR app Flask mínima solo para configurar BD
            from flask import Flask
            temp_app = Flask(__name__)
            temp_app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

            # INICIALIZAR BD con app temporal
            success = db_config.init_app(temp_app)
            if success:
                logger.info("✅ BD ligera configurada")
                return db_config
            else:
                logger.info("ℹ️  BD no disponible")
                return None

        except Exception as e:
            logger.warning(f"⚠️  Error configurando BD ligera: {e}")
            return None

    def initialize_memory(self):
        """Inicializar sistema de memoria para chat local"""
        try:
            logger.info("Inicializando memoria para chat local",
                       extra={"component": "chat_local", "action": "init_memory"})

            # CREAR directorio de memoria
            from services.memory_service import create_memory_directory
            create_memory_directory()

            # INICIALIZAR memoria volátil (más apropiada para testing)
            self.user_states = {}
            self.user_memories = {}

            # INTENTAR memoria persistente solo si BD está disponible
            if hasattr(self, 'services') and 'database' in self.services:
                try:
                    from services.persistent_state_service import PersistentStateService, CompatibilityStateManager

                    # SOLO crear si realmente hay BD configurada
                    db_config = getattr(self, 'database_config', None)
                    if db_config and db_config.database_available:
                        persistent_service = PersistentStateService(db_config.db, enable_caching=True)
                        compatibility_manager = CompatibilityStateManager(persistent_service)

                        self.user_states = compatibility_manager.create_compatible_user_states()
                        self.user_memories = compatibility_manager.create_compatible_user_memories()

                        logger.info("✅ Memoria persistente inicializada")
                    else:
                        logger.info("ℹ️  Usando memoria volátil (recomendado para testing)")
                except Exception as persist_error:
                    logger.warning(f"⚠️  Memoria persistente no disponible: {persist_error}")
                    logger.info("ℹ️  Usando memoria volátil")
            else:
                logger.info("ℹ️  Usando memoria volátil (sin BD)")

            logger.info("✅ Sistema de memoria inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando memoria: {e}",
                        extra={"component": "chat_local"})
            return False

    def create_tools(self):
        """Crear herramientas disponibles para chat local"""
        try:
            tools = []

            logger.info("Creando herramientas para chat local",
                       extra={"component": "chat_local", "action": "create_tools"})

            # CREAR herramientas RAG si están disponibles
            if 'rag_tools' in self.services:
                try:
                    from services.rag_tools_service import create_rag_tools
                    rag_tools = create_rag_tools(
                        self.services['rag_tools'],
                        self.services.get('availability')  # Puede ser None
                    )
                    tools.extend(rag_tools)
                    logger.info(f"✅ {len(rag_tools)} herramientas RAG creadas")
                except Exception as rag_error:
                    logger.warning(f"⚠️  Error creando herramientas RAG: {rag_error}")

            # CREAR herramientas básicas de fallback
            if not tools:
                logger.info("ℹ️  Creando herramientas básicas de fallback")
                tools = self._create_fallback_tools()

            logger.info(f"✅ Total herramientas creadas: {len(tools)}",
                       extra={"component": "chat_local", "tools_count": len(tools)})

            return tools

        except Exception as e:
            logger.error(f"❌ Error creando herramientas: {e}",
                        extra={"component": "chat_local"})
            return []

    def _create_fallback_tools(self):
        """Crear herramientas básicas de fallback para modo sin RAG"""
        from langchain.tools import Tool

        fallback_tools = []

        # HERRAMIENTA de información general
        def info_general(query: str) -> str:
            return """🌟 **Glamping Brillo de Luna**

📍 **Ubicación:** Guatavita, Colombia
🏞️ **Concepto:** Experiencia de lujo en contacto con la naturaleza
🏠 **Domos:** 4 tipos disponibles (Antares, Polaris, Sirius, Centaury)
📞 **Contacto:** WhatsApp: +57 305 461 4926

✨ *Modo de prueba local - Funcionalidad limitada*"""

        fallback_tools.append(Tool(
            name="informacion_general",
            description="Información general sobre Glamping Brillo de Luna",
            func=info_general
        ))

        # HERRAMIENTA de domos
        def info_domos(query: str) -> str:
            return """🏠 **Nuestros Domos:**

🌟 **Antares** - Domo romántico para 2 personas
🌟 **Polaris** - Domo familiar para 4 personas  
🌟 **Sirius** - Domo de lujo con jacuzzi
🌟 **Centaury** - Domo panorámico con vista

💰 Consulta precios y disponibilidad por WhatsApp

✨ *Modo de prueba local - Para información detallada contacta directamente*"""

        fallback_tools.append(Tool(
            name="domos_info",
            description="Información sobre los domos disponibles",
            func=info_domos
        ))

        return fallback_tools
    
    def load_user_memory(self, user_id):
        """Cargar memoria del usuario"""
        return self.user_service.load_user_memory(user_id)
    
    def save_user_memory(self, user_id, memory):
        """Guardar memoria del usuario"""
        return self.user_service.save_user_memory(user_id, memory)
    
    def is_greeting_message(self, message):
        """Detectar si es un mensaje de saludo"""
        return self.validation_service.is_greeting_message(message)
    
    def get_welcome_menu(self):
        """Obtener menú de bienvenida"""
        return self.validation_service.get_welcome_menu()
    
    def is_menu_selection(self, message):
        """Detectar selección de menú"""
        return self.validation_service.is_menu_selection(message)
    
    def handle_menu_selection(self, message, qa_chains, memory, save_memory_func, user_id):
        """Manejar selección de menú"""
        return self.validation_service.handle_menu_selection(
            message, qa_chains, memory, save_memory_func, user_id
        )
    
    def handle_availability_request(self, message, memory, save_memory_func, user_id):
        """Manejar solicitud de disponibilidad"""
        return self.availability_service.handle_availability_request(
            message, memory, save_memory_func, user_id
        )
    
    def parse_reservation_details(self, message):
        """Parsear detalles de reserva"""
        return self.reservation_service.parse_reservation_details(message)
    
    def validate_and_process_reservation_data(self, reservation_data):
        """Validar y procesar datos de reserva"""
        return self.reservation_service.validate_and_process_reservation_data(reservation_data)
    
    def calcular_precio_reserva(self, reservation_data):
        """Calcular precio de reserva"""
        return self.reservation_service.calcular_precio_reserva(reservation_data)
    
    def save_reservation_to_pinecone(self, reservation_data):
        """Guardar reserva en Pinecone"""
        return self.reservation_service.save_reservation_to_pinecone(reservation_data)
    
    def initialize_agent_safe(self, tools, memory, max_retries=3):
        """Inicializar agente de forma segura"""
        return self.llm_service.initialize_agent_safe(tools, memory, max_retries)
    
    def run_agent_safe(self, agent, user_input, max_retries=2):
        """Ejecutar agente de forma segura"""
        return self.llm_service.run_agent_safe(agent, user_input, max_retries)
    
    def process_message(self, user_input):
        """Procesar mensaje del usuario"""
        if not self.services_initialized:
            return "❌ Error: Servicios no inicializados. Ejecuta initialize_services() primero."
        
        try:
            # Usar process_chat_conversation del conversation service
            response_data = process_chat_conversation(
                user_input=user_input,
                session_id=self.session_id,
                user_memories=self.user_memories,
                user_states=self.user_states,
                load_user_memory_func=self.load_user_memory,
                save_user_memory_func=self.save_user_memory,
                is_greeting_message_func=self.is_greeting_message,
                get_welcome_menu_func=self.get_welcome_menu,
                is_menu_selection_func=self.is_menu_selection,
                handle_menu_selection_func=self.handle_menu_selection,
                handle_availability_request_func=self.handle_availability_request,
                parse_reservation_details_func=self.parse_reservation_details,
                validate_and_process_reservation_data_func=self.validate_and_process_reservation_data,
                calcular_precio_reserva_func=self.calcular_precio_reserva,
                db=self.database_service,
                Reserva=None,  # Se maneja dentro del servicio
                save_reservation_to_pinecone_func=self.save_reservation_to_pinecone,
                tools=self.tools,
                initialize_agent_safe_func=self.initialize_agent_safe,
                run_agent_safe_func=self.run_agent_safe,
                qa_chains=self.qa_chains
            )
            
            # Aplicar personalidad si está disponible
            response = response_data.get("response", "No hay respuesta disponible")
            if self.personality_service:
                response = self.personality_service.apply_personality_to_response(response, "general")
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Error procesando mensaje: {e}"
            logger.error(error_msg)
            return error_msg
    
    def run_interactive_chat(self):
        """Ejecutar chat interactivo"""
        # INICIALIZAR LLM service primero
        try:
            print("🔧 Inicializando LLM service...")
            self.llm_service = get_llm_service()
            self.llm_service.initialize_all()
            print("✅ LLM Service básico inicializado")
        except Exception as e:
            print(f"⚠️ LLM Service no disponible: {e}")
            
        if not self.initialize_services():
            print("❌ No se pudieron inicializar los servicios. Saliendo...")
            return
        
        print("\n🚀 Chat Local iniciado correctamente!")
        print("💬 Escribe 'salir', 'exit', 'quit' o 'q' para terminar")
        print("💬 Escribe 'limpiar' o 'clear' para limpiar la sesión")
        print("=" * 50)
        
        # Mostrar saludo inicial
        initial_greeting = self.personality_service.get_greeting_variations()[0] if self.personality_service else "¡Hola! ¿En qué puedo ayudarte?"
        print(f"\n🤖 Asistente: {initial_greeting}")
        
        while True:
            try:
                # Solicitar input del usuario
                user_input = input("\n👤 Tú: ").strip()
                
                # Comandos especiales
                if user_input.lower() in ['salir', 'exit', 'quit', 'q']:
                    print("\n👋 ¡Hasta luego! Gracias por usar Glamping Brillo de Luna")
                    break
                
                if user_input.lower() in ['limpiar', 'clear']:
                    self.session_id = str(uuid.uuid4())
                    self.user_memories.clear()
                    self.user_states.clear()
                    print("🔄 Sesión limpiada. Nueva sesión iniciada.")
                    continue
                
                if not user_input:
                    print("⚠️ Por favor, escribe tu mensaje.")
                    continue
                
                # Procesar mensaje
                print("🤖 Procesando...")
                response = self.process_message(user_input)
                print(f"\n🤖 Asistente: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrumpido. ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")
                logger.error(f"Error en chat interactivo: {e}")

def main():
    """Función principal"""
    print("🌟 Iniciando Glamping Brillo de Luna Chat Local...")
    
    try:
        # La configuración ya fue verificada en setup_local_environment()
        print("🔧 Configuración de entorno completada")
        
        # Crear instancia de chat
        chat = ChatLocal()
        
        # Ejecutar chat interactivo
        chat.run_interactive_chat()
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        logger.error(f"Error fatal en main: {e}")

if __name__ == "__main__":
    main()