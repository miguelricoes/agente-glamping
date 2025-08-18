# Validation utilities - Centralized validation logic extracted from agente.py
# Contains functions for validating guest names, dates, contact info, and reservation data

import re
from datetime import datetime, date
from typing import Tuple, List, Dict, Any

def validate_guest_names(names_data) -> Tuple[bool, List[str], str]:
    """Validates and normalizes guest names"""
    try:
        if not names_data:
            return False, [], "No se proporcionaron nombres de huéspedes"
        
        # Convert to list if string
        if isinstance(names_data, str):
            # Split by commas, "y", "&" or line breaks
            names_data = re.split(r'[,&\n]|\s+y\s+', names_data)
        
        if not isinstance(names_data, list):
            return False, [], "Formato de nombres inválido"
        
        validated_names = []
        for name in names_data:
            if not name or not isinstance(name, str):
                continue
                
            # Clean and normalize name
            clean_name = re.sub(r'[^\w\sáéíóúñü.-]', '', name.strip(), flags=re.IGNORECASE)
            clean_name = ' '.join(clean_name.split())  # Normalize spaces
            
            # Validate length and format
            if len(clean_name) < 2:
                continue
            if len(clean_name) > 100:
                clean_name = clean_name[:100]
            
            # Verify it has at least one letter
            if not re.search(r'[a-záéíóúñü]', clean_name, re.IGNORECASE):
                continue
                
            # Capitalize correctly
            clean_name = ' '.join(word.capitalize() for word in clean_name.split())
            validated_names.append(clean_name)
        
        if not validated_names:
            return False, [], "No se encontraron nombres válidos"
        
        # Limit to maximum 10 guests
        if len(validated_names) > 10:
            validated_names = validated_names[:10]
            return True, validated_names, f"Se limitó a 10 huéspedes (máximo permitido)"
        
        return True, validated_names, f"OK: {len(validated_names)} nombre(s) validado(s)"
        
    except Exception as e:
        return False, [], f"Error al validar nombres: {str(e)}"

def parse_flexible_date(date_str: str) -> Tuple[bool, date, str]:
    """Flexible date parsing that accepts multiple formats"""
    if not date_str or not isinstance(date_str, str):
        return False, None, "Fecha no proporcionada"
    
    # Clean the date string
    date_str = date_str.strip().replace('/', '-').replace('.', '-')
    
    # Patterns to try (prioritizing DD/MM/YYYY format for Spanish)
    patterns = [
        "%d-%m-%Y",    # DD/MM/YYYY
        "%d-%m-%y",    # DD/MM/YY
        "%Y-%m-%d",    # YYYY-MM-DD
        "%m-%d-%Y",    # MM/DD/YYYY
        "%d de %B de %Y",  # DD de Month de YYYY (Spanish)
        "%d de %b de %Y",  # DD de Mon de YYYY (Spanish)
        "%B %d, %Y",   # Month DD, YYYY (English)
        "%d %B %Y",    # DD Month YYYY
        "%d-%B-%Y",    # DD-Month-YYYY
    ]
    
    # Spanish month names mapping
    spanish_months = {
        'enero': 'January', 'febrero': 'February', 'marzo': 'March',
        'abril': 'April', 'mayo': 'May', 'junio': 'June',
        'julio': 'July', 'agosto': 'August', 'septiembre': 'September',
        'octubre': 'October', 'noviembre': 'November', 'diciembre': 'December'
    }
    
    # Replace Spanish month names with English for parsing
    date_str_en = date_str.lower()
    for es_month, en_month in spanish_months.items():
        date_str_en = date_str_en.replace(es_month, en_month)
    
    for pattern in patterns:
        try:
            parsed_date = datetime.strptime(date_str_en, pattern.lower()).date()
            
            # Validate that the date is reasonable (not too far in the past or future)
            today = date.today()
            if parsed_date < today:
                return False, None, f"La fecha {date_str} está en el pasado"
            if parsed_date.year > today.year + 5:
                return False, None, f"La fecha {date_str} está muy lejos en el futuro"
            
            return True, parsed_date, f"OK: Fecha parseada como {parsed_date.strftime('%d/%m/%Y')}"
            
        except ValueError:
            continue
    
    return False, None, f"No se pudo interpretar la fecha: {date_str}. Use formato DD/MM/YYYY"

def validate_date_range(fecha_entrada: date, fecha_salida: date) -> Tuple[bool, str]:
    """Validates that the date range is logical"""
    try:
        if not fecha_entrada or not fecha_salida:
            return False, "Fechas de entrada y salida requeridas"
        
        if fecha_entrada >= fecha_salida:
            return False, "La fecha de salida debe ser posterior a la fecha de entrada"
        
        # Calculate duration
        duration = (fecha_salida - fecha_entrada).days
        
        if duration > 30:
            return False, "La estadía no puede ser mayor a 30 días"
        
        if duration < 1:
            return False, "La estadía debe ser de al menos 1 día"
        
        return True, f"OK: Estadía de {duration} día(s)"
        
    except Exception as e:
        return False, f"Error validando rango de fechas: {str(e)}"

def validate_contact_info(phone: str, email: str) -> Tuple[bool, str, str, List[str]]:
    """Validates contact information"""
    errors = []
    clean_phone = phone.strip() if phone else ""
    clean_email = email.strip().lower() if email else ""
    
    # Validate phone
    if not clean_phone:
        errors.append("Número de teléfono requerido")
    else:
        # Remove all non-digits
        phone_digits = re.sub(r'\D', '', clean_phone)
        
        # Must have between 7 and 15 digits
        if len(phone_digits) < 7:
            errors.append("Número de teléfono muy corto")
        elif len(phone_digits) > 15:
            errors.append("Número de teléfono muy largo")
        else:
            # Format the phone number
            if len(phone_digits) == 10:
                clean_phone = f"+57{phone_digits}"  # Colombian format
            elif not phone_digits.startswith('57') and len(phone_digits) == 12:
                clean_phone = f"+{phone_digits}"
            else:
                clean_phone = f"+{phone_digits}"
    
    # Validate email
    if not clean_email:
        errors.append("Correo electrónico requerido")
    else:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, clean_email):
            errors.append("Formato de correo electrónico inválido")
        elif len(clean_email) > 100:
            errors.append("Correo electrónico muy largo")
    
    success = len(errors) == 0
    return success, clean_phone, clean_email, errors

def validate_domo_selection(domo: str) -> Tuple[bool, str, str]:
    """Validates dome selection"""
    if not domo:
        return False, "", "Tipo de domo requerido"
    
    # Valid domes mapping
    valid_domos = {
        'antares': 'Antares',
        'polaris': 'Polaris', 
        'sirius': 'Sirius',
        'centaury': 'Centaury',
        'luna': 'Antares',  # Common alias
        'sol': 'Polaris',   # Common alias
    }
    
    domo_lower = domo.strip().lower()
    
    # Try exact match first
    if domo_lower in valid_domos:
        return True, valid_domos[domo_lower], f"OK: Domo {valid_domos[domo_lower]} seleccionado"
    
    # Try partial match
    for key, value in valid_domos.items():
        if key in domo_lower or domo_lower in key:
            return True, value, f"OK: Domo {value} detectado (interpretado de '{domo}')"
    
    return False, "", f"Domo '{domo}' no reconocido. Opciones: Antares, Polaris, Sirius, Centaury"

def validate_service_selection(servicio: str) -> Tuple[bool, str, str]:
    """Validates service selection"""
    if not servicio:
        return True, "Servicio estándar", "OK: Servicio estándar seleccionado por defecto"
    
    # Service mapping
    services = {
        'estandar': 'Servicio estándar',
        'standard': 'Servicio estándar',
        'basico': 'Servicio estándar',
        'romantico': 'Cena romántica',
        'romantica': 'Cena romántica',
        'cena': 'Cena romántica',
        'premium': 'Servicio premium',
        'especial': 'Servicio especial',
        'vip': 'Servicio VIP',
    }
    
    servicio_lower = servicio.strip().lower()
    
    # Try exact match first
    if servicio_lower in services:
        return True, services[servicio_lower], f"OK: {services[servicio_lower]} seleccionado"
    
    # Try partial match
    for key, value in services.items():
        if key in servicio_lower or servicio_lower in key:
            return True, value, f"OK: {value} detectado (interpretado de '{servicio}')"
    
    # If no match, use as-is but clean it
    clean_service = re.sub(r'[^\w\s.-]', '', servicio.strip())[:100]
    return True, clean_service, f"OK: Servicio personalizado '{clean_service}'"

def validate_payment_method(metodo: str) -> Tuple[bool, str, str]:
    """Validates payment method"""
    if not metodo:
        return True, "No especificado", "OK: Método de pago por confirmar"
    
    # Payment method mapping
    payment_methods = {
        'efectivo': 'Efectivo',
        'cash': 'Efectivo',
        'transferencia': 'Transferencia bancaria',
        'transfer': 'Transferencia bancaria',
        'banco': 'Transferencia bancaria',
        'tarjeta': 'Tarjeta de crédito/débito',
        'card': 'Tarjeta de crédito/débito',
        'credito': 'Tarjeta de crédito/débito',
        'debito': 'Tarjeta de crédito/débito',
        'pse': 'PSE',
        'nequi': 'Nequi',
        'daviplata': 'Daviplata',
        'paypal': 'PayPal',
    }
    
    metodo_lower = metodo.strip().lower()
    
    # Try exact match first
    if metodo_lower in payment_methods:
        return True, payment_methods[metodo_lower], f"OK: {payment_methods[metodo_lower]} seleccionado"
    
    # Try partial match
    for key, value in payment_methods.items():
        if key in metodo_lower or metodo_lower in key:
            return True, value, f"OK: {value} detectado (interpretado de '{metodo}')"
    
    # If no match, use as-is but clean it
    clean_method = re.sub(r'[^\w\s.-]', '', metodo.strip())[:50]
    return True, clean_method, f"OK: Método personalizado '{clean_method}'"

def validate_additional_services(adicciones: str) -> Tuple[bool, str, str]:
    """Validates additional services/additions"""
    if not adicciones:
        return True, "Ninguna", "OK: Sin servicios adicionales"
    
    # Clean and limit length
    clean_adicciones = re.sub(r'[^\w\s.,;:-]', '', adicciones.strip())[:200]
    
    if not clean_adicciones:
        return True, "Ninguna", "OK: Sin servicios adicionales válidos"
    
    return True, clean_adicciones, f"OK: Servicios adicionales registrados"

def validate_special_comments(comentarios: str) -> Tuple[bool, str, str]:
    """Validates special comments"""
    if not comentarios:
        return True, "Ninguno", "OK: Sin comentarios especiales"
    
    # Clean and limit length
    clean_comentarios = re.sub(r'[^\w\s.,;:!?()-]', '', comentarios.strip())[:500]
    
    if not clean_comentarios:
        return True, "Ninguno", "OK: Sin comentarios especiales válidos"
    
    return True, clean_comentarios, f"OK: Comentarios registrados"