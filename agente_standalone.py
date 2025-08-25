# Aplicación principal completamente modular 
# Reemplaza completamente agente.py y agente_modular.py

import os
import sys
from typing import Dict, Any, Optional

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Configuración centralizada
from config.app_config import create_app
from config.database_config import init_database_config

# Servicios modulares
from services.llm_service import initialize_llm_service
from services.database_service import DatabaseService
from services.availability_service import AvailabilityService
from services.user_service import UserService
from services.validation_service import ValidationService
from services.reservation_service import ReservationService
from services.rag_tools_service import get_rag_tools_service, create_rag_tools
from services.persistent_state_service import PersistentStateService, CompatibilityStateManager
from services.memory_service import create_memory_directory
from migrations.create_conversation_state_table import run_migration

# Rutas modulares
from routes.whatsapp_routes import register_whatsapp_routes
from routes.chat_routes import register_chat_routes
from routes.api_routes import register_api_routes

# Utilidades
from utils.logger import get_logger

# Configurar logger principal
logger = get_logger(__name__)

class StandaloneAgent:
    """
    Aplicación principal completamente modular
    No depende de agente.py
    """
    
    def __init__(self):
        """Inicializar aplicación standalone"""
        self.app = None
        self.db = None
        self.database_config = None
        self.llm_service = None
        self.services = {}
        self.user_states = {}
        self.user_memories = {}
        
        logger.info("StandaloneAgent inicializado", 
                   extra={"component": "standalone_agent", "phase": "startup"})
    
    def initialize_app(self) -> bool:
        """
        Inicializa la aplicación Flask
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando aplicación Flask", 
                       extra={"component": "standalone_agent", "action": "init_app"})
            
            # Crear aplicación Flask
            self.app = create_app(validate_env=True)
            
            if not self.app:
                logger.error("Error creando aplicación Flask", 
                            extra={"component": "standalone_agent"})
                return False
            
            logger.info("Aplicación Flask inicializada exitosamente", 
                       extra={"component": "standalone_agent"})
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando aplicación: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def initialize_database(self) -> bool:
        """
        Inicializa configuración de base de datos
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando configuración de base de datos", 
                       extra={"component": "standalone_agent", "action": "init_database"})
            
            if not self.app:
                logger.error("Aplicación Flask no inicializada", 
                            extra={"component": "standalone_agent"})
                return False
            
            # Inicializar configuración de base de datos
            self.database_config = init_database_config(self.app)
            
            if self.database_config:
                self.db = self.database_config.db
                logger.info(f"Base de datos inicializada: {self.database_config.database_available}", 
                           extra={"component": "standalone_agent", "db_available": self.database_config.database_available})
                return True
            else:
                logger.warning("Configuración de base de datos no disponible", 
                              extra={"component": "standalone_agent"})
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def initialize_llm(self) -> bool:
        """
        Inicializa servicio de LLM
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando servicio LLM", 
                       extra={"component": "standalone_agent", "action": "init_llm"})
            
            # Inicializar servicio LLM
            self.llm_service = initialize_llm_service()
            
            if self.llm_service and self.llm_service.llm:
                logger.info("Servicio LLM inicializado exitosamente", 
                           extra={"component": "standalone_agent", "llm_available": True})
                return True
            else:
                logger.warning("Servicio LLM no disponible", 
                              extra={"component": "standalone_agent"})
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando LLM: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def initialize_services(self) -> bool:
        """
        Inicializa todos los servicios modulares
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando servicios modulares", 
                       extra={"component": "standalone_agent", "action": "init_services"})
            
            # Inicializar servicios básicos
            self.services['validation_service'] = ValidationService()
            self.services['validation'] = self.services['validation_service']  # Compatibilidad
            
            # Servicios que requieren base de datos
            if self.db and self.database_config:
                Reserva = self.database_config.Reserva
                Usuario = self.database_config.Usuario
                
                if Reserva and Usuario:
                    self.services['database'] = DatabaseService(self.db, Reserva, Usuario)
                    self.services['user'] = UserService(self.db, Usuario)
                    
                if Reserva:
                    self.services['availability'] = AvailabilityService(self.db, Reserva)
                    self.services['reservation'] = ReservationService(self.db, Reserva)
            
            # Servicio RAG
            if self.llm_service and self.llm_service.qa_chains:
                self.services['rag_tools'] = get_rag_tools_service(self.llm_service.qa_chains)
            
            logger.info(f"Servicios inicializados: {len(self.services)}", 
                       extra={"component": "standalone_agent", "services_count": len(self.services)})
            
            return len(self.services) > 0
            
        except Exception as e:
            logger.error(f"Error inicializando servicios: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def initialize_memory_system(self) -> bool:
        """
        Inicializa sistema de memoria
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando sistema de memoria", 
                       extra={"component": "standalone_agent", "action": "init_memory"})
            
            # Crear directorio de memoria
            create_memory_directory()
            
            # Inicializar estado persistente si la base de datos está disponible
            if self.db:
                try:
                    # Ejecutar migración con contexto de aplicación Flask
                    with self.app.app_context():
                        migration_success = run_migration(self.db, self.user_states, self.user_memories)
                    
                    if migration_success:
                        # Inicializar servicio persistente
                        persistent_state_service = PersistentStateService(self.db, enable_caching=True)
                        compatibility_manager = CompatibilityStateManager(persistent_state_service)
                        
                        # Reemplazar diccionarios con versiones persistentes
                        self.user_states = compatibility_manager.create_compatible_user_states()
                        self.user_memories = compatibility_manager.create_compatible_user_memories()
                        
                        logger.info("Sistema de estado persistente inicializado", 
                                   extra={"component": "standalone_agent", "persistent": True})
                    else:
                        logger.warning("Migración falló, usando sistema volátil", 
                                      extra={"component": "standalone_agent"})
                        
                except Exception as e:
                    logger.warning(f"Error en estado persistente: {e}, usando sistema volátil", 
                                  extra={"component": "standalone_agent"})
            else:
                logger.info("Usando sistema de memoria volátil", 
                           extra={"component": "standalone_agent", "persistent": False})
            
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando sistema de memoria: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def create_tools(self) -> list:
        """
        Crea herramientas para el agente
        
        Returns:
            list: Lista de herramientas
        """
        try:
            tools = []
            
            # Crear herramientas RAG si están disponibles
            if 'rag_tools' in self.services:
                tools = create_rag_tools(
                    self.services['rag_tools'], 
                    self.services.get('availability')  # Puede ser None si no hay BD
                )
            
            logger.info(f"Herramientas creadas: {len(tools)}", 
                       extra={"component": "standalone_agent", "tools_count": len(tools)})
            
            return tools
            
        except Exception as e:
            logger.error(f"Error creando herramientas: {e}", 
                        extra={"component": "standalone_agent"})
            return []
    
    def register_routes(self) -> bool:
        """
        Registra todas las rutas modulares
        
        Returns:
            bool: True si el registro fue exitoso
        """
        try:
            logger.info("Registrando rutas modulares", 
                       extra={"component": "standalone_agent", "action": "register_routes"})
            
            if not self.app:
                logger.error("Aplicación Flask no disponible", 
                            extra={"component": "standalone_agent"})
                return False
            
            # Crear herramientas
            tools = self.create_tools()
            
            # Funciones auxiliares (implementación básica)
            def load_user_memory(user_id: str):
                # Implementación básica de carga de memoria con límite de tokens
                from langchain.memory import ConversationBufferWindowMemory
                # Usar window memory para limitar contexto a últimos 5 intercambios
                return ConversationBufferWindowMemory(
                    memory_key="chat_history", 
                    return_messages=True,
                    k=5  # Solo mantener últimos 5 intercambios
                )
            
            def save_user_memory(user_id: str, memory):
                # Implementación básica de guardado de memoria
                pass
            
            def is_greeting_message(message: str) -> bool:
                # Use the improved ValidationService for greeting detection
                if 'validation' in self.services:
                    return self.services['validation'].is_greeting_message(message)
                else:
                    # Fallback to basic detection
                    greetings = ['hola', 'holi', 'hello', 'hi', 'buenas', 'saludos', 'holiwis', 'hey']
                    return any(greeting in message.lower() for greeting in greetings)
            
            def handle_menu_selection(selection: str, qa_chains: dict) -> str:
                try:
                    # Use the new menu service instead of the dummy response
                    from services.validation_service import ValidationService
                    from services.menu_service import create_menu_service
                    
                    validation_service = ValidationService()
                    menu_service = create_menu_service(qa_chains, validation_service)
                    
                    # Create a dummy user_state for the menu service
                    user_state = {"current_flow": "none"}
                    
                    result = menu_service.handle_menu_selection(selection, user_state)
                    
                    # Handle dictionary responses (some menu options return dicts)
                    if isinstance(result, dict):
                        return result.get("message", str(result))
                    
                    return result
                except Exception as e:
                    logger.error(f"Error en handle_menu_selection: {e}")
                    return f"Error procesando la opción {selection}. Intenta de nuevo."
            
            def handle_availability_request(message: str) -> str:
                if 'availability' in self.services:
                    return self.services['availability'].consultar_disponibilidades_natural(message)
                return "Servicio de disponibilidades no disponible en este momento."
            
            # Funciones de reserva
            def parse_reservation_details(user_input: str):
                if 'reservation' in self.services:
                    return self.services['reservation'].parse_reservation_details(user_input)
                return False, {}, "Servicio de reservas no disponible"
            
            def validate_and_process_reservation_data(parsed_data: dict, from_number: str):
                if 'reservation' in self.services:
                    return self.services['reservation'].validate_and_process_reservation_data(parsed_data, from_number)
                return False, parsed_data, ["Servicio de reservas no disponible"]
            
            def calcular_precio_reserva(*args, **kwargs):
                if 'reservation' in self.services:
                    return self.services['reservation'].calcular_precio_reserva(*args, **kwargs)
                return False, 0.0, "Servicio de reservas no disponible"
            
            def save_reservation_to_pinecone(phone: str, data: dict):
                if 'reservation' in self.services:
                    return self.services['reservation'].save_reservation_to_pinecone(phone, data)
                return False
            
            def initialize_agent_safe(tools_list, memory, max_retries=3):
                if self.llm_service:
                    return self.llm_service.initialize_agent_safe(tools_list, memory, max_retries)
                return False, None, "LLM service no disponible"
            
            def run_agent_safe(agent, user_input: str, user_id: str = "anonymous"):
                if self.llm_service:
                    return self.llm_service.run_agent_safe(agent, user_input, user_id=user_id)
                return False, "", "LLM service no disponible"
            
            def get_welcome_menu() -> str:
                """
                Función que genera el menú de bienvenida para WhatsApp
                """
                return """🌟 **¡Bienvenido a Glamping Brillo de Luna!** 🌟

🏞️ Tu escape perfecto en Guatavita, Colombia

**¿En qué puedo ayudarte hoy?**

1️⃣ 📍 **Información General** - Ubicación, concepto, contacto
2️⃣ 🏠 **Domos Disponibles** - Tipos, características, precios
3️⃣ 📅 **Consultar Disponibilidad** - Fechas libres para reservar
4️⃣ 🛎️ **Servicios Incluidos** - Qué incluye tu estadía
5️⃣ 📋 **Políticas del Glamping** - Normas y condiciones

💬 **Escribe el número de tu opción o pregúntame directamente**

✨ *Estoy aquí para hacer tu experiencia inolvidable*"""
            
            def is_menu_selection_standalone(message: str) -> bool:
                """
                Función que detecta si el mensaje es una selección del menú
                Replica la lógica del ValidationService
                """
                message_clean = message.lower().strip()
                
                # Detectar números directos (1-5)
                if message_clean in ['1', '2', '3', '4', '5']:
                    return True
                
                # Detectar variantes textuales
                menu_variants = {
                    '1': ['informacion', 'información', 'informacion general', 'información general'],
                    '2': ['domos', 'domos disponibles'],
                    '3': ['disponibilidad', 'consultar disponibilidad'],
                    '4': ['servicios', 'servicios incluidos'],
                    '5': ['politicas', 'políticas']
                }
                
                for option, variants in menu_variants.items():
                    for variant in variants:
                        if variant == message_clean or f" {variant}" in message_clean:
                            return True
                
                return False
            
            # Registrar rutas WhatsApp
            register_whatsapp_routes(
                app=self.app,
                db=self.db,
                user_memories=self.user_memories,
                user_states=self.user_states,
                tools=tools,
                qa_chains=self.llm_service.qa_chains if self.llm_service else {},
                load_user_memory=load_user_memory,
                save_user_memory=save_user_memory,
                is_greeting_message=is_greeting_message,
                handle_menu_selection=handle_menu_selection,
                handle_availability_request=handle_availability_request,
                parse_reservation_details=parse_reservation_details,
                validate_and_process_reservation_data=validate_and_process_reservation_data,
                calcular_precio_reserva=calcular_precio_reserva,
                Reserva=self.database_config.Reserva if self.database_config else None,
                save_reservation_to_pinecone=save_reservation_to_pinecone,
                initialize_agent_safe=initialize_agent_safe,
                run_agent_safe=run_agent_safe,
                # AGREGAR estos argumentos faltantes:
                get_welcome_menu=get_welcome_menu,
                is_menu_selection=is_menu_selection_standalone
            )
            
            # Registrar rutas Chat
            register_chat_routes(
                app=self.app,
                user_memories=self.user_memories,
                user_states=self.user_states,
                load_user_memory=load_user_memory,
                save_user_memory=save_user_memory,
                is_greeting_message=is_greeting_message,
                handle_menu_selection=handle_menu_selection,
                handle_availability_request=handle_availability_request,
                parse_reservation_details=parse_reservation_details,
                validate_and_process_reservation_data=validate_and_process_reservation_data,
                calcular_precio_reserva=calcular_precio_reserva,
                db=self.db,
                Reserva=self.database_config.Reserva if self.database_config else None,
                save_reservation_to_pinecone=save_reservation_to_pinecone,
                tools=tools,
                initialize_agent_safe=initialize_agent_safe,
                run_agent_safe=run_agent_safe,
                qa_chains=self.llm_service.qa_chains if self.llm_service else {},
                get_welcome_menu=get_welcome_menu,
                is_menu_selection=is_menu_selection_standalone
            )
            
            # Registrar rutas API
            register_api_routes(
                app=self.app,
                db=self.db,
                Reserva=self.database_config.Reserva if self.database_config else None,
                Usuario=self.database_config.Usuario if self.database_config else None,
                database_available=self.database_config.database_available if self.database_config else False,
                database_url=self.database_config.get_database_url() if self.database_config else None,
                database_service=self.services.get('database'),
                availability_service=self.services.get('availability')
            )
            
            # Ruta principal
            @self.app.route("/")
            def home():
                return "Servidor Flask con Agente RAG y WhatsApp conectado. Arquitectura 100% modular sin dependencias de agente.py."
            
            logger.info("Rutas registradas exitosamente", 
                       extra={"component": "standalone_agent"})
            
            return True
            
        except Exception as e:
            logger.error(f"Error registrando rutas: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def initialize_all(self) -> bool:
        """
        Inicializa todos los componentes de la aplicación
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Iniciando inicialización completa de StandaloneAgent", 
                       extra={"component": "standalone_agent", "action": "init_all"})
            
            # Inicializar componentes en orden
            steps = [
                ("Aplicación Flask", self.initialize_app),
                ("Base de datos", self.initialize_database),
                ("Servicio LLM", self.initialize_llm),
                ("Servicios modulares", self.initialize_services),
                ("Sistema de memoria", self.initialize_memory_system),
                ("Rutas", self.register_routes)
            ]
            
            for step_name, step_func in steps:
                logger.info(f"Inicializando: {step_name}", 
                           extra={"component": "standalone_agent", "step": step_name})
                
                success = step_func()
                
                if success:
                    logger.info(f"✓ {step_name} inicializado exitosamente", 
                               extra={"component": "standalone_agent", "step": step_name})
                else:
                    logger.warning(f"⚠ {step_name} falló, continuando...", 
                                  extra={"component": "standalone_agent", "step": step_name})
            
            logger.info("Inicialización completa de StandaloneAgent terminada", 
                       extra={"component": "standalone_agent", "success": True})
            
            return True
            
        except Exception as e:
            logger.error(f"Error en inicialización completa: {e}", 
                        extra={"component": "standalone_agent"})
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud de la aplicación
        
        Returns:
            Dict[str, Any]: Estado de salud completo
        """
        try:
            health = {
                'application': 'StandaloneAgent',
                'status': 'healthy',
                'components': {
                    'flask_app': self.app is not None,
                    'database_config': self.database_config is not None,
                    'database_available': self.database_config.database_available if self.database_config else False,
                    'llm_service': self.llm_service is not None and self.llm_service.llm is not None,
                    'services_count': len(self.services),
                    'memory_system': len(self.user_states) >= 0
                },
                'services': {}
            }
            
            # Estado de servicios individuales
            for service_name, service in self.services.items():
                if hasattr(service, 'get_health_status'):
                    health['services'][service_name] = service.get_health_status()
                else:
                    health['services'][service_name] = {'status': 'available'}
            
            # Estado general
            critical_components = ['flask_app', 'database_config']
            health['status'] = 'healthy' if all(health['components'][comp] for comp in critical_components) else 'degraded'
            
            return health
            
        except Exception as e:
            return {
                'application': 'StandaloneAgent',
                'status': 'error',
                'error': str(e)
            }
    
    def run(self, host: str = "0.0.0.0", port: Optional[int] = None, debug: bool = False):
        """Ejecuta la aplicación con configuraciones de producción"""
        try:
            if not self.app:
                logger.error("Aplicación no inicializada",
                            extra={"component": "standalone_agent"})
                return

            # Puerto por defecto
            if port is None:
                port = int(os.environ.get("PORT", 8080))

            # AGREGAR: Configuración de producción
            is_production = os.environ.get("ENV", "development") == "production"

            if is_production:
                # Configuración de seguridad para producción
                self.app.config['DEBUG'] = False
                self.app.config['TESTING'] = False

                logger.info(f"Iniciando servidor en modo PRODUCCIÓN {host}:{port}",
                           extra={"component": "standalone_agent", "mode": "production"})

                # Usar Gunicorn en producción (Railway lo maneja automáticamente)
                self.app.run(host=host, port=port, debug=False, threaded=True)
            else:
                logger.info(f"Iniciando servidor en modo DESARROLLO {host}:{port}",
                           extra={"component": "standalone_agent", "mode": "development"})
                self.app.run(host=host, port=port, debug=debug)

        except Exception as e:
            logger.error(f"Error ejecutando aplicación: {e}",
                        extra={"component": "standalone_agent"})


def main():
    """Función principal para ejecutar la aplicación standalone"""
    try:
        logger.info("=== INICIANDO GLAMPING BRILLO DE LUNA - ARQUITECTURA MODULAR ===", 
                   extra={"component": "main"})
        
        # Crear y configurar aplicación
        agent = StandaloneAgent()
        
        # Inicializar todos los componentes
        success = agent.initialize_all()
        
        if success:
            logger.info("Aplicación inicializada exitosamente", 
                       extra={"component": "main"})
            
            # Mostrar estado de salud
            health = agent.get_health_status()
            logger.info(f"Estado de salud: {health['status']}", 
                       extra={"component": "main", "health": health})
            
            # Ejecutar aplicación
            agent.run()
        else:
            logger.error("Error en inicialización de aplicación", 
                        extra={"component": "main"})
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Aplicación detenida por usuario", 
                   extra={"component": "main"})
    except Exception as e:
        logger.error(f"Error fatal en aplicación: {e}", 
                    extra={"component": "main"})
        sys.exit(1)


# Factory pattern implementation for Docker/Gunicorn deployment
def create_standalone_app():
    """Factory para crear la aplicación Flask"""
    try:
        logger.info("Creando aplicación con factory pattern", 
                   extra={"component": "standalone_agent"})
        
        # Crear instancia del agente
        agent = StandaloneAgent()
        
        # Usar initialize_all como método de inicialización completa
        success = agent.initialize_all()

        if not success:
            logger.error("Error en inicialización completa del sistema", 
                        extra={"component": "standalone_agent"})
            raise RuntimeError("Failed to initialize application")

        logger.info("Aplicación inicializada exitosamente", 
                   extra={"component": "standalone_agent"})
        return agent.app
        
    except Exception as e:
        logger.error(f"Error en factory de aplicación: {e}", 
                    extra={"component": "standalone_agent"})
        raise RuntimeError(f"Failed to initialize application: {e}")

# Variable app para Gunicorn
app = create_standalone_app()

# Para ejecución directa
if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)