# services/domain_validation_service.py
import re
from typing import Tuple, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class DomainValidationService:
    """Servicio para validar que las consultas estén dentro del dominio del glamping"""

    def __init__(self):
        self.glamping_keywords = self._init_glamping_keywords()
        self.prohibited_keywords = self._init_prohibited_keywords()
        self.redirect_patterns = self._init_redirect_patterns()
        
        logger.info("DomainValidationService inicializado")

    def _init_glamping_keywords(self) -> List[str]:
        """Palabras clave que indican consultas válidas del glamping"""
        return [
            # Glamping específico
            "glamping", "domo", "domos", "antares", "polaris", "sirius", "centaury",
            "brillo de luna", "brillo", "luna",
            
            # Hospedaje
            "reserva", "reservar", "disponibilidad", "precio", "precios", "tarifa",
            "hospedaje", "alojamiento", "hotel", "cabana", "cabaña",
            
            # Servicios
            "servicios", "amenidades", "incluido", "desayuno", "wifi", "parqueadero",
            "jacuzzi", "terraza", "fogata", "bbq", "masajes",
            
            # Ubicación
            "guatavita", "cundinamarca", "colombia", "ubicacion", "ubicación", 
            "donde", "dónde", "direccion", "dirección", "como llegar", "cómo llegar",
            "tomíne", "tomine", "embalse", "lago",
            
            # Actividades
            "actividades", "senderismo", "caminata", "navegacion", "navegación",
            "velero", "lancha", "avistamiento", "aves", "caballo", "jet ski",
            
            # Términos generales de turismo
            "turismo", "viaje", "vacaciones", "fin de semana", "escapada",
            "experiencia", "natura", "naturaleza", "aire libre",
            
            # Políticas
            "politicas", "políticas", "cancelacion", "cancelación", "mascotas",
            "normas", "reglas", "check", "privacidad",
            
            # Contacto
            "contacto", "telefono", "teléfono", "email", "whatsapp", "información"
        ]

    def _init_prohibited_keywords(self) -> List[str]:
        """Palabras clave que indican consultas prohibidas o fuera de dominio"""
        return [
            # Violencia y armas
            "arma", "pistola", "fusil", "bomba", "explotar", "matar", "asesinar",
            "violencia", "guerra", "terrorismo", "droga", "drogas",
            
            # Contenido adulto
            "sexo", "porno", "pornografia", "desnudo", "sexual", "adulto",
            
            # Actividades ilegales
            "robar", "estafar", "hackear", "ilegal", "fraude", "soborno",
            "contrabando", "lavado", "dinero sucio",
            
            # Otros negocios competencia
            "hotel marriott", "hilton", "decameron", "airbnb específico de otros",
            "booking.com reserva", "expedia reserva",
            
            # Temas muy alejados del turismo
            "matematicas", "química", "fisica", "programacion", "codigo",
            "receta cocina", "medicina", "enfermedad", "dolor",
            "politica", "gobierno", "elecciones", "presidente",
            
            # Solicitudes de tareas no relacionadas
            "tarea", "homework", "essay", "ensayo", "trabajo universidad",
            "traducir texto", "hacer resumen", "escribir carta"
        ]

    def _init_redirect_patterns(self) -> dict:
        """Patrones para redireccionar consultas hacia el glamping"""
        return {
            "hoteles": {
                "keywords": ["hotel", "hoteles", "hospedaje", "alojamiento"],
                "redirect": "✨ ¡Te interesa el hospedaje! Te encantará saber que el glamping es una experiencia única que combina la comodidad de un hotel con la magia de dormir bajo las estrellas. ¿Te gustaría conocer nuestros domos geodésicos?"
            },
            "naturaleza": {
                "keywords": ["naturaleza", "aire libre", "montaña", "lago", "paisaje"],
                "redirect": "🏔️ ¡Perfecto! Glamping Brillo de Luna está rodeado de naturaleza espectacular. Desde nuestros domos puedes disfrutar vistas al embalse de Tominé y paisajes de montaña. ¿Te interesa conocer nuestras actividades al aire libre?"
            },
            "vacaciones": {
                "keywords": ["vacaciones", "fin de semana", "descanso", "escapada"],
                "redirect": "🌟 ¡Una escapada suena genial! El glamping es perfecto para desconectarte de la rutina. ¿Te gustaría conocer nuestros paquetes para fin de semana o consultar disponibilidad?"
            },
            "actividades": {
                "keywords": ["que hacer", "qué hacer", "planes", "diversión", "aventura"],
                "redirect": "🎯 ¡Te va a encantar todo lo que puedes hacer! Tenemos senderismo, navegación en el lago, avistamiento de aves, y mucho más. ¿Qué tipo de actividades prefieres?"
            },
            "comida": {
                "keywords": ["comida", "restaurante", "comer", "almuerzo", "cena"],
                "redirect": "🍽️ ¡La gastronomía es parte de la experiencia! Incluimos desayuno natural y saludable, además puedes solicitar servicios adicionales como cenas románticas. ¿Te interesa conocer nuestros servicios gastronómicos?"
            }
        }

    def validate_domain(self, message: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida si un mensaje está dentro del dominio del glamping
        
        Returns:
            Tuple[bool, str, Optional[str]]: (is_valid, reason, redirect_suggestion)
        """
        try:
            message_lower = message.lower().strip()
            
            # 1. Verificar palabras prohibidas primero
            if self._contains_prohibited_content(message_lower):
                return False, "prohibited_content", None
            
            # 2. Verificar si contiene palabras clave del glamping
            if self._contains_glamping_keywords(message_lower):
                return True, "glamping_related", None
            
            # 3. Buscar oportunidades de redirección
            redirect_suggestion = self._find_redirect_opportunity(message_lower)
            if redirect_suggestion:
                return False, "redirect_opportunity", redirect_suggestion
            
            # 4. Si no hay palabras clave de glamping ni redirección obvia
            if len(message_lower.split()) < 3:
                # Mensajes muy cortos pueden ser ambiguos, dar el beneficio de la duda
                return True, "short_message_benefit", None
            
            return False, "out_of_domain", None
            
        except Exception as e:
            logger.error(f"Error validando dominio: {e}")
            return True, "validation_error", None  # En caso de error, permitir

    def _contains_prohibited_content(self, message: str) -> bool:
        """Verifica si el mensaje contiene contenido prohibido"""
        return any(keyword in message for keyword in self.prohibited_keywords)

    def _contains_glamping_keywords(self, message: str) -> bool:
        """Verifica si el mensaje contiene palabras clave del glamping"""
        return any(keyword in message for keyword in self.glamping_keywords)

    def _find_redirect_opportunity(self, message: str) -> Optional[str]:
        """Busca oportunidades de redirección hacia temas del glamping"""
        for pattern_name, pattern_data in self.redirect_patterns.items():
            if any(keyword in message for keyword in pattern_data["keywords"]):
                return pattern_data["redirect"]
        return None

    def get_rejection_response(self, reason: str, user_message: str = "") -> str:
        """Genera respuesta de rechazo amigable pero firme"""
        responses = {
            "prohibited_content": """🙏 Disculpa, pero no puedo ayudarte con ese tipo de consultas. 

🏠 **¿Te gustaría conocer sobre nuestro glamping?**
• ✨ Experiencia única bajo las estrellas
• 🏔️ Vistas espectaculares al lago Tominé  
• 🛎️ Servicios y comodidades incluidas
• 🎯 Actividades en naturaleza

💬 ¿En qué aspecto del glamping puedo ayudarte?""",

            "out_of_domain": f"""✨ ¡Hola! Soy el asistente especializado de Glamping Brillo de Luna.

🏠 **Mi expertise está en ayudarte con:**
• 🏠 **Información de domos** - Antares, Polaris, Sirius, Centaury
• 📅 **Disponibilidad y reservas** - Fechas libres y precios
• 🛎️ **Servicios incluidos** - Todo lo que está incluido en tu estadía
• 🎯 **Actividades disponibles** - Senderismo, navegación, relajación
• 📍 **Ubicación y contacto** - Cómo llegar a Guatavita

💬 ¿Qué te gustaría saber sobre tu próxima experiencia de glamping?""",

            "general": """🌟 ¡Me especializo en todo lo relacionado con Glamping Brillo de Luna!

🏔️ **¿Listo para descubrir la magia del glamping en Guatavita?**

• 🏠 Conoce nuestros domos geodésicos únicos
• 📅 Consulta disponibilidad para tus fechas  
• 🛎️ Descubre servicios y amenidades incluidas
• 🎯 Explora actividades en naturaleza
• 💰 Obtén información de precios y paquetes

💬 ¿Por dónde empezamos tu aventura?"""
        }
        
        return responses.get(reason, responses["general"])

    def validate_and_redirect(self, message: str) -> Tuple[bool, str]:
        """
        Validación avanzada con redirección inteligente usando prompt específico
        
        Returns:
            Tuple[bool, str]: (needs_redirect, redirect_response)
        """
        try:
            message_lower = message.lower().strip()
            
            # 1. Verificar contenido prohibido
            if self._contains_prohibited_content(message_lower):
                redirect_response = self.get_rejection_response("prohibited_content", message)
                return True, redirect_response
            
            # 2. Verificar si está claramente dentro del dominio del glamping
            if self._contains_glamping_keywords(message_lower):
                return False, ""  # No necesita redirección, puede continuar
            
            # 3. Buscar oportunidades de redirección inteligente
            redirect_suggestion = self._find_redirect_opportunity(message_lower)
            if redirect_suggestion:
                return True, redirect_suggestion
            
            # 4. Análisis de complejidad para determinar si necesita redirección
            analysis = self.analyze_query_complexity(message)
            
            # Si es una consulta compleja pero sin términos de glamping, redirigir
            if analysis["is_complex"] and not analysis["has_glamping_terms"]:
                redirect_response = self.get_rejection_response("out_of_domain", message)
                return True, redirect_response
            
            # 5. Mensajes muy simples - dar beneficio de la duda
            if analysis["word_count"] < 3:
                return False, ""
            
            # 6. Por defecto, redirigir consultas que no tienen relación con glamping
            redirect_response = self.get_rejection_response("out_of_domain", message)
            return True, redirect_response
            
        except Exception as e:
            logger.error(f"Error en validate_and_redirect: {e}")
            return False, ""  # En caso de error, permitir continuar

    def get_redirect_response(self, redirect_message: str) -> str:
        """Genera respuesta de redirección hacia temas del glamping"""
        return redirect_message

    def is_follow_up_question(self, message: str, previous_context: str = "") -> bool:
        """Determina si es una pregunta de seguimiento válida"""
        follow_up_indicators = [
            "más información", "mas informacion", "detalles", "cuéntame", "cuentame",
            "explícame", "explicame", "y qué", "y que", "también", "ademas", "además",
            "otra pregunta", "otra cosa", "algo más", "algo mas"
        ]
        
        # Si hay contexto previo del glamping y palabras de seguimiento
        if previous_context and any(indicator in message.lower() for indicator in follow_up_indicators):
            return True
            
        return False

    def analyze_query_complexity(self, message: str) -> dict:
        """Analiza la complejidad y naturaleza de la consulta"""
        analysis = {
            "word_count": len(message.split()),
            "has_questions": "?" in message,
            "has_glamping_terms": self._contains_glamping_keywords(message.lower()),
            "has_prohibited_terms": self._contains_prohibited_content(message.lower()),
            "complexity_score": 0
        }
        
        # Calcular score de complejidad
        if analysis["word_count"] > 10:
            analysis["complexity_score"] += 2
        if analysis["word_count"] >= 4:  # Queries medianas también pueden ser complejas
            analysis["complexity_score"] += 1
        if analysis["has_questions"]:
            analysis["complexity_score"] += 1
        if analysis["has_glamping_terms"]:
            analysis["complexity_score"] += 3
        if analysis["has_prohibited_terms"]:
            analysis["complexity_score"] -= 5
        
        # Ajustar lógica para mejor detección de necesidad de agente IA
        analysis["is_complex"] = analysis["complexity_score"] >= 4
        
        # Activar agente IA para consultas glamping que necesiten información detallada
        detailed_inquiry_keywords = [
            "cuéntame", "cuentame", "explica", "describe", "detalles", 
            "información", "informacion", "qué", "que", "cómo", "como",
            "actividades", "servicios", "precio", "precios", "disponible"
        ]
        
        has_detailed_inquiry = any(keyword in message.lower() for keyword in detailed_inquiry_keywords)
        
        analysis["needs_ai_agent"] = (
            (analysis["is_complex"] and analysis["has_glamping_terms"]) or
            (analysis["has_glamping_terms"] and has_detailed_inquiry)
        )
        
        return analysis

# Instancia global
_domain_validation_service = DomainValidationService()

def get_domain_validation_service() -> DomainValidationService:
    return _domain_validation_service