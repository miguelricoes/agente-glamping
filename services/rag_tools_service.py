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
    
    # Funciones específicas para archivos originales 
    def concepto_glamping_func(self, query: str) -> str:
        """Información sobre el concepto del glamping"""
        return self.call_chain_safe("concepto_glamping", query)
    
    def ubicacion_contacto_func(self, query: str) -> str:
        """Información sobre ubicación y contacto"""
        return self.call_chain_safe("ubicacion_contacto", query)
    
    def domos_info_func(self, query: str) -> str:
        """Información sobre los domos"""
        return self.call_chain_safe("domos_info", query)
    
    def servicios_incluidos_func(self, query: str) -> str:
        """Información sobre servicios incluidos"""
        return self.call_chain_safe("servicios_incluidos", query)
    
    def actividades_adicionales_func(self, query: str) -> str:
        """Información sobre actividades adicionales"""
        return self.call_chain_safe("actividades_adicionales", query)
    
    def politicas_glamping_func(self, query: str) -> str:
        """Información sobre políticas del glamping"""
        return self.call_chain_safe("politicas_glamping", query)
    
    def accesibilidad_func(self, query: str) -> str:
        """Información sobre accesibilidad"""
        return self.call_chain_safe("accesibilidad", query)
    
    def requisitos_reserva_func(self, query: str) -> str:
        """Información sobre requisitos de reserva"""
        return self.call_chain_safe("requisitos_reserva", query)
    
    # Funciones específicas para archivos nuevos
    def domos_precios_func(self, query: str) -> str:
        """Información detallada sobre precios de domos"""
        return self.call_chain_safe("domos_precios", query)
    
    def que_es_brillo_luna_func(self, query: str) -> str:
        """Información sobre qué es Brillo de Luna"""
        return self.call_chain_safe("que_es_brillo_luna", query)
    
    def servicios_externos_func(self, query: str) -> str:
        """Información sobre servicios externos y actividades"""
        return self.call_chain_safe("servicios_externos", query)
    
    def sugerencias_movilidad_reducida_func(self, query: str) -> str:
        """Información específica sobre movilidad reducida"""
        return self.call_chain_safe("sugerencias_movilidad_reducida", query)
    
    def politicas_privacidad_func(self, query: str) -> str:
        """Información sobre políticas de privacidad"""
        return self.call_chain_safe("politicas_privacidad", query)
    
    def politicas_cancelacion_func(self, query: str) -> str:
        """Información sobre políticas de cancelación"""
        return self.call_chain_safe("politicas_cancelacion", query)
    
    def links_imagenes_func(self, query: Optional[str] = None) -> str:
        """
        Función robusta que SIEMPRE devuelve los links (extraído de agente.py líneas 771-788)
        
        Args:
            query: Consulta del usuario (opcional)
            
        Returns:
            str: Respuesta con links siempre incluidos
        """
        try:
            if query is None:
                query = "Enlaces para ver imágenes de los domos"
            
            # Usar RAG para contexto, pero siempre incluir los links
            response = self.call_chain_safe("links_imagenes", query)
            
            # Crear respuesta que SIEMPRE incluya los links
            links_response = (
                "Aquí tienes los enlaces que necesitas:\n\n"
                "**Para ver imágenes de los domos**: https://www.glampingbrillodeluna.com/domos\n\n"
                "**Página web oficial**: https://www.glampingbrillodeluna.com\n\n"
                "En estos enlaces podrás ver todas las fotos de nuestros hermosos domos geodésicos, "
                "conocer las instalaciones y realizar reservas directamente."
            )
            
            logger.info("Links de imágenes proporcionados", 
                       extra={"component": "rag_tools_service", "action": "links_imagenes"})
            
            return links_response
            
        except Exception as e:
            logger.error(f"Error en links_imagenes_func: {e}", 
                        extra={"component": "rag_tools_service"})
            # Siempre devolver los links incluso si hay error
            return (
                "Aquí tienes los enlaces que necesitas:\n\n"
                "**Para ver imágenes de los domos**: https://www.glampingbrillodeluna.com/domos\n\n"
                "**Página web oficial**: https://www.glampingbrillodeluna.com"
            )
    
    def menu_principal_func(self, query: Optional[str] = None) -> str:
        """
        Muestra el menú principal de navegación (extraído de agente.py líneas 1038-1040)
        
        Args:
            query: Consulta del usuario (opcional)
            
        Returns:
            str: Menú principal
        """
        try:
            # Función movida localmente para eliminar dependencia de agente.py
            return """
🏕️ **BIENVENIDO A GLAMPING BRILLO DE LUNA** 🌙

1️⃣ **Información General** - Concepto, ubicación, contacto
2️⃣ **Domos Disponibles** - Tipos, características y precios  
3️⃣ **Consultar Disponibilidad** - Fechas y reservas
4️⃣ **Servicios Incluidos** - Qué incluye tu estadía
5️⃣ **Actividades Adicionales** - Experiencias únicas
6️⃣ **Políticas** - Cancelación, mascotas, normas
7️⃣ **Ver Imágenes** - Galería de fotos
8️⃣ **Accesibilidad** - Información para movilidad reducida

💬 Escribe el número o describe lo que necesitas
            """
        except Exception as e:
            logger.warning(f"Error generando menú: {e}", 
                          extra={"component": "rag_tools_service"})
            return (
                "🏕️ **MENÚ PRINCIPAL - GLAMPING BRILLO DE LUNA** 🌙\n\n"
                "1️⃣ **Información General** - Concepto, ubicación, contacto\n"
                "2️⃣ **Domos Disponibles** - Tipos, características y precios\n"
                "3️⃣ **Consultar Disponibilidad** - Fechas y reservas\n"
                "4️⃣ **Servicios Incluidos** - Qué incluye tu estadía\n"
                "5️⃣ **Actividades Adicionales** - Experiencias únicas\n"
                "6️⃣ **Políticas** - Cancelación, mascotas, normas\n"
                "7️⃣ **Ver Imágenes** - Galería de fotos\n"
                "8️⃣ **Accesibilidad** - Información para movilidad reducida\n\n"
                "💬 Escribe el número o describe lo que necesitas"
            )

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
            
            # Herramientas de información básica
            Tool(
                name="ConceptoGlamping",
                func=rag_tools_service.concepto_glamping_func,
                description="Útil para responder preguntas generales sobre el concepto del glamping."
            ),
            Tool(
                name="UbicacionContactoGlamping",
                func=rag_tools_service.ubicacion_contacto_func,
                description="Información sobre ubicación, contacto, RNT, etc."
            ),
            Tool(
                name="DomosInfoGlamping",
                func=rag_tools_service.domos_info_func,
                description="Tipos de domos, precios y características básicas."
            ),
            Tool(
                name="ServiciosIncluidosGlamping",
                func=rag_tools_service.servicios_incluidos_func,
                description="Servicios incluidos como desayuno, WiFi, parqueadero, etc."
            ),
            Tool(
                name="ActividadesServiciosAdicionalesGlamping",
                func=rag_tools_service.actividades_adicionales_func,
                description="Servicios adicionales y actividades como masajes, paseos, etc."
            ),
            Tool(
                name="PoliticasGlamping",
                func=rag_tools_service.politicas_glamping_func,
                description="Políticas de cancelación, mascotas, normas del lugar."
            ),
            Tool(
                name="AccesibilidadMovilidadReducidaGlamping",
                func=rag_tools_service.accesibilidad_func,
                description="Útil cuando el usuario menciona silla de ruedas, discapacidad, movilidad reducida, accesibilidad, o necesidades especiales. Proporciona adaptaciones y recomendaciones para personas con limitaciones de movilidad."
            ),
            Tool(
                name="RequisitosReserva",
                func=rag_tools_service.requisitos_reserva_func,
                description="Requisitos para que el usuario pueda reservar."
            ),
            
            # Herramientas específicas avanzadas
            Tool(
                name="DomosPreciosDetallados",
                func=rag_tools_service.domos_precios_func,
                description="Devuelve los precios de los domos. Input: pregunta del usuario, por ejemplo 'precios de los domos para el 12/09'."
            ),
            Tool(
                name="QueEsBrilloDeLuna",
                func=rag_tools_service.que_es_brillo_luna_func,
                description="Explicación completa sobre qué es Glamping Brillo de Luna, su filosofía y propósito único."
            ),
            Tool(
                name="ServiciosExternos",
                func=rag_tools_service.servicios_externos_func,
                description="USAR CUANDO el usuario pregunte sobre actividades, qué hacer, turismo, paseos, diversión, entretenimiento, planes, experiencias, o lugares para visitar en Guatavita. Incluye laguna sagrada, jet ski, paseos a caballo, avistamiento de aves, navegación y más."
            ),
            Tool(
                name="SugerenciasMovilidadReducida",
                func=rag_tools_service.sugerencias_movilidad_reducida_func,
                description="SIEMPRE usar esta herramienta cuando el usuario mencione: 'silla de ruedas', 'amigo en silla de ruedas', 'persona con discapacidad', 'movilidad reducida', 'accesibilidad', 'limitaciones físicas', 'necesidades especiales', 'adaptaciones', 'personas mayores'. Esta herramienta contiene información específica sobre rutas accesibles, equipos de apoyo, medidas de seguridad, personal capacitado y todas las adaptaciones disponibles en Brillo de Luna para personas con movilidad limitada."
            ),
            Tool(
                name="PoliticasPrivacidad",
                func=rag_tools_service.politicas_privacidad_func,
                description="Políticas de privacidad, manejo de datos personales y protección de información."
            ),
            Tool(
                name="PoliticasCancelacion",
                func=rag_tools_service.politicas_cancelacion_func,
                description="Políticas específicas de cancelación, términos y condiciones de reserva."
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