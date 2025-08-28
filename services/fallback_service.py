# services/fallback_service.py
from typing import Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

def detect_topic_and_provide_fallback(message: str) -> Tuple[bool, str, str]:
    """
    Detecta tema específico y proporciona fallback directo
    Returns: (handled, response, topic)
    """
    message_lower = message.lower().strip()

    # NUEVO: No procesar si es claramente datos de reserva
    reservation_indicators = [
        'entrada' in message_lower and 'salida' in message_lower,
        'huéspedes' in message_lower and ('correo' in message_lower or 'email' in message_lower),
        'domo' in message_lower and 'pago' in message_lower,
        message_lower.startswith('reserva para') or 'reserva para' in message_lower
    ]

    if any(reservation_indicators):
        logger.debug(f"Mensaje detectado como datos de reserva, no aplicando fallback: {message[:50]}")
        return False, "", ""

    # SERVICIOS INEXISTENTES - Detectar menciones de servicios que no ofrecemos
    servicios_inexistentes = [
        'yate', 'barco', 'lancha', 'navegación', 'paseo en yate', 'paseo en barco',
        'buceo', 'snorkel', 'surf', 'windsurf', 'jet ski',
        'casino', 'discoteca', 'bar nocturno', 'club nocturno',
        'esquí', 'snowboard', 'patinaje en hielo',
        'paracaidismo', 'parapente', 'ala delta',
        'deportes extremos', 'bungee', 'puenting'
    ]
    
    if any(servicio in message_lower for servicio in servicios_inexistentes):
        response = """🚫 **SERVICIOS NO DISPONIBLES**

Lo siento, pero el servicio que mencionas no está disponible en Brillo de Luna Glamping.

🌟 **SERVICIOS QUE SÍ OFRECEMOS:**

🧘 **Bienestar y Relajación:**
• Yoga matutino con vista panorámica
• Masajes relajantes (bajo reserva)
• Meditación al amanecer
• Spa y tratamientos de bienestar

🚶 **Actividades de Naturaleza:**
• Senderismo guiado por senderos naturales
• Caminatas ecológicas
• Observación de aves y fauna local
• Tours de reconocimiento de flora

🎯 **Experiencias Especiales:**
• Observación astronómica con telescopio
• Fotografía de paisajes y naturaleza
• Fogatas nocturnas con marshmallows
• Pesca deportiva en la Represa del Tominé

🚴 **Deportes y Aventura:**
• Ciclomontañismo por la región
• Alquiler de bicicletas
• Rappel (según disponibilidad)
• Kayak en temporadas específicas

¿Te interesa alguna de estas actividades que sí tenemos disponibles? 😊"""

        logger.info(f"Servicio inexistente detectado en mensaje", extra={"topic": "servicio_inexistente"})
        return True, response, "servicio_inexistente"

    # UBICACIÓN Y CONTACTO
    ubicacion_patterns = [
        'ubicacion', 'ubicación', 'donde', 'dónde', 'dirección', 'direccion',
        'como llegar', 'cómo llegar', 'maps', 'coordenadas', 'lugar',
        'localización', 'localizacion', 'address'
    ]

    if any(pattern in message_lower for pattern in ubicacion_patterns):
        response = """📍 **UBICACIÓN - BRILLO DE LUNA GLAMPING**

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
• Llamadas: Mismo número"""

        logger.info(f"Topic fallback triggered: ubicacion", extra={"topic": "ubicacion"})
        return True, response, "ubicacion"

    # POLÍTICAS - EVALUADAS PRIMERO PARA EVITAR CONFLICTOS
    politicas_patterns = [
        'politicas', 'políticas', 'normas', 'reglas', 'cancelacion', 'cancelación',
        'reembolso', 'devolucion', 'devolución', 'términos', 'terminos',
        'condiciones', 'policy', 'policies',
        # Variantes adicionales
        'politica', 'política', 'regla', 'norma', 'condicion', 'condición',
        'cancelar', 'devolver', 'reglamento', 'reglamentos'
    ]

    if any(pattern in message_lower for pattern in politicas_patterns):
        response = """📋 **POLÍTICAS BRILLO DE LUNA GLAMPING**

💳 **RESERVAS Y PAGOS:**
• Anticipo: 50% para confirmar reserva
• Saldo: Al momento del check-in
• Métodos: Efectivo, transferencia, tarjetas
• Confirmación: WhatsApp o email

🕐 **CHECK-IN / CHECK-OUT:**
• Check-in: 3:00 PM - 8:00 PM
• Check-out: Hasta las 12:00 PM
• Check-in tardío: Coordinar previamente
• Depósito de garantía: $100.000 COP

❌ **CANCELACIONES:**
• **+48 horas:** Reembolso 100%
• **24-48 horas:** Reembolso 50%
• **-24 horas:** Sin reembolso
• Emergencias médicas: Caso por caso

🚫 **POLÍTICAS GENERALES:**
• **Mascotas:** No permitidas (alergias otros huéspedes)
• **Fumar:** Prohibido en domos (permitido en terrazas)
• **Ruido:** Respeto después de 10:00 PM
• **Capacidad:** Máximo según domo elegido
• **Fiestas:** No permitidas (ambiente tranquilo)

🛡️ **RESPONSABILIDADES:**
• Huésped responde por daños
• Objetos de valor: Bajo responsabilidad del huésped
• Seguro médico: Recomendado
• Menores: Bajo supervisión adulta

🌿 **COMPROMISO AMBIENTAL:**
• Separación de residuos obligatoria
• Uso consciente del agua
• Respeto por flora y fauna
• Prohibido cortar plantas o molestar animales

📱 **COMUNICACIÓN:**
• WhatsApp: +57 305 461 4926
• Email: glampingbrillodelunaguatavita@gmail.com
• Respuesta: Máximo 2 horas"""

        logger.info(f"Topic fallback triggered: politicas", extra={"topic": "politicas"})
        return True, response, "politicas"

    # CONCEPTOS Y FILOSOFÍA DEL GLAMPING  
    concepto_patterns = [
        'concepto', 'conceptos', 'que es glamping', 'qué es glamping',
        'filosofia', 'filosofía', 'sobre el glamping',
        'historia', 'mision', 'misión', 'vision', 'visión', 'nosotros'
    ]

    if any(pattern in message_lower for pattern in concepto_patterns):
        response = """🌙 **BRILLO DE LUNA GLAMPING - NUESTRA FILOSOFÍA**

✨ **¿Qué es Glamping?**
Glamping combina lo mejor del camping tradicional con el lujo y comodidad de un hotel. Es "Glamorous Camping" -
acampar con estilo y sin renunciar a las comodidades.

🏔️ **Nuestra Misión:**
Ofrecer una experiencia única de conexión con la naturaleza en las montañas de Cundinamarca, sin sacrificar
comodidad ni seguridad.

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
• Actividades de conexión con la naturaleza"""

        logger.info(f"Topic fallback triggered: concepto", extra={"topic": "concepto"})
        return True, response, "concepto"

    # SERVICIOS INCLUIDOS
    servicios_patterns = [
        'servicios', 'servicio', 'que incluyen', 'qué incluyen',
        'que ofrecen', 'qué ofrecen', 'incluido', 'amenidades',
        'comodidades', 'beneficios', 'extras'
    ]

    if any(pattern in message_lower for pattern in servicios_patterns):
        response = """🛎️ **SERVICIOS BRILLO DE LUNA GLAMPING**

✅ **INCLUIDO EN TODOS LOS DOMOS:**
• 🍳 Desayuno natural y saludable
• 🎫 Tarjeta de asistencia al turista
• 🚗 Parqueadero gratis y seguro
• 🌐 WiFi gratuito
• 🔥 BBQ y fogata (áreas comunes)
• 🧹 Servicio diario de aseo del domo
• 🚿 Baño incorporado con agua caliente
• 🛏️ Colchón premium con toper de plumas
• 🧺 Lencería de calidad
• 🔌 Calienta camas eléctrico doble plaza
• 🛌 Cobija eléctrica anti-frío
• ☕ Café ilimitado disponible

🏔️ **CARACTERÍSTICAS EXCLUSIVAS POR DOMO:**
• 🌟 **Domo Antares:** Jacuzzi romántico + malla catamarán
• 🌟 **Domos Antares & Polaris:** Cocinetas equipadas completas
• 🌟 **Terrazas con parasol:** Vista panorámica a represa
• 🌟 **Diseño para observación astronómica** en todos los domos

🎯 **SERVICIOS OPCIONALES (Costos adicionales):**
• ⛵ Paseo en velero/lancha - Embalse Tominé
• 💆 Masajes relajantes - Desde $90.000/persona
• 🥾 Caminata Montecillo - 6km (3.5h, +500m altitud)
• 🏞️ Caminata Pozo Azul - 10-14km (3-4h, +1km altitud)
• 🎨 Decoraciones personalizadas - Desde $60.000

🍽️ **EXPERIENCIAS GASTRONÓMICAS:**
• Desayuno incluido con productos locales
• Menús personalizados disponibles
• Opciones vegetarianas y veganas
• Picnic para excursiones

⭐ **EXPERIENCIAS ESPECIALES:**
• 🔭 Observación de estrellas con telescopio
• 📸 Talleres de fotografía de naturaleza
• 🧘 Yoga matutino vista panorámica
• 🔥 Fogatas nocturnas con marshmallows
• 🎣 Pesca deportiva en Represa Tominé

💬 **¿Necesitas algo específico?**
Contáctanos al +57 305 461 4926 para personalizar tu experiencia."""

        logger.info(f"Topic fallback triggered: servicios", extra={"topic": "servicios"})
        return True, response, "servicios"

    # ACTIVIDADES
    actividades_patterns = [
        'actividades', 'actividad', 'hacer', 'planes', 'entretenimiento',
        'diversión', 'pasear', 'experiencias', 'turismo', 'excursiones'
    ]

    if any(pattern in message_lower for pattern in actividades_patterns):
        response = """🎯 **ACTIVIDADES EN BRILLO DE LUNA**

🌅 **ACTIVIDADES MATUTINAS:**
• ☀️ Yoga al amanecer con vista panorámica
• 🚶 Senderismo por senderos naturales
• 📸 Fotografía de paisajes y fauna
• ☕ Desayuno contemplativo en terraza
• 🚴 Ciclomontañismo por la región

🌞 **ACTIVIDADES DIURNAS:**
• 🎣 Pesca deportiva en Represa del Tominé
• 🛶 Kayak y deportes acuáticos (temporadas)
• 🏔️ Trekking a miradores naturales
• 🌿 Tours de reconocimiento de flora local
• 📚 Lectura en hamacas con vista

🌅 **ACTIVIDADES VESPERTINAS:**
• 🔥 Fogatas comunitarias con marshmallows
• ⭐ Observación astronómica con telescopio
• 🎸 Noches de música acústica
• 🍷 Cata de vinos locales (fines de semana)
• 💆 Masajes relajantes bajo las estrellas

🌙 **EXPERIENCIAS NOCTURNAS:**
• 🔭 Astronomía y constelaciones
• 🦉 Avistamiento de fauna nocturna
• 🔥 Historias alrededor del fuego
• 🧘 Meditación nocturna
• 🌌 Fotografía de la Vía Láctea

🎨 **TALLERES ESPECIALES:**
• 🖼️ Pintura de paisajes naturales
• 📷 Fotografía de naturaleza
• 🌱 Jardinería y plantas medicinales
• 🍳 Cocina tradicional colombiana

¿Te interesa alguna actividad en particular?"""

        logger.info(f"Topic fallback triggered: actividades", extra={"topic": "actividades"})
        return True, response, "actividades"

    # POLÍTICAS - ELIMINADA DUPLICACIÓN (YA MOVIDA ARRIBA)

    logger.debug(f"No topic fallback found for message: {message[:50]}")
    return False, "", ""


# Funciones auxiliares para extensibilidad futura

def get_available_topics() -> list:
    """
    Obtiene lista de temas disponibles para fallback
    
    Returns:
        list: Lista de nombres de temas
    """
    return ["ubicacion", "concepto", "servicios", "actividades", "politicas", "servicio_inexistente"]


def add_topic_pattern(topic: str, patterns: list) -> bool:
    """
    Permite agregar nuevos patrones a temas existentes (para futuro)
    
    Args:
        topic: Nombre del tema
        patterns: Lista de patrones a agregar
        
    Returns:
        bool: True si se agregó exitosamente
    """
    # Implementación futura para extensibilidad
    logger.info(f"Future feature: add patterns {patterns} to topic {topic}")
    return False


def get_topic_stats() -> dict:
    """
    Obtiene estadísticas de uso de temas (para futuro)
    
    Returns:
        dict: Estadísticas de uso por tema
    """
    # Implementación futura para analytics
    return {
        "total_requests": 0,
        "topics": {}
    }