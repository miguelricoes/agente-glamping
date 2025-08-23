# services/intelligent_trigger_service.py
import re
from typing import Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class IntelligentTriggerService:
    """
    Servicio que detecta cuándo activar el agente IA automáticamente
    para temas específicos sin usar el menú
    """

    def __init__(self):
        self.accessibility_patterns = [
            r'\bsilla\s+de\s+ruedas\b', r'\bmovilidad\s+reducida\b',
            r'\bdiscapacidad\b', r'\baccesibilidad\b', r'\baccesible\b',
            r'\bradiografía\b', r'\bbaston\b', r'\bbastón\b',
            r'\bminusválid[oa]\b', r'\blimitaciones\s+físicas\b',
            r'\bpersona\s+con\s+discapacidad\b'
        ]

        self.images_patterns = [
            r'\bver\s+(?:fotos|imágenes|imagenes)\b', r'\bgalería\b', r'\bgaleria\b',
            r'\bfotos\s+del\s+(?:lugar|glamping|domos?)\b',
            r'\bimágenes\s+del\s+(?:lugar|glamping|domos?)\b',
            r'\bmostrar\s+(?:fotos|imágenes)\b', r'\bpágina\s+web\b',
            r'\bver\s+el\s+lugar\b', r'\blink\s+(?:de\s+)?(?:la\s+)?página\b',
            r'\benlace\s+(?:de\s+)?(?:la\s+)?web\b',
            r'\bimágenes\b', r'\bimagenes\b', r'\bfotos\b'
        ]

        self.services_included_patterns = [
            r'\bservicios\s+incluidos\b', r'\bqué\s+incluye\b', r'\bque\s+incluye\b',
            r'\bincluye\s+(?:el\s+)?(?:domo|glamping|estadía|estadia)\b',
            r'\bamenidades\b', r'\bcomodidades\b', r'\bservicios\s+(?:básicos|base)\b',
            r'\bqué\s+servicios\s+(?:están|estan)\s+incluidos\b',
            r'\bque\s+servicios\s+(?:están|estan)\s+incluidos\b',
            r'\bservicios\s+sin\s+costo\b', r'\bsin\s+costo\s+(?:adicional|extra)\b',
            r'\bincluido\s+en\s+(?:el\s+)?precio\b', r'\bincluido\s+en\s+(?:la\s+)?tarifa\b'
        ]

        self.services_additional_patterns = [
            r'\bservicios\s+(?:adicionales|externos|extra)\b',
            r'\bactividades\s+(?:adicionales|extras?)\b',
            r'\bqué\s+(?:hacer|actividades)\b', r'\bque\s+(?:hacer|actividades)\b',
            r'\bturismo\b', r'\bpaseos\b', r'\bexperiencias\b',
            r'\bdiversión\b', r'\bentretenimiento\b'
        ]

    def should_activate_ai_for_accessibility(self, message: str) -> Tuple[bool, str]:
        """Detecta si debe activar IA para temas de accesibilidad"""
        message_lower = message.lower()

        for pattern in self.accessibility_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"Activación IA para accesibilidad detectada: {pattern}")
                return True, "accessibility"

        return False, ""

    def should_activate_ai_for_images(self, message: str) -> Tuple[bool, str]:
        """Detecta si debe activar IA para solicitudes de imágenes/web"""
        message_lower = message.lower()

        for pattern in self.images_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"Activación IA para imágenes/web detectada: {pattern}")
                return True, "images_website"

        return False, ""

    def should_activate_ai_for_services(self, message: str) -> Tuple[bool, str]:
        """Detecta tipo de servicios solicitados"""
        message_lower = message.lower()

        # Verificar servicios incluidos primero (más específico)
        for pattern in self.services_included_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"Servicios incluidos detectados: {pattern}")
                return True, "services_included"

        # Verificar servicios adicionales
        for pattern in self.services_additional_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"Servicios adicionales detectados: {pattern}")
                return True, "services_additional"

        return False, ""

    def analyze_message(self, message: str) -> Tuple[bool, str, str]:
        """
        Analiza mensaje para determinar si activar IA automáticamente

        Returns:
            Tuple[bool, str, str]: (should_activate_ai, trigger_type, rag_context)
        """
        # Orden de prioridad de detección

        # 1. Accesibilidad
        should_activate, trigger = self.should_activate_ai_for_accessibility(message)
        if should_activate:
            return True, trigger, "accesibilidad+sugerencias_movilidad_reducida"

        # 2. Imágenes/Web
        should_activate, trigger = self.should_activate_ai_for_images(message)
        if should_activate:
            return True, trigger, "links_imagenes"

        # 3. Servicios
        should_activate, trigger = self.should_activate_ai_for_services(message)
        if should_activate:
            if trigger == "services_included":
                return True, trigger, "servicios_incluidos"
            elif trigger == "services_additional":
                return True, trigger, "actividades_adicionales+servicios_externos"

        return False, "", ""

# Instancia global
_intelligent_trigger_service = None

def get_intelligent_trigger_service() -> IntelligentTriggerService:
    """Factory function para obtener instancia del servicio"""
    global _intelligent_trigger_service
    if _intelligent_trigger_service is None:
        _intelligent_trigger_service = IntelligentTriggerService()
    return _intelligent_trigger_service