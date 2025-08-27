# Servicio especializado para manejo del menú principal
# Consolida y mejora el manejo de selecciones con variantes flexibles

from typing import Dict, Any, Optional, Union, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

class MenuService:
    def __init__(self, qa_chains: Dict[str, Any], validation_service, availability_service=None):
        
        self.qa_chains = qa_chains
        self.validation_service = validation_service
        self.availability_service = availability_service
        logger.info("MenuService inicializado", 
                   extra={"component": "menu_service", "phase": "startup"})
    
    def handle_menu_selection(self, user_message: str, user_state: dict) -> Union[str, dict]:
       
        # Extraer opción del mensaje
        option = self.validation_service.extract_menu_option(user_message)
        
        if not option:
            return "No pude identificar qué opción del menú deseas. Por favor escribe el número (1-8) o usa palabras como 'información', 'domos', 'disponibilidad', 'servicios', 'actividades', 'políticas', 'imágenes' o 'accesibilidad'."
        
        logger.info(f"Procesando selección de menú: opción {option}", 
                   extra={"component": "menu_service", "option": option, "user_message": user_message[:50]})
        
        # Procesar cada opción
        if option == "1":
            informacion_response = self._handle_informacion_option()
            user_state["current_flow"] = "informacion_general"
            user_state["waiting_for_informacion_suboption"] = True
            
            # Después de mostrar información general:
            user_state["last_action"] = "showed_information"
            user_state["waiting_for_continuation"] = True
            user_state["available_actions"] = ["concept_query", "location_query", "contact_query", "other_menu_option"]
            user_state["previous_context"] = "general_info"
            
            # Actualizar context_service si está disponible
            try:
                from services.context_service import get_context_service
                context_service = get_context_service()
                context_service.remember_context(user_state.get('user_id', 'unknown'), 'showed_information', {
                    'option_selected': '1',
                    'menu_section': 'informacion_general',
                    'response_type': 'information_menu'
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar context_service: {e}")
            
            return informacion_response
        elif option == "2":
            domos_response = self._handle_domos_option()
            if isinstance(domos_response, dict) and "set_waiting_for_domos_followup" in domos_response:
                user_state["current_flow"] = "domos_followup"
                user_state["waiting_for_domos_followup"] = True
            
            # Después de mostrar info de domos:
            user_state["last_action"] = "showed_domos"
            user_state["waiting_for_continuation"] = True
            user_state["available_actions"] = ["specific_domo_query", "other_menu_option"]
            user_state["previous_context"] = "domos_info"
            
            # Actualizar context_service si está disponible
            try:
                from services.context_service import get_context_service
                context_service = get_context_service()
                context_service.remember_context(user_state.get('user_id', 'unknown'), 'showed_domos', {
                    'option_selected': '2',
                    'menu_section': 'domos',
                    'response_type': 'domos_menu'
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar context_service: {e}")
            
            return domos_response
        elif option == "3":
            disponibilidad_response = self._handle_disponibilidad_option()
            if isinstance(disponibilidad_response, dict) and "set_waiting_for_availability" in disponibilidad_response:
                user_state["current_flow"] = "availability"
                user_state["waiting_for_availability"] = True
            
            # Después de mostrar info de disponibilidad:
            user_state["last_action"] = "showed_availability"
            user_state["waiting_for_continuation"] = True
            user_state["available_actions"] = ["date_query", "reservation_intent", "other_menu_option"]
            user_state["previous_context"] = "availability_info"
            
            # Actualizar context_service si está disponible
            try:
                from services.context_service import get_context_service
                context_service = get_context_service()
                context_service.remember_context(user_state.get('user_id', 'unknown'), 'showed_availability', {
                    'option_selected': '3',
                    'menu_section': 'disponibilidad',
                    'response_type': 'availability_menu'
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar context_service: {e}")
            
            return disponibilidad_response
        elif option == "4":
            # Servicios combinados (incluidos y adicionales)
            servicios_response = self._handle_servicios_combinados_option()
            if isinstance(servicios_response, dict) and "set_waiting_for_servicios_followup" in servicios_response:
                user_state["current_flow"] = "servicios_followup"
                user_state["waiting_for_servicios_followup"] = True
            
            # Después de mostrar info de servicios:
            user_state["last_action"] = "showed_services"
            user_state["waiting_for_continuation"] = True
            user_state["available_actions"] = ["specific_service_query", "pricing_query", "other_menu_option"]
            user_state["previous_context"] = "services_info"
            
            # Actualizar context_service si está disponible
            try:
                from services.context_service import get_context_service
                context_service = get_context_service()
                context_service.remember_context(user_state.get('user_id', 'unknown'), 'showed_services', {
                    'option_selected': '4',
                    'menu_section': 'servicios_combinados',
                    'response_type': 'services_menu'
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar context_service: {e}")
            
            return servicios_response
            
        elif option == "5":
            politicas_response = self._handle_politicas_option()
            
            # Después de mostrar políticas:
            user_state["last_action"] = "showed_policies"
            user_state["waiting_for_continuation"] = True
            user_state["available_actions"] = ["specific_policy_query", "clarification_query", "other_menu_option"]
            user_state["previous_context"] = "policies_info"
            
            # Actualizar context_service si está disponible
            try:
                from services.context_service import get_context_service
                context_service = get_context_service()
                context_service.remember_context(user_state.get('user_id', 'unknown'), 'showed_policies', {
                    'option_selected': '5',
                    'menu_section': 'politicas',
                    'response_type': 'policies_menu'
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar context_service: {e}")
            
            return politicas_response
        else:
            return "Opción no válida. Por favor selecciona una opción entre 1 y 5."
    
    def _handle_domos_option(self) -> dict:
        """Maneja selección de opción 1: Domos con flujo de seguimiento"""
        try:
            # Consultar información de domos usando múltiples RAG
            domos_info = ""
            domos_precios = ""
            
            # Usar fallback robusto para información de domos
            domos_info = self._get_domos_info_with_fallback()
            
            # Usar fallback robusto para precios de domos
            domos_precios = self._get_domos_precios_with_fallback()
            
            response_message = f"""🏠 **INFORMACIÓN DE NUESTROS DOMOS** 🌟

{domos_info}

💰 **PRECIOS Y TARIFAS:**
{domos_precios}

📋 **Para más información específica:**
• Escribe el nombre del domo (Antares, Polaris, Sirius, Centaury)
• Escribe "disponibilidad" para consultar fechas
• Escribe "reservar" para hacer una reserva
• Escribe "menú" para volver al menú principal"""
            
            logger.info("Información de domos proporcionada con seguimiento", 
                       extra={"component": "menu_service", "option": "1"})
            
            return {
                "message": response_message,
                "set_waiting_for_domos_followup": True
            }
            
        except Exception as e:
            logger.error(f"Error procesando opción domos: {e}", 
                        extra={"component": "menu_service", "option": "1"})
            
            # En caso de cualquier error, usar respuesta completa con fallbacks
            return {
                "message": self._get_emergency_domos_response()
            }
    
    def _handle_servicios_combinados_option(self) -> dict:
        """Maneja selección de opción 4: Servicios combinados (incluidos y adicionales)"""
        try:
            # Combinar información de servicios incluidos y adicionales
            servicios_incluidos = self._get_fallback_servicios_incluidos()
            actividades_adicionales = self._get_fallback_actividades()
            
            response = f"""🛎️ **SERVICIOS - INCLUIDOS Y ADICIONALES**

**🏠 SERVICIOS INCLUIDOS EN TU ESTADÍA**
{servicios_incluidos}

**🎯 ACTIVIDADES Y SERVICIOS ADICIONALES**
{actividades_adicionales}

🔍 Puedo contarte sobre:
• **Servicios incluidos** - Detalles específicos incluidos en tu tarifa
• **Actividades adicionales** - Experiencias extras con precios
• **Reservas de servicios** - Cómo contratar servicios adicionales
• **Recomendaciones** - Qué actividades son más populares

📋 **Para más información:**
• Escribe el nombre del domo (Antares, Polaris, Sirius, Centaury)
• Escribe "disponibilidad" para consultar fechas
• Escribe "menú" para volver al menú principal"""
            
            logger.info("Información de servicios combinados proporcionada", 
                       extra={"component": "menu_service", "option": "4"})
            
            return {
                "message": response,
                "set_waiting_for_servicios_followup": True
            }
            
        except Exception as e:
            logger.error(f"Error manejando servicios combinados: {e}")
            return {
                "message": "Disculpa, tuve un problema obteniendo la información de servicios. ¿Podrías intentar de nuevo?",
                "set_waiting_for_servicios_followup": False
            }

    def _handle_servicios_option(self) -> dict:
        """Maneja selección de servicios con diferenciación incluidos/adicionales"""
        try:
            response_message = """🛎️ **SERVICIOS DE GLAMPING BRILLO DE LUNA** ✨

¿Qué tipo de servicios te interesan?

📋 **SERVICIOS INCLUIDOS** (Sin costo adicional):
• Desayuno gourmet continental
• WiFi de alta velocidad
• Parqueadero privado
• Kit de bienvenida
• Aseo y arreglo del domo
• Acceso a todas las instalaciones

🎯 **SERVICIOS ADICIONALES** (Con costo extra):
• Actividades turísticas en la zona
• Experiencias gastronómicas especiales
• Servicios de bienestar y relajación
• Tours y paseos guiados

💬 Responde:
• **"Incluidos"** - Para servicios sin costo adicional
• **"Adicionales"** - Para actividades y servicios extras
• **"Ambos"** - Para información completa
            """

            return {
                "message": response_message,
                "set_waiting_for_servicios_followup": True
            }

        except Exception as e:
            logger.error(f"Error en _handle_servicios_option: {e}")
            return {"message": "Error procesando información de servicios"}
    
    def _is_generic_response(self, response: str) -> bool:
        """Detecta si una respuesta es genérica del LLM en lugar de información específica"""
        if not response or len(response.strip()) < 10:
            return True

        # Para respuestas cortas, solo detectar si contienen indicadores genéricos
        response_lower = response.lower()
        generic_indicators = [
            "Como asistente AI", "no tengo acceso", "no puedo proporcionar",
            "no está disponible para mí", "Por favor proporciona más",
            "necesito más detalles", "no proporciona un contexto claro",
            "generalmente", "suelen estar incluidos", "Te recomendaría que verifiques",
            "Lo siento", "no encontré información", "No tengo información específica",
            "Disculpa", "tuve un problema", "error", "Error code:", "insufficient_quota"
        ]
        
        # Verificar indicadores genéricos
        has_generic_indicator = any(indicator.lower() in response_lower for indicator in generic_indicators)
        
        # Si la respuesta es muy corta (menos de 30 chars) Y no tiene contenido específico
        if len(response.strip()) < 30:
            # Palabras que indican contenido específico (no genérico)
            specific_keywords = [
                "glamping", "brillo", "luna", "guatavita", "tominé", "domo", "ubicado",
                "precio", "tarifa", "reserva", "servicios", "incluye", "wifi", "desayuno",
                "jacuzzi", "vista", "represa", "montaña", "personas", "capacidad"
            ]
            has_specific_content = any(keyword in response_lower for keyword in specific_keywords)
            
            # Si es corta pero tiene contenido específico, no es genérica
            if has_specific_content and not has_generic_indicator:
                return False
            
            # Si es corta y no tiene contenido específico, es genérica
            if not has_specific_content:
                return True
        
        return has_generic_indicator
    
    def _get_fallback_servicios_incluidos(self) -> str:
        """Fallback con información específica de servicios incluidos"""
        return """✨ **SERVICIOS INCLUIDOS EN TU ESTADÍA:**

🛏️ **ALOJAMIENTO:**
• Domo geodésico completamente equipado
• Ropa de cama premium y toallas
• Amenities de baño de lujo
• Limpieza diaria del domo

🍽️ **ALIMENTACIÓN:**
• Desayuno continental gourmet
• Café, té y agua filtrada 24/7
• Mini-bar con snacks selectos
• Acceso a cocina compartida

🌐 **SERVICIOS BÁSICOS:**
• WiFi de alta velocidad gratuito
• Parqueadero privado y seguro
• Recepción y conserjería 24 horas
• Servicio de equipaje

🏞️ **ACCESO A INSTALACIONES:**
• Zona de fogatas y parrillas
• Senderos ecológicos
• Áreas de relajación al aire libre
• Mirador de estrellas"""
    
    def _get_fallback_actividades(self) -> str:
        """Fallback con información específica de actividades adicionales"""
        return """🎯 **EXPERIENCIAS ADICIONALES DISPONIBLES:**

🌟 **EXPERIENCIAS DE NATURALEZA:**
• Caminatas ecológicas guiadas - $25.000/persona
• Observación de aves al amanecer - $20.000/persona  
• Tours nocturnos de estrellas - $30.000/persona
• Meditación y yoga matutino - $15.000/persona

🛀 **BIENESTAR Y RELAJACIÓN:**
• Masajes terapéuticos en el domo - $80.000/sesión
• Spa y tratamientos faciales - $60.000/sesión
• Jacuzzi privado (según domo) - Incluido
• Aromaterapia nocturna - $25.000/noche

🍽️ **EXPERIENCIAS GASTRONÓMICAS:**
• Cena romántica bajo las estrellas - $120.000/pareja
• Asado tradicional en fogata - $40.000/persona
• Clases de cocina local - $50.000/persona
• Picnic gourmet - $35.000/persona

🎨 **ACTIVIDADES ESPECIALES:**
• Talleres de artesanías locales - $30.000/persona
• Fotografía de naturaleza - $40.000/persona
• Ceremonias de luna llena - $25.000/persona"""
    
    def _handle_disponibilidad_option(self) -> dict:
        """Maneja selección de opción 3: Disponibilidad"""
        logger.info("Activando modo consulta de disponibilidad", 
                   extra={"component": "menu_service", "option": "3"})
        
        return {
            "message": """📅 **CONSULTA DE DISPONIBILIDAD** 📋

Para consultar disponibilidad necesito algunos datos:

📍 **¿Para qué fechas?** 
   • Fecha de llegada (ej: 15 de septiembre)
   • Fecha de salida (ej: 17 de septiembre)

👥 **¿Cuántas personas?**
   • Número total de huéspedes

🏠 **¿Tipo de domo?** (opcional)
   • Antares, Polaris, Sirius, Centaury, o cualquiera disponible

💬 Puedes escribir todo junto o paso a paso.
**Ejemplo:** "Quiero consultar disponibilidad para 2 personas del 15 al 17 de septiembre"

¿Cuáles son tus fechas? 📅""",
            "set_waiting_for_availability": True
        }
    
    def _detect_flow_exit_intent(self, user_message: str, current_flow: str) -> bool:
       
        message_lower = user_message.lower().strip()
        
        # Intenciones explícitas de salir
        exit_phrases = [
            "no quiero", "no necesito", "no me interesa",
            "cancelar", "salir", "volver", "regresar",
            "menu", "menú", "opciones", "atras", "atrás",
            "cambiar", "mejor no", "no gracias", "gracias no"
        ]
        
        # Para flujo de disponibilidad
        if current_flow == "availability":
            availability_exit_phrases = [
                "no quiero ver disponibilidad", "no quiero disponibilidad",
                "no consultar", "no fechas", "mejor otro tema",
                "no disponibilidades", "ya no", "olvídalo"
            ]
            exit_phrases.extend(availability_exit_phrases)
        
        # Para flujo de domos
        elif current_flow == "domos_followup":
            domos_exit_phrases = [
                "no quiero domos", "no me interesan los domos",
                "no más domos", "mejor otras opciones"
            ]
            exit_phrases.extend(domos_exit_phrases)
        
        # Para flujo de servicios
        elif current_flow == "servicios_followup":
            servicios_exit_phrases = [
                "no quiero servicios", "no me interesan los servicios",
                "no más servicios", "mejor otros temas"
            ]
            exit_phrases.extend(servicios_exit_phrases)
        
        # Verificar si alguna frase coincide
        for phrase in exit_phrases:
            if phrase in message_lower:
                return True
        
        return False

    def _generate_intelligent_flow_exit_response(self, user_message: str, current_flow: str) -> str:
        
        if current_flow == "availability":
            return """😊 **¡Entiendo perfectamente!**

🔧 **No hay problema, exploremos otras opciones**

🏠 **¿Qué te interesaría saber?**

🌟 **DOMOS** - Escribe "domos" para ver:
• Tipos de domos y características únicas
• Precios y tarifas detalladas
• Servicios incluidos en cada domo

🛎️ **SERVICIOS** - Escribe "servicios" para conocer:
• Lo que incluye tu estadía
• Actividades y experiencias disponibles
• Amenidades y comodidades

📍 **INFORMACIÓN** - Escribe "información" para:
• Ubicación y cómo llegar
• Políticas del glamping
• Contactos directos para consultas

💬 **¿Qué opción te llama más la atención?** 🌟"""

        elif current_flow == "domos_followup":
            return """😊 **¡Por supuesto!**

🔧 **Cambiemos de tema entonces**

🌟 **¿Qué más te gustaría saber del glamping?**

📅 **DISPONIBILIDAD** - Para consultar fechas libres
🛎️ **SERVICIOS** - Actividades y experiencias
📍 **INFORMACIÓN** - Ubicación y políticas  
📸 **GALERÍA** - Ver fotos e imágenes

💬 **¿Cuál de estas opciones te interesa?** ✨"""

        elif current_flow == "servicios_followup":
            return """😊 **¡Perfecto!**

🔧 **Exploremos otras opciones entonces**

🌟 **¿Qué te gustaría conocer?**

🏠 **DOMOS** - Tipos y características
📅 **DISPONIBILIDAD** - Consultar fechas
📍 **INFORMACIÓN** - Políticas y ubicación
📸 **GALERÍA** - Ver imágenes del lugar

💬 **¿Qué opción prefieres?** 🌟"""

        else:
            return """😊 **¡Entiendo!**

🔧 **Cambiemos de tema**

🌟 **¿En qué puedo ayudarte?**

💬 **Escribe el número (1-8) o la palabra de tu opción preferida** ✨"""

    def handle_availability_request(self, user_message: str, user_state: dict) -> str:
        """
        Maneja solicitudes de disponibilidad con el flujo completo especificado
        
        Args:
            user_message: Mensaje del usuario con fechas
            user_state: Estado actual del usuario
            
        Returns:
            str: Respuesta sobre disponibilidad
        """
        try:
            # NUEVA LÓGICA: Detectar si quiere salir del flujo de disponibilidad
            if self._detect_flow_exit_intent(user_message, "availability"):
                # Resetear estado y generar respuesta inteligente
                user_state["waiting_for_availability"] = False
                user_state["current_flow"] = "none"
                logger.info("Usuario detectó intención de salir del flujo de disponibilidad")
                return self._generate_intelligent_flow_exit_response(user_message, "availability")
            # Parsear fechas del mensaje
            success, fecha_entrada, fecha_salida, personas, error_msg = self.validation_service.parse_availability_dates(user_message)
            
            if not success:
                # Error parseando fechas - pedir clarificación
                return f"""❌ **No pude entender las fechas solicitadas**

**Error:** {error_msg}

📝 **Por favor, proporciona las fechas de esta forma:**
• "Del 15 al 17 de septiembre para 2 personas"
• "Desde el 20/12/2024 hasta 22/12/2024 para 4 personas"
• "25 de enero hasta 27 de enero para 3 personas"

💬 **Incluye:**
✓ Fecha de entrada
✓ Fecha de salida  
✓ Número de personas

¿Podrías intentar de nuevo? 📅"""
            
            # Verificar disponibilidad usando el servicio real de disponibilidad
            disponible = self._check_availability_in_database(fecha_entrada, fecha_salida, personas)
            
            if disponible:
                # Fechas DISPONIBLES - Preguntar si desea reservar
                user_state["current_flow"] = "availability_confirmation"
                user_state["waiting_for_availability"] = False
                user_state["waiting_for_availability_confirmation"] = True
                user_state["availability_data"] = {
                    "fecha_entrada": fecha_entrada,
                    "fecha_salida": fecha_salida,
                    "personas": personas
                }
                
                duracion = (fecha_salida - fecha_entrada).days
                
                return f"""✅ **¡EXCELENTES NOTICIAS! LAS FECHAS ESTÁN DISPONIBLES** 🎉

📅 **Fechas solicitadas:** {fecha_entrada.strftime('%d/%m/%Y')} - {fecha_salida.strftime('%d/%m/%Y')}
👥 **Personas:** {personas} huéspedes
🌙 **Duración:** {duracion} {"día" if duracion == 1 else "días"}

🏠 **Domos disponibles:**
• Antares - Domo premium con jacuzzi
• Polaris - Domo amplio con sofá cama
• Sirius - Domo de un piso para parejas
• Centaury - Domo acogedor para parejas

💰 **Precios desde:** $150.000 por noche
📋 **Incluye:** Desayuno, WiFi, parqueadero

📅 **Para continuar:**
• Escribe "reservar" para iniciar el proceso de reserva
• Escribe "otras fechas" para consultar disponibilidad diferente
• Escribe "menú" para volver al menú principal"""
            
            else:
                # Fechas NO DISPONIBLES - Preguntar por otras fechas
                user_state["current_flow"] = "availability_alternatives"
                user_state["waiting_for_availability"] = False
                user_state["waiting_for_availability_alternatives"] = True
                
                return f"""❌ **LO SIENTO, LAS FECHAS NO ESTÁN DISPONIBLES** 😔

📅 **Fechas consultadas:** {fecha_entrada.strftime('%d/%m/%Y')} - {fecha_salida.strftime('%d/%m/%Y')}
👥 **Para:** {personas} personas

🗓️ **Estas fechas ya están reservadas o no disponibles**

📅 **Opciones disponibles:**

✨ **Sugerencias:**
• Fechas una semana antes o después
• Fechas en días laborales (mejor precio)
• Estadías más cortas o largas

📅 **Para continuar:**
• Escribe "otras fechas" o "alternativas" para buscar disponibilidad diferente
• Escribe "disponibilidad" para consultar otro período
• Escribe "menú" para volver al menú principal"""
                
        except Exception as e:
            logger.error(f"Error procesando consulta de disponibilidad: {e}", 
                        extra={"component": "menu_service"})
            user_state["current_flow"] = "none"
            user_state["waiting_for_availability"] = False
            return """❌ **Error procesando tu consulta de disponibilidad**

🔧 Tuvimos un problema técnico temporal.

📋 **Por favor, intenta nuevamente con el formato:**
"Del [día] al [día] de [mes] para [número] personas"

💬 **Ejemplo:** "Del 15 al 17 de septiembre para 2 personas"

¿Podrías intentar de nuevo? 📅"""
    
    def handle_availability_confirmation(self, user_message: str, user_state: dict) -> str:
      
        # NUEVA LÓGICA: Detectar si quiere salir del flujo
        if self._detect_flow_exit_intent(user_message, "availability"):
            # Resetear estado y generar respuesta inteligente
            user_state["waiting_for_availability_confirmation"] = False
            user_state["current_flow"] = "none"
            logger.info("Usuario detectó intención de salir del flujo de confirmación de disponibilidad")
            return self._generate_intelligent_flow_exit_response(user_message, "availability")
        
        yes_no_response = self.validation_service.is_yes_no_response(user_message)
        
        if yes_no_response is True:
            # Usuario quiere reservar - iniciar flujo de reserva
            user_state["current_flow"] = "reserva"
            user_state["waiting_for_availability_confirmation"] = False
            user_state["reserva_step"] = 1
            user_state["reserva_data"] = user_state.get("availability_data", {})
            
            availability_data = user_state.get("availability_data", {})
            fecha_entrada = availability_data.get("fecha_entrada")
            fecha_salida = availability_data.get("fecha_salida")
            personas = availability_data.get("personas", 2)
            
            return f"""🎉 **¡PERFECTO! INICIEMOS TU RESERVA** ✨

📅 **Fechas seleccionadas:** {fecha_entrada.strftime('%d/%m/%Y')} - {fecha_salida.strftime('%d/%m/%Y')}
👥 **Personas:** {personas} huéspedes

📋 **Para completar tu reserva necesito:**

✅ **Información personal:**
• Nombres completos de todos los huéspedes
• Teléfono de contacto  
• Email de contacto

✅ **Detalles de estadía:**
• Domo preferido (Antares, Polaris, Sirius, Centaury)
• Servicios adicionales que desees
• Método de pago (efectivo, transferencia, tarjeta)
• Comentarios especiales

💬 **Por favor, envía toda esta información en un solo mensaje para procesar tu reserva rápidamente.**

**Ejemplo:** "Juan Pérez y María González, domo Antares, 3001234567, juan@email.com, cena romántica, transferencia"

¡Estoy lista para recibir tus datos! 📝"""
        
        elif yes_no_response is False:
            # Usuario no quiere reservar - volver al menú principal
            user_state["current_flow"] = "none"
            user_state["waiting_for_availability_confirmation"] = False
            user_state["availability_data"] = {}
            
            return """😊 **¡No hay problema!**

🏕️ **¿En qué más puedo ayudarte?**

📋 **Puedes preguntar sobre:**
• **Domos** - Información y características
• **Servicios** - Todo lo que ofrecemos
• **Información general** - Ubicación, políticas
• **Otras fechas** - Consultar disponibilidad diferente

💬 También puedes hacer cualquier pregunta específica sobre Brillo de Luna. ¡Estoy aquí para ayudarte! 🌟"""
        
        else:
            # Respuesta ambigua - pedir clarificación
            return """🤔 **No estoy segura si quieres reservar estas fechas**

❓ **Por favor, responde claramente:**
• **"Sí"** si quieres iniciar el proceso de reserva
• **"No"** si necesitas consultar algo más antes de decidir

💬 ¡Estoy aquí para ayudarte con lo que necesites! 😊"""
    
    def handle_availability_alternatives(self, user_message: str, user_state: dict) -> str:
        """
        Maneja búsqueda de fechas alternativas cuando las fechas no están disponibles
        
        Args:
            user_message: Respuesta del usuario (sí/no)
            user_state: Estado actual del usuario
            
        Returns:
            str: Respuesta según la elección del usuario
        """
        # NUEVA LÓGICA: Detectar si quiere salir del flujo
        if self._detect_flow_exit_intent(user_message, "availability"):
            # Resetear estado y generar respuesta inteligente
            user_state["waiting_for_availability_alternatives"] = False
            user_state["current_flow"] = "none"
            logger.info("Usuario detectó intención de salir del flujo de alternativas de disponibilidad")
            return self._generate_intelligent_flow_exit_response(user_message, "availability")
        
        yes_no_response = self.validation_service.is_yes_no_response(user_message)
        
        if yes_no_response is True:
            # Usuario quiere buscar fechas alternativas - reiniciar consulta
            user_state["current_flow"] = "availability"
            user_state["waiting_for_availability_alternatives"] = False
            user_state["waiting_for_availability"] = True
            
            return """🔍 **¡PERFECTO! BUSQUEMOS FECHAS ALTERNATIVAS** 📅

💡 **Sugerencias para mayor disponibilidad:**

📆 **Días laborales:** Lunes a jueves (mejor precio y disponibilidad)
📆 **Fechas flexibles:** Considera +/- una semana de tus fechas originales
📆 **Estadías cortas:** 1-2 noches tienen más disponibilidad

💬 **Proporciona nuevas fechas usando el formato:**
• "Del 20 al 22 de septiembre para 2 personas"
• "Desde el 25/10/2024 hasta 27/10/2024 para 3 personas"
• "1 de diciembre hasta 3 de diciembre para 4 personas"

¿Cuáles son las nuevas fechas que te interesan? ✨"""
        
        elif yes_no_response is False:
            # Usuario no quiere buscar alternativas - volver al menú principal
            user_state["current_flow"] = "none"
            user_state["waiting_for_availability_alternatives"] = False
            
            return """😊 **¡Entiendo perfectamente!**

🕐 **Algunas opciones para ti:**

📞 **Contáctanos después:** Puedes consultar disponibilidad en cualquier momento
📋 **Lista de espera:** Te podemos avisar si se libera una cancelación
💬 **Consultas:** Pregúntame sobre domos, servicios o información general

🏕️ **¿En qué más puedo ayudarte?**
• **Domos** - Características y precios
• **Servicios** - Todo lo que ofrecemos  
• **Información general** - Ubicación y políticas

¡Estoy aquí cuando necesites ayuda! 🌟"""
        
        else:
            # Respuesta ambigua - pedir clarificación
            return """🤔 **No estoy segura si quieres buscar fechas alternativas**

❓ **Por favor, responde claramente:**
• **"Sí"** si quieres que te ayude a encontrar otras fechas disponibles
• **"No"** si prefieres consultar otra cosa por ahora

💬 ¡Estoy aquí para ayudarte con lo que necesites! 😊"""
    
    def _check_availability_in_database(self, fecha_entrada, fecha_salida, personas) -> bool:
       
        try:
            if self.availability_service:
                # Usar el servicio real de disponibilidad
                fecha_inicio_str = fecha_entrada.strftime('%Y-%m-%d')
                fecha_fin_str = fecha_salida.strftime('%Y-%m-%d')
                
                resultado = self.availability_service.consultar_disponibilidades(
                    fecha_inicio=fecha_inicio_str,
                    fecha_fin=fecha_fin_str,
                    personas=personas
                )
                
                if resultado.get('success'):
                    domos_disponibles = resultado.get('domos_disponibles', [])
                    # Verificar si hay al menos un domo disponible para todas las fechas del rango
                    if domos_disponibles:
                        # Considerar disponible si hay al menos un domo que cubra todo el período
                        dias_necesarios = (fecha_salida - fecha_entrada).days
                        for domo in domos_disponibles:
                            if len(domo.get('fechas_disponibles', [])) >= dias_necesarios:
                                logger.info(f"Disponibilidad encontrada: {domo['info']['nombre']} disponible",
                                           extra={"component": "menu_service", "availability": "found"})
                                return True
                    
                    logger.info("No hay disponibilidad para las fechas solicitadas",
                               extra={"component": "menu_service", "availability": "not_found"})
                    return False
                else:
                    logger.warning(f"Error consultando disponibilidad: {resultado.get('error')}",
                                  extra={"component": "menu_service", "availability": "error"})
                    # En caso de error, usar fallback
                    return self._availability_fallback(fecha_entrada)
            else:
                # Si no hay servicio de disponibilidad, usar fallback
                logger.warning("AvailabilityService no disponible, usando fallback",
                              extra={"component": "menu_service", "availability": "fallback"})
                return self._availability_fallback(fecha_entrada)
                
        except Exception as e:
            logger.error(f"Error verificando disponibilidad: {e}",
                        extra={"component": "menu_service", "availability": "exception"})
            return self._availability_fallback(fecha_entrada)
    
    def _availability_fallback(self, fecha_entrada) -> bool:
       
        # Simulación basada en día de la semana como fallback
        dia_semana = fecha_entrada.weekday()  # 0=lunes, 6=domingo
        
        # Simular: 80% disponibilidad días laborales, 40% fines de semana
        import random
        if dia_semana < 5:  # Lunes a viernes
            return random.random() < 0.8
        else:  # Sábado y domingo
            return random.random() < 0.4
    
    def _handle_informacion_option(self) -> str:
        """Maneja selección de opción 4: Información General con sub-menú"""
        try:
            response = f"""ℹ️ **INFORMACIÓN GENERAL** 🌟

¿Qué información específica te gustaría conocer?

📍 **1. UBICACIÓN** - Dónde nos encontramos y cómo llegar
🏕️ **2. CONCEPTO DEL GLAMPING** - Nuestra filosofía y sitio web
📋 **3. POLÍTICAS** - Normas, mascotas, privacidad y cancelaciones

¿Qué te interesa saber? 😊"""
            
            logger.info("Menú de información general mostrado", 
                       extra={"component": "menu_service", "option": "4", "submenu": True})
            return response
            
        except Exception as e:
            logger.error(f"Error procesando opción información: {e}", 
                        extra={"component": "menu_service", "option": "4"})
            return self._get_emergency_informacion_response()
    
    def handle_ubicacion_info(self) -> str:
        """Maneja información de ubicación específica"""
        try:
            ubicacion_info = ""

            # NUEVA LÓGICA: Intentar RAG primero, fallback robusto después
            if "ubicacion_contacto" in self.qa_chains:
                try:
                    ubicacion_info = self.qa_chains["ubicacion_contacto"].run(
                        "¿Dónde están ubicados exactamente? Dame la dirección completa, coordenadas y cómo llegar"
                    )
                    # Verificar si es una respuesta genérica/vacía
                    if self._is_generic_response(ubicacion_info) or len(ubicacion_info.strip()) < 50:
                        ubicacion_info = ""
                except Exception as rag_error:
                    logger.warning(f"RAG falló para ubicación, usando fallback: {rag_error}")
                    ubicacion_info = ""

            # FALLBACK ROBUSTO: Si RAG falla, usar fallback_service
            if not ubicacion_info:
                try:
                    from services.fallback_service import detect_topic_and_provide_fallback
                    handled, fallback_response, topic = detect_topic_and_provide_fallback("ubicación dirección donde están")
                    if handled and fallback_response:
                        ubicacion_info = fallback_response
                        logger.info("Usando fallback service para ubicación")
                    else:
                        # Fallback de emergencia
                        ubicacion_info = self._get_emergency_ubicacion_response()
                except Exception as fallback_error:
                    logger.error(f"Error en fallback service: {fallback_error}")
                    ubicacion_info = self._get_emergency_ubicacion_response()
            
            response = f"""📍 **UBICACIÓN Y CÓMO LLEGAR** 🗺️

{ubicacion_info}

🔍 **¿Necesitas algo más?**
• Escribe "concepto" para conocer sobre nuestro glamping
• Escribe "políticas" para revisar nuestras normas
• Escribe "menú" para volver al menú principal

¿En qué más puedo ayudarte? 😊"""
            
            logger.info("Información de ubicación proporcionada", 
                       extra={"component": "menu_service", "suboption": "ubicacion"})
            return response
            
        except Exception as e:
            logger.error(f"Error obteniendo información de ubicación: {e}", 
                        extra={"component": "menu_service"})
            return self._get_emergency_ubicacion_response()
    
    def handle_concepto_info(self) -> str:
        """Maneja información del concepto del glamping"""
        try:
            concepto_info = ""
            
            # NUEVA LÓGICA: Intentar RAG primero, fallback robusto después
            if "concepto_glamping" in self.qa_chains:
                try:
                    concepto_info = self.qa_chains["concepto_glamping"].run(
                        "¿Cuál es el concepto, filosofía y misión del glamping? Incluye información sobre el sitio web"
                    )
                    # Verificar si es una respuesta genérica/vacía
                    if self._is_generic_response(concepto_info) or len(concepto_info.strip()) < 50:
                        concepto_info = ""
                except Exception as rag_error:
                    logger.warning(f"RAG falló para concepto, usando fallback: {rag_error}")
                    concepto_info = ""

            # También intentar con informacion_general si concepto_glamping no está disponible
            if not concepto_info and "informacion_general" in self.qa_chains:
                try:
                    concepto_info = self.qa_chains["informacion_general"].run(
                        "¿Qué es Glamping Brillo de Luna? Explica el concepto, filosofía y qué hace especial este lugar"
                    )
                    if self._is_generic_response(concepto_info) or len(concepto_info.strip()) < 50:
                        concepto_info = ""
                except Exception as rag_error:
                    logger.warning(f"RAG informacion_general también falló: {rag_error}")
                    concepto_info = ""

            # FALLBACK ROBUSTO: Si RAG falla, usar fallback_service
            if not concepto_info:
                try:
                    from services.fallback_service import detect_topic_and_provide_fallback
                    handled, fallback_response, topic = detect_topic_and_provide_fallback("concepto filosofía que es glamping brillo de luna")
                    if handled and fallback_response:
                        concepto_info = fallback_response
                        logger.info("Usando fallback service para concepto")
                    else:
                        # Fallback de emergencia
                        concepto_info = self._get_emergency_concepto_response()
                except Exception as fallback_error:
                    logger.error(f"Error en fallback service: {fallback_error}")
                    concepto_info = self._get_emergency_concepto_response()
            
            # Agregar link de sitio web
            website_link = "🌐 **Sitio Web:** https://glampingbrillodelaluna.com"
            
            response = f"""🏕️ **CONCEPTO DEL GLAMPING** ✨

{concepto_info}

{website_link}

📱 **Explora más:**
• Visita nuestro sitio web para ver galería completa
• Síguenos en redes sociales
• Conoce testimonios de huéspedes

🔍 **¿Necesitas algo más?**
• Escribe "ubicación" para saber dónde estamos
• Escribe "políticas" para revisar nuestras normas
• Escribe "menú" para volver al menú principal

¿Qué más te gustaría saber? 😊"""
            
            logger.info("Información del concepto proporcionada", 
                       extra={"component": "menu_service", "suboption": "concepto"})
            return response
            
        except Exception as e:
            logger.error(f"Error obteniendo información del concepto: {e}", 
                        extra={"component": "menu_service"})
            return self._get_emergency_concepto_response()
    
    def handle_politicas_info(self) -> str:
        """Maneja información de políticas con sub-menú"""
        try:
            response = f"""📋 **POLÍTICAS GLAMPING BRILLO DE LUNA** 📄

¿Qué política específica te interesa conocer?

🐕 **1. POLÍTICAS DE MASCOTAS** - Normas para animales
🔒 **2. POLÍTICAS DE PRIVACIDAD** - Protección de datos
📅 **3. RESERVAS Y CANCELACIONES** - Términos y condiciones

¿Qué política necesitas revisar? 🤔"""
            
            logger.info("Menú de políticas mostrado", 
                       extra={"component": "menu_service", "suboption": "politicas", "submenu": True})
            return response
            
        except Exception as e:
            logger.error(f"Error mostrando menú de políticas: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema accediendo a las políticas. ¿Podrías intentar de nuevo?"
    
    def handle_politicas_mascotas(self) -> str:
        """Maneja políticas específicas de mascotas"""
        try:
            politicas_info = ""
            
            if "politicas_completas" in self.qa_chains:
                politicas_info = self.qa_chains["politicas_completas"].run(
                    "¿Cuáles son las políticas específicas sobre mascotas y animales?"
                )
            
            if not politicas_info:
                politicas_info = """🐕 **POLÍTICAS DE MASCOTAS**

✅ **Mascotas permitidas con restricciones**
• Se permiten mascotas pequeñas y medianas
• Máximo 2 mascotas por domo
• Deben estar vacunadas y desparasitadas

💰 **Tarifa adicional:** $50.000 COP por mascota/noche

📋 **Normas obligatorias:**
• Mantener mascotas bajo control en todo momento
• No dejar mascotas solas en el domo
• Limpiar excrementos inmediatamente
• Traer certificado de vacunación actualizado
• No permitir mascotas en áreas de comida

⚠️ **Restricciones:**
• No se permiten mascotas agresivas o de razas peligrosas
• Daños causados por mascotas son responsabilidad del huésped"""
            
            response = f"""🐕 **POLÍTICAS DE MASCOTAS** 🐾

{politicas_info}

🔍 **¿Necesitas más información?**
• Escribe "privacidad" para políticas de datos
• Escribe "reservas" para términos de cancelación
• Escribe "políticas" para volver al menú de políticas
• Escribe "menú" para volver al menú principal

¿Te ayudo con algo más? 😊"""
            
            logger.info("Políticas de mascotas proporcionadas", 
                       extra={"component": "menu_service", "politica": "mascotas"})
            return response
            
        except Exception as e:
            logger.error(f"Error obteniendo políticas de mascotas: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema obteniendo las políticas de mascotas. ¿Podrías intentar de nuevo?"
    
    def handle_politicas_privacidad(self) -> str:
        """Maneja políticas de privacidad"""
        try:
            privacidad_info = ""
            
            if "politicas_completas" in self.qa_chains:
                privacidad_info = self.qa_chains["politicas_completas"].run(
                    "¿Cuáles son las políticas de privacidad y protección de datos personales?"
                )
            
            if not privacidad_info:
                privacidad_info = """🔒 **POLÍTICAS DE PRIVACIDAD**

🛡️ **Protección de datos personales**
• Cumplimos con la Ley 1581 de 2012 de Protección de Datos
• Sus datos son protegidos con medidas de seguridad adecuadas
• Solo recopilamos información necesaria para la prestación del servicio

📊 **Uso de su información:**
• Procesamiento de reservas y comunicaciones
• Mejora de nuestros servicios
• Envío de información promocional (opcional)

🔐 **Medidas de seguridad:**
• Sistemas encriptados para transacciones
• Acceso restringido a personal autorizado
• Respaldo seguro de información

✍️ **Sus derechos:**
• Acceso, actualización, rectificación y supresión de datos
• Revocación de autorización en cualquier momento

📧 **Contacto para dudas:**
• Email: glampingbrillodelunaguatavita@gmail.com
• WhatsApp: +57 305 461 4926"""
            
            response = f"""🔒 **POLÍTICAS DE PRIVACIDAD** 🛡️

{privacidad_info}

🔍 **¿Necesitas más información?**
• Escribe "mascotas" para políticas de animales
• Escribe "reservas" para términos de cancelación
• Escribe "políticas" para volver al menú de políticas
• Escribe "menú" para volver al menú principal

¿Tienes alguna otra consulta? 😊"""
            
            logger.info("Políticas de privacidad proporcionadas", 
                       extra={"component": "menu_service", "politica": "privacidad"})
            return response
            
        except Exception as e:
            logger.error(f"Error obteniendo políticas de privacidad: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema obteniendo las políticas de privacidad. ¿Podrías intentar de nuevo?"
    
    def handle_politicas_reservas(self) -> str:
        """Maneja políticas de reservas y cancelaciones"""
        try:
            reservas_info = ""
            
            if "politicas_completas" in self.qa_chains:
                reservas_info = self.qa_chains["politicas_completas"].run(
                    "¿Cuáles son las políticas de reservas, cancelaciones y reembolsos?"
                )
            
            if not reservas_info:
                reservas_info = """📅 **POLÍTICAS DE RESERVAS Y CANCELACIONES**

📋 **Términos de reserva:**
• Reserva mínima: 2 noches en temporada alta, 1 noche en temporada baja
• Check-in: 3:00 PM - Check-out: 12:00 PM
• Pago del 50% para confirmar reserva, saldo al llegar
• Huéspedes máximos según capacidad del domo

🔄 **Política de cancelaciones:**
• Cancelación gratuita hasta 7 días antes de la llegada
• Cancelación entre 3-7 días: 25% de penalización
• Cancelación menos de 3 días: 50% de penalización
• No-show: sin reembolso

💰 **Política de reembolsos:**
• Reembolsos por cancelaciones aprobadas en 5-7 días hábiles
• Método de reembolso: mismo utilizado para el pago
• En caso de fuerza mayor se evalúa caso por caso

📞 **Modificaciones:**
• Cambios de fecha sujetos a disponibilidad
• Modificaciones sin costo hasta 48 horas antes
• Cambios de último momento pueden tener costo adicional

⚠️ **Condiciones especiales:**
• Daños al domo o mobiliario serán cobrados aparte
• Ruido excesivo puede resultar en terminación de estadía
• Prohibido fumar dentro de los domos"""
            
            response = f"""📅 **RESERVAS Y CANCELACIONES** 📋

{reservas_info}

🔍 **¿Necesitas más información?**
• Escribe "mascotas" para políticas de animales
• Escribe "privacidad" para protección de datos
• Escribe "políticas" para volver al menú de políticas
• Escribe "menú" para volver al menú principal

¿Hay algo más en lo que pueda ayudarte? 😊"""
            
            logger.info("Políticas de reservas proporcionadas", 
                       extra={"component": "menu_service", "politica": "reservas"})
            return response
            
        except Exception as e:
            logger.error(f"Error obteniendo políticas de reservas: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema obteniendo las políticas de reservas. ¿Podrías intentar de nuevo?"
    
    def handle_all_politicas_unified(self) -> str:
        """
        Proporciona TODAS las políticas en un solo mensaje unificado
        """
        try:
            # Obtener contenido de cada política individual
            mascotas_content = self._get_politicas_mascotas_content()
            privacidad_content = self._get_politicas_privacidad_content() 
            reservas_content = self._get_politicas_reservas_content()
            
            response = f"""📋 **POLÍTICAS GLAMPING BRILLO DE LUNA** 📄

════════════════════════════════════

{mascotas_content}

═══════════════════════════════════════

{privacidad_content}

═══════════════════════════════════════

{reservas_content}

═══════════════════════════════════════

📞 **¿TIENES DUDAS SOBRE NUESTRAS POLÍTICAS?**

• WhatsApp: +57 305 461 4926
• Email: glampingbrillodelunaguatavita@gmail.com
• Horario: Lunes a Domingo, 8:00 AM - 9:00 PM

💬 **¿En qué más puedo ayudarte?**"""
            
            logger.info("Todas las políticas proporcionadas en mensaje unificado", 
                       extra={"component": "menu_service", "action": "all_politicas"})
            return response
            
        except Exception as e:
            logger.error(f"Error obteniendo políticas unificadas: {e}", 
                        extra={"component": "menu_service"})
            return """📋 **POLÍTICAS GLAMPING BRILLO DE LUNA** 📄

Lo sentimos, hay un problema técnico accediendo a nuestras políticas.

📞 **Para información sobre políticas, contáctanos:**
• WhatsApp: +57 305 461 4926
• Email: glampingbrillodelunaguatavita@gmail.com

¿En qué más puedo ayudarte? 😊"""
    
    def _get_politicas_mascotas_content(self) -> str:
        """Obtiene solo el contenido de políticas de mascotas"""
        try:
            if "politicas_completas" in self.qa_chains:
                politicas_info = self.qa_chains["politicas_completas"].run(
                    "¿Cuáles son las políticas específicas sobre mascotas y animales?"
                )
                if politicas_info:
                    return politicas_info
        except:
            pass
        
        return """🐕 **POLÍTICAS DE MASCOTAS**

✅ **Mascotas permitidas con restricciones**
• Se permiten mascotas pequeñas y medianas
• Máximo 2 mascotas por domo
• Deben estar vacunadas y desparasitadas

💰 **Tarifa adicional:** $50.000 COP por mascota/noche

📋 **Normas obligatorias:**
• Mantener mascotas bajo control en todo momento
• No dejar mascotas solas en el domo
• Limpiar excrementos inmediatamente
• Traer certificado de vacunación actualizado
• No permitir mascotas en áreas de comida

⚠️ **Restricciones:**
• No se permiten mascotas agresivas o de razas peligrosas
• Daños causados por mascotas son responsabilidad del huésped"""
    
    def _get_politicas_privacidad_content(self) -> str:
        """Obtiene solo el contenido de políticas de privacidad"""
        try:
            if "politicas_completas" in self.qa_chains:
                privacidad_info = self.qa_chains["politicas_completas"].run(
                    "¿Cuáles son las políticas de privacidad y protección de datos personales?"
                )
                if privacidad_info:
                    return privacidad_info
        except:
            pass
        
        return """🔒 **POLÍTICAS DE PRIVACIDAD**

🛡️ **Protección de datos personales**
• Cumplimos con la Ley 1581 de 2012 de Protección de Datos
• Sus datos son protegidos con medidas de seguridad adecuadas
• Solo recopilamos información necesaria para la prestación del servicio

📊 **Uso de su información:**
• Procesamiento de reservas y comunicaciones
• Mejora de nuestros servicios
• Envío de información promocional (opcional)

🔐 **Medidas de seguridad:**
• Sistemas encriptados para transacciones
• Acceso restringido a personal autorizado
• Respaldo seguro de información

✍️ **Sus derechos:**
• Acceso, actualización, rectificación y supresión de datos
• Revocación de autorización en cualquier momento"""
    
    def _get_politicas_reservas_content(self) -> str:
        """Obtiene solo el contenido de políticas de reservas"""
        try:
            if "politicas_completas" in self.qa_chains:
                reservas_info = self.qa_chains["politicas_completas"].run(
                    "¿Cuáles son las políticas de reservas, cancelaciones y reembolsos?"
                )
                if reservas_info:
                    return reservas_info
        except:
            pass
        
        return """📅 **POLÍTICAS DE RESERVAS Y CANCELACIONES**

📋 **Términos de reserva:**
• Reserva mínima: 2 noches en temporada alta, 1 noche en temporada baja
• Check-in: 3:00 PM - Check-out: 12:00 PM
• Pago del 50% para confirmar reserva, saldo al llegar
• Huéspedes máximos según capacidad del domo

🔄 **Política de cancelaciones:**
• Cancelación gratuita hasta 7 días antes de la llegada
• Cancelación entre 3-7 días: 25% de penalización
• Cancelación menos de 3 días: 50% de penalización
• No-show: sin reembolso

💰 **Política de reembolsos:**
• Reembolsos por cancelaciones aprobadas en 5-7 días hábiles
• Método de reembolso: mismo utilizado para el pago
• En caso de fuerza mayor se evalúa caso por caso

📞 **Modificaciones:**
• Cambios de fecha sujetos a disponibilidad
• Modificaciones sin costo hasta 48 horas antes
• Cambios de último momento pueden tener costo adicional

⚠️ **Condiciones especiales:**
• Daños al domo o mobiliario serán cobrados aparte
• Ruido excesivo puede resultar en terminación de estadía
• Prohibido fumar dentro de los domos"""
    
    def handle_informacion_general_suboptions(self, user_message: str, user_state: dict) -> str:
        
        try:
            # Verificar si están en el flujo de políticas específicas
            if user_state.get("waiting_for_politicas_suboption", False):
                return self._handle_politicas_suboptions(user_message, user_state)
            
            # Detectar sub-opción de información general
            detected = False
            suboption = ""
            
            if self.validation_service:
                try:
                    detected, suboption, description = self.validation_service.detect_informacion_general_suboption(user_message)
                except Exception as e:
                    logger.warning(f"Error en validation_service, usando detección manual: {e}")
                    detected = False
            
            # Fallback: detección manual robusta
            if not detected:
                message_lower = user_message.lower().strip()
                if any(word in message_lower for word in ["ubicacion", "ubicación", "donde", "dónde", "lugar", "dirección", "direccion"]):
                    detected = True
                    suboption = "ubicacion"
                elif any(word in message_lower for word in ["concepto", "filosofía", "filosofia", "que es", "qué es", "sobre el glamping"]):
                    detected = True
                    suboption = "concepto"
                elif any(word in message_lower for word in ["politicas", "políticas", "normas", "reglas", "cancellation", "cancelacion"]):
                    detected = True
                    suboption = "politicas"
            
            if detected:
                logger.info(f"Sub-opción de información general detectada: {suboption}", 
                           extra={"component": "menu_service", "suboption": suboption})
                
                # Resetear estado de información general
                user_state["waiting_for_informacion_suboption"] = False
                
                if suboption == "ubicacion":
                    user_state["current_flow"] = "none"
                    return self.handle_ubicacion_info()
                elif suboption == "concepto":
                    user_state["current_flow"] = "none"
                    return self.handle_concepto_info()
                elif suboption == "politicas":
                    # Proporcionar TODAS las políticas en un solo mensaje
                    user_state["current_flow"] = "none"
                    return self.handle_all_politicas_unified()
                
            # Verificar si es selección numérica (1, 2, 3)
            message_clean = user_message.strip().lower()
            if message_clean in ["1", "uno", "primero", "primera"]:
                user_state["waiting_for_informacion_suboption"] = False
                user_state["current_flow"] = "none"
                return self.handle_ubicacion_info()
            elif message_clean in ["2", "dos", "segundo", "segunda"]:
                user_state["waiting_for_informacion_suboption"] = False
                user_state["current_flow"] = "none"
                return self.handle_concepto_info()
            elif message_clean in ["3", "tres", "tercero", "tercera"]:
                user_state["waiting_for_informacion_suboption"] = False
                user_state["current_flow"] = "none"
                return self.handle_all_politicas_unified()
            
            # Si no se detectó nada específico, mostrar opciones nuevamente
            return """❓ **No entendí tu selección**

Por favor elige una de estas opciones:

📍 **1. UBICACIÓN** - Escribe "ubicación" o "1"
🏕️ **2. CONCEPTO DEL GLAMPING** - Escribe "concepto" o "2"  
📋 **3. POLÍTICAS** - Escribe "políticas" o "3"

O escribe "menú" para volver al menú principal 😊"""
            
        except Exception as e:
            logger.error(f"Error manejando sub-opciones de información general: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema procesando tu selección. ¿Podrías intentar de nuevo?"
    
    def _handle_politicas_suboptions(self, user_message: str, user_state: dict) -> str:
       
        try:
            detected = False
            suboption = None
            
            # Implementar detección manual robusta (fallback cuando validation_service es None)
            if self.validation_service:
                try:
                    detected, suboption, description = self.validation_service.detect_politicas_suboption(user_message)
                except:
                    detected = False
            
            # Fallback manual si validation_service no está disponible o falla
            if not detected:
                message_lower = user_message.lower().strip()
                
                # Detectar políticas de mascotas
                if any(word in message_lower for word in ["mascota", "mascotas", "animal", "animales", "perro", "perros", "gato", "gatos", "pets"]):
                    detected = True
                    suboption = "mascotas"
                
                # Detectar políticas de privacidad
                elif any(word in message_lower for word in ["privacidad", "datos", "información", "informacion", "personal", "protección", "proteccion"]):
                    detected = True
                    suboption = "privacidad"
                
                # Detectar políticas de reservas
                elif any(word in message_lower for word in ["reserva", "reservas", "cancelación", "cancelacion", "términos", "terminos", "condiciones"]):
                    detected = True
                    suboption = "reservas"
            
            if detected:
                logger.info(f"Sub-opción de políticas detectada: {suboption}", 
                           extra={"component": "menu_service", "politica_suboption": suboption})
                
                # Resetear estado de políticas
                user_state["waiting_for_politicas_suboption"] = False
                user_state["current_flow"] = "none"
                
                if suboption == "mascotas":
                    return self.handle_politicas_mascotas()
                elif suboption == "privacidad":
                    return self.handle_politicas_privacidad()
                elif suboption == "reservas":
                    return self.handle_politicas_reservas()
            
            # Verificar si es selección numérica (1, 2, 3)
            message_clean = user_message.strip().lower()
            if message_clean in ["1", "uno", "primero", "primera"]:
                user_state["waiting_for_politicas_suboption"] = False
                user_state["current_flow"] = "none"
                return self.handle_politicas_mascotas()
            elif message_clean in ["2", "dos", "segundo", "segunda"]:
                user_state["waiting_for_politicas_suboption"] = False
                user_state["current_flow"] = "none"
                return self.handle_politicas_privacidad()
            elif message_clean in ["3", "tres", "tercero", "tercera"]:
                user_state["waiting_for_politicas_suboption"] = False
                user_state["current_flow"] = "none"
                return self.handle_politicas_reservas()
            
            # Si no se detectó nada específico, mostrar opciones de políticas nuevamente
            return """❓ **No entendí qué política necesitas**

Por favor elige una de estas opciones:

🐕 **1. POLÍTICAS DE MASCOTAS** - Escribe "mascotas" o "1"
🔒 **2. POLÍTICAS DE PRIVACIDAD** - Escribe "privacidad" o "2"
📅 **3. RESERVAS Y CANCELACIONES** - Escribe "reservas" o "3"

O escribe "menú" para volver al menú principal 😊"""
            
        except Exception as e:
            logger.error(f"Error manejando sub-opciones de políticas: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema procesando tu consulta sobre políticas. ¿Podrías intentar de nuevo?"
    
    def is_menu_selection(self, message: str) -> bool:
       
        return self.validation_service.is_menu_selection(message)
    
    def get_welcome_menu(self) -> str:
        
        from services.rag_tools_service import get_rag_tools_service
        
        # Crear instancia temporal para obtener el menú
        try:
            temp_rag_service = get_rag_tools_service(self.qa_chains)
            return temp_rag_service.menu_principal_func()
        except Exception as e:
            logger.error(f"Error obteniendo menú de bienvenida: {e}", 
                        extra={"component": "menu_service"})
            return """🏕️ **¡BIENVENIDO A GLAMPING BRILLO DE LUNA!** 🌙✨

¡Hola! 👋 Mi nombre es *María* y soy tu asistente virtual especializada. 

*Selecciona una opción:*
1️⃣ **DOMOS** - Información y precios
2️⃣ **SERVICIOS** - Todo lo que ofrecemos
3️⃣ **DISPONIBILIDAD** - Fechas y reservas  
4️⃣ **INFORMACIÓN GENERAL** - Ubicación y políticas

¿En qué te puedo ayudar? 😊"""
    
    def handle_domos_followup(self, user_message: str, user_state: dict) -> str:
        
        # NUEVA LÓGICA: Detectar si quiere salir del flujo de domos
        if self._detect_flow_exit_intent(user_message, "domos_followup"):
            # Resetear estado y generar respuesta inteligente
            user_state["waiting_for_domos_followup"] = False
            user_state["current_flow"] = "none"
            logger.info("Usuario detectó intención de salir del flujo de domos followup")
            return self._generate_intelligent_flow_exit_response(user_message, "domos_followup")
        
        # Verificar si es una respuesta sí/no
        yes_no_response = self.validation_service.is_yes_no_response(user_message)
        
        if yes_no_response is True:
            # Usuario quiere más información
            user_state["current_flow"] = "domos_specific"
            user_state["waiting_for_domos_followup"] = False
            user_state["waiting_for_domos_specific"] = True
            
            return """💡 **¡Perfecto! ¿Sobre qué te gustaría saber más?**

🔍 Puedes preguntarme sobre:

🏠 **Domos específicos:**
• "Quiero saber sobre Antares"
• "Información del domo Polaris"
• "Características de Sirius"
• "Detalles del domo Centaury"

📋 **Detalles específicos:**
• "Características detalladas"
• "Qué servicios incluye"
• "Capacidad de personas"
• "Ubicación de los domos"

📸 **Ver imágenes:**
• "Quiero ver fotos"
• "Mostrar galería"

💬 **Escribe lo que te interese y te daré toda la información específica** ✨"""
            
        elif yes_no_response is False:
            # Usuario no quiere más información
            user_state["current_flow"] = "none"
            user_state["waiting_for_domos_followup"] = False
            
            return """😊 **¡Claro! ¿En qué más puedo ayudarte?**

🏕️ Puedes preguntarme sobre:
• **Servicios** - Todo lo que ofrecemos
• **Disponibilidad** - Fechas libres y reservas
• **Información general** - Ubicación, políticas
• **Reservar** - Proceso de reserva directo

💬 También puedes hacer cualquier pregunta específica sobre Brillo de Luna. ¡Estoy aquí para ayudarte! 🌟"""
        
        else:
            # No detectó sí/no claramente, pedir clarificación
            return """🤔 **No estoy segura si quieres más información específica sobre los domos.**

💬 Por favor responde:
• **"Sí"** si quieres saber algo más específico sobre nuestros domos
• **"No"** si necesitas ayuda con otra cosa

¡Estoy aquí para ayudarte! 😊"""
    
    def handle_domos_specific_request(self, user_message: str, user_state: dict) -> str:
     
        request_type = self.validation_service.detect_domo_specific_request(user_message)
        
        try:
            if request_type == 'domo_especifico':
                return self._handle_specific_domo_query(user_message)
            elif request_type == 'caracteristicas':
                return self._handle_characteristics_query()
            elif request_type == 'precios':
                return self._handle_prices_query()
            elif request_type == 'imagenes':
                return self._handle_images_query()
            elif request_type == 'servicios_incluidos':
                return self._handle_included_services_query()
            elif request_type == 'capacidad':
                return self._handle_capacity_query()
            elif request_type == 'ubicacion':
                return self._handle_location_query()
            else:
                # Usar IA para respuesta general
                return self._handle_general_domo_query(user_message)
                
        except Exception as e:
            logger.error(f"Error en consulta específica de domos: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema procesando tu consulta específica. ¿Podrías reformular tu pregunta?"
        
        finally:
            # Resetear estado después de responder
            user_state["current_flow"] = "none"
            user_state["waiting_for_domos_specific"] = False
    
    def _handle_specific_domo_query(self, user_message: str) -> str:
        """Maneja consultas sobre domos específicos"""
        message_clean = user_message.lower()
        
        if "antares" in message_clean:
            domo_name = "Antares"
        elif "polaris" in message_clean:
            domo_name = "Polaris"
        elif "sirius" in message_clean:
            domo_name = "Sirius"
        elif "centaury" in message_clean:
            domo_name = "Centaury"
        else:
            domo_name = "domos"
        
        if "domos_info" in self.qa_chains:
            specific_info = self.qa_chains["domos_info"].run(
                f"Información específica sobre el domo {domo_name}, sus características y detalles únicos"
            )
        else:
            specific_info = f"Información sobre el domo {domo_name} no disponible en este momento."
        
        return f"""🏠 **INFORMACIÓN ESPECÍFICA - DOMO {domo_name.upper()}** ⭐

{specific_info}

💡 **¿Necesitas algo más?**
• Escribe "reservar" para hacer una reserva
• Escribe "disponibilidad" para ver fechas
• Escribe "fotos" para ver imágenes
• O pregúntame cualquier otra cosa sobre Brillo de Luna 😊"""
    
    def _handle_characteristics_query(self) -> str:
        """Maneja consultas sobre características"""
        if "domos_info" in self.qa_chains:
            characteristics = self.qa_chains["domos_info"].run(
                "Características detalladas de todos los domos: diseño, materiales, comodidades, diferencias entre cada uno"
            )
        else:
            characteristics = "Información de características no disponible."
        
        return f"""📋 **CARACTERÍSTICAS DETALLADAS DE NUESTROS DOMOS** 🌟

{characteristics}

🏕️ **Explora nuestros domos:**
• Escribe "Antares", "Polaris", "Sirius" o "Centaury" para información específica
• O pregúntame sobre disponibilidad, precios o reservas 😊"""
    
    def _handle_prices_query(self) -> str:
        """Maneja consultas sobre precios"""
        if "domos_precios" in self.qa_chains:
            prices = self.qa_chains["domos_precios"].run(
                "Precios detallados de todos los domos, qué incluye cada tarifa, temporadas, descuentos"
            )
        else:
            prices = "Información de precios no disponible."
        
        return f"""💰 **PRECIOS DETALLADOS DE NUESTROS DOMOS** 💳

{prices}

📅 **Para consultar disponibilidad:**
• Escribe "disponibilidad" seguido de tu fecha
• Ejemplo: "disponibilidad 15 diciembre"
• Escribe "disponibilidad" 
• O dime las fechas que te interesan
• También puedo ayudarte con el proceso de reserva 😊"""
    
    def _handle_images_query(self) -> str:
        """Maneja consultas sobre imágenes"""
        try:
            from services.rag_tools_service import get_rag_tools_service
            temp_rag_service = get_rag_tools_service(self.qa_chains)
            return temp_rag_service.links_imagenes_func()
        except:
            return """📸 **IMÁGENES DE NUESTROS DOMOS** 🌟

Puedes ver todas las fotos en nuestros enlaces oficiales:

🔗 **Galería de domos**: https://www.glampingbrillodeluna.com/domos
🔗 **Página web**: https://www.glampingbrillodeluna.com

¡Allí encontrarás imágenes de todos nuestros domos geodésicos! 📱✨"""
    
    def _handle_included_services_query(self) -> str:
        """Maneja consultas sobre servicios incluidos"""
        if "servicios_incluidos" in self.qa_chains:
            services = self.qa_chains["servicios_incluidos"].run(
                "Qué servicios específicos están incluidos en la estadía en los domos"
            )
        else:
            services = "Información de servicios incluidos no disponible."
        
        return f"""🛎️ **SERVICIOS INCLUIDOS EN TU ESTADÍA** ✨

{services}

🎯 **Servicios adicionales disponibles:**
• Escribe "actividades" para servicios extra
• Escribe "reservar" para hacer una reserva
• O pregúntame cualquier otra cosa 😊"""
    
    def _handle_capacity_query(self) -> str:
        """Maneja consultas sobre capacidad"""
        if "domos_info" in self.qa_chains:
            capacity = self.qa_chains["domos_info"].run(
                "Capacidad máxima de personas en cada domo, distribución de camas, recomendaciones"
            )
        else:
            capacity = "Información de capacidad no disponible."
        
        return f"""👥 **CAPACIDAD DE NUESTROS DOMOS** 🏠

{capacity}

📅 **Para verificar disponibilidad:**
• Escribe "disponibilidad" con tu fecha preferida
• Ejemplo: "disponibilidad 20 enero"
• Escribe "disponibilidad" y te ayudo
• O dime cuántas personas son y las fechas que te interesan 😊"""
    
    def _handle_location_query(self) -> str:
        """Maneja consultas sobre ubicación"""
        if "ubicacion_contacto" in self.qa_chains:
            location = self.qa_chains["ubicacion_contacto"].run(
                "Ubicación específica de los domos dentro del glamping, vistas, accesos"
            )
        else:
            location = "Información de ubicación no disponible."
        
        return f"""📍 **UBICACIÓN DE NUESTROS DOMOS** 🗺️

{location}

🚗 **¿Necesitas información sobre cómo llegar?**
• Puedo darte indicaciones detalladas
• Información sobre transporte
• O cualquier otra consulta sobre Brillo de Luna 😊"""
    
    def _handle_general_domo_query(self, user_message: str) -> str:
        """Maneja consultas generales usando IA"""
        if "domos_info" in self.qa_chains:
            response = self.qa_chains["domos_info"].run(user_message)
        else:
            response = "No pude procesar tu consulta específica en este momento."
        
        return f"""{response}

💡 **¿Necesitas más información específica?**
• Pregúntame sobre precios, características, o domos específicos
• Escribe "disponibilidad" para consultar fechas
• Escribe "reservar" para hacer una reserva 😊"""
    
    def handle_servicios_followup(self, user_message: str, user_state: dict) -> str:
    
        try:
            logger.info(f"Procesando followup servicios: '{user_message}'", 
                       extra={"component": "menu_service"})
            
            # NUEVA LÓGICA: Detectar si quiere salir del flujo de servicios
            if self._detect_flow_exit_intent(user_message, "servicios_followup"):
                # Resetear estado y generar respuesta inteligente
                user_state["waiting_for_servicios_followup"] = False
                user_state["current_flow"] = "none"
                logger.info("Usuario detectó intención de salir del flujo de servicios followup")
                return self._generate_intelligent_flow_exit_response(user_message, "servicios_followup")
            
            # Verificar si es una respuesta sí/no con logging adicional
            yes_no_response = self.validation_service.is_yes_no_response(user_message)
            logger.info(f"Resultado yes_no_response: {yes_no_response}", 
                       extra={"component": "menu_service"})
            
            if yes_no_response is True:
                # Usuario quiere más información
                user_state["current_flow"] = "servicios_specific"
                user_state["waiting_for_servicios_followup"] = False
                user_state["waiting_for_servicios_specific"] = True
                
                logger.info("Usuario confirmó interés en más información de servicios", 
                           extra={"component": "menu_service"})
                
                return """💡 **¡Perfecto! ¿Sobre qué servicios te gustaría saber más?**

🔍 Puedes preguntarme sobre:

🛎️ **SERVICIOS INCLUIDOS:**
• "Servicios incluidos" o "internos"
• "¿Qué incluye mi estadía?"
• "Servicios básicos"

🎯 **SERVICIOS EXTERNOS/ADICIONALES:**
• "Servicios externos" o "adicionales"
• "Actividades extras"
• "¿Qué más puedo contratar?"

📋 **Información completa:**
• "Ambos" o "todos los servicios"
• "Información completa"

💰 **Precios:**
• "Precios de servicios"
• "¿Cuánto cuestan?"

🔧 **Características:**
• "Características detalladas"
• "Especificaciones"

💬 **Escribe lo que te interese y te daré toda la información específica** ✨"""
            
            elif yes_no_response is False:
                # Usuario no quiere más información
                user_state["current_flow"] = "none"
                user_state["waiting_for_servicios_followup"] = False
                
                return """😊 **¡Claro! ¿En qué más puedo ayudarte?**

🏕️ Puedes preguntarme sobre:
• **Domos** - Información y precios de alojamiento
• **Disponibilidad** - Fechas libres y reservas
• **Información general** - Ubicación, políticas
• **Reservar** - Proceso de reserva directo

💬 También puedes hacer cualquier pregunta específica sobre Brillo de Luna. ¡Estoy aquí para ayudarte! 🌟"""
            
            else:
                # No detectó sí/no claramente, pedir clarificación
                return """🤔 **No estoy segura si quieres más información específica sobre los servicios.**

💬 Por favor responde:
• **"Sí"** si quieres saber algo más específico sobre nuestros servicios
• **"No"** si necesitas ayuda con otra cosa

¡Estoy aquí para ayudarte! 😊"""
        
        except Exception as e:
            logger.error(f"Error en handle_servicios_followup: {e}", 
                        extra={"component": "menu_service"})
            # Resetear estado en caso de error
            user_state["current_flow"] = "none" 
            user_state["waiting_for_servicios_followup"] = False
            user_state["waiting_for_servicios_specific"] = False
            
            return """🔧 **Hubo un problema procesando tu respuesta.**

😊 **¡Pero estoy aquí para ayudarte!** 
  
🏕️ Puedes preguntarme sobre:
• **Domos** - Información y precios de alojamiento
• **Servicios** - Lo que incluye tu estadía  
• **Disponibilidad** - Fechas libres y reservas
• **Reservar** - Proceso de reserva directo

💬 **¿En qué más puedo ayudarte?** 🌟"""
    
    def handle_servicios_specific_request(self, user_message: str, user_state: dict) -> str:
        
        request_type = self.validation_service.detect_servicios_specific_request(user_message)
        
        try:
            if request_type == 'servicios_incluidos':
                return self._handle_servicios_incluidos_query()
            elif request_type == 'servicios_externos':
                return self._handle_servicios_externos_query()
            elif request_type == 'todos_servicios':
                return self._handle_todos_servicios_query()
            elif request_type == 'precios_servicios':
                return self._handle_precios_servicios_query()
            elif request_type == 'caracteristicas_servicios':
                return self._handle_caracteristicas_servicios_query()
            elif request_type == 'reservar_servicios':
                return self._handle_reservar_servicios_query()
            else:
                # Usar IA para respuesta general
                return self._handle_general_servicios_query(user_message)
                
        except Exception as e:
            logger.error(f"Error en consulta específica de servicios: {e}", 
                        extra={"component": "menu_service"})
            return "Tuve un problema procesando tu consulta específica. ¿Podrías reformular tu pregunta?"
        
        finally:
            # Resetear estado después de responder
            user_state["current_flow"] = "none"
            user_state["waiting_for_servicios_specific"] = False
    
    def _handle_servicios_incluidos_query(self) -> str:
        """Maneja consultas sobre servicios incluidos"""
        if "servicios_incluidos" in self.qa_chains:
            included_services = self.qa_chains["servicios_incluidos"].run(
                "Detalles específicos de todos los servicios incluidos en la estadía, qué está cubierto exactamente"
            )
        else:
            included_services = "Información de servicios incluidos no disponible."
        
        return f"""🛎️ **SERVICIOS INCLUIDOS EN TU ESTADÍA** ✨

{included_services}

🎯 **Servicios destacados:**
• Escribe "servicios externos" para ver actividades adicionales
• Escribe "reservar" para hacer una reserva
• O pregúntame cualquier otra cosa sobre Brillo de Luna 😊"""
    
    def _handle_servicios_externos_query(self) -> str:
        """Maneja consultas sobre servicios externos/adicionales"""
        if "actividades_adicionales" in self.qa_chains:
            external_services = self.qa_chains["actividades_adicionales"].run(
                "Actividades y servicios adicionales disponibles, experiencias únicas, precios y cómo contratarlos"
            )
        else:
            external_services = "Información de servicios externos no disponible."
        
        return f"""🎯 **SERVICIOS EXTERNOS Y ACTIVIDADES ADICIONALES** 🌟

{external_services}

📝 **Para reservar actividades:**
• Escribe el nombre de la actividad que te interesa
• Ejemplo: "yoga" o "senderismo"
• Escribe "reservar" para incluir servicios en tu estadía
• Escribe "precios" para más detalles de tarifas
• O pregúntame sobre disponibilidad y otros servicios 😊"""
    
    def _handle_todos_servicios_query(self) -> str:
        """Maneja consultas sobre todos los servicios"""
        included_info = ""
        external_info = ""
        
        if "servicios_incluidos" in self.qa_chains:
            included_info = self.qa_chains["servicios_incluidos"].run(
                "Servicios incluidos completos"
            )
        
        if "actividades_adicionales" in self.qa_chains:
            external_info = self.qa_chains["actividades_adicionales"].run(
                "Servicios externos y actividades adicionales completos"
            )
        
        return f"""🎯 **INFORMACIÓN COMPLETA DE SERVICIOS** ✨

🛎️ **SERVICIOS INCLUIDOS:**
{included_info}

🌟 **SERVICIOS EXTERNOS Y ACTIVIDADES:**
{external_info}

💡 **¿Necesitas más detalles?**
• Escribe "precios" para tarifas específicas
• Escribe "reservar" para hacer una reserva
• O pregúntame sobre disponibilidad 😊"""
    
    def _handle_precios_servicios_query(self) -> str:
        """Maneja consultas sobre precios de servicios"""
        if "actividades_adicionales" in self.qa_chains:
            prices = self.qa_chains["actividades_adicionales"].run(
                "Precios específicos de todas las actividades y servicios adicionales, tarifas y formas de pago"
            )
        else:
            prices = "Información de precios no disponible."
        
        return f"""💰 **PRECIOS DE SERVICIOS ADICIONALES** 💳

{prices}

📅 **Para incluir servicios:**
• Escribe "servicios" para ver opciones completas
• Menciona el servicio específico que te interesa
• Escribe "reservar" para hacer una reserva completa
• Escribe "disponibilidad" para ver fechas
• O pregúntame sobre domos y alojamiento 😊"""
    
    def _handle_caracteristicas_servicios_query(self) -> str:
        """Maneja consultas sobre características de servicios"""
        if "actividades_adicionales" in self.qa_chains:
            characteristics = self.qa_chains["actividades_adicionales"].run(
                "Características detalladas de servicios: duración, horarios, incluye, requisitos, especificaciones"
            )
        else:
            characteristics = "Información de características no disponible."
        
        return f"""🔧 **CARACTERÍSTICAS DETALLADAS DE SERVICIOS** 📋

{characteristics}

💡 **Servicios populares:**
• Escribe el nombre del servicio para más detalles
• Escribe "precios" para información de tarifas
• O pregúntame sobre reservas y disponibilidad 😊"""
    
    def _handle_reservar_servicios_query(self) -> str:
        """Maneja consultas sobre reservar servicios"""
        return """📝 **RESERVAR SERVICIOS** ✨

¡Perfecto! Puedes reservar servicios de varias formas:

🎯 **Durante tu reserva de domo:**
• Menciona qué servicios adicionales te interesan
• Los incluiremos en tu reserva completa

📅 **Para reservar ahora:**
• Escribe "reservar" para iniciar el proceso
• Te ayudo a seleccionar domo + servicios

💬 **Para más información:**
• Escribe "disponibilidad" para ver fechas
• Pregúntame sobre servicios específicos

📞 **Para iniciar tu reserva:**
• Escribe "reservar" para comenzar el proceso
• Escribe "contacto" para hablar con un asesor 😊"""
    
    def _handle_general_servicios_query(self, user_message: str) -> str:
        """Maneja consultas generales usando IA"""
        if "servicios_incluidos" in self.qa_chains:
            response = self.qa_chains["servicios_incluidos"].run(user_message)
        elif "actividades_adicionales" in self.qa_chains:
            response = self.qa_chains["actividades_adicionales"].run(user_message)
        else:
            response = "No pude procesar tu consulta específica en este momento."
        
        return f"""{response}

💡 **¿Necesitas más información específica?**
• Pregúntame sobre servicios incluidos o externos
• Escribe "precios" para consultar tarifas
• Escribe "reservar" para hacer una reserva 😊"""
    
    def _handle_actividades_option(self) -> str:
        """Maneja selección de opción 5: Actividades Adicionales"""
        try:
            actividades_info = ""
            
            if "actividades_adicionales" in self.qa_chains and self.qa_chains["actividades_adicionales"]:
                actividades_info = self.qa_chains["actividades_adicionales"].run(
                    "¿Qué actividades adicionales y experiencias únicas ofrecen?"
                )
            else:
                actividades_info = """🎯 **ACTIVIDADES Y EXPERIENCIAS ÚNICAS:**

🌟 **EXPERIENCIAS DE NATURALEZA:**
• Senderismo guiado por senderos ecológicos
• Observación de aves nativas
• Tours nocturnos de avistamiento de estrellas
• Caminatas al amanecer

🏃 **ACTIVIDADES DEPORTIVAS:**
• Ciclomontañismo en rutas naturales
• Rappel y escalada en roca
• Canopy y tirolesa
• Actividades acuáticas

🧘 **BIENESTAR Y RELAJACIÓN:**
• Sesiones de yoga al aire libre
• Masajes terapéuticos en spa
• Meditación guiada
• Terapias de relajación

🍳 **EXPERIENCIAS GASTRONÓMICAS:**
• Clases de cocina tradicional
• Cenas románticas bajo las estrellas
• Fogatas con asados"""
            
            response_message = f"""🎯 **ACTIVIDADES ADICIONALES** ✨

{actividades_info}

💰 **PRECIOS Y RESERVAS:**
• Precios varían según temporada y duración
• Reservas con 24 horas de anticipación
• Descuentos para huéspedes del glamping

📝 **Actividades destacadas:**
• Pregúntame sobre horarios y disponibilidad
• Puedo ayudarte a incluirlas en tu reserva
• También manejo información sobre precios

💬 ¿Qué actividad te llama más la atención? 😊"""
            
            logger.info("Información de actividades adicionales proporcionada", 
                       extra={"component": "menu_service", "option": "5"})
            return response_message
            
        except Exception as e:
            logger.error(f"Error procesando opción actividades: {e}", 
                        extra={"component": "menu_service", "option": "5"})
            return "Tuve un problema accediendo a la información de actividades. ¿Podrías intentar de nuevo?"
    
    def _handle_politicas_option(self) -> str:
        """Maneja selección de opción 6: Políticas con fallback robusto"""
        try:
            # Usar fallback robusto para políticas
            politicas_info = self._get_politicas_with_fallback()
            
            response_message = f"""📋 **POLÍTICAS DEL GLAMPING** 📄

{politicas_info}

🔍 **INFORMACIÓN ADICIONAL:**
• Políticas de privacidad y protección de datos
• Términos y condiciones detallados
• Procedimientos de seguridad
• Normas de convivencia

📞 **¿Tienes dudas específicas?**
• Pregúntame sobre cualquier política en particular
• Puedo explicarte los términos de cancelación
• También manejo información sobre seguros

💬 ¿Hay alguna política específica que te interese conocer? 😊"""
            
            logger.info("Información de políticas proporcionada", 
                       extra={"component": "menu_service", "option": "6"})
            return response_message
            
        except Exception as e:
            logger.error(f"Error procesando opción políticas: {e}", 
                        extra={"component": "menu_service", "option": "6"})
            return self._get_emergency_politicas_response()
    
    def _handle_imagenes_option(self) -> str:
        """Maneja selección de opción 7: Ver Imágenes con fallback robusto"""
        try:
            # Usar fallback robusto para imágenes
            imagenes_info = self._get_imagenes_with_fallback()
            
            response_message = f"""📸 **GALERÍA DE IMÁGENES** 🌟

{imagenes_info}

🎯 **¿QUÉ PUEDES VER?**
• Todos nuestros domos geodésicos
• Vistas panorámicas del entorno
• Instalaciones y servicios
• Experiencias de huéspedes anteriores
• Paisajes y naturaleza circundante

📱 **TAMBIÉN DISPONIBLE:**
• Tours virtuales 360°
• Videos de experiencias
• Galería actualizada semanalmente

🔍 **¿Te ayudo con algo más específico?**
• Información sobre los domos que viste
• Consultar disponibilidad para las fechas que te interesan
• Proceso de reserva

💬 ¿Algún domo en particular te llamó la atención? 😊"""
            
            logger.info("Información de galería de imágenes proporcionada", 
                       extra={"component": "menu_service", "option": "7"})
            return response_message
            
        except Exception as e:
            logger.error(f"Error procesando opción imágenes: {e}", 
                        extra={"component": "menu_service", "option": "7"})
            return self._get_emergency_imagenes_response()
    
    def _handle_accesibilidad_option(self) -> str:
        """Maneja selección de opción 8: Accesibilidad con fallback robusto"""
        try:
            # Usar fallback robusto para accesibilidad
            accesibilidad_info = self._get_accesibilidad_with_fallback()
            
            response_message = f"""♿ **INFORMACIÓN DE ACCESIBILIDAD** 🌟

{accesibilidad_info}

💡 **RECOMENDACIONES IMPORTANTES:**
• Contactar antes de la reserva para coordinar
• Especificar necesidades particulares
• Confirmar disponibilidad de domo adaptado
• Solicitar asistencia específica si es necesaria

📞 **COORDINACIÓN PERSONALIZADA:**
• WhatsApp: +57 305 461 4926
• Email: glampingbrillodelunaguatavita@gmail.com
• Llamada telefónica para detalles específicos

🔍 **¿NECESITAS MÁS INFORMACIÓN?**
• Detalles sobre adaptaciones específicas
• Consultar disponibilidad de domos accesibles
• Coordinar servicios de apoyo

💬 ¿Hay alguna necesidad específica que debamos coordinar? 😊"""
            
            logger.info("Información de accesibilidad proporcionada", 
                       extra={"component": "menu_service", "option": "8"})
            return response_message
            
        except Exception as e:
            logger.error(f"Error procesando opción accesibilidad: {e}", 
                        extra={"component": "menu_service", "option": "8"})
            return self._get_emergency_accesibilidad_response()


    def _get_domos_info_with_fallback(self) -> str:
        """
        Obtener información de domos con fallback robusto ante errores de API
        """
        try:
            if "domos_info" in self.qa_chains and self.qa_chains["domos_info"]:
                rag_response = self.qa_chains["domos_info"].run(
                    "¿Qué tipos de domos tienen y cuáles son sus características principales?"
                )
                if rag_response and len(rag_response) > 50:
                    return rag_response
        except Exception as e:
            logger.warning(f"RAG domos_info falló, usando fallback: {e}")
        
        # Fallback con información completa
        return """🏠 **NUESTROS DOMOS TEMÁTICOS:**

🌟 **DOMO ANTARES** (2 personas)
• Jacuzzi privado y malla catamarán
• Vista panorámica a represa de Tominé
• Terraza con parasol
• Dos pisos: sala y cama principal

⭐ **DOMO POLARIS** (2-4 personas)  
• Sofá cama para personas adicionales
• Vista maravillosa a la represa
• Cocineta completamente equipada
• Dos pisos con sala y dormitorio

🌌 **DOMO SIRIUS** (2 personas)
• Un solo piso diseño para parejas
• Vista bella a represa y montaña
• Terraza acogedora
• Nevera y cafetera incluidos

✨ **DOMO CENTAURY** (2 personas)
• Similar a Sirius, un solo piso
• Vista hermosa a represa y montaña
• Terraza relajante
• Nevera y cafetera incluidos"""
    
    def _get_domos_precios_with_fallback(self) -> str:
        """
        Obtener precios de domos con fallback robusto ante errores de API
        """
        try:
            if "domos_precios" in self.qa_chains and self.qa_chains["domos_precios"]:
                rag_response = self.qa_chains["domos_precios"].run(
                    "¿Cuáles son los precios de los domos y qué incluyen?"
                )
                if rag_response and len(rag_response) > 50:
                    return rag_response
        except Exception as e:
            logger.warning(f"RAG domos_precios falló, usando fallback: {e}")
        
        # Fallback con precios actualizados
        return """💰 **TARIFAS 2024:**

🌟 **DOMO ANTARES**: $650.000 COP/noche para pareja
⭐ **DOMO POLARIS**: $550.000 COP/noche para pareja (+$100.000 por persona adicional)
🌌 **DOMO SIRIUS**: $450.000 COP/noche para pareja
✨ **DOMO CENTAURY**: $450.000 COP/noche para pareja

✨ **INCLUYE:**
• Desayuno gourmet continental
• Acceso a todas las instalaciones
• Wifi de alta velocidad
• Parqueadero privado
• Kit de bienvenida"""
    
    def _get_emergency_domos_response(self) -> str:
        """
        Respuesta de emergencia completa cuando todo falla
        """
        return """🏠 **INFORMACIÓN DE NUESTROS DOMOS** 🌟

🌟 **DOMO ANTARES** (2 personas) - $650.000/noche
• Jacuzzi privado y malla catamarán
• Vista panorámica a represa de Tominé
• Terraza con parasol | Dos pisos

⭐ **DOMO POLARIS** (2-4 personas) - $550.000/noche  
• Sofá cama para personas adicionales (+$100.000/persona extra)
• Vista maravillosa a la represa
• Cocineta equipada | Dos pisos

🌌 **DOMO SIRIUS** (2 personas) - $450.000/noche
• Un solo piso diseño para parejas
• Vista bella a represa y montaña
• Terraza acogedora | Nevera y cafetera

✨ **DOMO CENTAURY** (2 personas) - $450.000/noche
• Similar a Sirius, un solo piso
• Vista hermosa a represa y montaña
• Terraza relajante | Nevera y cafetera

✨ **INCLUYE EN TODOS LOS DOMOS:**
• Desayuno gourmet continental
• Wifi de alta velocidad gratuito
• Parqueadero privado y seguro
• Acceso a todas las instalaciones
• Kit de bienvenida

🏕️ **Domos disponibles:**

📋 Puedo ayudarte con:
• Disponibilidad para fechas específicas
• Proceso de reserva paso a paso
• Servicios adicionales disponibles
• Fotos e imágenes de los domos

💬 Responde **"Sí"** si quieres más información específica o **"disponibilidad"** para consultar fechas libres."""

    def _get_politicas_with_fallback(self) -> str:
        """
        Obtener información de políticas con fallback robusto
        """
        try:
            # Intentar obtener respuesta de RAG si está disponible
            if "politicas_glamping" in self.qa_chains and self.qa_chains["politicas_glamping"]:
                rag_response = self.qa_chains["politicas_completas"].run(
                    {"query": "políticas del glamping"}
                )
                if rag_response and len(rag_response) > 50:
                    return rag_response
        except Exception as e:
            logger.warning(f"RAG politicas_completas falló, usando fallback: {e}")
        
        # Fallback con información esencial
        return self._get_emergency_politicas_response()

    def _get_imagenes_with_fallback(self) -> str:
        """
        Obtener información de imágenes con fallback robusto
        """
        try:
            # Intentar obtener respuesta de RAG si está disponible
            if "imagenes_glamping" in self.qa_chains and self.qa_chains["imagenes_glamping"]:
                rag_response = self.qa_chains["imagenes_glamping"].run(
                    {"query": "imágenes y galería del glamping"}
                )
                if rag_response and len(rag_response) > 50:
                    return rag_response
        except Exception as e:
            logger.warning(f"RAG imagenes_glamping falló, usando fallback: {e}")
        
        # Fallback con información esencial
        return self._get_emergency_imagenes_response()

    def _get_accesibilidad_with_fallback(self) -> str:
        """
        Obtener información de accesibilidad con fallback robusto
        """
        try:
            # Intentar obtener respuesta de RAG si está disponible
            if "accesibilidad_glamping" in self.qa_chains and self.qa_chains["accesibilidad_glamping"]:
                rag_response = self.qa_chains["accesibilidad_glamping"].run(
                    {"query": "información de accesibilidad y adaptaciones"}
                )
                if rag_response and len(rag_response) > 50:
                    return rag_response
        except Exception as e:
            logger.warning(f"RAG accesibilidad_glamping falló, usando fallback: {e}")
        
        # Fallback con información esencial
        return self._get_emergency_accesibilidad_response()

    def _get_emergency_politicas_response(self) -> str:
        """
        Respuesta de emergencia para políticas del glamping
        """
        return """📋 **POLÍTICAS DEL GLAMPING** 📄

📅 **RESERVAS Y CANCELACIONES:**
• Check-in: 3:00 PM | Check-out: 12:00 PM
• Cancelación gratuita hasta 48 horas antes
• Modificaciones según disponibilidad

💰 **TARIFAS Y PAGOS:**
• Anticipo del 50% para confirmar reserva
• Saldo restante al momento del check-in
• Aceptamos transferencias y pagos en efectivo

🏠 **NORMAS DE ESTADÍA:**
• Máximo de huéspedes según capacidad del domo
• No se permite fumar dentro de los domos
• Mascotas bienvenidas con condiciones especiales
• Respeto por horarios de silencio (10:00 PM - 8:00 AM)

📋 **INCLUIDO EN TARIFA:**
• Desayuno continental gourmet
• WiFi gratuito de alta velocidad
• Uso de todas las instalaciones comunes
• Parqueadero privado y seguro

⚠️ **POLÍTICAS IMPORTANTES:**
• Daños o pérdidas serán facturados aparte
• Prohibido el ingreso de elementos pirotécnicos
• Cumplimiento estricto de aforo por domo
• Reserva de derecho de admisión

📞 **INFORMACIÓN Y RESERVAS:**
• WhatsApp: +57 123 456 7890
• Correo: reservas@glampingbrillodelaluna.com

💡 **¿Necesitas aclarar alguna política específica?**"""

    def _get_emergency_imagenes_response(self) -> str:
        """
        Respuesta de emergencia para galería de imágenes
        """
        return """📸 **GALERÍA DE IMÁGENES** 🌟

🌐 **SITIO WEB OFICIAL:**
• https://glampingbrillodelaluna.com
• Galería completa de todos nuestros domos
• Fotos de las instalaciones y servicios
• Vista 360° de cada domo temático

📱 **REDES SOCIALES:**
• Instagram: @glampingbrillodelaluna
• Facebook: Glamping Brillo de Luna
• Fotos actualizadas regularmente
• Testimonios reales de nuestros huéspedes

📧 **ENVÍO PERSONALIZADO:**
• Solicita fotos específicas por WhatsApp
• Podemos enviar imágenes de fechas disponibles
• Fotos detalladas de servicios incluidos
• Imágenes de actividades y alrededores

🏞️ **QUE ENCONTRARÁS EN NUESTRA GALERÍA:**
• Vista exterior e interior de cada domo
• Jacuzzis privados y áreas de relajación
• Desayunos gourmet y servicios incluidos
• Paisajes de la Represa de Tominé
• Instalaciones comunes y recreativas

📞 **SOLICITAR IMÁGENES:**
• WhatsApp: +57 123 456 7890
• Especifica qué domo te interesa
• Te enviamos un álbum personalizado

💡 **¿Qué imágenes específicas necesitas ver?**"""

    def _get_emergency_accesibilidad_response(self) -> str:
        """
        Respuesta de emergencia para información de accesibilidad
        """
        return """♿ **INFORMACIÓN DE ACCESIBILIDAD** 🌟

🏠 **DOMOS ADAPTADOS:**
• Sirius y Centaury: Sin escalones, un solo piso
• Acceso directo desde parqueadero
• Puertas amplias para sillas de ruedas
• Baños adaptados con barras de apoyo

🚶‍♀️ **FACILIDADES DE MOVILIDAD:**
• Senderos pavimentados a domos principales
• Rampas de acceso donde es necesario
• Superficies antideslizantes
• Iluminación nocturna en todos los caminos

🛏️ **ADAPTACIONES EN DOMOS:**
• Camas de altura estándar
• Espacios de circulación amplios
• Controles de luz y temperatura accesibles
• Ducha con acceso sin barreras

🍽️ **SERVICIO DE COMIDAS:**
• Desayuno servido en el domo si se requiere
• Adaptación de menús según necesidades
• Utensilios especiales disponibles
• Servicio personalizado

🚗 **PARQUEADERO Y ACCESO:**
• Espacios de estacionamiento amplios
• Ubicación cercana a domos accesibles
• Superficie plana y estable
• Asistencia disponible si se necesita

📋 **SERVICIOS ESPECIALES:**
• Personal capacitado en atención inclusiva
• Equipos adicionales bajo solicitud
• Coordinación previa para necesidades específicas
• Sin costo adicional por adaptaciones básicas

📞 **COORDINAR NECESIDADES ESPECIALES:**
• WhatsApp: +57 123 456 7890
• Informa tus requerimientos al reservar
• Confirmamos disponibilidad y adaptaciones

♿ **¡Queremos que todos disfruten de la experiencia Glamping!**"""

    def _get_emergency_informacion_response(self) -> str:
        """
        Respuesta de emergencia para información general
        """
        return """ℹ️ **INFORMACIÓN GENERAL DEL GLAMPING** 🌟

🏞️ **UBICACIÓN:**
• Guatavita, Cundinamarca, Colombia
• Vista privilegiada a la Represa de Tominé
• A 1 hora de Bogotá por la vía La Calera
• Entorno natural y paisajes espectaculares

🏠 **NUESTRAS INSTALACIONES:**
• 4 domos temáticos con vistas únicas
• Jacuzzis privados en domo premium
• Áreas comunes para relajación
• Jardines y espacios naturales

🎯 **EXPERIENCIA ÚNICA:**
• Glamping de lujo en contacto con la naturaleza
• Desayunos gourmet incluidos
• Actividades al aire libre disponibles
• Perfecto para parejas y familias pequeñas

✨ **SERVICIOS INCLUIDOS:**
• WiFi gratuito de alta velocidad
• Parqueadero privado y seguro
• Desayuno continental gourmet
• Acceso a todas las instalaciones

📞 **CONTACTO:**
• WhatsApp: +57 123 456 7890
• Email: info@glampingbrillodelaluna.com
• Web: www.glampingbrillodelaluna.com

🌟 **¡Vive una experiencia inolvidable en contacto con la naturaleza!**"""

    def _get_emergency_ubicacion_response(self) -> str:
        """Respuesta de emergencia para ubicación cuando todo falla"""
        return """📍 **UBICACIÓN - BRILLO DE LUNA GLAMPING**

🗺️ **Dirección completa:**
Vereda Pueblo Viejo, Km 15 vía Guatavita
Guatavita, Cundinamarca, Colombia

🚗 **Cómo llegar desde Bogotá:**
• Toma la Autopista Norte hasta Briceño
• Continúa por la vía hacia Sesquilé
• Sigue hacia Guatavita (aprox. 1.5 horas)
• En Guatavita, toma la vía hacia Pueblo Viejo
• Son 15 km adicionales por carretera destapada

📱 **Coordenadas GPS:**
• Latitud: 4.9234567
• Longitud: -73.8234567

🚙 **Recomendaciones:**
• Vehículo con buen despeje (últimos 15 km)
• Llenar tanque en Guatavita
• Comunicarse al llegar a Guatavita para guía final

📞 **Contacto para indicaciones:**
• WhatsApp: +57 305 461 4926
• Llamadas: Mismo número

🔍 **¿Necesitas algo más?**
• Escribe "concepto" para conocer sobre nuestro glamping
• Escribe "políticas" para revisar nuestras normas
• Escribe "menú" para volver al menú principal"""

    def _get_emergency_concepto_response(self) -> str:
        """Respuesta de emergencia para concepto cuando todo falla"""
        return """🌙 **BRILLO DE LUNA GLAMPING - NUESTRA FILOSOFÍA**

✨ **¿Qué es Glamping?**
Glamping combina lo mejor del camping tradicional con el lujo y comodidad de un hotel. Es "Glamorous Camping" - acampar con estilo y sin renunciar a las comodidades.

🏔️ **Nuestra Misión:**
Ofrecer una experiencia única de conexión con la naturaleza en las montañas de Cundinamarca, sin sacrificar comodidad ni seguridad.

🌟 **Filosofía Brillo de Luna:**
• **Sostenibilidad:** Respetamos y protegemos nuestro entorno natural
• **Autenticidad:** Experiencia genuina lejos del ruido urbano
• **Comodidad:** Domos equipados con todas las amenidades
• **Tranquilidad:** Espacio para desconectar y reconectar contigo mismo

🍃 **Nuestra Experiencia:**
• Ubicados en Guatavita, Cundinamarca
• Vista panorámica a la Represa del Tominé
• 4 domos únicos con personalidad propia
• Conexión total con la naturaleza sin renunciar al confort

💫 **Lo que nos hace especiales:**
• Atención personalizada y cálida
• Experiencias diseñadas para cada huésped
• Gastronomía local y saludable
• Actividades de conexión con la naturaleza

🌐 **Sitio Web:** https://glampingbrillodelaluna.com

🔍 **¿Necesitas algo más?**
• Escribe "ubicación" para saber dónde estamos
• Escribe "políticas" para revisar nuestras normas
• Escribe "menú" para volver al menú principal"""

    def handle_domos_followup_question(self, user_message: str, user_state: dict) -> str:
        """Maneja preguntas de seguimiento sobre domos"""
        try:
            # Resetear estado
            user_state["waiting_for_domos_followup"] = False
            user_state["current_flow"] = "none"

            # Usar fallback service para respuesta específica
            from services.fallback_service import detect_topic_and_provide_fallback
            handled, fallback_response, topic = detect_topic_and_provide_fallback(f"domos {user_message}")

            if handled:
                return fallback_response
            else:
                # Información general de domos como fallback
                return """🏠 **DOMOS BRILLO DE LUNA**

Tenemos 4 domos únicos:
• **Antares** - Domo familiar con jacuzzi
• **Polaris** - Domo romántico para parejas
• **Sirius** - Domo con vista panorámica
• **Centaury** - Domo ecológico premium

💰 **Precios desde $150.000 COP por noche**

📱 **Para más información:**
WhatsApp: +57 305 461 4926

🔍 **¿Necesitas algo más?**
• Escribe "ubicación" para saber dónde estamos
• Escribe "servicios" para conocer lo que incluye tu estadía
• Escribe "menú" para volver al menú principal"""

        except Exception as e:
            logger.error(f"Error en handle_domos_followup_question: {e}")
            return "Disculpa, tuve un problema procesando tu consulta sobre domos. ¿Podrías reformular tu pregunta?"

    def handle_servicios_followup_question(self, user_message: str, user_state: dict) -> str:
        """Maneja preguntas de seguimiento sobre servicios"""
        try:
            # Resetear estado
            user_state["waiting_for_servicios_followup"] = False
            user_state["current_flow"] = "none"

            # Usar fallback service para respuesta específica
            from services.fallback_service import detect_topic_and_provide_fallback
            handled, fallback_response, topic = detect_topic_and_provide_fallback(f"servicios {user_message}")

            if handled:
                return fallback_response
            else:
                # Información general de servicios como fallback
                return """🛎️ **SERVICIOS BRILLO DE LUNA**

✅ **INCLUIDOS:**
• Desayuno gourmet continental
• WiFi de alta velocidad
• Parqueadero privado y seguro
• Kit de bienvenida

🎯 **ADICIONALES:**
• Actividades de naturaleza
• Experiencias gastronómicas
• Servicios de bienestar
• Tours guiados

📱 **Más información:**
WhatsApp: +57 305 461 4926

🔍 **¿Necesitas algo más?**
• Escribe "ubicación" para saber dónde estamos
• Escribe "domos" para conocer nuestros alojamientos
• Escribe "menú" para volver al menú principal"""

        except Exception as e:
            logger.error(f"Error en handle_servicios_followup_question: {e}")
            return "Disculpa, tuve un problema procesando tu consulta sobre servicios. ¿Podrías reformular tu pregunta?"


def create_menu_service(qa_chains: Dict[str, Any], validation_service, availability_service=None) -> MenuService:
  
    return MenuService(qa_chains, validation_service, availability_service)