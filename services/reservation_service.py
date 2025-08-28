# Servicio centralizado de reservas
# Extrae procesamiento de reservas y cálculo de precios de agente.py

import json
import re
import os
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import get_logger
from services.validation_service import ValidationService

logger = get_logger(__name__)

class ReservationService:
    """
    Servicio centralizado para procesamiento de reservas
    Consolida parsing, validación y cálculo de precios
    """
    
    def __init__(self, db=None, Reserva=None):
        """
        Inicializar servicio de reservas
        
        Args:
            db: Instancia de base de datos
            Reserva: Modelo de Reserva
        """
        self.db = db
        self.Reserva = Reserva
        self.validation_service = ValidationService()
        self.fallback_mode = (db is None or Reserva is None)
        
        if self.fallback_mode:
            logger.warning("⚠️ ReservationService iniciado en MODO FALLBACK (sin base de datos)")
            # Lista temporal para guardar reservas en memoria
            self.temp_reservations = []
        
        logger.info("ReservationService inicializado", 
                   extra={"component": "reservation_service", "phase": "startup", "fallback_mode": self.fallback_mode})
    
    def _save_reservation_fallback(self, reservation_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Guardar reserva en modo fallback (sin base de datos)
        Guarda en memoria y archivo temporal
        """
        try:
            # Agregar timestamp y ID único
            reservation_data['timestamp'] = datetime.now().isoformat()
            reservation_data['fallback_id'] = len(self.temp_reservations) + 1
            
            # Guardar en memoria
            self.temp_reservations.append(reservation_data)
            
            # Guardar en archivo temporal
            fallback_file = "/tmp/reservas_fallback.json"
            try:
                # Cargar reservas existentes o crear lista vacía
                if os.path.exists(fallback_file):
                    with open(fallback_file, 'r', encoding='utf-8') as f:
                        existing_reservations = json.load(f)
                else:
                    existing_reservations = []
                
                # Agregar nueva reserva
                existing_reservations.append(reservation_data)
                
                # Guardar de vuelta
                with open(fallback_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_reservations, f, ensure_ascii=False, indent=2, default=str)
                
                logger.warning(f"⚠️ Reserva guardada en modo FALLBACK - archivo: {fallback_file}")
                
            except Exception as file_error:
                logger.error(f"Error guardando archivo fallback: {file_error}")
                # No fallar si no se puede guardar el archivo, al menos está en memoria
            
            # Log de la reserva para monitoreo
            logger.info(f"✅ Reserva FALLBACK guardada - ID: {reservation_data['fallback_id']}, "
                       f"Huésped: {reservation_data.get('email_contacto', 'N/A')}, "
                       f"Domo: {reservation_data.get('domo', 'N/A')}, "
                       f"Fechas: {reservation_data.get('fecha_entrada')} - {reservation_data.get('fecha_salida')}")
            
            return True, f"Reserva guardada exitosamente (ID fallback: {reservation_data['fallback_id']})", reservation_data['fallback_id']
            
        except Exception as e:
            logger.error(f"Error en guardado fallback: {e}")
            return False, f"Error guardando reserva en modo fallback: {str(e)}", None
    
    def calcular_precio_reserva(self, domo: str, cantidad_huespedes: int, 
                               fecha_entrada: date, fecha_salida: date, 
                               servicios_adicionales: Optional[List[str]] = None) -> Tuple[bool, float, str]:
        """
        Calcula precio de reserva (extraído de agente.py líneas 487-577)
        
        Args:
            domo: Nombre del domo
            cantidad_huespedes: Cantidad de huéspedes
            fecha_entrada: Fecha de entrada
            fecha_salida: Fecha de salida
            servicios_adicionales: Lista de servicios adicionales
            
        Returns:
            Tuple[bool, float, str]: (success, precio_total, mensaje)
        """
        try:
            logger.info(f"Calculando precio para reserva: {domo}, {cantidad_huespedes} huéspedes", 
                       extra={"component": "reservation_service", "domo": domo, "guests": cantidad_huespedes})
            
            # Validar inputs
            if not all([domo, cantidad_huespedes, fecha_entrada, fecha_salida]):
                return False, 0.0, "Datos incompletos para cálculo de precio"
            
            # Validar domo
            success_domo, domo_clean, error_domo = self.validation_service.validate_domo_selection(domo)
            if not success_domo:
                return False, 0.0, error_domo
            
            # Validar cantidad de huéspedes
            success_guests, guests_clean, error_guests = self.validation_service.validate_guest_count(cantidad_huespedes)
            if not success_guests:
                return False, 0.0, error_guests
            
            # Validar fechas
            success_dates, error_dates = self.validation_service.validate_date_range(fecha_entrada, fecha_salida)
            if not success_dates:
                return False, 0.0, error_dates
            
            # Precios base por domo (por noche)
            precios_base = {
                'Antares': 650000,    # Domo premium
                'Polaris': 550000,    # Domo estándar premium  
                'Sirius': 450000,     # Domo estándar
                'Centaury': 450000    # Domo estándar
            }
            
            precio_base_noche = precios_base.get(domo_clean, 450000)
            
            # Calcular número de noches
            noches = (fecha_salida - fecha_entrada).days
            
            # Precio base total
            precio_base_total = precio_base_noche * noches
            
            # Ajuste por cantidad de huéspedes
            precio_ajustado = precio_base_total
            if guests_clean > 2:
                # Cargo adicional por huésped extra
                huespedes_extra = guests_clean - 2
                cargo_extra_por_huesped = 50000  # Por noche por huésped extra
                precio_ajustado += (cargo_extra_por_huesped * huespedes_extra * noches)
            
            # Servicios adicionales
            precio_servicios = 0.0
            if servicios_adicionales:
                precios_servicios = {
                    'Cena romántica': 180000,
                    'Masaje relajante': 150000,
                    'Paseo a caballo': 80000,
                    'Navegación en lancha': 100000,
                    'Jet ski': 120000,
                    'Avistamiento de aves': 60000,
                    'Senderismo guiado': 40000,
                    'Fogata nocturna': 30000
                }
                
                for servicio in servicios_adicionales:
                    precio_servicios += precios_servicios.get(servicio, 0)
            
            # Precio final
            precio_total = precio_ajustado + precio_servicios
            
            # Aplicar descuentos por estadía prolongada
            if noches >= 7:
                descuento = 0.10  # 10% descuento por semana
                precio_total *= (1 - descuento)
                mensaje_descuento = " (10% descuento por estadía de 7+ noches)"
            elif noches >= 4:
                descuento = 0.05  # 5% descuento por 4+ noches
                precio_total *= (1 - descuento)
                mensaje_descuento = " (5% descuento por estadía de 4+ noches)"
            else:
                mensaje_descuento = ""
            
            mensaje = (
                f"Precio calculado para {domo_clean}: {noches} noches, {guests_clean} huéspedes. "
                f"Precio base: ${precio_base_total:,.0f}, "
                f"Servicios: ${precio_servicios:,.0f}, "
                f"Total: ${precio_total:,.0f}{mensaje_descuento}"
            )
            
            logger.info(f"Precio calculado exitosamente: ${precio_total:,.0f}", 
                       extra={"component": "reservation_service", "precio": precio_total, "noches": noches})
            
            return True, precio_total, mensaje
            
        except Exception as e:
            error_msg = f"Error calculando precio de reserva: {e}"
            logger.error(error_msg, extra={"component": "reservation_service"})
            return False, 0.0, error_msg
    
    def parse_reservation_details(self, user_input: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Parsea detalles de reserva desde input del usuario (extraído de agente.py líneas 1654-1770)
        
        Args:
            user_input: Input del usuario con detalles de reserva
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, parsed_data, error_message)
        """
        try:
            logger.info("Parseando detalles de reserva", 
                       extra={"component": "reservation_service", "input_length": len(user_input)})
            
            if not user_input or not user_input.strip():
                return False, {}, "Input vacío"
            
            # Inicializar datos parseados
            parsed_data = {
                'nombres_huespedes': '',
                'numero_whatsapp': '',
                'email_contacto': '',
                'cantidad_huespedes': 0,
                'domo': '',
                'fecha_entrada': None,
                'fecha_salida': None,
                'metodo_pago': '',
                'servicios_adicionales': [],
                'comentarios_especiales': '',
                'numero_contacto': ''
            }
            
            # Patrones de extracción
            patterns = {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'telefono': r'(?:\+57\s?)?(?:3\d{2}|\d{3})\s?\d{3}\s?\d{4}',
                # Improved date pattern to catch more formats
                'fecha': r'\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}|\d{1,2}\s+de\s+\w+\s+de?\s+\d{4})\b',
                # More flexible number pattern with accent and encoding handling
                'numero': r'\b(?:cantidad|personas|hu[eéè�]spedes?|huespedes?|guests?|para)[:\s]*(\d+)\b|\b(\d+)\s+(?:personas?|hu[eéè�]spedes?|huespedes?|guests?)\b',
                'domo': r'\b(antares|polaris|sirius|centaury|centauro)\b',
                'pago': r'\b(efectivo|tarjeta|transferencia|nequi|daviplata)\b'
            }
            
            text_lower = user_input.lower()
            
            # Extraer email
            email_match = re.search(patterns['email'], user_input, re.IGNORECASE)
            if email_match:
                parsed_data['email_contacto'] = email_match.group().strip()
            
            # Extraer teléfono
            phone_match = re.search(patterns['telefono'], user_input)
            if phone_match:
                phone = re.sub(r'[^\d\+]', '', phone_match.group())
                parsed_data['numero_whatsapp'] = phone
                parsed_data['numero_contacto'] = phone
            
            # Extraer fechas
            date_matches = re.findall(patterns['fecha'], user_input)
            if len(date_matches) >= 2:
                # Parsear fechas - usar parsing simple sin validación de futuro
                for i, date_str in enumerate(date_matches[:2]):
                    try:
                        # Intentar diferentes formatos de fecha
                        from datetime import datetime
                        date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d']
                        
                        parsed_date = None
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if parsed_date:
                            if i == 0:
                                parsed_data['fecha_entrada'] = parsed_date
                            else:
                                parsed_data['fecha_salida'] = parsed_date
                    except Exception:
                        continue
            
            # Extraer cantidad de huéspedes - improved logic for flexible pattern
            numero_match = re.search(patterns['numero'], text_lower)
            if numero_match:
                try:
                    # Try both capture groups since the pattern has alternatives
                    number = numero_match.group(1) if numero_match.group(1) else numero_match.group(2)
                    if number:
                        parsed_data['cantidad_huespedes'] = int(number)
                except (ValueError, IndexError):
                    pass
            
            # Extraer domo
            domo_match = re.search(patterns['domo'], text_lower)
            if domo_match:
                domo_raw = domo_match.group().strip()
                success, domo_clean, _ = self.validation_service.validate_domo_selection(domo_raw)
                if success:
                    parsed_data['domo'] = domo_clean
            
            # Extraer método de pago
            pago_match = re.search(patterns['pago'], text_lower)
            if pago_match:
                pago_raw = pago_match.group().strip()
                success, pago_clean, _ = self.validation_service.validate_payment_method(pago_raw)
                if success:
                    parsed_data['metodo_pago'] = pago_clean
            
            # Extraer nombres (todo lo que no sea email, teléfono, fecha o números)
            text_for_names = user_input
            # Remover patrones conocidos
            for pattern in [patterns['email'], patterns['telefono'], patterns['fecha']]:
                text_for_names = re.sub(pattern, '', text_for_names, flags=re.IGNORECASE)
            
            # Extraer posibles nombres (palabras que empiecen con mayúscula)
            nombres_matches = re.findall(r'\b[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)*\b', text_for_names)
            if nombres_matches:
                parsed_data['nombres_huespedes'] = ', '.join(nombres_matches[:3])  # Máximo 3 nombres
            
            # Verificar si se parsearon datos suficientes para una reserva válida
            # Necesitamos al menos los campos críticos para proceder
            critical_fields = ['email_contacto', 'numero_whatsapp', 'cantidad_huespedes', 'domo']
            optional_critical_fields = ['fecha_entrada', 'fecha_salida', 'metodo_pago']
            
            # Contar campos críticos presentes
            critical_present = sum(1 for field in critical_fields if parsed_data.get(field))
            optional_present = sum(1 for field in optional_critical_fields if parsed_data.get(field))
            
            # Necesitamos al menos 3 campos críticos + 1 opcional para considerar éxito
            total_required = critical_present + optional_present
            
            if critical_present < 3 or total_required < 4:
                missing_fields = [field for field in critical_fields if not parsed_data.get(field)]
                missing_optional = [field for field in optional_critical_fields if not parsed_data.get(field)]
                return False, parsed_data, f"Información insuficiente: faltan {missing_fields + missing_optional[:2]}"
            
            logger.info(f"Detalles parseados exitosamente: {total_required} campos importantes", 
                       extra={"component": "reservation_service", "parsed_fields": total_required})
            
            return True, parsed_data, f"Parseados {total_required} campos importantes"
            
        except Exception as e:
            error_msg = f"Error parseando detalles de reserva: {e}"
            logger.error(error_msg, extra={"component": "reservation_service"})
            return False, {}, error_msg
    
    def validate_and_process_reservation_data(self, parsed_data: Dict[str, Any], 
                                            from_number: str) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Valida y procesa datos de reserva (extraído de agente.py líneas 1771-1860)
        
        Args:
            parsed_data: Datos parseados de la reserva
            from_number: Número de origen
            
        Returns:
            Tuple[bool, Dict[str, Any], List[str]]: (success, processed_data, errores)
        """
        try:
            logger.info("Validando y procesando datos de reserva", 
                       extra={"component": "reservation_service"})
            
            processed_data = parsed_data.copy()
            errors = []
            
            # Usar número de WhatsApp como fallback para teléfono
            if not processed_data.get('numero_whatsapp') and from_number:
                phone = from_number.replace("whatsapp:", "") if from_number else ""
                processed_data['numero_whatsapp'] = phone
                processed_data['numero_contacto'] = phone
            
            # Validar campos importantes usando el servicio de validación
            validation_success, validation_errors = self.validation_service.validate_campos_importantes_reserva(processed_data)
            
            if not validation_success:
                errors.extend(validation_errors)
                logger.warning(f"Errores de validación: {validation_errors}", 
                              extra={"component": "reservation_service", "errors": validation_errors})
                return False, processed_data, errors
            
            # Calcular precio si hay datos suficientes
            if all(processed_data.get(field) for field in ['domo', 'cantidad_huespedes', 'fecha_entrada', 'fecha_salida']):
                precio_success, precio_total, precio_msg = self.calcular_precio_reserva(
                    domo=processed_data['domo'],
                    cantidad_huespedes=processed_data['cantidad_huespedes'],
                    fecha_entrada=processed_data['fecha_entrada'],
                    fecha_salida=processed_data['fecha_salida'],
                    servicios_adicionales=processed_data.get('servicios_adicionales', [])
                )
                
                if precio_success:
                    processed_data['monto_total'] = precio_total
                    processed_data['precio_detalle'] = precio_msg
                else:
                    errors.append(f"Error calculando precio: {precio_msg}")
            
            # Agregar timestamp
            processed_data['fecha_creacion'] = datetime.utcnow()
            
            logger.info("Datos de reserva validados y procesados exitosamente", 
                       extra={"component": "reservation_service", "has_price": 'monto_total' in processed_data})
            
            return True, processed_data, errors
            
        except Exception as e:
            error_msg = f"Error validando y procesando datos de reserva: {e}"
            logger.error(error_msg, extra={"component": "reservation_service"})
            return False, parsed_data, [error_msg]
    
    def save_reservation_to_pinecone(self, user_phone_number: str, reservation_data: Dict[str, Any]) -> bool:
        """
        Stub para compatibilidad - Pinecone no se usa en este sistema
        
        Args:
            user_phone_number: Número de teléfono del usuario
            reservation_data: Datos de la reserva
            
        Returns:
            bool: Always True for compatibility
        """
        # Stub function - Pinecone functionality removed
        # All reservation data is stored in PostgreSQL
        return True
    
    def create_reservation_summary(self, reservation_data: Dict[str, Any]) -> str:
        """
        Crea resumen de reserva para el usuario
        
        Args:
            reservation_data: Datos de la reserva
            
        Returns:
            str: Resumen formateado
        """
        try:
            summary = "📋 **RESUMEN DE RESERVA**\n\n"
            
            if reservation_data.get('nombres_huespedes'):
                summary += f"👤 **Huéspedes:** {reservation_data['nombres_huespedes']}\n"
            
            if reservation_data.get('domo'):
                summary += f"🏠 **Domo:** {reservation_data['domo']}\n"
            
            if reservation_data.get('cantidad_huespedes'):
                summary += f"👥 **Cantidad:** {reservation_data['cantidad_huespedes']} personas\n"
            
            if reservation_data.get('fecha_entrada') and reservation_data.get('fecha_salida'):
                entrada = reservation_data['fecha_entrada']
                salida = reservation_data['fecha_salida']
                noches = (salida - entrada).days
                summary += f"📅 **Fechas:** {entrada} al {salida} ({noches} noches)\n"
            
            if reservation_data.get('metodo_pago'):
                summary += f"💳 **Pago:** {reservation_data['metodo_pago']}\n"
            
            if reservation_data.get('monto_total'):
                summary += f"💰 **Total:** ${reservation_data['monto_total']:,.0f} COP\n"
            
            if reservation_data.get('email_contacto'):
                summary += f"📧 **Email:** {reservation_data['email_contacto']}\n"
            
            if reservation_data.get('numero_contacto'):
                summary += f"📞 **Contacto:** {reservation_data['numero_contacto']}\n"
            
            summary += "\n✅ Reserva procesada exitosamente"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creando resumen de reserva: {e}", 
                        extra={"component": "reservation_service"})
            return "Error generando resumen de reserva"

    def save_reservation_atomic(self, reservation_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Guardar reserva de forma atómica con validaciones"""
        
        # MODO FALLBACK - Si no hay BD, guardar en memoria y archivo
        if self.fallback_mode:
            return self._save_reservation_fallback(reservation_data)
        
        try:
            with self.db.session.begin():  # Transacción automática
                # 1. Validar datos antes de guardar
                valid, errors = self.validation_service.validate_campos_importantes_reserva(reservation_data)
                if not valid:
                    raise ValueError(f"Datos de reserva inválidos: {errors}")

                # 2. Verificar disponibilidad (con lock para evitar race conditions)
                availability_check = self.db.session.execute(
                    """SELECT id FROM reservas
                       WHERE domo = :domo
                       AND fecha_entrada < :fecha_salida
                       AND fecha_salida > :fecha_entrada
                       FOR UPDATE""",
                    {
                        'domo': reservation_data['domo'],
                        'fecha_entrada': reservation_data['fecha_entrada'],
                        'fecha_salida': reservation_data['fecha_salida']
                    }
                ).fetchall()

                if availability_check:
                    raise ValueError("Domo no disponible para las fechas seleccionadas")

                # 3. Crear reserva
                nueva_reserva = self.Reserva(
                    numero_whatsapp=reservation_data['numero_whatsapp'],
                    email_contacto=reservation_data['email_contacto'],
                    cantidad_huespedes=reservation_data['cantidad_huespedes'],
                    nombres_huespedes=json.dumps(reservation_data.get('nombres_huespedes', [])),
                    domo=reservation_data['domo'],
                    fecha_entrada=reservation_data['fecha_entrada'],
                    fecha_salida=reservation_data['fecha_salida'],
                    precio_total=reservation_data.get('precio_total', 0.0),
                    metodo_pago=reservation_data['metodo_pago'],
                    estado='confirmada',
                    fecha_creacion=datetime.utcnow()
                )

                self.db.session.add(nueva_reserva)
                self.db.session.flush()  # Obtener ID sin commit

                logger.info(f"Reserva guardada atómicamente: ID {nueva_reserva.id}")
                return True, f"Reserva confirmada con ID {nueva_reserva.id}", nueva_reserva.id

        except ValueError as ve:
            logger.warning(f"Error de validación en reserva: {ve}")
            return False, str(ve), None
        except Exception as e:
            logger.error(f"Error guardando reserva: {e}")
            return False, "Error interno procesando reserva", None
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud del servicio de reservas
        
        Returns:
            Dict[str, Any]: Estado de salud
        """
        try:
            return {
                'service_name': 'ReservationService',
                'status': 'healthy',
                'database_available': self.db is not None,
                'model_available': self.Reserva is not None,
                'validation_service_available': self.validation_service is not None,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'service_name': 'ReservationService',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


def get_reservation_service(db=None, Reserva=None) -> ReservationService:
    """
    Factory function para crear instancia de ReservationService
    
    Args:
        db: Instancia de base de datos
        Reserva: Modelo de Reserva
        
    Returns:
        ReservationService: Instancia del servicio
    """
    return ReservationService(db, Reserva)