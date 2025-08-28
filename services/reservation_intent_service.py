# Servicio especializado para manejo inteligente del flujo de reservas
# Implementa detección específica según Variable 3 - Flujo inteligente de reservas

import re
from typing import Optional, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)

class ReservationIntentService:
    """
    Servicio que detecta y maneja intenciones de reserva según triggers específicos:
    - Solo inicia flujo con "quiero hacer una reserva" o variantes específicas
    - Si solo dice "reservas", pregunta si quiere hacer una o necesita información
    - Diferencia entre intención de reservar vs solicitar información sobre reservas
    """
    
    def __init__(self):
        """Inicializar el servicio de detección de intenciones de reserva"""
        # Definir patrones específicos para cada caso
        self._init_detection_patterns()
        
        logger.info("ReservationIntentService inicializado", 
                   extra={"component": "reservation_intent_service", "phase": "startup"})
    
    def _init_detection_patterns(self):
        """Inicializar patrones de detección para cada caso específico"""
        
        # Trigger 1: Intención clara de hacer una reserva (inicia flujo)
        self.make_reservation_patterns = [
            r'\bquiero\s+hacer\s+una\s+reserva\b', r'\bquisiera\s+hacer\s+una\s+reserva\b',
            r'\bnecesito\s+hacer\s+una\s+reserva\b', r'\bme\s+gustaría\s+hacer\s+una\s+reserva\b',
            r'\bvoy\s+a\s+hacer\s+una\s+reserva\b', r'\bhacer\s+una\s+reserva\b',
            r'\bquiero\s+reservar\b', r'\bquisiera\s+reservar\b', r'\bnecesito\s+reservar\b',
            r'\bme\s+gustaría\s+reservar\b', r'\bvoy\s+a\s+reservar\b',
            r'\bquiero\s+una\s+reserva\b', r'\bnecesito\s+una\s+reserva\b',
            r'\bme\s+gustaría\s+una\s+reserva\b', r'\bquisiera\s+una\s+reserva\b',
            r'\bnueva\s+reserva\b', r'\brealizar\s+una\s+reserva\b', r'\bcrear\s+una\s+reserva\b',
            # Variantes con "reservación"
            r'\bquiero\s+hacer\s+una\s+reservación\b', r'\bhacer\s+una\s+reservación\b',
            r'\bquiero\s+una\s+reservación\b', r'\bnecesito\s+una\s+reservación\b',
            # Variantes de hospedaje/alojamiento
            r'\bquiero\s+hospedarme\b', r'\bnecesito\s+alojarme\b', r'\bbusco\s+alojamiento\b',
            r'\bquiero\s+quedarme\b', r'\bnecesito\s+hospedaje\b'
        ]
        
        # Trigger 2: Palabra ambigua "reservas" (requiere clarificación)
        self.ambiguous_reservation_patterns = [
            r'^\s*reservas?\s*$',  # Solo "reserva" o "reservas"
            r'^\s*reservaciones?\s*$',  # Solo "reservación" o "reservaciones"
            r'^\s*sobre\s+reservas?\s*$',  # "sobre reservas"
            r'^\s*acerca\s+de\s+reservas?\s*$',  # "acerca de reservas"
            r'^\s*info\s+reservas?\s*$',  # "info reservas"
            r'^\s*información\s+reservas?\s*$',  # "información reservas"
            r'^\s*informacion\s+reservas?\s*$'  # "informacion reservas"
        ]
        
        # Trigger 3: Solicitud de información sobre reservas (no inicia flujo)
        self.reservation_info_patterns = [
            r'\binformación\s+sobre\s+reservas?\b', r'\binformacion\s+sobre\s+reservas?\b',
            r'\bpolíticas\s+de\s+reservas?\b', r'\bpoliticas\s+de\s+reservas?\b',
            r'\brequisitos\s+para\s+reservar\b', r'\brequisitos\s+de\s+reservas?\b',
            r'\bcómo\s+funciona\s+la\s+reserva\b', r'\bcomo\s+funciona\s+la\s+reserva\b',
            r'\bproceso\s+de\s+reserva\b', r'\bprocedimiento\s+de\s+reserva\b',
            r'\bcondiciones\s+de\s+reserva\b', r'\btérminos\s+de\s+reserva\b',
            r'\bterminos\s+de\s+reserva\b', r'\bnormas\s+de\s+reserva\b',
            r'\bqué\s+necesito\s+para\s+reservar\b', r'\bque\s+necesito\s+para\s+reservar\b',
            r'\bdatos\s+para\s+reservar\b', r'\binformación\s+de\s+reserva\b',
            r'\bcancelación\s+de\s+reservas?\b', r'\bcancelacion\s+de\s+reservas?\b'
        ]
        
        # Trigger 4: Consultas sobre estado de reservas existentes
        self.reservation_status_patterns = [
            r'\bmi\s+reserva\b', r'\bmis\s+reservas?\b', r'\bla\s+reserva\s+que\s+hice\b',
            r'\bestado\s+de\s+mi\s+reserva\b', r'\bconsultar\s+mi\s+reserva\b',
            r'\bver\s+mi\s+reserva\b', r'\breserva\s+confirmada\b',
            r'\bconfirmación\s+de\s+reserva\b', r'\bconfirmacion\s+de\s+reserva\b',
            r'\bnúmero\s+de\s+reserva\b', r'\bnumero\s+de\s+reserva\b'
        ]
    
    def analyze_reservation_intent(self, message: str, user_state: dict = None) -> Tuple[str, str, str]:
        """
        Analiza la intención de reserva del usuario según Variable 3
        
        Args:
            message: Mensaje del usuario
            user_state: Estado actual del usuario (crítico para contexto)
            
        Returns:
            Tuple[str, str, str]: (intent_type, action, reason)
            intent_type: 'make_reservation', 'ambiguous', 'info_request', 'status_check', 'none'
            action: 'start_flow', 'ask_clarification', 'provide_info', 'check_status', 'none'
            reason: Descripción de por qué se tomó esta decisión
        """
        try:
            message_clean = message.lower().strip()
            
            logger.info(f"Analizando intención de reserva: '{message_clean[:50]}...'", 
                       extra={"component": "reservation_intent_service", "action": "analyze_intent"})
            
            # CRÍTICO: Si el usuario ya está en flujo de reserva, no detectar nueva intención
            if user_state and user_state.get("current_flow") == "reserva":
                logger.info("Usuario ya en flujo de reserva - no analizar nueva intención", 
                           extra={"component": "reservation_intent_service", "current_flow": "reserva"})
                return "none", "none", "Usuario ya está en flujo de reserva activo"
            
            # Verificar cada tipo de intención en orden de prioridad
            
            # 1. Intención clara de hacer reserva (más específico primero)
            if self._matches_patterns(message_clean, self.make_reservation_patterns):
                logger.info("Intención detectada: hacer reserva - iniciando flujo", 
                           extra={"component": "reservation_intent_service", "intent": "make_reservation"})
                return "make_reservation", "start_flow", "Usuario quiere hacer una reserva específicamente"
            
            # 2. Consulta sobre estado de reservas existentes
            if self._matches_patterns(message_clean, self.reservation_status_patterns):
                logger.info("Intención detectada: consultar estado de reserva", 
                           extra={"component": "reservation_intent_service", "intent": "status_check"})
                return "status_check", "check_status", "Usuario consulta sobre una reserva existente"
            
            # 3. Solicitud de información sobre reservas
            if self._matches_patterns(message_clean, self.reservation_info_patterns):
                logger.info("Intención detectada: información sobre reservas", 
                           extra={"component": "reservation_intent_service", "intent": "info_request"})
                return "info_request", "provide_info", "Usuario solicita información sobre políticas/requisitos"
            
            # 4. Palabra ambigua "reservas" (requiere clarificación)
            if self._matches_patterns(message_clean, self.ambiguous_reservation_patterns):
                logger.info("Intención detectada: ambigua - requiere clarificación", 
                           extra={"component": "reservation_intent_service", "intent": "ambiguous"})
                return "ambiguous", "ask_clarification", "Usuario dijo solo 'reservas' - necesita clarificación"
            
            logger.info("No se detectó intención de reserva", 
                       extra={"component": "reservation_intent_service", "result": "no_intent"})
            return "none", "none", "No se detectó intención relacionada con reservas"
            
        except Exception as e:
            logger.error(f"Error analizando intención de reserva: {e}", 
                        extra={"component": "reservation_intent_service"})
            return "none", "none", f"Error en análisis: {e}"
    
    def _matches_patterns(self, message: str, patterns: List[str]) -> bool:
        """Verifica si el mensaje coincide con alguno de los patrones"""
        try:
            for pattern in patterns:
                if re.search(pattern, message):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error verificando patrones: {e}", 
                        extra={"component": "reservation_intent_service"})
            return False
    
    def generate_clarification_response(self, user_message: str = "") -> str:
        """
        Genera respuesta de clarificación cuando el usuario dice solo "reservas"
        
        Args:
            user_message: Mensaje original del usuario
            
        Returns:
            str: Respuesta de clarificación
        """
        try:
            logger.info("Generando respuesta de clarificación para reservas", 
                       extra={"component": "reservation_intent_service", "action": "clarification"})
            
            return """🤔 **¿QUÉ TE GUSTARÍA HACER CON LAS RESERVAS?**

Por favor, dime qué necesitas:

🏕️ **¿QUIERES HACER UNA RESERVA?**
• Escribe: "Quiero hacer una reserva"
• O: "Quiero reservar"

📋 **¿NECESITAS INFORMACIÓN SOBRE RESERVAS?**
• Escribe: "Información sobre reservas"
• O: "Políticas de reservas"
• O: "Requisitos para reservar"

📊 **¿QUIERES CONSULTAR UNA RESERVA EXISTENTE?**
• Escribe: "Mi reserva"
• O: "Estado de mi reserva"

💬 **¡Dime exactamente qué necesitas y te ayudo de inmediato!** 😊"""
            
        except Exception as e:
            logger.error(f"Error generando respuesta de clarificación: {e}", 
                        extra={"component": "reservation_intent_service"})
            return "¿Quieres hacer una reserva o necesitas información sobre reservas? Por favor, especifica qué necesitas."
    
    def generate_info_response(self, user_message: str = "") -> str:
        """
        Genera respuesta con información sobre reservas (usando RAG)
        
        Args:
            user_message: Mensaje original del usuario
            
        Returns:
            str: Indicación de que se debe usar RAG para requisitos de reserva
        """
        try:
            logger.info("Generando respuesta de información sobre reservas", 
                       extra={"component": "reservation_intent_service", "action": "info_response"})
            
            # Esto indica que se debe usar el RAG de requisitos_reserva
            return "RAG_REQUISITOS_RESERVA"
            
        except Exception as e:
            logger.error(f"Error generando respuesta de información: {e}", 
                        extra={"component": "reservation_intent_service"})
            return "RAG_REQUISITOS_RESERVA"
    
    def generate_status_check_response(self, user_message: str = "") -> str:
        """
        Genera respuesta para consulta de estado de reservas
        
        Args:
            user_message: Mensaje original del usuario
            
        Returns:
            str: Respuesta para consulta de estado
        """
        try:
            logger.info("Generando respuesta para consulta de estado de reserva", 
                       extra={"component": "reservation_intent_service", "action": "status_check"})
            
            return """📋 **CONSULTA DE RESERVAS EXISTENTES**

Para consultar el estado de tu reserva, necesito algunos datos:

📝 **Información requerida:**
• Tu nombre completo
• Número de teléfono con el que hiciste la reserva
• Fechas aproximadas de la reserva

📞 **O puedes contactarnos directamente:**
• WhatsApp: +57 3054614926
• Email: glampingbrillodelunaguatavita@gmail.com

🕐 **Horario de atención**: Lunes a Domingo, 8:00 AM a 9:00 PM

¿Tienes estos datos para consultar tu reserva? 📱"""
            
        except Exception as e:
            logger.error(f"Error generando respuesta de consulta: {e}", 
                        extra={"component": "reservation_intent_service"})
            return "Para consultar tu reserva, necesito tu nombre y número de teléfono. ¿Los tienes disponibles?"
    
    def should_start_reservation_flow(self, message: str, user_state: dict = None) -> bool:
        """
        Determina si se debe iniciar el flujo de reservas según Variable 3
        
        Args:
            message: Mensaje del usuario
            user_state: Estado actual del usuario (crítico para detectar flujos activos)
            
        Returns:
            bool: True si debe iniciar el flujo de reservas
        """
        try:
            # CRÍTICO: Si ya hay un flujo de reserva activo, NO iniciar nuevo flujo
            if user_state and user_state.get("current_flow") == "reserva":
                logger.info("Usuario ya tiene flujo de reserva activo - NO iniciar nuevo flujo", 
                           extra={"component": "reservation_intent_service", "current_flow": user_state.get("current_flow")})
                return False
            
            intent_type, action, reason = self.analyze_reservation_intent(message, user_state)
            should_start = (intent_type == "make_reservation" and action == "start_flow")
            
            if should_start:
                logger.info("Flujo de reservas debe iniciarse", 
                           extra={"component": "reservation_intent_service", "reason": reason})
            else:
                logger.info(f"Flujo de reservas NO debe iniciarse: {reason}", 
                           extra={"component": "reservation_intent_service", "intent": intent_type})
            
            return should_start
            
        except Exception as e:
            logger.error(f"Error determinando inicio de flujo: {e}", 
                        extra={"component": "reservation_intent_service"})
            return False


# Instancia global del servicio
reservation_intent_service = ReservationIntentService()

def get_reservation_intent_service() -> ReservationIntentService:
    """Obtener instancia global del servicio de intenciones de reserva"""
    return reservation_intent_service