# Servicio especializado para manejo inteligente de contactos de administradores
# Implementa detección específica según Variable 2 - Solo para PQRS y solicitudes de contacto

import re
from typing import Optional, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)

class AdminContactService:
    """
    Servicio que detecta cuándo compartir contactos de administradores según triggers específicos:
    - Cuando soliciten información de contacto específicamente
    - Cuando quieran hacer una PQRS (Petición, Queja, Reclamo, Sugerencia)
    - Cuando necesiten hablar con un administrador/gerente
    """
    
    def __init__(self):
        """Inicializar el servicio de detección de contactos admin"""
        # Información de contacto de administradores
        self.admin_phone = "+57 3054614926"
        self.admin_email = "glampingbrillodelunaguatavita@gmail.com"
        self.business_hours = "Lunes a Domingo, de 8:00 AM a 9:00 PM"
        self.rnt_number = "172465"
        
        # Definir patrones específicos para cada trigger
        self._init_detection_patterns()
        
        logger.info("AdminContactService inicializado", 
                   extra={"component": "admin_contact_service", "phase": "startup"})
    
    def _init_detection_patterns(self):
        """Inicializar patrones de detección para cada caso específico"""
        
        # Trigger 1: Solicitud directa de contacto/información de contacto
        self.contact_request_patterns = [
            r'\bcontacto\b', r'\bcontactar\b', r'\bcontactarlos\b',
            r'\bteléfono\b', r'\btelefono\b', r'\bnúmero\b', r'\bnumero\b',
            r'\bemail\b', r'\bcorreo\b', r'\bcorreo\s+electrónico\b', r'\bcorreo\s+electronico\b',
            r'\bwhatsapp\b', r'\binformación\s+de\s+contacto\b', r'\binformacion\s+de\s+contacto\b',
            r'\bcómo\s+los\s+contacto\b', r'\bcomo\s+los\s+contacto\b',
            r'\bdónde\s+los\s+encuentro\b', r'\bdonde\s+los\s+encuentro\b',
            r'\bdirección\s+de\s+contacto\b', r'\bdireccion\s+de\s+contacto\b'
        ]
        
        # Trigger 2: PQRS - Peticiones
        self.peticion_patterns = [
            r'\bpetición\b', r'\bpeticion\b', r'\bpedir\b', r'\bpido\b',
            r'\bsolicitar\b', r'\bsolicito\b', r'\bsolicitud\b',
            r'\brequerir\b', r'\brequiero\b', r'\brequerimiento\b',
            r'\bnecesito\s+hablar\b', r'\bquiero\s+hablar\b',
            r'\bpropuesta\b', r'\bsugerir\b'
        ]
        
        # Trigger 3: PQRS - Quejas
        self.queja_patterns = [
            r'\bqueja\b', r'\bquejar\b', r'\bquejarme\b',
            r'\bmolesto\b', r'\bmolesta\b', r'\bmolestar\b',
            r'\binsatisfecho\b', r'\binsatisfecha\b', r'\binsatisfacción\b',
            r'\bproblema\b', r'\bproblemas\b', r'\binconveniente\b',
            r'\bmal\s+servicio\b', r'\bservicio\s+malo\b',
            r'\bno\s+me\s+gustó\b', r'\bno\s+me\s+gusto\b',
            r'\bmala\s+experiencia\b', r'\bexperiencia\s+mala\b'
        ]
        
        # Trigger 4: PQRS - Reclamos (patrones más específicos)
        self.reclamo_patterns = [
            r'\breclamo\b', r'\breclamar\b', r'\breclamos\b',
            r'\breembolso\b', r'\bdevolver\b', r'\bdevolución\b', r'\bdevolucion\b',
            r'\bfacturación\b', r'\bfacturacion\b', r'\bproblema\s+con\s+la\s+facturación\b',
            r'\bproblema\s+con\s+la\s+facturacion\b', r'\bcobro\s+incorrecto\b',
            r'\bcobro\s+indebido\b', r'\bme\s+cobraron\s+mal\b', r'\bcobros\s+erroneos\b',
            r'\bcancelar\s+mi\s+reserva\b', r'\bcancelar\s+reserva\b', 
            r'\bquiero\s+cancelar\b', r'\bnecesito\s+cancelar\b',
            r'\bno\s+funciona\b', r'\bno\s+sirvió\b', r'\bno\s+sirvio\b',
            r'\bdefraudado\b', r'\bdefraudada\b', r'\bfraude\b',
            r'\bestafa\b', r'\bescándalo\b', r'\bescandalo\b'
        ]
        
        # Trigger 5: PQRS - Sugerencias
        self.sugerencia_patterns = [
            r'\bsugerencia\b', r'\bsugerir\b', r'\bsugerencias\b',
            r'\bidea\b', r'\bideas\b', r'\bproponerr\b', r'\bpropongo\b',
            r'\bmejorar\b', r'\bmejora\b', r'\bmejoras\b',
            r'\brecomendación\b', r'\brecomendacion\b', r'\brecomendar\b',
            r'\bfeedback\b', r'\bopinión\b', r'\bopinion\b',
            r'\bcomentario\b', r'\bcomentarios\b', r'\bcrítica\s+constructiva\b',
            r'\bcritica\s+constructiva\b'
        ]
        
        # Trigger 6: Solicitud de hablar con administrador/gerente
        self.admin_request_patterns = [
            r'\badministrador\b', r'\badmin\b', r'\bgerente\b', r'\bmanager\b',
            r'\bresponsable\b', r'\bencargado\b', r'\bencargada\b',
            r'\bjefe\b', r'\bjefa\b', r'\bsupervisor\b', r'\bsupervisora\b',
            r'\bhablar\s+con\s+alguien\s+más\b', r'\bhablar\s+con\s+alguien\s+mas\b',
            r'\bpersona\s+a\s+cargo\b', r'\bquien\s+está\s+a\s+cargo\b',
            r'\bquien\s+esta\s+a\s+cargo\b', r'\bmás\s+autoridad\b', r'\bmas\s+autoridad\b'
        ]
    
    def should_share_admin_contact(self, message: str) -> Tuple[bool, str, str]:
        """
        Determina si se debe compartir contacto de administradores según los triggers
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple[bool, str, str]: (should_share, trigger_type, reason)
        """
        try:
            message_clean = message.lower().strip()
            
            logger.info(f"Analizando mensaje para contacto admin: '{message_clean[:50]}...'", 
                       extra={"component": "admin_contact_service", "action": "analyze_message"})
            
            # Verificar cada tipo de trigger en orden de prioridad (más específicos primero)
            trigger_checks = [
                (self.contact_request_patterns, "contact_request", "Solicitud directa de información de contacto"),
                (self.reclamo_patterns, "reclamo", "Reclamo o solicitud de reembolso"),  # Reclamos primero
                (self.queja_patterns, "queja", "Queja o problema reportado"),
                (self.admin_request_patterns, "admin_request", "Solicitud de hablar con administrador"),
                (self.peticion_patterns, "peticion", "Petición o solicitud especial"),
                (self.sugerencia_patterns, "sugerencia", "Sugerencia o feedback")
            ]
            
            for patterns, trigger_type, reason in trigger_checks:
                if self._matches_patterns(message_clean, patterns):
                    logger.info(f"Trigger de contacto admin detectado: {trigger_type} - {reason}", 
                               extra={"component": "admin_contact_service", "trigger": trigger_type})
                    return True, trigger_type, reason
            
            logger.info("No se detectó trigger para compartir contacto admin", 
                       extra={"component": "admin_contact_service", "result": "no_trigger"})
            return False, "", ""
            
        except Exception as e:
            logger.error(f"Error analizando mensaje para contacto admin: {e}", 
                        extra={"component": "admin_contact_service"})
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
                        extra={"component": "admin_contact_service"})
            return False
    
    def generate_admin_contact_response(self, trigger_type: str, user_message: str = "") -> str:
        """
        Genera respuesta apropiada con contacto según el tipo de trigger
        
        Args:
            trigger_type: Tipo de trigger detectado
            user_message: Mensaje original del usuario
            
        Returns:
            str: Respuesta formateada con contacto apropiado
        """
        try:
            logger.info(f"Generando respuesta de contacto admin para trigger: {trigger_type}", 
                       extra={"component": "admin_contact_service", "trigger": trigger_type})
            
            if trigger_type == "contact_request":
                return self._generate_contact_info_response()
            elif trigger_type == "queja":
                return self._generate_complaint_contact_response()
            elif trigger_type == "reclamo":
                return self._generate_claim_contact_response()
            elif trigger_type == "admin_request":
                return self._generate_admin_request_response()
            elif trigger_type == "peticion":
                return self._generate_petition_contact_response()
            elif trigger_type == "sugerencia":
                return self._generate_suggestion_contact_response()
            else:
                return self._generate_generic_contact_response()
                
        except Exception as e:
            logger.error(f"Error generando respuesta de contacto admin: {e}", 
                        extra={"component": "admin_contact_service"})
            return self._generate_generic_contact_response()
    
    def _generate_contact_info_response(self) -> str:
        """Respuesta para solicitudes directas de contacto"""
        return f"""📞 **INFORMACIÓN DE CONTACTO GLAMPING BRILLO DE LUNA** 📧

📱 **Teléfono/WhatsApp**: {self.admin_phone}
📧 **Correo electrónico**: {self.admin_email}

🕐 **Horario de atención**: {self.business_hours}

📍 **Ubicación**: Guatavita, Cundinamarca, Colombia
🏷️ **Registro Nacional de Turismo (RNT)**: {self.rnt_number}

📱 **¿Prefieres WhatsApp?** Escríbenos directamente al {self.admin_phone}
📧 **¿Prefieres email?** Envíanos un mensaje a {self.admin_email}

¡Estamos aquí para ayudarte! 😊"""
    
    def _generate_complaint_contact_response(self) -> str:
        """Respuesta para quejas"""
        return f"""😔 **LAMENTAMOS QUE HAYAS TENIDO UNA MALA EXPERIENCIA**

Nos tomamos muy en serio todas las quejas y queremos solucionarlo de inmediato.

📞 **CONTACTO DIRECTO CON ADMINISTRACIÓN:**
📱 **WhatsApp urgente**: {self.admin_phone}
📧 **Email para quejas**: {self.admin_email}

🕐 **Horario de atención**: {self.business_hours}

📝 **Para una atención más rápida, por favor incluye:**
• Fecha de tu estadía o reserva
• Número de reserva (si lo tienes)
• Descripción detallada del problema
• Tu nombre completo

💬 **Te responderemos en máximo 24 horas**
🏷️ **Registro Nacional de Turismo (RNT)**: {self.rnt_number}

¡Queremos hacer las cosas bien! 🙏"""
    
    def _generate_claim_contact_response(self) -> str:
        """Respuesta para reclamos (especialmente financieros)"""
        return f"""📋 **RECLAMOS Y REEMBOLSOS - CONTACTO ADMINISTRATIVO**

Entendemos tu situación y queremos resolverlo rápidamente.

📞 **CONTACTO DIRECTO PARA RECLAMOS:**
📱 **WhatsApp prioritario**: {self.admin_phone}
📧 **Email especializado**: {self.admin_email}

🕐 **Horario de atención**: {self.business_hours}

📝 **Información necesaria para tu reclamo:**
• Número de reserva o comprobante de pago
• Fecha y monto de la transacción
• Descripción detallada del problema
• Método de pago utilizado

⚡ **Tiempo de respuesta**: Máximo 48 horas
💰 **Reembolsos**: Procesamos en 5-10 días hábiles
🏷️ **Registro Nacional de Turismo (RNT)**: {self.rnt_number}

¡Tu reclamo es importante para nosotros! 📞"""
    
    def _generate_admin_request_response(self) -> str:
        """Respuesta para solicitudes de hablar con administrador"""
        return f"""👔 **CONTACTO DIRECTO CON ADMINISTRACIÓN**

Te conectamos directamente con nuestro equipo administrativo.

📞 **ADMINISTRACIÓN GLAMPING BRILLO DE LUNA:**
📱 **WhatsApp directo**: {self.admin_phone}
📧 **Email administración**: {self.admin_email}

🕐 **Horario de atención**: {self.business_hours}

👥 **Nuestro equipo administrativo incluye:**
• Gerencia general
• Atención al cliente especializada
• Coordinación de reservas
• Resolución de problemas

📱 **Recomendamos WhatsApp** para una respuesta más rápida
📧 **O email** si prefieres comunicación formal

¡Te atenderemos personalmente! 🤝"""
    
    def _generate_petition_contact_response(self) -> str:
        """Respuesta para peticiones especiales"""
        return f"""📝 **PETICIONES Y SOLICITUDES ESPECIALES**

Nos encanta atender solicitudes especiales para hacer tu experiencia única.

📞 **CONTACTO PARA PETICIONES:**
📱 **WhatsApp coordinación**: {self.admin_phone}
📧 **Email peticiones**: {self.admin_email}

🕐 **Horario de atención**: {self.business_hours}

✨ **Servicios especiales que podemos coordinar:**
• Cenas románticas personalizadas
• Decoraciones especiales
• Actividades exclusivas
• Servicios de transporte
• Celebraciones especiales

📱 **Escríbenos con anticipación** para una mejor coordinación
⏰ **Tiempo de respuesta**: 24-48 horas

¡Hagamos tu estadía inolvidable! 🌟"""
    
    def _generate_suggestion_contact_response(self) -> str:
        """Respuesta para sugerencias"""
        return f"""💡 **SUGERENCIAS Y FEEDBACK - ¡NOS INTERESA TU OPINIÓN!**

Tus sugerencias nos ayudan a mejorar continuamente.

📞 **CONTACTO PARA SUGERENCIAS:**
📱 **WhatsApp feedback**: {self.admin_phone}
📧 **Email sugerencias**: {self.admin_email}

🕐 **Horario de atención**: {self.business_hours}

📝 **Nos interesa tu opinión sobre:**
• Servicios y amenidades
• Instalaciones y comodidades
• Actividades y experiencias
• Atención al cliente
• Ideas para nuevos servicios

🎯 **Todas las sugerencias son revisadas por gerencia**
📊 **Implementamos mejoras basadas en feedback de huéspedes**

¡Tu opinión es valiosa para nosotros! 💭"""
    
    def _generate_generic_contact_response(self) -> str:
        """Respuesta genérica como fallback"""
        return f"""📞 **CONTACTO GLAMPING BRILLO DE LUNA**

📱 **WhatsApp**: {self.admin_phone}
📧 **Email**: {self.admin_email}
🕐 **Horario**: {self.business_hours}

¡Estamos aquí para ayudarte! 😊"""
    
    def get_admin_contact_info(self) -> dict:
        """Obtener información de contacto completa"""
        return {
            "phone": self.admin_phone,
            "email": self.admin_email,
            "business_hours": self.business_hours,
            "rnt_number": self.rnt_number
        }
    
    def update_admin_contact_info(self, phone: Optional[str] = None, email: Optional[str] = None, 
                                 hours: Optional[str] = None, rnt: Optional[str] = None):
        """Actualizar información de contacto si es necesario"""
        if phone:
            self.admin_phone = phone
            logger.info(f"Teléfono admin actualizado: {phone}", 
                       extra={"component": "admin_contact_service"})
        
        if email:
            self.admin_email = email
            logger.info(f"Email admin actualizado: {email}", 
                       extra={"component": "admin_contact_service"})
                       
        if hours:
            self.business_hours = hours
            logger.info(f"Horario actualizado: {hours}", 
                       extra={"component": "admin_contact_service"})
                       
        if rnt:
            self.rnt_number = rnt
            logger.info(f"RNT actualizado: {rnt}", 
                       extra={"component": "admin_contact_service"})


# Instancia global del servicio
admin_contact_service = AdminContactService()

def get_admin_contact_service() -> AdminContactService:
    """Obtener instancia global del servicio de contactos admin"""
    return admin_contact_service