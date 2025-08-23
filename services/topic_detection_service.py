# services/topic_detection_service.py
import re
from typing import Tuple, List, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class TopicDetectionService:
    """Servicio para detectar temas en consultas y redirigir hacia el glamping"""

    def __init__(self):
        self.topic_patterns = self._init_topic_patterns()
        self.glamping_connections = self._init_glamping_connections()
        self.smart_redirects = self._init_smart_redirects()
        
        logger.info("TopicDetectionService inicializado")

    def _init_topic_patterns(self) -> Dict[str, List[str]]:
        """Patrones para detectar diferentes temas en las consultas"""
        return {
            "accommodation": [
                "hotel", "hostal", "motel", "resort", "hospedaje", "alojamiento",
                "donde dormir", "dónde dormir", "donde quedarme", "dónde quedarme",
                "habitacion", "habitación", "suite", "apartamento"
            ],
            "nature_activities": [
                "senderismo", "hiking", "caminar", "montaña", "naturaleza",
                "aire libre", "outdoor", "aventura", "ecoturismo", "paisaje",
                "bosque", "río", "lago", "agua", "verde"
            ],
            "relaxation": [
                "relajarse", "descansar", "spa", "masajes", "tranquilo",
                "paz", "serenidad", "escapar", "desestresarse", "bienestar",
                "meditacion", "meditación", "yoga", "wellness"
            ],
            "romantic": [
                "romantico", "romántico", "pareja", "luna de miel", "aniversario",
                "amor", "intimate", "privado", "especial", "celebrar",
                "propuesta", "matrimonio", "cena romantica", "cena romántica"
            ],
            "food_drink": [
                "comida", "restaurante", "comer", "almuerzo", "cena", "desayuno",
                "bar", "bebida", "cocina", "gastronomia", "gastronómia",
                "menu", "menú", "platos", "especialidad"
            ],
            "photography": [
                "fotos", "fotografias", "fotografías", "selfie", "pictures",
                "instagram", "social media", "beautiful", "hermoso", "bonito",
                "paisaje", "sunset", "amanecer", "atardecer", "vista"
            ],
            "weather_seasons": [
                "clima", "tiempo", "lluvia", "sol", "frio", "frío", "calor",
                "temporada", "epoca", "época", "mejor momento", "cuando ir", "cuándo ir"
            ],
            "transportation": [
                "como llegar", "cómo llegar", "transporte", "bus", "carro",
                "distancia", "tiempo viaje", "ruta", "direcciones", "gps",
                "uber", "taxi", "publico", "público"
            ],
            "budget_planning": [
                "precio", "costo", "barato", "economico", "económico", "presupuesto",
                "ofertas", "descuento", "promocion", "promoción", "paquete",
                "incluye", "vale la pena", "comparar"
            ],
            "group_travel": [
                "grupo", "amigos", "familia", "niños", "niños", "adolescentes",
                "personas", "cuantos", "cuántos", "capacidad", "espacio"
            ]
        }

    def _init_glamping_connections(self) -> Dict[str, str]:
        """Conexiones inteligentes entre temas detectados y aspectos del glamping"""
        return {
            "accommodation": "domos_overview",
            "nature_activities": "activities_external", 
            "relaxation": "services_wellness",
            "romantic": "domos_romantic",
            "food_drink": "services_food",
            "photography": "gallery_links",
            "weather_seasons": "best_times",
            "transportation": "location_access",
            "budget_planning": "pricing_packages",
            "group_travel": "capacity_groups"
        }

    def _init_smart_redirects(self) -> Dict[str, Dict[str, str]]:
        """Respuestas inteligentes de redirección por tema"""
        return {
            "accommodation": {
                "connection": "domos_overview",
                "response": """🏠 ¡Perfecto! Si buscas hospedaje único, te va a encantar el glamping.

✨ **¿Por qué elegir nuestros domos geodésicos?**
• 🌟 **Comodidad de hotel** + **aventura de camping**
• 🏔️ **Vistas espectaculares** al embalse de Tominé  
• ⭐ **Dormir bajo las estrellas** con total comodidad
• 🛎️ **Servicios incluidos** - WiFi, desayuno, parqueadero

🏠 **Tenemos 4 domos únicos:** Antares (con jacuzzi), Polaris, Sirius y Centaury

💬 ¿Te gustaría conocer más sobre nuestros domos o consultar disponibilidad?"""
            },
            
            "nature_activities": {
                "connection": "activities_external", 
                "response": """🏔️ ¡Genial! Glamping Brillo de Luna es el lugar perfecto para los amantes de la naturaleza.

🌟 **Actividades en naturaleza disponibles:**
• 🥾 **Senderismo** - Caminatas a Montecillo y Pozo Azul
• 🚤 **Navegación** - Velero y lanchas en el embalse de Tominé
• 🐦 **Avistamiento de aves** - Especies únicas de la región
• 🐎 **Paseos a caballo** - Explorando paisajes muiscas
• 🏄 **Jet ski** - Aventura acuática en el embalse

🏠 **Y desde nuestros domos geodésicos** puedes disfrutar vistas increíbles 24/7

💬 ¿Qué tipo de actividad en naturaleza te llama más la atención?"""
            },
            
            "relaxation": {
                "connection": "services_wellness",
                "response": """🧘‍♀️ ¡Excelente! El glamping es el escape perfecto para relajarte y renovar energías.

✨ **Experiencias de relajación disponibles:**
• 🛁 **Jacuzzi privado** - En el domo Antares bajo las estrellas
• 💆‍♀️ **Masajes** - Desde $90.000, para renovar tu energía
• 🌅 **Amaneceres espectaculares** - Desde la terraza de tu domo
• 🔥 **Fogata nocturna** - Área común para contemplar las estrellas
• 🌿 **Entorno natural** - Silencio y aire puro del lago Tominé

🏠 **Cada domo está diseñado para el descanso total** con vistas relajantes

💬 ¿Te interesa más el jacuzzi, los masajes, o prefieres info general de relajación?"""
            },
            
            "romantic": {
                "connection": "domos_romantic",
                "response": """💕 ¡Romántico! Glamping Brillo de Luna es perfecto para parejas que buscan algo especial.

🌟 **Experiencias románticas únicas:**
• 💖 **Domo Antares** - Jacuzzi privado bajo las estrellas
• 🌅 **Amaneceres mágicos** - Vistas al lago desde tu terraza privada
• ⭐ **Noches estrelladas** - Diseño para contemplar el cielo
• 💐 **Decoraciones especiales** - Desde $60.000 para sorprender
• 🍽️ **Cenas románticas** - Servicios gastronómicos especiales

🏠 **Cada domo tiene vistas panorámicas** y privacidad total para parejas

💬 ¿Te interesa el domo Antares con jacuzzi o prefieres conocer las opciones de decoración?"""
            },
            
            "food_drink": {
                "connection": "services_food",
                "response": """🍽️ ¡La gastronomía es parte especial de la experiencia glamping!

✨ **Servicios gastronómicos incluidos y adicionales:**
• 🥐 **Desayuno incluido** - Natural y saludable cada mañana
• ☕ **Café ilimitado** - Disponible en cada domo
• 🍖 **BBQ área común** - Parrilla y fogata para uso libre
• 🍷 **Cenas románticas** - Servicios especiales bajo las estrellas
• 🍳 **Cocinetas equipadas** - En domos Antares y Polaris

🏠 **Además puedes explorar** la gastronomía local de Guatavita

💬 ¿Te interesa más el desayuno incluido, las facilidades de BBQ, o servicios de cenas especiales?"""
            },
            
            "photography": {
                "connection": "gallery_links", 
                "response": """📸 ¡Perfecto para fotografía! Glamping Brillo de Luna ofrece escenarios únicos.

🌟 **Spots perfectos para fotos increíbles:**
• 🏠 **Domos geodésicos** - Arquitectura única bajo las estrellas
• 🏔️ **Vistas al lago Tominé** - Panorámicas desde cada terraza
• 🌅 **Amaneceres espectaculares** - Colores mágicos sobre las montañas
• ⭐ **Cielo nocturno** - Astrofotografía desde tu domo
• 🌿 **Entorno natural** - Paisajes de Cundinamarca

📱 **¡Ve nuestras fotos reales!**
• 🌐 **Galería completa:** https://www.glampingbrillodeluna.com/domos
• 📸 **Página principal:** https://www.glampingbrillodeluna.com

💬 ¿Te gustaría ver fotos específicas de algún domo o conocer los mejores momentos para fotografía?"""
            },
            
            "transportation": {
                "connection": "location_access",
                "response": """🚗 ¡Llegar a Glamping Brillo de Luna es más fácil de lo que piensas!

📍 **Ubicación en Guatavita, Cundinamarca:**
• 🗺️ **Coordenadas:** Plus Code W5H8+83V
• 🚗 **En carro:** Aproximadamente 1.5 horas desde Bogotá
• 🚌 **Transporte público:** Bus hasta Guatavita + taxi/uber al glamping
• 🛣️ **Ruta principal:** Autopista Norte → Guatavita

🏠 **Servicios de llegada incluidos:**
• 🚗 **Parqueadero gratuito** y seguro
• 📱 **WhatsApp:** +57 305 461 4926 para coordinar llegada
• 🕒 **Check-in:** Horarios flexibles coordinando previamente

💬 ¿Vienes desde Bogotá o desde otra ciudad? ¿Prefieres venir en carro propio o necesitas info de transporte público?"""
            },
            
            "budget_planning": {
                "connection": "pricing_packages",
                "response": """💰 ¡Excelente planificar el presupuesto! Te ayudo con info completa de precios.

✨ **Lo que incluye la tarifa base del domo:**
• 🛏️ **Hospedaje** - Domo geodésico con todas las comodidades
• 🥐 **Desayuno incluido** - Natural y saludable 
• 🚗 **Parqueadero gratuito** - Seguro y vigilado
• 📶 **WiFi gratis** - Conexión en todo el glamping
• 🛁 **Amenidades** - Baño privado con agua caliente
• 🔥 **Áreas comunes** - BBQ y fogata de uso libre

💫 **Servicios opcionales adicionales:**
• 💐 **Decoraciones especiales** - Desde $60.000
• 💆‍♀️ **Masajes** - Desde $90.000 por persona
• 🚤 **Actividades acuáticas** - Velero y lanchas

💬 ¿Te gustaría conocer precios específicos por domo o información sobre paquetes especiales?"""
            },
            
            "group_travel": {
                "connection": "capacity_groups",
                "response": """👨‍👩‍👧‍👦 ¡Genial para grupos! Glamping Brillo de Luna recibe familias y amigos.

🏠 **Capacidad por domo:**
• 🌟 **Antares** - Hasta 2 personas (romántico con jacuzzi)
• 🌟 **Polaris** - Hasta 4 personas (ideal familias)
• 🌟 **Sirius** - Hasta 2 personas (vistas espectaculares)
• 🌟 **Centaury** - Hasta 2 personas (terraza panorámica)

👥 **Para grupos grandes:**
• 🏠 **Reservar múltiples domos** - Están cerca entre sí
• 🔥 **Áreas comunes compartidas** - BBQ y fogata para todo el grupo
• 🎯 **Actividades grupales** - Senderismo, navegación, aventuras

👶 **Familias con niños:** ¡Bienvenidas! Entorno seguro y natural

💬 ¿Cuántas personas son en tu grupo? ¿Prefieres domos cercanos o tienes preferencia por algún domo específico?"""
            }
        }

    def detect_topic_and_redirect(self, message: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Detecta el tema principal y genera redirección inteligente hacia glamping
        
        Returns:
            Tuple[bool, Optional[str], Optional[str], Optional[str]]: 
            (needs_redirect, detected_topic, glamping_connection, redirect_response)
        """
        try:
            message_lower = message.lower().strip()
            
            # Detectar tema principal
            detected_topic = self._identify_main_topic(message_lower)
            
            if not detected_topic:
                return False, None, None, None
            
            # Obtener conexión con glamping
            glamping_connection = self.glamping_connections.get(detected_topic)
            
            if not glamping_connection:
                return False, detected_topic, None, None
            
            # Generar respuesta de redirección
            redirect_data = self.smart_redirects.get(detected_topic)
            if redirect_data:
                redirect_response = redirect_data["response"]
                return True, detected_topic, glamping_connection, redirect_response
            
            return False, detected_topic, glamping_connection, None
            
        except Exception as e:
            logger.error(f"Error detectando tema: {e}")
            return False, None, None, None

    def _identify_main_topic(self, message: str) -> Optional[str]:
        """Identifica el tema principal del mensaje"""
        topic_scores = {}
        
        # Calcular score para cada tema
        for topic, keywords in self.topic_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in message:
                    # Score más alto para coincidencias exactas de palabras completas
                    if re.search(rf'\b{re.escape(keyword)}\b', message):
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                topic_scores[topic] = score
        
        # Retornar el tema con mayor score
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        
        return None

    def enhance_query_with_context(self, original_query: str, detected_topic: str) -> str:
        """Enriquece la consulta original con contexto del tema detectado"""
        topic_context = {
            "accommodation": "hospedaje y alojamiento único",
            "nature_activities": "actividades en naturaleza y aventura",
            "relaxation": "relajación y bienestar",
            "romantic": "experiencias románticas para parejas",
            "food_drink": "gastronomía y servicios de alimentación",
            "photography": "fotografía y escenarios visuales",
            "weather_seasons": "clima y mejor época para visitar",
            "transportation": "acceso y cómo llegar",
            "budget_planning": "precios y planificación de presupuesto",
            "group_travel": "viajes en grupo y capacidad"
        }
        
        context = topic_context.get(detected_topic, "información general")
        
        return f"[CONTEXTO: Usuario interesado en {context}] {original_query}"

    def get_follow_up_suggestions(self, topic: str) -> List[str]:
        """Genera sugerencias de seguimiento basadas en el tema detectado"""
        suggestions = {
            "accommodation": [
                "¿Te gustaría ver fotos de nuestros domos?",
                "¿Prefieres domo con jacuzzi o con vistas panorámicas?",
                "¿Para cuántas personas necesitas el hospedaje?"
            ],
            "nature_activities": [
                "¿Prefieres actividades acuáticas o de montaña?",
                "¿Te interesa el senderismo o actividades más tranquilas?",
                "¿Quieres incluir actividades en tu paquete de hospedaje?"
            ],
            "relaxation": [
                "¿Te interesa más el jacuzzi o los masajes?",
                "¿Buscas relajación total o combinada con algo de aventura?",
                "¿Prefieres relajación en pareja o individual?"
            ],
            "romantic": [
                "¿Es para una ocasión especial como aniversario?",
                "¿Te interesa agregar decoración especial?",
                "¿Quieres incluir cena romántica en tu experiencia?"
            ],
            "food_drink": [
                "¿Te interesa usar las facilidades de BBQ?",
                "¿Quieres información sobre cenas especiales?",
                "¿Tienes alguna restricción alimentaria que debamos saber?"
            ],
            "photography": [
                "¿Qué tipo de fotos te gusta más: paisajes o arquitectura?",
                "¿Planeas una sesión fotográfica profesional?",
                "¿Te interesa la fotografía nocturna de estrellas?"
            ],
            "transportation": [
                "¿Vienes desde Bogotá o desde otra ciudad?",
                "¿Prefieres venir en carro propio o necesitas opciones de transporte?",
                "¿Necesitas coordinar horario específico de llegada?"
            ],
            "budget_planning": [
                "¿Para qué fechas estás planeando tu visita?",
                "¿Te interesan paquetes que incluyan actividades?",
                "¿Cuántas noches planeas quedarte?"
            ],
            "group_travel": [
                "¿Cuántas personas son en total en tu grupo?",
                "¿Prefieren domos cercanos o no importa la distribución?",
                "¿Hay niños en el grupo?"
            ]
        }
        
        return suggestions.get(topic, [
            "¿Te gustaría conocer más detalles?",
            "¿Tienes alguna pregunta específica?",
            "¿En qué más puedo ayudarte?"
        ])

    def analyze_redirect_success(self, original_message: str, user_response: str) -> bool:
        """Analiza si la redirección fue exitosa basándose en la respuesta del usuario"""
        positive_indicators = [
            "sí", "si", "claro", "perfecto", "genial", "excelente", "me interesa",
            "quiero saber", "dime más", "cuéntame", "sounds good", "está bien"
        ]
        
        negative_indicators = [
            "no", "no me interesa", "otro tema", "no es lo que busco",
            "cambiar", "diferente", "no gracias"
        ]
        
        response_lower = user_response.lower().strip()
        
        # Si contiene indicadores positivos
        if any(indicator in response_lower for indicator in positive_indicators):
            return True
        
        # Si contiene indicadores negativos
        if any(indicator in response_lower for indicator in negative_indicators):
            return False
        
        # Si la respuesta parece seguir el tema del glamping
        if any(keyword in response_lower for keyword in self.topic_patterns.get("accommodation", [])):
            return True
        
        # Por defecto, asumir éxito si no hay señales claras negativas
        return len(negative_indicators) == 0

# Instancia global
_topic_detection_service = TopicDetectionService()

def get_topic_detection_service() -> TopicDetectionService:
    return _topic_detection_service