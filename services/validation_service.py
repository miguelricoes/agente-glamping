# Servicio centralizado de validación y parsing de datos
# Extrae validaciones dispersas de agente.py (líneas 1454-1857)

import re
import json
from datetime import date, datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ValidationService:
    """
    Servicio centralizado para validación y parsing de datos
    Consolida todas las validaciones dispersas en agente.py
    """
    
    def __init__(self):
        """Inicializar servicio de validación"""
        logger.info("Inicializando ValidationService", 
                   extra={"component": "validation_service", "phase": "startup"})
    
    def is_greeting_message(self, message: str) -> bool:
        """
        Detecta si un mensaje es un saludo inicial
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            bool: True si es un saludo
        """
        greeting_patterns = [
            r'\bhola\b', r'\bholi\b', r'\bhi\b', r'\bhey\b', r'\bbuenas?\b', 
            r'\bsaludos?\b', r'\bbuen[ao]s?\s?(d[ií]as?|tardes?|noches?)\b',
            r'\bqué\s+tal\b', r'\bcómo\s+est[áa]s?\b', r'\b¿?hola\b',
            r'\bque\s+m[aá]s\b', r'\bqué\s+m[aá]s\b', r'\bholiwis\b', r'\bholiii\b',
            r'\bbuenos\s+d[ií]as\b', r'\bbuenas\s+tardes\b', r'\bbuenas\s+noches\b',
            r'\bhello\b', r'\bgood\s+morning\b', r'\bgood\s+afternoon\b', r'\bgood\s+evening\b',
            r'\bholaaaa\b', r'\bholita\b', r'\bholaaa\b', r'\bholiwi\b'
        ]
        
        message_lower = message.lower().strip()
        
        # ANTES de return, agregar:
        continuation_responses = ['sí', 'si', 'yes', 'no', 'ok', 'vale', 'bien', 'perfecto', 'continuar']
        if message_lower in continuation_responses:
            return False
            
        return any(re.search(pattern, message_lower) for pattern in greeting_patterns)
    
    def is_menu_selection(self, message: str) -> bool:
        """
        Detecta si el mensaje es una selección del menú (números o palabras clave)
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            bool: True si es una selección de menú válida
        """
        message_clean = message.lower().strip()
        
        # Detectar números directos (1-5 para el menú simplificado)
        if re.match(r'^[1-5]$', message_clean):
            return True
        
        # Excluir consultas específicas que contengan palabras clave de consulta detallada
        specific_query_keywords = ['más información', 'mas información', 'detalles', 'cuéntame', 'cuentame', 'explícame', 'explicame', 'polaris', 'aurora', 'quasar', 'cassiopeia', 'caracteristicas', 'características', 'jacuzzi', 'amenidades']
        if any(keyword in message_clean for keyword in specific_query_keywords):
            return False
        
        # Detectar variantes textuales - palabras simples Y exactas
        menu_variants = {
            '1': ['informacion', 'información', 'informacion general', 'información general', 'opcion 1', 'opción 1'],
            '2': ['domos', 'domos disponibles', 'opcion 2', 'opción 2'],
            '3': ['disponibilidad', 'consultar disponibilidad', 'opcion 3', 'opción 3'],
            '4': ['servicios', 'servicios incluidos', 'servicios combinados', 'opcion 4', 'opción 4'],
            '5': ['politicas', 'políticas', 'opcion 5', 'opción 5']
            # Opciones 6, 7, 8 eliminadas - ahora se manejan via auto-activación IA
        }
        
        for option, variants in menu_variants.items():
            # Para palabras simples como "servicios" en "no, quiero servicios", buscar palabra exacta
            for variant in variants:
                if variant == message_clean or f" {variant}" in message_clean or f"{variant} " in message_clean or f" {variant} " in message_clean:
                    return True
        
        return False
    
    def extract_menu_option(self, message: str) -> str:
        """
        Extrae la opción del menú seleccionada
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            str: Número de opción ('1'-'8') o vacío si no se detecta
        """
        message_clean = message.lower().strip()
        
        # Números directos (1-5 para menú simplificado)
        if re.match(r'^[1-5]$', message_clean):
            return message_clean
        
        # Excluir consultas específicas que contengan palabras clave de consulta detallada
        specific_query_keywords = ['más información', 'mas información', 'detalles', 'cuéntame', 'cuentame', 'explícame', 'explicame', 'polaris', 'aurora', 'quasar', 'cassiopeia', 'caracteristicas', 'características', 'jacuzzi', 'amenidades']
        if any(keyword in message_clean for keyword in specific_query_keywords):
            return ""
        
        # Variantes textuales con detección para todas las opciones - palabras simples Y exactas
        menu_variants = {
            '1': ['informacion', 'información', 'informacion general', 'información general', 'opcion 1', 'opción 1'],
            '2': ['domos', 'domos disponibles', 'opcion 2', 'opción 2'],
            '3': ['disponibilidad', 'consultar disponibilidad', 'opcion 3', 'opción 3'],
            '4': ['servicios', 'servicios incluidos', 'servicios combinados', 'opcion 4', 'opción 4'],
            '5': ['politicas', 'políticas', 'opcion 5', 'opción 5']
            # Opciones 6, 7, 8 eliminadas - ahora se manejan via auto-activación IA
        }
        
        for option, variants in menu_variants.items():
            # Para palabras simples como "servicios" en "no, quiero servicios", buscar palabra exacta
            for variant in variants:
                if variant == message_clean or f" {variant}" in message_clean or f"{variant} " in message_clean or f" {variant} " in message_clean:
                    return option
        
        return ""
    
    def is_yes_no_response(self, message: str) -> Optional[bool]:
        """
        Detecta si el mensaje es una respuesta sí/no
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Optional[bool]: True para sí, False para no, None si no es una respuesta sí/no
        """
        message_clean = message.lower().strip()
        
        # Respuestas afirmativas
        yes_patterns = [
            'si', 'sí', 'yes', 'claro', 'por supuesto', 'seguro', 'dale', 'ok', 'okay',
            'perfecto', 'genial', 'excelente', 'bueno', 'bien', 'confirmo', 'correcto',
            'afirmativo', 'efectivamente', 'exacto', 'obvio', 'desde luego'
        ]
        
        # Respuestas negativas (evitar palabras ambiguas como "no sé")
        no_patterns = [
            'no,', 'nop', 'nope', 'para nada', 'negativo', 'nunca', 'jamás', 'jamas',
            'ni modo', 'no gracias', 'no, gracias', 'mejor no', 'no me interesa',
            'paso', 'cancel', 'cancelar', 'mejor otro día', 'no por ahora'
        ]
        
        # Patrones ambiguos que deben retornar None
        ambiguous_patterns = [
            'no sé', 'no se', 'tal vez', 'quizás', 'quizas', 'puede ser', 
            'mmm', 'veamos', 'no estoy seguro', 'no estoy segura'
        ]
        
        # Verificar patrones ambiguos primero
        for pattern in ambiguous_patterns:
            if pattern in message_clean:
                return None
        
        # Verificar respuestas exactas
        if message_clean in yes_patterns:
            return True
        elif message_clean in no_patterns:
            return False
        
        # Verificar patrones parciales para frases más largas
        for pattern in yes_patterns:
            if pattern in message_clean:
                return True
        
        # Verificar "no" simple pero no ambiguo
        if message_clean == 'no':
            return False
        
        # Verificar si empieza con "no," (como "no, quiero servicios")
        if message_clean.startswith('no,') or message_clean.startswith('no '):
            return False
        
        for pattern in no_patterns:
            if pattern in message_clean:
                return False
        
        return None
    
    def detect_domo_specific_request(self, message: str) -> Optional[str]:
        """
        Detecta qué información específica de domos solicita el usuario
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Optional[str]: Tipo de información solicitada o None
        """
        message_clean = message.lower().strip()
        
        # Patrones para información específica de domos
        if any(word in message_clean for word in ['antares', 'polaris', 'sirius', 'centaury', 'domo específico', 'domo especifico']):
            return 'domo_especifico'
        elif any(word in message_clean for word in ['características', 'caracteristicas', 'detalles', 'especificaciones', 'especificacion']):
            return 'caracteristicas'
        elif any(word in message_clean for word in ['precios', 'precio', 'costo', 'tarifa', 'tarifas', 'cuestan', 'cuesta', 'cuánto']):
            return 'precios'
        elif any(word in message_clean for word in ['fotos', 'imágenes', 'imagenes', 'galería', 'galeria', 'ver']):
            return 'imagenes'
        elif any(word in message_clean for word in ['servicios incluidos', 'qué incluye', 'que incluye', 'amenidades']):
            return 'servicios_incluidos'
        elif any(word in message_clean for word in ['capacidad', 'personas', 'cuántas personas', 'cuantas personas']):
            return 'capacidad'
        elif any(word in message_clean for word in ['ubicación', 'ubicacion', 'donde', 'dónde']):
            return 'ubicacion'
        
        return None
    
    def detect_servicios_specific_request(self, message: str) -> Optional[str]:
        """
        Detecta qué información específica de servicios solicita el usuario
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Optional[str]: Tipo de información solicitada o None
        """
        message_clean = message.lower().strip()
        
        # Patrones para información específica de servicios
        if any(word in message_clean for word in ['servicios incluidos', 'incluidos', 'que incluye', 'qué incluye', 'internos']):
            return 'servicios_incluidos'
        elif any(word in message_clean for word in ['servicios externos', 'externos', 'actividades', 'adicionales', 'extras']):
            return 'servicios_externos'
        elif any(word in message_clean for word in ['ambos', 'todos', 'completa', 'completo', 'toda la información']):
            return 'todos_servicios'
        elif any(word in message_clean for word in ['precios', 'precio', 'costo', 'cuestan', 'cuesta', 'cuánto', 'tarifas']):
            return 'precios_servicios'
        elif any(word in message_clean for word in ['características', 'caracteristicas', 'detalles', 'especificaciones']):
            return 'caracteristicas_servicios'
        elif any(word in message_clean for word in ['reservar', 'reserva', 'contratar', 'agendar']):
            return 'reservar_servicios'
        
        return None
    
    def detect_website_link_request(self, message: str) -> Tuple[bool, str, str]:
        """
        Detecta si el usuario solicita el link de la página web según triggers específicos
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[bool, str, str]: (should_share, trigger_type, reason)
        """
        try:
            # Usar ImportResolver para evitar dependencias circulares
            from services.import_resolver import get_import_resolver
            resolver = get_import_resolver()
            website_service = resolver.get_service('website_link_service')
            
            if website_service:
                # Usar el servicio especializado para detectar
                should_share, trigger_type, reason = website_service.should_share_website_link(message)
                
                if should_share:
                    logger.info(f"Solicitud de link detectada: {trigger_type} - {reason}", 
                               extra={"component": "validation_service", "website_trigger": trigger_type})
                
                return should_share, trigger_type, reason
            else:
                logger.warning("Website service no disponible en ImportResolver")
                return False, "", "Service not available"
            
        except Exception as e:
            logger.error(f"Error detectando solicitud de website: {e}", 
                        extra={"component": "validation_service"})
            return False, "", ""
    
    def detect_admin_contact_request(self, message: str) -> Tuple[bool, str, str]:
        """
        Detecta si el usuario solicita contacto de administradores según triggers de PQRS
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[bool, str, str]: (should_share, trigger_type, reason)
        """
        try:
            # Usar ImportResolver para evitar dependencias circulares
            from services.import_resolver import get_import_resolver
            resolver = get_import_resolver()
            
            # Buscar en conversation_handlers el admin_contact
            conversation_handlers = resolver.get_service('conversation_handlers')
            if conversation_handlers and 'admin_contact' in conversation_handlers:
                admin_handler = conversation_handlers['admin_contact']
                
                # El handler debería retornar el formato esperado
                should_share, trigger_type, reason = admin_handler(message, self)
                
                if should_share:
                    logger.info(f"Solicitud de contacto admin detectada: {trigger_type} - {reason}", 
                               extra={"component": "validation_service", "admin_trigger": trigger_type})
                
                return should_share, trigger_type, reason
            else:
                logger.warning("Admin contact handler no disponible en ImportResolver")
                return False, "", "Handler not available"
            
        except Exception as e:
            logger.error(f"Error detectando solicitud de contacto admin: {e}", 
                        extra={"component": "validation_service"})
            return False, "", ""
    
    def analyze_reservation_intent_v3(self, message: str) -> Tuple[str, str, str]:
        """
        Analiza intención de reserva según Variable 3 - Flujo inteligente
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[str, str, str]: (intent_type, action, reason)
        """
        try:
            # Usar ImportResolver para evitar dependencias circulares
            from services.import_resolver import get_import_resolver
            resolver = get_import_resolver()
            
            # Buscar en conversation_handlers el reservation_intent
            conversation_handlers = resolver.get_service('conversation_handlers')
            if conversation_handlers and 'reservation_intent' in conversation_handlers:
                reservation_handler = conversation_handlers['reservation_intent']
                
                # El handler debería retornar el formato esperado
                intent_type, action, reason = reservation_handler(message, self)
                
                logger.info(f"Intención de reserva analizada: {intent_type} -> {action}", 
                           extra={"component": "validation_service", "reservation_intent": intent_type})
                
                return intent_type, action, reason
            else:
                logger.warning("Reservation intent handler no disponible en ImportResolver")
                return "none", "none", "Handler not available"
            
        except Exception as e:
            logger.error(f"Error analizando intención de reserva: {e}", 
                        extra={"component": "validation_service"})
            return "none", "none", f"Error: {e}"
    
    def detect_availability_request(self, message: str) -> Optional[str]:
        """
        Detecta qué tipo de consulta de disponibilidad solicita el usuario
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Optional[str]: Tipo de consulta de disponibilidad o None
        """
        message_clean = message.lower().strip()
        
        # Patrones para diferentes tipos de consulta de disponibilidad (más específicos primero)
        if any(pattern in message_clean for pattern in ['otras fechas', 'diferentes fechas']):
            return 'otras_fechas'
        elif any(pattern in message_clean for pattern in ['reservar', 'reserva', 'quiero reservar']):
            return 'reserva_intent'
        elif any(pattern in message_clean for pattern in ['disponible', 'disponibilidad', 'libre', 'ocupado']):
            return 'disponibilidad_consulta'
        elif any(pattern in message_clean for pattern in ['fechas', 'fecha', 'cuando', 'cuándo', 'día', 'dias']):
            return 'fecha_consulta'
        
        return None
    
    def parse_availability_dates(self, message: str) -> Tuple[bool, Optional[date], Optional[date], int, str]:
        """
        Parsea fechas de entrada y salida desde un mensaje de disponibilidad
        
        Args:
            message: Mensaje del usuario con fechas
            
        Returns:
            Tuple[bool, date, date, int, str]: (success, fecha_entrada, fecha_salida, personas, mensaje_error)
        """
        try:
            message_clean = message.lower().strip()
            
            # Extraer número de personas
            personas = 2  # Por defecto
            person_patterns = [
                r'(\d+)\s*persona[s]?',
                r'para\s*(\d+)',
                r'(\d+)\s*huespedes?',
                r'somos\s*(\d+)'
            ]
            
            for pattern in person_patterns:
                match = re.search(pattern, message_clean)
                if match:
                    try:
                        personas = int(match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Patrones para extraer fechas
            date_patterns = [
                # "del X al Y de mes"
                r'del\s+(\d{1,2})\s+al\s+(\d{1,2})\s+de\s+(\w+)',
                # "desde X hasta Y de mes"
                r'desde\s+(\d{1,2})\s+hasta\s+(\d{1,2})\s+de\s+(\w+)',
                # "X al Y de mes"
                r'(\d{1,2})\s+al\s+(\d{1,2})\s+de\s+(\w+)',
                # "X de mes hasta Y de mes"
                r'(\d{1,2})\s+de\s+(\w+)\s+hasta\s+(\d{1,2})\s+de\s+(\w+)',
                # Fechas con formato DD/MM/YYYY
                r'(\d{1,2}/\d{1,2}/\d{4})\s*(?:al|hasta|a)\s*(\d{1,2}/\d{1,2}/\d{4})',
                # Fechas con formato DD-MM-YYYY
                r'(\d{1,2}-\d{1,2}-\d{4})\s*(?:al|hasta|a)\s*(\d{1,2}-\d{1,2}-\d{4})'
            ]
            
            fecha_entrada = None
            fecha_salida = None
            
            # Mapear nombres de meses
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            
            # Buscar patrones de fecha
            for pattern in date_patterns:
                match = re.search(pattern, message_clean)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:  # del X al Y de mes
                        dia_entrada, dia_salida, mes_nombre = groups
                        mes_num = meses.get(mes_nombre, None)
                        if mes_num:
                            año_actual = date.today().year
                            try:
                                fecha_entrada = date(año_actual, mes_num, int(dia_entrada))
                                fecha_salida = date(año_actual, mes_num, int(dia_salida))
                            except ValueError:
                                continue
                    
                    elif len(groups) == 4:  # X de mes hasta Y de mes
                        dia_entrada, mes1, dia_salida, mes2 = groups
                        mes1_num = meses.get(mes1, None)
                        mes2_num = meses.get(mes2, None)
                        if mes1_num and mes2_num:
                            año_actual = date.today().year
                            try:
                                fecha_entrada = date(año_actual, mes1_num, int(dia_entrada))
                                fecha_salida = date(año_actual, mes2_num, int(dia_salida))
                            except ValueError:
                                continue
                    
                    elif len(groups) == 2:  # Fechas con formato completo
                        fecha_str1, fecha_str2 = groups
                        success1, fecha_entrada, _ = self.parse_flexible_date(fecha_str1)
                        success2, fecha_salida, _ = self.parse_flexible_date(fecha_str2)
                        if success1 and success2:
                            break
                    
                    if fecha_entrada and fecha_salida:
                        break
            
            # Validar fechas encontradas
            if fecha_entrada and fecha_salida:
                # Validar que las fechas sean lógicas
                valid_range, range_error = self.validate_date_range(fecha_entrada, fecha_salida)
                if valid_range:
                    logger.info(f"Fechas de disponibilidad parseadas: {fecha_entrada} - {fecha_salida} para {personas} personas", 
                               extra={"component": "validation_service", "entrada": str(fecha_entrada), "salida": str(fecha_salida), "personas": personas})
                    return True, fecha_entrada, fecha_salida, personas, ""
                else:
                    return False, None, None, personas, range_error
            else:
                return False, None, None, personas, "No se pudieron detectar fechas válidas en el mensaje"
            
        except Exception as e:
            error_msg = f"Error parseando fechas de disponibilidad: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, None, None, 2, error_msg
    
    def validate_guest_names(self, names_data) -> Tuple[bool, List, str]:
        """
        Valida y procesa nombres de huéspedes
        
        Args:
            names_data: Datos de nombres (string o lista)
            
        Returns:
            Tuple[bool, List, str]: (success, nombres_procesados, mensaje_error)
        """
        try:
            logger.info("Validando nombres de huéspedes", 
                       extra={"component": "validation_service", "action": "validate_guest_names"})
            
            if not names_data:
                return False, [], "No se proporcionaron nombres de huéspedes"
            
            # Procesar según el tipo de dato
            if isinstance(names_data, str):
                if names_data.strip():
                    # Dividir por comas o saltos de línea
                    nombres = [name.strip() for name in re.split(r'[,\n]', names_data) if name.strip()]
                else:
                    return False, [], "Los nombres no pueden estar vacíos"
            elif isinstance(names_data, list):
                nombres = [str(name).strip() for name in names_data if str(name).strip()]
            else:
                return False, [], "Formato de nombres inválido"
            
            if not nombres:
                return False, [], "Debe proporcionar al menos un nombre"
            
            # Validar cada nombre
            nombres_validados = []
            for nombre in nombres:
                # Remover caracteres especiales excepto espacios, acentos y guiones
                nombre_limpio = re.sub(r'[^\w\s\-áéíóúñüÁÉÍÓÚÑÜ]', '', nombre).strip()
                
                if len(nombre_limpio) < 2:
                    return False, [], f"El nombre '{nombre}' es demasiado corto"
                
                if len(nombre_limpio) > 50:
                    return False, [], f"El nombre '{nombre}' es demasiado largo"
                
                nombres_validados.append(nombre_limpio.title())
            
            logger.info(f"Nombres validados exitosamente: {len(nombres_validados)} nombres", 
                       extra={"component": "validation_service", "names_count": len(nombres_validados)})
            
            return True, nombres_validados, ""
            
        except Exception as e:
            error_msg = f"Error validando nombres de huéspedes: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, [], error_msg
    
    def parse_flexible_date(self, date_str: str) -> Tuple[bool, Optional[date], str]:
        """
        Parsea fechas en formato flexible (extraído de agente.py líneas 1504-1582)
        
        Args:
            date_str: String de fecha a parsear
            
        Returns:
            Tuple[bool, date, str]: (success, fecha_parseada, mensaje_error)
        """
        try:
            if not date_str or not date_str.strip():
                return False, None, "Fecha vacía"
            
            date_str = date_str.strip().lower()
            
            # Patrones de fecha comunes
            patterns = [
                # Formato ISO: YYYY-MM-DD
                (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', lambda m: date(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
                
                # Formato DD/MM/YYYY
                (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', lambda m: date(int(m.group(3)), int(m.group(2)), int(m.group(1)))),
                
                # Formato DD-MM-YYYY
                (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', lambda m: date(int(m.group(3)), int(m.group(2)), int(m.group(1)))),
                
                # Formato DD.MM.YYYY
                (r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', lambda m: date(int(m.group(3)), int(m.group(2)), int(m.group(1)))),
                
                # Formato MM/DD/YYYY (menos común en Colombia)
                (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', lambda m: date(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
            ]
            
            for pattern, date_constructor in patterns:
                match = re.match(pattern, date_str)
                if match:
                    try:
                        parsed_date = date_constructor(match)
                        
                        # Validar que la fecha sea razonable
                        today = date.today()
                        min_date = today - timedelta(days=1)  # Permitir hoy
                        max_date = today + timedelta(days=365)  # Máximo 1 año adelante
                        
                        if parsed_date < min_date:
                            return False, None, f"La fecha {parsed_date} es anterior a hoy"
                        
                        if parsed_date > max_date:
                            return False, None, f"La fecha {parsed_date} está muy lejos en el futuro"
                        
                        logger.info(f"Fecha parseada exitosamente: {parsed_date}", 
                                   extra={"component": "validation_service", "date": str(parsed_date)})
                        
                        return True, parsed_date, ""
                        
                    except ValueError as e:
                        continue  # Probar siguiente patrón
            
            # Intentar parseo con palabras relativas
            relative_patterns = {
                'hoy': 0,
                'mañana': 1,
                'pasado mañana': 2,
                'próximo fin de semana': 7,
                'la próxima semana': 7,
                'el próximo mes': 30
            }
            
            for phrase, days_offset in relative_patterns.items():
                if phrase in date_str:
                    target_date = date.today() + timedelta(days=days_offset)
                    logger.info(f"Fecha relativa parseada: {phrase} -> {target_date}", 
                               extra={"component": "validation_service", "relative_phrase": phrase})
                    return True, target_date, ""
            
            return False, None, f"No se pudo parsear la fecha: {date_str}"
            
        except Exception as e:
            error_msg = f"Error parseando fecha '{date_str}': {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, None, error_msg
    
    def validate_date_range(self, fecha_entrada: date, fecha_salida: date) -> Tuple[bool, str]:
        """
        Valida que el rango de fechas sea lógico
        
        Args:
            fecha_entrada: Fecha de entrada
            fecha_salida: Fecha de salida
            
        Returns:
            Tuple[bool, str]: (valid, mensaje_error)
        """
        try:
            if fecha_salida <= fecha_entrada:
                return False, "La fecha de salida debe ser posterior a la fecha de entrada"
            
            # Validar duración máxima (ej. 30 días)
            duration = (fecha_salida - fecha_entrada).days
            if duration > 30:
                return False, f"La estadía no puede ser mayor a 30 días (solicitado: {duration} días)"
            
            if duration < 1:
                return False, "La estadía debe ser de al menos 1 día"
            
            logger.info(f"Rango de fechas validado: {fecha_entrada} - {fecha_salida} ({duration} días)", 
                       extra={"component": "validation_service", "duration": duration})
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Error validando rango de fechas: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, error_msg
    
    def validate_contact_info(self, phone: str, email: str) -> Tuple[bool, str, str, List[str]]:
        """
        Valida información de contacto
        
        Args:
            phone: Número de teléfono
            email: Dirección de email
            
        Returns:
            Tuple[bool, str, str, List[str]]: (valid, phone_clean, email_clean, errores)
        """
        try:
            errors = []
            phone_clean = ""
            email_clean = ""
            
            # Validar teléfono
            if phone:
                # Remover caracteres no numéricos excepto +
                phone_clean = re.sub(r'[^\d\+]', '', phone.strip())
                
                # Validar formato básico
                if not re.match(r'^\+?[\d]{10,15}$', phone_clean):
                    errors.append("Formato de teléfono inválido. Use formato: +57XXXXXXXXXX o XXXXXXXXXX")
                else:
                    # Agregar código de país si no lo tiene
                    if not phone_clean.startswith('+'):
                        if phone_clean.startswith('57'):
                            phone_clean = '+' + phone_clean
                        elif len(phone_clean) == 10:
                            phone_clean = '+57' + phone_clean
                        else:
                            phone_clean = '+57' + phone_clean
            else:
                errors.append("Número de teléfono es requerido")
            
            # Validar email
            if email:
                email_clean = email.strip().lower()
                # Patrón básico de email
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email_clean):
                    errors.append("Formato de email inválido")
            else:
                errors.append("Email es requerido")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("Información de contacto validada exitosamente", 
                           extra={"component": "validation_service", "phone": phone_clean, "email": email_clean})
            else:
                logger.warning(f"Errores en validación de contacto: {errors}", 
                              extra={"component": "validation_service", "errors": errors})
            
            return is_valid, phone_clean, email_clean, errors
            
        except Exception as e:
            error_msg = f"Error validando información de contacto: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, "", "", [error_msg]
    
    def validate_guest_count(self, cantidad_huespedes: Any) -> Tuple[bool, int, str]:
        """
        Valida cantidad de huéspedes
        
        Args:
            cantidad_huespedes: Cantidad a validar
            
        Returns:
            Tuple[bool, int, str]: (valid, cantidad_validada, mensaje_error)
        """
        try:
            if cantidad_huespedes is None:
                return False, 0, "Cantidad de huéspedes es requerida"
            
            # Convertir a entero
            try:
                cantidad = int(cantidad_huespedes)
            except (ValueError, TypeError):
                return False, 0, f"Cantidad de huéspedes inválida: {cantidad_huespedes}"
            
            # Validar rango
            if cantidad < 1:
                return False, 0, "Debe haber al menos 1 huésped"
            
            if cantidad > 10:  # Límite máximo razonable
                return False, 0, f"Cantidad máxima de huéspedes es 10 (solicitado: {cantidad})"
            
            logger.info(f"Cantidad de huéspedes validada: {cantidad}", 
                       extra={"component": "validation_service", "guest_count": cantidad})
            
            return True, cantidad, ""
            
        except Exception as e:
            error_msg = f"Error validando cantidad de huéspedes: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, 0, error_msg
    
    def validate_domo_selection(self, domo: str) -> Tuple[bool, str, str]:
        """
        Valida selección de domo
        
        Args:
            domo: Nombre del domo seleccionado
            
        Returns:
            Tuple[bool, str, str]: (valid, domo_normalizado, mensaje_error)
        """
        try:
            if not domo or not domo.strip():
                return False, "", "Selección de domo es requerida"
            
            domo_clean = domo.strip().lower()
            
            # Domos válidos
            domos_validos = {
                'antares': 'Antares',
                'polaris': 'Polaris', 
                'sirius': 'Sirius',
                'centaury': 'Centaury',
                'centauro': 'Centaury'  # Alias
            }
            
            if domo_clean in domos_validos:
                domo_normalizado = domos_validos[domo_clean]
                logger.info(f"Domo validado: {domo} -> {domo_normalizado}", 
                           extra={"component": "validation_service", "domo": domo_normalizado})
                return True, domo_normalizado, ""
            else:
                domos_disponibles = ", ".join(set(domos_validos.values()))
                return False, "", f"Domo '{domo}' no válido. Domos disponibles: {domos_disponibles}"
            
        except Exception as e:
            error_msg = f"Error validando selección de domo: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, "", error_msg
    
    def validate_payment_method(self, metodo_pago: str) -> Tuple[bool, str, str]:
        """
        Valida método de pago
        
        Args:
            metodo_pago: Método de pago seleccionado
            
        Returns:
            Tuple[bool, str, str]: (valid, metodo_normalizado, mensaje_error)
        """
        try:
            if not metodo_pago or not metodo_pago.strip():
                return False, "", "Método de pago es requerido"
            
            metodo_clean = metodo_pago.strip().lower()
            
            # Métodos válidos
            metodos_validos = {
                'efectivo': 'Efectivo',
                'tarjeta': 'Tarjeta',
                'tarjeta de credito': 'Tarjeta',
                'tarjeta de débito': 'Tarjeta',
                'transferencia': 'Transferencia',
                'nequi': 'Nequi',
                'daviplata': 'Daviplata'
            }
            
            if metodo_clean in metodos_validos:
                metodo_normalizado = metodos_validos[metodo_clean]
                logger.info(f"Método de pago validado: {metodo_pago} -> {metodo_normalizado}", 
                           extra={"component": "validation_service", "payment_method": metodo_normalizado})
                return True, metodo_normalizado, ""
            else:
                metodos_disponibles = ", ".join(set(metodos_validos.values()))
                return False, "", f"Método de pago '{metodo_pago}' no válido. Métodos disponibles: {metodos_disponibles}"
            
        except Exception as e:
            error_msg = f"Error validando método de pago: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, "", error_msg
    
    def parse_llm_json_safe(self, llm_response: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Parsea respuesta JSON del LLM de forma segura (extraído de agente.py líneas 1906-1948)
        
        Args:
            llm_response: Respuesta del LLM
            
        Returns:
            Tuple[bool, Dict, str]: (success, datos_parseados, mensaje_error)
        """
        try:
            if not llm_response or not llm_response.strip():
                return False, {}, "Respuesta LLM vacía"
            
            # Limpiar respuesta
            response_clean = llm_response.strip()
            
            # Buscar JSON entre marcadores comunes
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```',
                r'(\{.*?\})'
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, response_clean, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    try:
                        parsed_data = json.loads(json_str)
                        logger.info("JSON parseado exitosamente desde respuesta LLM", 
                                   extra={"component": "validation_service", "json_keys": list(parsed_data.keys())})
                        return True, parsed_data, ""
                    except json.JSONDecodeError:
                        continue
            
            # Intentar parsear directamente
            try:
                parsed_data = json.loads(response_clean)
                logger.info("JSON parseado directamente desde respuesta LLM", 
                           extra={"component": "validation_service", "json_keys": list(parsed_data.keys())})
                return True, parsed_data, ""
            except json.JSONDecodeError as e:
                error_msg = f"No se pudo parsear JSON de respuesta LLM: {e}"
                logger.error(error_msg, extra={"component": "validation_service", "response": response_clean[:200]})
                return False, {}, error_msg
            
        except Exception as e:
            error_msg = f"Error parseando respuesta LLM: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, {}, error_msg
    
    def validate_campos_importantes_reserva(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida campos importantes de una reserva (extraído de agente.py líneas 425-484)
        
        Args:
            data: Datos de la reserva
            
        Returns:
            Tuple[bool, List[str]]: (valid, lista_errores)
        """
        try:
            errors = []
            
            # Campos requeridos con sus validaciones
            required_fields = {
                'numero_whatsapp': 'Teléfono',
                'email_contacto': 'Email', 
                'cantidad_huespedes': 'Cantidad de huéspedes',
                'domo': 'Domo',
                'fecha_entrada': 'Fecha de entrada',
                'fecha_salida': 'Fecha de salida',
                'metodo_pago': 'Método de pago'
            }
            
            # Verificar campos requeridos
            for field, display_name in required_fields.items():
                if field not in data or not data[field]:
                    errors.append(f"{display_name} es requerido")
            
            # Validaciones específicas si los campos están presentes
            if 'numero_whatsapp' in data and data['numero_whatsapp']:
                _, _, _, phone_errors = self.validate_contact_info(str(data['numero_whatsapp']), "temp@example.com")
                if phone_errors and phone_errors[0] != "Email es requerido":
                    errors.extend([err for err in phone_errors if "Email" not in err])
            
            if 'email_contacto' in data and data['email_contacto']:
                _, _, _, email_errors = self.validate_contact_info("1234567890", str(data['email_contacto']))
                if email_errors and email_errors[0] != "Número de teléfono es requerido":
                    errors.extend([err for err in email_errors if "teléfono" not in err])
            
            if 'cantidad_huespedes' in data and data['cantidad_huespedes']:
                valid_guests, _, guest_error = self.validate_guest_count(data['cantidad_huespedes'])
                if not valid_guests:
                    errors.append(guest_error)
            
            if 'domo' in data and data['domo']:
                valid_domo, _, domo_error = self.validate_domo_selection(str(data['domo']))
                if not valid_domo:
                    errors.append(domo_error)
            
            if 'metodo_pago' in data and data['metodo_pago']:
                valid_payment, _, payment_error = self.validate_payment_method(str(data['metodo_pago']))
                if not valid_payment:
                    errors.append(payment_error)
            
            # Validar fechas si ambas están presentes
            if all(field in data and data[field] for field in ['fecha_entrada', 'fecha_salida']):
                try:
                    if isinstance(data['fecha_entrada'], str):
                        valid_entrada, fecha_entrada, _ = self.parse_flexible_date(data['fecha_entrada'])
                    else:
                        fecha_entrada = data['fecha_entrada']
                        valid_entrada = True
                    
                    if isinstance(data['fecha_salida'], str):
                        valid_salida, fecha_salida, _ = self.parse_flexible_date(data['fecha_salida'])
                    else:
                        fecha_salida = data['fecha_salida']
                        valid_salida = True
                    
                    if valid_entrada and valid_salida:
                        valid_range, range_error = self.validate_date_range(fecha_entrada, fecha_salida)
                        if not valid_range:
                            errors.append(range_error)
                except Exception as e:
                    errors.append(f"Error validando fechas: {e}")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("Campos importantes de reserva validados exitosamente", 
                           extra={"component": "validation_service", "fields_count": len(required_fields)})
            else:
                logger.warning(f"Errores en validación de reserva: {errors}", 
                              extra={"component": "validation_service", "errors": errors})
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"Error validando campos importantes de reserva: {e}"
            logger.error(error_msg, extra={"component": "validation_service"})
            return False, [error_msg]
    
    def detect_informacion_general_suboption(self, message: str) -> Tuple[bool, str, str]:
        """
        Detecta sub-opciones de información general
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[bool, str, str]: (detected, suboption, message_description)
        """
        try:
            message_clean = message.lower().strip()
            
            # Patrones para ubicación
            ubicacion_patterns = [
                'ubicacion', 'ubicación', 'donde', 'dónde', 'lugar', 'dirección', 'direccion',
                'como llegar', 'cómo llegar', 'address', 'localización', 'localizacion',
                'coordenadas', 'maps', 'mapa'
            ]
            
            # Patrones para concepto
            concepto_patterns = [
                'concepto', 'filosofia', 'filosofía', 'que es', 'qué es', 'sobre el glamping',
                'historia', 'mision', 'misión', 'vision', 'visión', 'web', 'website',
                'pagina', 'página', 'sitio web', 'link', 'enlace', 'url'
            ]
            
            # Patrones para políticas
            politicas_patterns = [
                'politicas', 'políticas', 'normas', 'reglas', 'policy', 'policies',
                'términos', 'terminos', 'condiciones', 'regulaciones'
            ]
            
            # Detectar ubicación
            if any(pattern in message_clean for pattern in ubicacion_patterns):
                logger.info("Sub-opción detectada: ubicación", 
                           extra={"component": "validation_service", "suboption": "ubicacion"})
                return True, "ubicacion", "Información sobre ubicación y cómo llegar"
            
            # Detectar concepto
            elif any(pattern in message_clean for pattern in concepto_patterns):
                logger.info("Sub-opción detectada: concepto", 
                           extra={"component": "validation_service", "suboption": "concepto"})
                return True, "concepto", "Concepto y filosofía del glamping"
            
            # Detectar políticas
            elif any(pattern in message_clean for pattern in politicas_patterns):
                logger.info("Sub-opción detectada: políticas", 
                           extra={"component": "validation_service", "suboption": "politicas"})
                return True, "politicas", "Políticas y normas del glamping"
            
            return False, "", ""
            
        except Exception as e:
            logger.error(f"Error detectando sub-opción información general: {e}", 
                        extra={"component": "validation_service"})
            return False, "", ""
    
    def detect_politicas_suboption(self, message: str) -> Tuple[bool, str, str]:
        """
        Detecta sub-opciones específicas de políticas
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[bool, str, str]: (detected, suboption, message_description)
        """
        try:
            message_clean = message.lower().strip()
            
            # Patrones para reservas y cancelaciones (detectar primero para evitar conflictos)
            reservas_patterns = [
                'reservas', 'cancelacion', 'cancelación', 'cancelar', 'devolucion',
                'devolución', 'reembolso', 'modificar', 'cambios', 'cambio',
                'política de reservas', 'politica de reservas'
            ]
            
            # Patrones para políticas de mascotas
            mascotas_patterns = [
                'mascotas', 'perros', 'gatos', 'animales', 'pets', 'mascota',
                'perro', 'gato', 'animal', 'felino'
            ]
            
            # Patrones para políticas de privacidad
            privacidad_patterns = [
                'privacidad', 'datos', 'informacion personal', 'información personal',
                'datos personales', 'privacy', 'proteccion datos', 'protección datos',
                'gdpr', 'confidencialidad'
            ]
            
            # Detectar políticas de reservas PRIMERO
            if any(pattern in message_clean for pattern in reservas_patterns):
                logger.info("Sub-opción de políticas detectada: reservas", 
                           extra={"component": "validation_service", "politicas_suboption": "reservas"})
                return True, "reservas", "Políticas de reservas y cancelaciones"
            
            # Detectar políticas de mascotas
            elif any(pattern in message_clean for pattern in mascotas_patterns):
                logger.info("Sub-opción de políticas detectada: mascotas", 
                           extra={"component": "validation_service", "politicas_suboption": "mascotas"})
                return True, "mascotas", "Políticas sobre mascotas y animales"
            
            # Detectar políticas de privacidad
            elif any(pattern in message_clean for pattern in privacidad_patterns):
                logger.info("Sub-opción de políticas detectada: privacidad", 
                           extra={"component": "validation_service", "politicas_suboption": "privacidad"})
                return True, "privacidad", "Políticas de privacidad y protección de datos"
            
            return False, "", ""
            
        except Exception as e:
            logger.error(f"Error detectando sub-opción de políticas: {e}", 
                        extra={"component": "validation_service"})
            return False, "", ""
    
    def is_specific_query(self, message: str, context: str) -> bool:
        """Detecta si es consulta específica que requiere agente IA"""
        specific_patterns = [
            r'más información.*domo.*polaris',
            r'detalles.*domo.*antares',
            r'características.*sirius',
            r'cuéntame.*sobre.*centaury'
        ]
        return any(re.search(pattern, message.lower()) for pattern in specific_patterns)

    def detect_auto_ai_activation(self, message: str) -> Tuple[bool, str, str]:
        """
        Detecta si debe activar automáticamente el agente IA

        Args:
            message: Mensaje del usuario

        Returns:
            Tuple[bool, str, str]: (should_activate, trigger_type, rag_context)
        """
        try:
            # Usar domain validation y topic detection en lugar de intelligent_trigger_service
            from services.domain_validation_service import get_domain_validation_service
            from services.topic_detection_service import get_topic_detection_service
            
            domain_service = get_domain_validation_service()
            topic_service = get_topic_detection_service()
            
            # Primero validar que esté en dominio
            is_valid, reason, redirect = domain_service.validate_domain(message)
            
            if not is_valid:
                return False, "out_of_domain", reason
            
            # Luego detectar si necesita redirección inteligente
            needs_redirect, topic, connection, response = topic_service.detect_topic_and_redirect(message)
            
            if needs_redirect:
                return True, "topic_redirect", topic
            
            # Analizar complejidad para determinar si necesita agente IA
            analysis = domain_service.analyze_query_complexity(message)
            
            if analysis.get("needs_ai_agent", False):
                return True, "complex_query", "glamping_related"
            
            return False, "simple_query", ""

        except Exception as e:
            logger.error(f"Error en detección auto-activación IA: {e}")
            return False, "error", str(e)


# Instancia global del servicio
validation_service = ValidationService()

def get_validation_service() -> ValidationService:
    """Obtener instancia global del servicio de validación"""
    return validation_service