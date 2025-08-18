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
                    logger.info(f"Fecha relativa parseada: {phrase} → {target_date}", 
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
                logger.info(f"Domo validado: {domo} → {domo_normalizado}", 
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
                logger.info(f"Método de pago validado: {metodo_pago} → {metodo_normalizado}", 
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


# Instancia global del servicio
validation_service = ValidationService()

def get_validation_service() -> ValidationService:
    """Obtener instancia global del servicio de validación"""
    return validation_service