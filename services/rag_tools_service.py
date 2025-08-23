# Servicio centralizado de herramientas RAG
# Extrae herramientas y funciones RAG de agente.py (líneas 706-1133)

from typing import List, Dict, Any, Optional
from langchain.tools import Tool, BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)

class RAGToolsService:
    """
    Servicio centralizado para herramientas RAG
    Consolida todas las herramientas de consulta y funciones RAG
    """
    
    def __init__(self, qa_chains: Dict[str, Any]):
        """
        Inicializar servicio de herramientas RAG
        
        Args:
            qa_chains: Diccionario de cadenas de QA configuradas
        """
        self.qa_chains = qa_chains
        logger.info("RAGToolsService inicializado", 
                   extra={"component": "rag_tools_service", "phase": "startup", 
                          "chains_available": len(qa_chains) if qa_chains else 0})
    
    def call_chain_safe(self, chain_name: str, query: str) -> str:
        """
        Llama una cadena RAG de forma segura (extraído de agente.py líneas 707-725)
        
        Args:
            chain_name: Nombre de la cadena a llamar
            query: Consulta a procesar
            
        Returns:
            str: Respuesta de la cadena o mensaje de error
        """
        try:
            logger.info(f"Llamando cadena RAG: {chain_name}", 
                       extra={"component": "rag_tools_service", "chain": chain_name, "query": query[:100]})
            
            if not self.qa_chains or chain_name not in self.qa_chains:
                logger.warning(f"Cadena RAG no disponible: {chain_name}", 
                              extra={"component": "rag_tools_service", "chain": chain_name})
                return f"Lo siento, la información sobre {chain_name} no está disponible en este momento."
            
            chain = self.qa_chains[chain_name]
            if not chain:
                logger.warning(f"Cadena RAG es None: {chain_name}", 
                              extra={"component": "rag_tools_service", "chain": chain_name})
                return f"Lo siento, tuve un problema accediendo a la información de {chain_name}."
            
            response = chain.run(query)
            
            logger.info(f"Cadena RAG ejecutada exitosamente: {chain_name}", 
                       extra={"component": "rag_tools_service", "chain": chain_name, "response_length": len(response)})
            
            return response
            
        except Exception as e:
            error_msg = f"Error ejecutando cadena RAG {chain_name}: {e}"
            logger.error(error_msg, extra={"component": "rag_tools_service", "chain": chain_name})
            return "Disculpa, tuve un problema accediendo a esa información. ¿Podrías reformular tu pregunta?"
    
    # ================================================
    # FUNCIONES RAG OPTIMIZADAS (POST-FUSIÓN)
    # ================================================

    def informacion_general_func(self, query: str) -> str:
        """Información general unificada (concepto + filosofía)"""
        return self.call_chain_safe("informacion_general", query)

    def domos_completos_func(self, query: str) -> str:
        """Información completa de domos (info + precios)"""
        return self.call_chain_safe("domos_completos", query)

    def politicas_completas_func(self, query: str) -> str:
        """Políticas completas unificadas"""
        return self.call_chain_safe("politicas_completas", query)

    def accesibilidad_completa_func(self, query: str) -> str:
        """Accesibilidad completa unificada"""
        return self.call_chain_safe("accesibilidad_completa", query)

    def actividades_servicios_externos_func(self, query: str) -> str:
        """Actividades y servicios externos combinados"""
        # Primero intentar actividades adicionales
        response_adicionales = self.call_chain_safe("actividades_adicionales", query)
        # Luego servicios externos
        response_externos = self.call_chain_safe("servicios_externos", query)
        
        if "no está disponible" not in response_adicionales and "no está disponible" not in response_externos:
            return f"{response_adicionales}\n\n{response_externos}"
        elif "no está disponible" not in response_adicionales:
            return response_adicionales
        elif "no está disponible" not in response_externos:
            return response_externos
        else:
            return "Lo siento, la información sobre actividades no está disponible en este momento."

    # ================================================
    # FUNCIONES RAG ACTIVAS (SIN CAMBIOS)
    # ================================================

    def ubicacion_contacto_func(self, query: str) -> str:
        """Información sobre ubicación y contacto"""
        return self.call_chain_safe("ubicacion_contacto", query)

    def servicios_incluidos_func(self, query: str) -> str:
        """Información sobre servicios incluidos"""
        return self.call_chain_safe("servicios_incluidos", query)
    
    def links_imagenes_func(self, query: Optional[str] = None) -> str:
        """
        Función que maneja solicitudes de links usando la nueva lógica inteligente (Variable 1)
        Solo proporciona links cuando el trigger es apropiado
        
        Args:
            query: Consulta del usuario (opcional)
            
        Returns:
            str: Respuesta con links solo cuando corresponde según Variable 1
        """
        try:
            if query is None:
                query = "Enlaces para ver imágenes de los domos"
            
            # Usar la nueva lógica inteligente de detección de links
            from services.website_link_service import get_website_link_service
            website_service = get_website_link_service()
            
            # Detectar si debe mostrar links según triggers específicos
            should_share, trigger_type, reason = website_service.should_share_website_link(query)
            
            if should_share:
                # Generar respuesta apropiada con links
                response = website_service.generate_website_response(trigger_type, query)
                logger.info(f"Links proporcionados por trigger: {trigger_type}", 
                           extra={"component": "rag_tools_service", "trigger": trigger_type})
                return response
            else:
                # No mostrar links, usar RAG para respuesta contextual sin links
                rag_response = self.call_chain_safe("links_imagenes", query)
                
                if rag_response and len(rag_response.strip()) > 10:
                    logger.info("Respuesta RAG sin links proporcionada", 
                               extra={"component": "rag_tools_service", "action": "rag_only"})
                    return rag_response
                else:
                    # Fallback sin links
                    logger.info("Fallback sin links usado", 
                               extra={"component": "rag_tools_service", "action": "fallback_no_links"})
                    return "Puedo ayudarte con información sobre nuestros domos y servicios. ¿Qué te gustaría saber específicamente?"
            
        except Exception as e:
            logger.error(f"Error en links_imagenes_func: {e}", 
                        extra={"component": "rag_tools_service"})
            # Fallback de error sin links automáticos
            return "Disculpa, tuve un problema procesando tu consulta. ¿Podrías reformular tu pregunta?"
    
    def menu_principal_func(self, query: Optional[str] = None) -> str:
        """
        Muestra el menú principal de navegación mejorado con variantes flexibles
        
        Args:
            query: Consulta del usuario (opcional)
            
        Returns:
            str: Menú principal con instrucciones de uso flexible
        """
        try:
            # Menú principal completo con las 8 opciones correctas
            return """🏕️ **BIENVENIDO A GLAMPING BRILLO DE LUNA** 🌙

1️⃣ **Información General** - Concepto, ubicación, contacto
2️⃣ **Domos Disponibles** - Tipos, características y precios
3️⃣ **Consultar Disponibilidad** - Fechas y reservas
4️⃣ **Servicios** - Incluidos y adicionales
5️⃣ **Políticas** - Cancelación, mascotas, normas

💬 Escribe el número o describe lo que necesitas

🤖 **Para consultas específicas, simplemente pregúntame:**
• "¿Qué actividades hay en la zona?"
• "Quiero ver fotos del lugar"
• "Información para personas en silla de ruedas"
            """
        except Exception as e:
            logger.warning(f"Error generando menú: {e}", 
                          extra={"component": "rag_tools_service"})
            return """🏕️ **BIENVENIDO A GLAMPING BRILLO DE LUNA** 🌙

1️⃣ **Información General** - Concepto, ubicación, contacto
2️⃣ **Domos Disponibles** - Tipos, características y precios
3️⃣ **Consultar Disponibilidad** - Fechas y reservas
4️⃣ **Servicios** - Incluidos y adicionales
5️⃣ **Políticas** - Cancelación, mascotas, normas

💬 Escribe el número o describe lo que necesitas

🤖 **Para consultas específicas, simplemente pregúntame:**
• "¿Qué actividades hay en la zona?"
• "Quiero ver fotos del lugar"
• "Información para personas en silla de ruedas" """

class ReservationRequestTool(BaseTool):
    """
    Herramienta para iniciar el flujo de reserva (extraído de agente.py líneas 1027-1036)
    """
    name: str = "SolicitarDatosReserva"
    description: str = "Útil para iniciar el proceso de recolección de datos de reserva. Úsala cuando el usuario exprese claramente su deseo de hacer una reserva (ej. 'quiero reservar', 'hacer una reserva', 'reservar un domo', 'cómo reservo')."

    def _run(self, query: str = None) -> str:
        """
        Ejecutar herramienta de solicitud de reserva
        
        Args:
            query: Consulta del usuario
            
        Returns:
            str: Código de solicitud de datos de reserva
        """
        # Esta herramienta no procesa la reserva, solo indica que el bot debe pedir los datos.
        logger.info("Herramienta de solicitud de reserva activada", 
                   extra={"component": "rag_tools_service", "tool": "ReservationRequestTool"})
        return "REQUEST_RESERVATION_DETAILS"

    async def _arun(self, query: str = None) -> str:
        """Versión asíncrona de _run"""
        return self._run(query)

def create_rag_tools(rag_tools_service: RAGToolsService, 
                    availability_service: Optional[Any] = None) -> List[Tool]:
    """
    Crea la lista completa de herramientas RAG (extraído de agente.py líneas 1042-1133)
    
    Args:
        rag_tools_service: Instancia del servicio RAG
        availability_service: Servicio de disponibilidades (opcional)
        
    Returns:
        List[Tool]: Lista de herramientas configuradas
    """
    try:
        logger.info("Creando herramientas RAG", 
                   extra={"component": "rag_tools_service", "action": "create_tools"})
        
        tools = [
            # Herramienta de solicitud de reserva
            ReservationRequestTool(),
            
            # Herramientas optimizadas unificadas
            Tool(
                name="InformacionGeneralGlamping",
                func=rag_tools_service.informacion_general_func,
                description="Información general, concepto, filosofía y qué es Glamping Brillo de Luna."
            ),
            Tool(
                name="DomosCompletos",
                func=rag_tools_service.domos_completos_func,
                description="Información completa de domos: tipos, precios, características, capacidad y servicios incluidos."
            ),
            Tool(
                name="PoliticasCompletas",
                func=rag_tools_service.politicas_completas_func,
                description="Políticas completas: reserva, cancelación, mascotas, requisitos y normas del lugar."
            ),
            Tool(
                name="AccesibilidadCompleta",
                func=rag_tools_service.accesibilidad_completa_func,
                description="SIEMPRE usar cuando el usuario mencione: 'silla de ruedas', 'discapacidad', 'movilidad reducida', 'accesibilidad', 'necesidades especiales'. Información completa sobre adaptaciones, equipos de apoyo y medidas de seguridad."
            ),
            Tool(
                name="ServiciosIncluidosGlamping",
                func=rag_tools_service.servicios_incluidos_func,
                description="Servicios incluidos como desayuno, WiFi, parqueadero, BBQ, etc."
            ),
            Tool(
                name="ActividadesServiciosExternos",
                func=rag_tools_service.actividades_servicios_externos_func,
                description="USAR CUANDO el usuario pregunte sobre actividades, qué hacer, turismo, paseos, diversión, entretenimiento en Guatavita. Incluye laguna sagrada, jet ski, paseos a caballo, avistamiento de aves."
            ),
            Tool(
                name="UbicacionContactoGlamping",
                func=rag_tools_service.ubicacion_contacto_func,
                description="Información sobre ubicación, contacto, RNT, dirección y cómo llegar."
            ),
            Tool(
                name="LinksImagenesWeb",
                func=rag_tools_service.links_imagenes_func,
                description="OBLIGATORIO: Usar cuando usuario pida: 'fotos', 'imágenes', 'galería', 'página web', 'sitio web', 'links', 'enlaces', 'ver domos'. SIEMPRE devuelve los links reales de la página web."
            ),
            Tool(
                name="MenuPrincipal",
                func=rag_tools_service.menu_principal_func,
                description="OBLIGATORIO: Usar cuando usuario pida: 'menú', 'menús', 'opciones', 'guía', 'ayuda', 'navegación', 'qué puedo hacer', 'cómo navegar'. Muestra el menú principal de opciones disponibles."
            )
        ]
        
        # Agregar herramienta de disponibilidades si el servicio está disponible
        if availability_service and hasattr(availability_service, 'consultar_disponibilidades_natural'):
            tools.insert(1, Tool(  # Insertar después de ReservationRequestTool
                name="ConsultarDisponibilidades",
                func=availability_service.consultar_disponibilidades_natural,
                description="Útil para consultar disponibilidades de domos, fechas específicas, capacidad y precios. Úsala cuando el usuario pregunte sobre disponibilidad, fechas libres, domos disponibles, si hay espacio para cierta cantidad de personas, o quiera saber qué opciones tiene para hospedarse."
            ))
        
        logger.info(f"Herramientas RAG creadas exitosamente: {len(tools)} herramientas", 
                   extra={"component": "rag_tools_service", "tools_count": len(tools)})
        
        return tools
        
    except Exception as e:
        logger.error(f"Error creando herramientas RAG: {e}", 
                    extra={"component": "rag_tools_service"})
        return []

def get_rag_tools_service(qa_chains: Dict[str, Any]) -> RAGToolsService:
    """
    Factory function para crear instancia de RAGToolsService
    
    Args:
        qa_chains: Diccionario de cadenas de QA configuradas
        
    Returns:
        RAGToolsService: Instancia del servicio
    """
    return RAGToolsService(qa_chains)