# services/personality_service.py
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class PersonalityService:
    """Servicio para personalidad conversacional de Glamping Brillo de Luna"""

    def __init__(self):
        self.brand_name = "Glamping Brillo de Luna"
        self.personality_traits = {
            "warmth": "cálido y acogedor",
            "expertise": "conocedor del glamping",
            "enthusiasm": "entusiasta por la naturaleza",
            "helpfulness": "siempre dispuesto a ayudar",
            "local_pride": "orgulloso de Guatavita"
        }
        
        self.voice_guidelines = {
            "tone": "amigable y profesional",
            "style": "conversacional pero informativo",
            "emoji_usage": "moderado y contextual",
            "formality": "tuteo cercano pero respetuoso"
        }
        
        logger.info("PersonalityService inicializado")

    def get_system_prompt(self) -> str:
        """Prompt optimizado del sistema con personalidad definida"""
        return f"""Asistente virtual de {self.brand_name}, glamping en Guatavita, Colombia.

PERSONALIDAD: Cálido, experto, entusiasta, servicial.

COMUNICACIÓN: Tono amigable, respuestas claras, emojis moderados.

VALORES: Naturaleza, estrellas, comodidad, hospitalidad colombiana.

Mantén este tono en todas las respuestas."""

    def apply_personality_to_response(self, response: str, context: str = "") -> str:
        """Aplica personalidad a una respuesta existente"""
        try:
            # Si la respuesta ya tiene personalidad (contiene emojis o es cálida), no modificar
            if self._has_personality_markers(response):
                return response
            
            # Agregar calidez y personalidad según el contexto
            if "domo" in context.lower():
                prefix = "🌟 "
                suffix = " Escribe el nombre del domo para conocer más detalles específicos."
            elif "precio" in context.lower():
                prefix = "💫 "
                suffix = " ¡Nuestras tarifas incluyen una experiencia completa bajo las estrellas!"
            elif "disponibilidad" in context.lower():
                prefix = "🗓️ "
                suffix = " ¡Esperamos poder recibirte pronto en nuestro rincón mágico!"
            elif "error" in context.lower():
                prefix = "🙏 "
                suffix = " No te preocupes, estoy aquí para ayudarte a planificar tu escape perfecto."
            else:
                prefix = "✨ "
                suffix = " ¿En qué más puedo ayudarte a descubrir la magia del glamping?"
            
            return f"{prefix}{response.strip()}{suffix}"
            
        except Exception as e:
            logger.error(f"Error aplicando personalidad: {e}")
            return response

    def _has_personality_markers(self, response: str) -> bool:
        """Detecta si la respuesta ya tiene personalidad aplicada"""
        personality_markers = [
            "✨", "🌟", "💫", "🏠", "🗓️", "🙏", "💬",
            "te gustaría", "esperamos", "nuestro rincón",
            "magia del glamping", "bajo las estrellas",
            "experiencia perfecta"
        ]
        return any(marker in response for marker in personality_markers)

    def get_greeting_variations(self) -> list:
        """Variaciones de saludo con personalidad"""
        return [
            f"✨ ¡Hola! Soy tu asistente de {self.brand_name}. ¿Listo para descubrir la magia de dormir bajo las estrellas en Guatavita?",
            f"🌟 ¡Bienvenido a {self.brand_name}! Estoy aquí para ayudarte a planificar tu escape perfecto al lado del hermoso lago Tominé.",
            f"💫 ¡Hola! Me encanta ayudarte a descubrir todo lo que {self.brand_name} tiene para ofrecerte. ¿Qué aventura buscas?",
            f"🏔️ ¡Saludos desde Guatavita! Soy tu guía para encontrar la experiencia de glamping perfecta en {self.brand_name}."
        ]

    def get_error_responses(self) -> Dict[str, str]:
        """Respuestas de error con personalidad"""
        return {
            "general": "🙏 Ups, tuve un pequeño inconveniente. Pero no te preocupes, ¡estoy aquí para ayudarte a planificar tu escapada perfecta!",
            "technical": "⚡ Parece que hay un problemita técnico. Mientras tanto, ¿te gustaría que te cuente sobre nuestros hermosos domos?",
            "timeout": "⏰ La conexión tomó más tiempo del esperado. ¡Pero mi entusiasmo por ayudarte sigue intacto! ¿En qué puedo asistirte?",
            "not_found": "🔍 No pude encontrar esa información específica, pero conozco cada rincón del glamping. ¿Puedo ayudarte con algo más?"
        }

    def get_closure_phrases(self) -> list:
        """Frases de cierre con personalidad"""
        return [
            "¡Esperamos recibirte pronto bajo nuestro cielo estrellado! 🌟",
            "¡Te esperamos para vivir la magia del glamping en Guatavita! ✨",
            "¡Que tengas un día tan hermoso como nuestros amaneceres! 🌅",
            "¡Gracias por elegir la aventura del glamping con nosotros! 💫"
        ]

    def enhance_menu_response(self, option: str, response: str) -> str:
        """Mejora respuestas del menú con personalidad"""
        enhancements = {
            "1": "🏔️ ¡Perfecto! Te encantará conocer más sobre nuestro pequeño paraíso en Guatavita.",
            "2": "🏠 ¡Excelente elección! Nuestros domos geodésicos son verdaderas joyas bajo las estrellas.",
            "3": "📅 ¡Genial! Vamos a encontrar las fechas perfectas para tu escape al glamping.",
            "4": "🛎️ ¡Fantástico! Te va a encantar todo lo que incluimos en tu experiencia.",
            "5": "📋 ¡Muy bien! Es importante conocer nuestras políticas para una estadía perfecta."
        }
        
        enhancement = enhancements.get(option, "✨ ")
        return f"{enhancement}\n\n{response}"

    def create_contextual_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Crea prompt contextual con personalidad"""
        base_prompt = self.get_system_prompt()
        
        contextual_additions = ""
        if context.get("last_action") == "showed_domos":
            contextual_additions = "\n\nEl usuario ya vio información de domos y quiere profundizar. Mantén el entusiasmo y sé específico con detalles técnicos pero siempre con calidez."
        elif context.get("last_action") == "showed_availability":
            contextual_additions = "\n\nEl usuario consultó disponibilidad. Ayúdalo a tomar la siguiente decisión con entusiasmo por su posible visita."
        elif context.get("interactions_count", 0) > 3:
            contextual_additions = "\n\nEste es un usuario frecuente. Puedes ser más específico y asumir conocimiento previo, pero mantén la calidez."
        
        return f"""{base_prompt}{contextual_additions}

Usuario pregunta: {user_input}

Responde manteniendo SIEMPRE la personalidad cálida y entusiasta de {self.brand_name}."""

# Instancia global
_personality_service = PersonalityService()

def get_personality_service() -> PersonalityService:
    return _personality_service