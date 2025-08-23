# Servicio especializado para manejo inteligente del link de la página web
# Implementa detección específica según Variable 1 definida por el usuario

import re
from typing import Optional, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)

class WebsiteLinkService:
    """
    Servicio que detecta cuándo compartir el link de la página web según triggers específicos:
    - Cuando piden fotos/imágenes
    - Cuando piden saber cómo son los domos o el glamping
    - Cuando solicitan específicamente la página web
    - Cuando piden reseñas/comentarios/calificaciones
    """
    
    def __init__(self):
        """Inicializar el servicio de detección de links"""
        self.website_url = "https://www.glampingbrillodeluna.com"
        self.domos_gallery_url = "https://www.glampingbrillodeluna.com/domos"
        
        # Definir patrones específicos para cada trigger
        self._init_detection_patterns()
        
        logger.info("WebsiteLinkService inicializado", 
                   extra={"component": "website_link_service", "phase": "startup"})
    
    def _init_detection_patterns(self):
        """Inicializar patrones de detección para cada caso específico"""
        
        # Trigger 1: Solicitud de fotos/imágenes
        self.photo_patterns = [
            r'\bfotos?\b', r'\bfoto\b', r'\bimágenes?\b', r'\bimagenes?\b',
            r'\bgalería\b', r'\bgaleria\b', r'\bver\s+domos?\b', 
            r'\bmostrar\s+domos?\b', r'\benseñar\s+domos?\b',
            r'\bcómo\s+se\s+ve\b', r'\bcomo\s+se\s+ve\b',
            r'\bcómo\s+es\b', r'\bcomo\s+es\b',
            r'\baspecto\b', r'\bapariencia\b', r'\bvisual\b'
        ]
        
        # Trigger 2: Preguntas sobre cómo son los domos o el glamping
        self.description_patterns = [
            r'\bcómo\s+son\s+los?\s+domos?\b', r'\bcomo\s+son\s+los?\s+domos?\b',
            r'\bcómo\s+es\s+el\s+glamping\b', r'\bcomo\s+es\s+el\s+glamping\b',
            r'\bqué\s+tal\s+es\b', r'\bque\s+tal\s+es\b',
            r'\bcómo\s+se\s+ve\b', r'\bcomo\s+se\s+ve\b',
            r'\bcómo\s+se\s+ven\s+los?\s+domos?\b', r'\bcomo\s+se\s+ven\s+los?\s+domos?\b',
            r'\bcómo\s+se\s+ve\s+el\s+lugar\b', r'\bcomo\s+se\s+ve\s+el\s+lugar\b',
            r'\bapariencia\s+del?\s+domo\b', r'\bapariencia\s+del?\s+glamping\b',
            r'\bforma\s+del?\s+domo\b', r'\bdiseño\s+del?\s+domo\b'
        ]
        
        # Trigger 3: Solicitud específica de página web
        self.website_patterns = [
            r'\bpágina\s+web\b', r'\bpagina\s+web\b',
            r'\bsitio\s+web\b', r'\bwebsite\b', r'\bweb\b',
            r'\blink\b', r'\blinks?\b', r'\benlace\b', r'\benlaces?\b',
            r'\burl\b', r'\bdirección\s+web\b', r'\bdireccion\s+web\b',
            r'\bonline\b', r'\ben\s+línea\b', r'\ben\s+linea\b'
        ]
        
        # Trigger 4: Solicitud de reseñas/comentarios/calificaciones
        self.reviews_patterns = [
            r'\breseñas?\b', r'\bresenas?\b', r'\bcomentarios?\b',
            r'\bcalificaciones?\b', r'\bopiniones?\b', r'\btestimonios?\b',
            r'\bexperiencias?\s+de\s+huéspedes?\b', r'\bexperiencias?\s+de\s+huespedes?\b',
            r'\bqué\s+dicen\b', r'\bque\s+dicen\b',
            r'\bvalor[ae]ciones?\b', r'\brating\b', r'\breviews?\b',
            r'\bfeedback\b', r'\bhuéspedes?\s+anteriores?\b', r'\bhuespedes?\s+anteriores?\b'
        ]
    
    def should_share_website_link(self, message: str) -> Tuple[bool, str, str]:
        """
        Determina si se debe compartir el link de la página web según los triggers
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[bool, str, str]: (should_share, trigger_type, reason)
        """
        try:
            message_clean = message.lower().strip()
            
            logger.info(f"Analizando mensaje para link: '{message_clean[:50]}...'", 
                       extra={"component": "website_link_service", "action": "analyze_message"})
            
            # Verificar cada tipo de trigger
            trigger_checks = [
                (self.photo_patterns, "photos", "Solicitud de fotos/imágenes"),
                (self.description_patterns, "description", "Pregunta sobre cómo son los domos/glamping"),
                (self.website_patterns, "website", "Solicitud específica de página web"),
                (self.reviews_patterns, "reviews", "Solicitud de reseñas/comentarios")
            ]
            
            for patterns, trigger_type, reason in trigger_checks:
                if self._matches_patterns(message_clean, patterns):
                    logger.info(f"Trigger detectado: {trigger_type} - {reason}", 
                               extra={"component": "website_link_service", "trigger": trigger_type})
                    return True, trigger_type, reason
            
            logger.info("No se detectó trigger para compartir link", 
                       extra={"component": "website_link_service", "result": "no_trigger"})
            return False, "", ""
            
        except Exception as e:
            logger.error(f"Error analizando mensaje para link: {e}", 
                        extra={"component": "website_link_service"})
            return False, "", ""
    
    def _matches_patterns(self, message: str, patterns: List[str]) -> bool:
        """Verifica si el mensaje coincide con alguno de los patrones"""
        try:
            for pattern in patterns:
                if re.search(pattern, message):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error verificando patrones: {e}", 
                        extra={"component": "website_link_service"})
            return False
    
    def generate_website_response(self, trigger_type: str, user_message: str = "") -> str:
        """
        Genera respuesta apropiada con link según el tipo de trigger
        
        Args:
            trigger_type: Tipo de trigger detectado
            user_message: Mensaje original del usuario
            
        Returns:
            str: Respuesta formateada con link apropiado
        """
        try:
            logger.info(f"Generando respuesta para trigger: {trigger_type}", 
                       extra={"component": "website_link_service", "trigger": trigger_type})
            
            if trigger_type == "photos":
                return self._generate_photos_response()
            elif trigger_type == "description":
                return self._generate_description_response()
            elif trigger_type == "website":
                return self._generate_website_response()
            elif trigger_type == "reviews":
                return self._generate_reviews_response()
            else:
                return self._generate_generic_response()
                
        except Exception as e:
            logger.error(f"Error generando respuesta de website: {e}", 
                        extra={"component": "website_link_service"})
            return self._generate_generic_response()
    
    def _generate_photos_response(self) -> str:
        """Respuesta específica para solicitudes de fotos"""
        return f"""📸 **¡PERFECTO! AQUÍ PUEDES VER TODAS LAS FOTOS** 🌟

🔗 **Galería completa de domos**: {self.domos_gallery_url}
🔗 **Sitio web oficial**: {self.website_url}

En estos enlaces encontrarás:
✨ Fotos en alta calidad de todos nuestros domos
🏞️ Imágenes del entorno natural y paisajes  
🌅 Vistas panorámicas de la represa de Tominé
🛏️ Interiores y comodidades de cada domo
🎯 Galería de actividades y experiencias

¡Explora y elige tu domo favorito! 📱✨"""
    
    def _generate_description_response(self) -> str:
        """Respuesta específica para preguntas sobre cómo son los domos/glamping"""
        return f"""🏠 **¡TE ENCANTARÁ CONOCER CÓMO ES NUESTRO GLAMPING!** ✨

🔗 **Ver cómo son los domos**: {self.domos_gallery_url}  
🔗 **Conocer todo el glamping**: {self.website_url}

🌟 **Podrás ver:**
🏗️ El diseño geodésico único de nuestros domos
🌿 El entorno natural que nos rodea
🏞️ Las vistas espectaculares a la represa
🛋️ Los interiores acogedores y modernos
🔥 Las áreas comunes y de relajación

¡Navega por las fotos y descubre por qué somos únicos! 📸🌙"""
    
    def _generate_website_response(self) -> str:
        """Respuesta específica para solicitudes directas de la página web"""
        return f"""🌐 **NUESTRA PÁGINA WEB OFICIAL** ✨

🔗 **Sitio principal**: {self.website_url}
🔗 **Galería de domos**: {self.domos_gallery_url}

📱 **En nuestro sitio web encontrarás:**
📸 Galería completa de fotos y videos
📋 Información detallada de servicios  
💰 Precios actualizados y promociones
📅 Calendario de disponibilidad en tiempo real
📞 Formulario de contacto directo
🎯 Tours virtuales 360°

¡Visítanos online y planifica tu escape perfecto! 🏕️🌟"""
    
    def _generate_reviews_response(self) -> str:
        """Respuesta específica para solicitudes de reseñas/comentarios"""
        return f"""⭐ **RESEÑAS Y EXPERIENCIAS DE HUÉSPEDES** 💬

🔗 **Ver testimonios completos**: {self.website_url}
🔗 **Fotos de huéspedes**: {self.domos_gallery_url}

📝 **Encontrarás:**
⭐ Calificaciones y reseñas verificadas
💬 Testimonios detallados de experiencias
📸 Fotos compartidas por huéspedes anteriores  
🏆 Reconocimientos y certificaciones
📊 Estadísticas de satisfacción
🎥 Videos testimoniales

¡Descubre por qué nuestros huéspedes nos aman! 😊✨

También puedes ver reseñas en:
📱 Google Maps | Facebook | TripAdvisor"""
    
    def _generate_generic_response(self) -> str:
        """Respuesta genérica como fallback"""
        return f"""🌐 **SITIO WEB GLAMPING BRILLO DE LUNA** ✨

🔗 **Página principal**: {self.website_url}
🔗 **Ver domos**: {self.domos_gallery_url}

¡Visita nuestro sitio para más información! 🏕️"""
    
    def get_website_urls(self) -> dict:
        """Obtener URLs configuradas"""
        return {
            "main_website": self.website_url,
            "domos_gallery": self.domos_gallery_url
        }
    
    def update_website_urls(self, main_url: Optional[str] = None, gallery_url: Optional[str] = None):
        """Actualizar URLs si es necesario"""
        if main_url:
            self.website_url = main_url
            logger.info(f"URL principal actualizada: {main_url}", 
                       extra={"component": "website_link_service"})
        
        if gallery_url:
            self.domos_gallery_url = gallery_url  
            logger.info(f"URL de galería actualizada: {gallery_url}", 
                       extra={"component": "website_link_service"})


# Instancia global del servicio
website_link_service = WebsiteLinkService()

def get_website_link_service() -> WebsiteLinkService:
    """Obtener instancia global del servicio de links"""
    return website_link_service