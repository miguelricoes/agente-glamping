# Servicio de recomendaciones inteligentes usando LLM como herramienta de lógica de negocio
# Python: Detección de intención + construcción de prompt
# LLM: Análisis, procesamiento y formateo de respuesta

from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

class RecommendationService:
    """
    Servicio que detecta intenciones de recomendación y usa el LLM 
    como herramienta de lógica de negocio para generar respuestas inteligentes
    """
    
    def __init__(self, qa_chains: Dict[str, Any]):
        """
        Inicializar servicio de recomendaciones
        
        Args:
            qa_chains: Cadenas RAG disponibles para recuperar información
        """
        self.qa_chains = qa_chains
        logger.info("RecommendationService inicializado con arquitectura LLM-as-tool", 
                   extra={"component": "recommendation_service"})
    
    def detect_recommendation_intent(self, user_message: str) -> bool:
        """
        ÚNICA RESPONSABILIDAD: Detectar si el mensaje solicita una recomendación
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            bool: True si es una solicitud de recomendación
        """
        message_lower = user_message.lower().strip()
        
        # Palabras clave que indican solicitud de recomendación
        recommendation_patterns = [
            "recomiend", "suger", "aconsej", "qué me conviene",
            "qué me recomiendas", "qué sugieres", "que me aconsejas",
            "que opinas", "que piensas", "cual es mejor",
            "donde ir", "que hacer", "que visitar",
            "planes", "ideas", "opciones", "ayuda para",
            "no se que", "no sé qué", "decidir"
        ]
        
        # Contextos familiares/grupales que suelen requerir recomendación
        contextual_patterns = [
            "ir de paseo", "salir con", "viajar con",
            "familia", "pareja", "niños", "amigos", 
            "fin de semana", "vacaciones", "celebrar"
        ]
        
        # Patrones de intención implícita (cuando alguien busca algo sin preguntar directamente)
        implicit_intent_patterns = [
            "quiero ir", "queremos ir", "busco", "buscamos",
            "necesito", "necesitamos", "estoy planeando",
            "estamos planeando", "me gustaría", "nos gustaría"
        ]
        
        # Detectar patrón principal
        has_recommendation_keyword = any(pattern in message_lower for pattern in recommendation_patterns)
        
        # Contexto + interrogativo (explícito)
        has_contextual = any(pattern in message_lower for pattern in contextual_patterns)
        has_question = any(word in message_lower for word in ["qué", "que", "cual", "cuál", "como", "cómo"])
        
        # Intención implícita + contexto familiar/grupal (NUEVO)
        has_implicit_intent = any(pattern in message_lower for pattern in implicit_intent_patterns)
        
        # Detectar si es una afirmación corta con contexto familiar (indica necesidad de recomendación)
        is_short_contextual = (has_contextual and len(message_lower.split()) <= 8)
        
        is_recommendation_request = (
            has_recommendation_keyword or 
            (has_contextual and has_question) or 
            (has_implicit_intent and has_contextual) or  # NUEVO: "Quiero ir de paseo con mi familia"
            is_short_contextual  # NUEVO: Frases cortas con contexto familiar
        )
        
        if is_recommendation_request:
            logger.info(f"Intención de recomendación detectada", 
                       extra={"component": "recommendation_service", "user_message": user_message[:50]})
        
        return is_recommendation_request
    
    def get_rag_context(self, user_message: str) -> str:
        """
        ÚNICA RESPONSABILIDAD: Recuperar información relevante del RAG
        
        Args:
            user_message: Mensaje original del usuario
            
        Returns:
            str: Información recuperada de las bases de conocimiento
        """
        # Consultas optimizadas para diferentes tipos de información
        rag_queries = [
            f"{user_message} domos tipos características precios",
            "información domos Antares Polaris Sirius Centaury precios servicios",
            "servicios incluidos actividades experiencias glamping",
            "ubicación instalaciones comodidades que incluye estadía"
        ]
        
        retrieved_info = []
        
        # Intentar recuperar información de diferentes fuentes RAG
        for chain_name in ["domos_info", "servicios_glamping", "actividades_glamping", "informacion_general"]:
            if chain_name in self.qa_chains and self.qa_chains[chain_name]:
                for query in rag_queries[:2]:  # Solo las 2 consultas más relevantes por cadena
                    try:
                        response = self.qa_chains[chain_name].run({"query": query})
                        if response and len(response.strip()) > 50:
                            retrieved_info.append(f"=== INFORMACIÓN DE {chain_name.upper()} ===\n{response.strip()}")
                            break  # Una respuesta buena por cadena es suficiente
                    except Exception as e:
                        logger.warning(f"Error recuperando de {chain_name}: {e}")
                        continue
        
        # Compilar toda la información recuperada
        if retrieved_info:
            context = "\n\n".join(retrieved_info)
            logger.info(f"Información RAG recuperada: {len(context)} caracteres de {len(retrieved_info)} fuentes")
            return context
        else:
            # Información de emergencia si RAG no está disponible
            logger.warning("RAG no disponible, usando información de emergencia")
            return """=== INFORMACIÓN BÁSICA DEL GLAMPING ===
            
DOMOS DISPONIBLES:
• ANTARES (2 personas) - $650.000/noche - Jacuzzi privado, vista panorámica, dos pisos
• POLARIS (2-4 personas) - $550.000/noche - Sofá cama, cocineta, dos pisos  
• SIRIUS (2 personas) - $450.000/noche - Un piso, terraza, ideal parejas
• CENTAURY (2 personas) - $450.000/noche - Un piso, vista a represa, tranquilo

SERVICIOS INCLUIDOS:
• Desayuno gourmet continental
• WiFi gratuito de alta velocidad  
• Parqueadero privado y seguro
• Acceso a todas las instalaciones
• Kit de bienvenida

UBICACIÓN:
• Guatavita, Cundinamarca - Vista a Represa de Tominé
• A 1 hora de Bogotá por vía La Calera
• Entorno natural privilegiado

CONTACTO:
• WhatsApp: +57 123 456 7890
• Web: glampingbrillodelaluna.com"""
    
    def build_llm_prompt(self, user_message: str, rag_context: str) -> str:
        """
        ÚNICA RESPONSABILIDAD: Construir el prompt que se enviará al LLM
        
        Args:
            user_message: Mensaje original del usuario
            rag_context: Información recuperada del RAG
            
        Returns:
            str: Prompt completo estructurado para el LLM
        """
        # PARTE 1: ROL DEL LLM
        role_instruction = """Eres María, una experta consultora en experiencias de glamping del "Glamping Brillo de Luna". Tienes conocimiento profundo sobre cada domo, sus características, precios, y qué tipo de experiencia ofrece cada uno. Tu especialidad es hacer recomendaciones personalizadas basándote en las necesidades específicas de cada cliente."""
        
        # PARTE 2: CONTEXTO (DATOS DEL RAG)  
        context_section = f"""INFORMACIÓN DISPONIBLE DEL GLAMPING:
{rag_context}"""
        
        # PARTE 3: TAREA ESPECÍFICA
        task_instruction = f"""SOLICITUD DEL CLIENTE: "{user_message}"

INSTRUCCIONES PARA TU RESPUESTA:

1. **ANALIZA** la solicitud del cliente para entender:
   - Tipo de grupo (familia, pareja, amigos, solo)
   - Intención (descanso, aventura, celebración, etc.)
   - Cualquier preferencia específica mencionada

2. **GENERA UNA RECOMENDACIÓN PERSONALIZADA** que incluya:
   - Saludo cálido y empático
   - Recomendación específica del domo más adecuado
   - Razones claras de por qué es la mejor opción
   - Servicios y actividades relevantes
   - Precio y qué incluye
   - Próximos pasos para reservar

3. **FORMATO DE RESPUESTA**:
   - Usa emojis apropiados para hacer la respuesta visualmente atractiva
   - Estructura con viñetas claras y secciones
   - Tono natural, amigable y profesional
   - Incluye llamada a la acción al final
   - Máximo 300 palabras para mantener la atención

4. **IMPORTANTE**: 
   - No inventes información que no esté en el contexto
   - Si necesitas más detalles del cliente, pregunta
   - Mantén el foco en crear una experiencia memorable

Genera tu respuesta ahora:"""
        
        # PROMPT FINAL ESTRUCTURADO
        final_prompt = f"""{role_instruction}

{context_section}

{task_instruction}"""
        
        logger.info("Prompt LLM construido", 
                   extra={"component": "recommendation_service", "prompt_length": len(final_prompt)})
        
        return final_prompt
    
    def process_recommendation_request(self, user_message: str, llm_agent_func) -> Tuple[bool, str]:
        """
        ORQUESTADOR: Coordina todo el proceso de recomendación
        EL LLM ES LA ÚNICA FUENTE DE RESPUESTAS - SIN FALLBACKS ESTÁTICOS
        
        Args:
            user_message: Mensaje del usuario
            llm_agent_func: Función que ejecuta el LLM agent
            
        Returns:
            Tuple[bool, str]: (procesado_exitosamente, respuesta_generada)
        """
        logger.info("Procesando solicitud de recomendación - LLM como única fuente", 
                   extra={"component": "recommendation_service"})
        
        # PASO 1: Recuperar contexto del RAG
        rag_context = self.get_rag_context(user_message)
        
        # PASO 2: Construir prompt para el LLM
        llm_prompt = self.build_llm_prompt(user_message, rag_context)
        
        # PASO 3: Ejecutar LLM con reintentos para garantizar respuesta
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Ejecutando LLM attempt {attempt + 1}/{max_attempts}")
                llm_response = llm_agent_func(llm_prompt)
                
                # Validación más flexible - aceptar cualquier respuesta no vacía
                if llm_response and len(llm_response.strip()) > 10:
                    logger.info("Recomendación inteligente generada exitosamente por LLM", 
                               extra={"component": "recommendation_service", "attempt": attempt + 1})
                    return True, llm_response.strip()
                else:
                    logger.warning(f"LLM attempt {attempt + 1} generó respuesta muy corta: {len(llm_response.strip()) if llm_response else 0} chars")
                    
                    # En lugar de usar fallback, modificar prompt para siguiente intento
                    if attempt < max_attempts - 1:
                        llm_prompt = self._enhance_prompt_for_retry(llm_prompt, attempt + 1)
                        continue
                        
            except Exception as e:
                logger.warning(f"Error en LLM attempt {attempt + 1}: {e}")
                
                # En lugar de usar fallback, modificar prompt para manejo de errores
                if attempt < max_attempts - 1:
                    llm_prompt = self._create_error_recovery_prompt(user_message, rag_context, str(e))
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        # ÚLTIMA OPCIÓN: Crear un prompt de emergencia que FUERCE al LLM a responder
        logger.warning("Todos los intentos de LLM fallaron, usando prompt de emergencia")
        
        try:
            emergency_prompt = self._create_emergency_prompt(user_message, rag_context)
            final_response = llm_agent_func(emergency_prompt)
            
            if final_response and len(final_response.strip()) > 5:  # Mínimo muy bajo
                logger.info("Respuesta de emergencia generada por LLM")
                return True, final_response.strip()
            else:
                # Solo si el LLM está completamente roto, devolver error
                logger.error("LLM completamente no funcional")
                return False, "Error: No se puede generar recomendación en este momento. Intenta de nuevo."
                
        except Exception as e:
            logger.error(f"Error crítico en prompt de emergencia: {e}")
            return False, "Error: Sistema de recomendaciones temporalmente no disponible."
    
    def _enhance_prompt_for_retry(self, original_prompt: str, retry_number: int) -> str:
        """
        Mejora el prompt para reintentos cuando el LLM no genera respuesta adecuada
        """
        enhancement = f"""

INSTRUCCIÓN ADICIONAL PARA REINTENTO #{retry_number}:
Tu respuesta anterior fue muy corta o vacía. Es OBLIGATORIO que generes una recomendación completa y útil.

REQUISITOS ESTRICTOS PARA ESTA RESPUESTA:
- Mínimo 150 palabras
- Incluye emojis para hacer la respuesta atractiva
- Menciona al menos un domo específico
- Incluye precios aproximados
- Proporciona información de contacto
- Termina con una pregunta para continuar la conversación

GENERA UNA RESPUESTA COMPLETA AHORA:"""
        
        return original_prompt + enhancement
    
    def _create_error_recovery_prompt(self, user_message: str, rag_context: str, error_msg: str) -> str:
        """
        Crea un prompt simplificado para recuperarse de errores del LLM
        """
        return f"""Eres María, asistente del Glamping Brillo de Luna.

El usuario preguntó: "{user_message}"

INFORMACIÓN DISPONIBLE:
{rag_context}

INSTRUCCIÓN SIMPLE: 
Genera una recomendación personalizada para este usuario.
Incluye información específica de nuestros domos y servicios.
Sé amigable y profesional.
Mínimo 100 palabras.

Tu recomendación:"""
    
    def _create_emergency_prompt(self, user_message: str, rag_context: str) -> str:
        """
        Prompt de emergencia ultra-simplificado que FUERZA una respuesta del LLM
        """
        return f"""Usuario: {user_message}

Información: {rag_context}

Responde como María del Glamping Brillo de Luna con una recomendación de 50+ palabras:"""


def create_recommendation_service(qa_chains: Dict[str, Any]) -> RecommendationService:
    """
    Factory function para crear instancia de RecommendationService
    
    Args:
        qa_chains: Cadenas QA disponibles
        
    Returns:
        RecommendationService: Instancia configurada
    """
    return RecommendationService(qa_chains)