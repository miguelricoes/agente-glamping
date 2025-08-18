# Servicio especializado de disponibilidades - Extrae lógica compleja de disponibilidades de agente.py
# Consolida consultas de disponibilidad, análisis de fechas y generación de respuestas

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from utils.logger import get_logger, log_database_operation, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

class AvailabilityService:
    """
    Servicio especializado para manejo de disponibilidades de domos
    Extrae toda la lógica compleja de consultas de disponibilidad
    """
    
    def __init__(self, db=None, Reserva=None):
        """
        Inicializar servicio de disponibilidades
        
        Args:
            db: Instancia de SQLAlchemy
            Reserva: Modelo de Reserva
        """
        self.db = db
        self.Reserva = Reserva
        
        # Configuración de domos
        self.domos_info = {
            'antares': {
                'nombre': 'Antares',
                'descripcion': 'Domo familiar con jacuzzi privado y vista panorámica',
                'capacidad_maxima': 6,
                'precio_base': 650000
            },
            'polaris': {
                'nombre': 'Polaris',
                'descripcion': 'Domo romántico con chimenea y terraza privada',
                'capacidad_maxima': 4,
                'precio_base': 550000
            },
            'sirius': {
                'nombre': 'Sirius',
                'descripcion': 'Domo acogedor perfecto para parejas',
                'capacidad_maxima': 2,
                'precio_base': 450000
            },
            'centaury': {
                'nombre': 'Centaury',
                'descripcion': 'Domo cómodo con todas las comodidades básicas',
                'capacidad_maxima': 4,
                'precio_base': 450000
            }
        }
        
        # Meses en español para parsing
        self.meses_espanol = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }
        
        logger.info("Servicio de disponibilidades inicializado",
                   extra={"phase": "startup", "component": "availability_service"})
    
    def _check_database_available(self) -> bool:
        """Verificar que la base de datos esté disponible"""
        return self.db is not None and self.Reserva is not None
    
    # ===== CONSULTA PRINCIPAL DE DISPONIBILIDADES =====
    
    def consultar_disponibilidades(self, fecha_inicio: str = None, fecha_fin: str = None, 
                                 domo_especifico: str = None, personas: int = None) -> Dict[str, Any]:
        """
        Consulta principal de disponibilidades
        
        Args:
            fecha_inicio: Fecha de inicio en formato YYYY-MM-DD
            fecha_fin: Fecha de fin en formato YYYY-MM-DD
            domo_especifico: Nombre específico del domo
            personas: Número de personas
            
        Returns:
            Diccionario con disponibilidades y metadatos
        """
        try:
            if not self._check_database_available():
                return {
                    'success': False,
                    'error': 'Base de datos no disponible',
                    'disponibilidades_por_fecha': {},
                    'domos_disponibles': [],
                    'mensaje': 'La base de datos no está disponible'
                }
            
            # Valores por defecto
            if not fecha_inicio:
                fecha_inicio = datetime.now().strftime('%Y-%m-%d')
            if not fecha_fin:
                fecha_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_fin = (fecha_obj + timedelta(days=2)).strftime('%Y-%m-%d')
            
            # Obtener reservas existentes en el rango
            reservas_existentes = self.Reserva.query.filter(
                self.Reserva.fecha_entrada <= fecha_fin,
                self.Reserva.fecha_salida >= fecha_inicio
            ).all()
            
            # Mapear reservas por fecha y domo
            reservas_por_fecha_domo = {}
            for reserva in reservas_existentes:
                fecha_actual = reserva.fecha_entrada
                while fecha_actual < reserva.fecha_salida:
                    fecha_str = fecha_actual.strftime('%Y-%m-%d')
                    domo_lower = (reserva.domo or '').lower()
                    
                    if fecha_str not in reservas_por_fecha_domo:
                        reservas_por_fecha_domo[fecha_str] = set()
                    reservas_por_fecha_domo[fecha_str].add(domo_lower)
                    
                    fecha_actual += timedelta(days=1)
            
            # Calcular disponibilidades día por día
            fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_limite = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            
            disponibilidades_por_fecha = {}
            domos_disponibles_resumen = []
            fechas_completamente_libres = []
            
            while fecha_actual <= fecha_limite:
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
                domos_ocupados = reservas_por_fecha_domo.get(fecha_str, set())
                
                # Todos los domos disponibles para esta fecha
                domos_disponibles = []
                for domo_key in self.domos_info.keys():
                    if domo_key not in domos_ocupados:
                        domos_disponibles.append(domo_key)
                
                # Filtrar por domo específico si se especifica
                if domo_especifico:
                    domo_lower = domo_especifico.lower()
                    domos_disponibles = [domo for domo in domos_disponibles if domo == domo_lower]
                
                # Filtrar por capacidad si se especifica personas
                if personas:
                    domos_disponibles = [
                        domo for domo in domos_disponibles 
                        if self.domos_info[domo]['capacidad_maxima'] >= personas
                    ]
                
                disponibilidades_por_fecha[fecha_str] = {
                    'fecha': fecha_str,
                    'fecha_formateada': fecha_actual.strftime('%A, %d de %B de %Y'),
                    'domos_disponibles': domos_disponibles,
                    'total_disponibles': len(domos_disponibles)
                }
                
                # Verificar si es fecha completamente libre
                if len(domos_disponibles) == len(self.domos_info):
                    fechas_completamente_libres.append(fecha_str)
                
                fecha_actual += timedelta(days=1)
            
            # Generar resumen de domos disponibles
            domos_con_fechas = {}
            for fecha_str, info_fecha in disponibilidades_por_fecha.items():
                for domo in info_fecha['domos_disponibles']:
                    if domo not in domos_con_fechas:
                        domos_con_fechas[domo] = []
                    domos_con_fechas[domo].append(fecha_str)
            
            for domo, fechas_disponibles in domos_con_fechas.items():
                domos_disponibles_resumen.append({
                    'domo': domo,
                    'info': self.domos_info[domo],
                    'fechas_disponibles': fechas_disponibles,
                    'total_fechas_disponibles': len(fechas_disponibles)
                })
            
            # Generar recomendaciones
            recomendaciones = self._generar_recomendaciones(
                domos_disponibles_resumen, fechas_completamente_libres, personas, domo_especifico
            )
            
            resultado = {
                'success': True,
                'disponibilidades_por_fecha': disponibilidades_por_fecha,
                'domos_disponibles': domos_disponibles_resumen,
                'fechas_completamente_libres': fechas_completamente_libres,
                'parametros_busqueda': {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'domo_especifico': domo_especifico,
                    'personas': personas
                },
                'resumen': recomendaciones,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            log_database_operation(logger, "QUERY", "disponibilidades", True, 
                                 f"Consulta exitosa: {len(domos_disponibles_resumen)} domos disponibles")
            
            return resultado
            
        except Exception as e:
            error_msg = f"Error consultando disponibilidades: {str(e)}"
            log_database_operation(logger, "QUERY", "disponibilidades", False, error_msg)
            return {
                'success': False,
                'error': str(e),
                'disponibilidades_por_fecha': {},
                'domos_disponibles': [],
                'mensaje': f'Error técnico: {str(e)}'
            }
    
    # ===== PROCESAMIENTO DE CONSULTAS EN LENGUAJE NATURAL =====
    
    def consultar_disponibilidades_natural(self, consulta_usuario: str) -> str:
        """
        Consulta disponibilidades usando consulta en lenguaje natural
        
        Args:
            consulta_usuario: Consulta del usuario en lenguaje natural
            
        Returns:
            Respuesta formateada para WhatsApp
        """
        try:
            logger.info(f"Consultando disponibilidades: {consulta_usuario}", 
                       extra={"phase": "availability", "component": "natural_query"})
            
            if not self._check_database_available():
                return "Lo siento, no puedo consultar las disponibilidades en este momento. La base de datos no está disponible."
            
            # Extraer parámetros de la consulta
            parametros = self.extraer_parametros_consulta(consulta_usuario)
            logger.info(f"Parámetros extraídos: {parametros}", 
                       extra={"phase": "availability", "component": "parameter_extraction"})
            
            # Asegurar fecha_fin si no se proporciona
            if parametros['fecha_inicio'] and not parametros['fecha_fin']:
                fecha_obj = datetime.strptime(parametros['fecha_inicio'], '%Y-%m-%d')
                parametros['fecha_fin'] = (fecha_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Consultar disponibilidades
            disponibilidades = self.consultar_disponibilidades(
                fecha_inicio=parametros['fecha_inicio'],
                fecha_fin=parametros['fecha_fin'],
                domo_especifico=parametros['domo'],
                personas=parametros['personas']
            )
            
            # Generar respuesta natural
            respuesta = self.generar_respuesta_natural(disponibilidades, parametros, consulta_usuario)
            
            logger.info(f"Respuesta generada: {respuesta[:100]}...", 
                       extra={"phase": "availability", "component": "response_generation"})
            
            return respuesta
            
        except Exception as e:
            error_msg = f"Error en consulta natural: {str(e)}"
            log_error(logger, e, {"component": "natural_query", "consulta": consulta_usuario})
            return f"Disculpa, tuve un problema técnico consultando las disponibilidades. Error: {str(e)}"
    
    def extraer_parametros_consulta(self, consulta: str) -> Dict[str, Any]:
        """
        Extrae parámetros de una consulta en lenguaje natural
        
        Args:
            consulta: Consulta del usuario
            
        Returns:
            Diccionario con parámetros extraídos
        """
        parametros = {
            'fecha_inicio': None,
            'fecha_fin': None,
            'domo': None,
            'personas': None
        }
        
        consulta_lower = consulta.lower()
        
        # Patrones de fecha mejorados
        patrones_fecha = [
            # DD/MM/YYYY o DD-MM-YYYY
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dmy'),
            # YYYY-MM-DD
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'ymd'),
            # "24 de diciembre del 2025"
            (r'(\d{1,2})\s+de\s+(\w+)\s+del?\s+(\d{4})', 'dmy_texto_con_año'),
            # "24 de diciembre" (sin año)
            (r'(\d{1,2})\s+de\s+(\w+)(?!\s+del?\s+\d)', 'dmy_texto_sin_año'),
            # "diciembre 24, 2025"
            (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', 'mdy_texto'),
        ]
        
        # Buscar fechas
        fechas_encontradas = []
        for patron, tipo in patrones_fecha:
            matches = re.findall(patron, consulta_lower)
            if matches:
                for match in matches:
                    try:
                        fecha_obj = self._parsear_fecha(match, tipo)
                        if fecha_obj:
                            fechas_encontradas.append(fecha_obj)
                    except:
                        continue
        
        # Asignar fechas encontradas
        if len(fechas_encontradas) >= 2:
            # Ordenar fechas y tomar primera y última
            fechas_encontradas.sort()
            parametros['fecha_inicio'] = fechas_encontradas[0].strftime('%Y-%m-%d')
            parametros['fecha_fin'] = fechas_encontradas[-1].strftime('%Y-%m-%d')
        elif len(fechas_encontradas) == 1:
            parametros['fecha_inicio'] = fechas_encontradas[0].strftime('%Y-%m-%d')
        
        # Extraer número de personas
        patron_personas = r'(\d+)\s*persona[s]?|para\s+(\d+)|(\d+)\s*huespedes?|(\d+)\s*adultos?'
        match_personas = re.search(patron_personas, consulta_lower)
        if match_personas:
            for grupo in match_personas.groups():
                if grupo:
                    parametros['personas'] = int(grupo)
                    break
        
        # Extraer tipo de domo
        domos_mencionados = []
        for domo_key, domo_info in self.domos_info.items():
            if domo_key in consulta_lower or domo_info['nombre'].lower() in consulta_lower:
                domos_mencionados.append(domo_key)
        
        if domos_mencionados:
            parametros['domo'] = domos_mencionados[0]
        
        # Buscar palabras clave de tipo de domo
        if 'romántico' in consulta_lower or 'pareja' in consulta_lower:
            parametros['domo'] = 'polaris'
        elif 'familiar' in consulta_lower or 'familia' in consulta_lower:
            parametros['domo'] = 'antares'
        elif 'económico' in consulta_lower or 'barato' in consulta_lower:
            parametros['domo'] = 'centaury'
        
        return parametros
    
    def _parsear_fecha(self, match: tuple, tipo: str) -> Optional[datetime]:
        """Parsea una fecha según el tipo de match"""
        try:
            if tipo == 'dmy':
                dia, mes, año = int(match[0]), int(match[1]), int(match[2])
                return datetime(año, mes, dia)
            elif tipo == 'ymd':
                año, mes, dia = int(match[0]), int(match[1]), int(match[2])
                return datetime(año, mes, dia)
            elif tipo == 'dmy_texto_con_año':
                dia = int(match[0])
                mes_nombre = match[1].lower()
                año = int(match[2])
                
                if mes_nombre in self.meses_espanol:
                    mes = self.meses_espanol[mes_nombre]
                    return datetime(año, mes, dia)
            elif tipo == 'dmy_texto_sin_año':
                dia = int(match[0])
                mes_nombre = match[1].lower()
                año = datetime.now().year
                
                if mes_nombre in self.meses_espanol:
                    mes = self.meses_espanol[mes_nombre]
                    # Si la fecha ya pasó este año, usar el próximo año
                    fecha_tentativa = datetime(año, mes, dia)
                    if fecha_tentativa.date() < datetime.now().date():
                        año += 1
                    return datetime(año, mes, dia)
            elif tipo == 'mdy_texto':
                mes_nombre = match[0].lower()
                dia = int(match[1])
                año = int(match[2])
                
                if mes_nombre in self.meses_espanol:
                    mes = self.meses_espanol[mes_nombre]
                    return datetime(año, mes, dia)
        except:
            pass
        return None
    
    # ===== GENERACIÓN DE RESPUESTAS =====
    
    def generar_respuesta_natural(self, datos: Dict[str, Any], parametros: Dict[str, Any], 
                                consulta_original: str) -> str:
        """
        Genera respuesta natural basada en datos de disponibilidades
        
        Args:
            datos: Datos de disponibilidades
            parametros: Parámetros extraídos
            consulta_original: Consulta original del usuario
            
        Returns:
            Respuesta formateada para WhatsApp
        """
        try:
            if not datos.get('success'):
                return f"Lo siento, tuve un problema consultando las disponibilidades: {datos.get('error', 'Error desconocido')}"
            
            domos_disponibles = datos.get('domos_disponibles', [])
            disponibilidades_por_fecha = datos.get('disponibilidades_por_fecha', {})
            
            if not domos_disponibles:
                if parametros.get('fecha_inicio'):
                    try:
                        fecha_formateada = datetime.strptime(parametros['fecha_inicio'], '%Y-%m-%d').strftime('%d de %B de %Y')
                        return f"❌ No tenemos domos disponibles para el {fecha_formateada}.\n\n¿Te gustaría consultar otras fechas? 📅"
                    except:
                        return f"❌ No tenemos domos disponibles para la fecha {parametros['fecha_inicio']}.\n\n¿Te gustaría consultar otras fechas? 📅"
                else:
                    return "❌ No encontré domos disponibles para las fechas consultadas.\n\n¿Podrías especificar otras fechas? 📅"
            
            # Construir respuesta positiva
            respuesta = "✅ *¡EXCELENTE!* Tenemos disponibilidad para ti 🎉\n\n"
            
            # Si hay fecha específica
            if parametros.get('fecha_inicio'):
                try:
                    fecha_formateada = datetime.strptime(parametros['fecha_inicio'], '%Y-%m-%d').strftime('%d de %B de %Y')
                    respuesta += f"📅 *Para el {fecha_formateada}*\n\n"
                except:
                    respuesta += f"📅 *Para la fecha consultada*\n\n"
            
            # Listar domos disponibles
            respuesta += "🏠 *DOMOS DISPONIBLES:*\n\n"
            
            for i, domo in enumerate(domos_disponibles, 1):
                info = domo['info']
                respuesta += f"{i}. *{info['nombre']}* 🌟\n"
                respuesta += f"   👥 Capacidad: {info['capacidad_maxima']} personas\n"
                respuesta += f"   💰 Precio: ${info['precio_base']:,}\n"
                respuesta += f"   📝 {info['descripcion']}\n"
                respuesta += f"   📅 Disponible {len(domo['fechas_disponibles'])} día(s)\n\n"
            
            # Agregar recomendaciones
            if datos.get('resumen'):
                respuesta += "💡 *RECOMENDACIONES:*\n"
                for recomendacion in datos['resumen']:
                    respuesta += f"• {recomendacion}\n"
                respuesta += "\n"
            
            respuesta += "¿Te gustaría hacer una reserva o necesitas más información? 🤔"
            
            return respuesta
            
        except Exception as e:
            log_error(logger, e, {"component": "response_generation"})
            return "Disculpa, tuve un problema generando la respuesta sobre disponibilidades."
    
    def _generar_recomendaciones(self, domos_disponibles: List[Dict], fechas_libres: List[str], 
                               personas: int = None, domo_especifico: str = None) -> List[str]:
        """
        Genera recomendaciones en lenguaje natural
        
        Args:
            domos_disponibles: Lista de domos disponibles
            fechas_libres: Lista de fechas completamente libres
            personas: Número de personas (opcional)
            domo_especifico: Domo específico solicitado (opcional)
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        if not domos_disponibles:
            return ["No hay disponibilidad en las fechas consultadas. Sugiere fechas alternativas al cliente."]
        
        # Recomendaciones por número de personas
        if personas:
            domos_perfectos = [
                domo for domo in domos_disponibles 
                if domo['info']['capacidad_maxima'] == personas
            ]
            domos_amplios = [
                domo for domo in domos_disponibles 
                if domo['info']['capacidad_maxima'] > personas
            ]
            
            if domos_perfectos:
                recomendaciones.append(f"Capacidad perfecta: {domos_perfectos[0]['info']['nombre']} para {personas} personas")
            elif domos_amplios:
                mejor_amplio = min(domos_amplios, key=lambda x: x['info']['capacidad_maxima'])
                recomendaciones.append(f"Recomendado: {mejor_amplio['info']['nombre']} (capacidad {mejor_amplio['info']['capacidad_maxima']})")
        
        # Recomendaciones por fechas
        if fechas_libres:
            if len(fechas_libres) >= 3:
                recomendaciones.append(f"Excelente disponibilidad: {len(fechas_libres)} fechas con todos los domos libres")
            else:
                recomendaciones.append(f"Disponibilidad limitada: solo {len(fechas_libres)} fechas con plena disponibilidad")
        
        # Recomendaciones específicas por domo
        if domo_especifico:
            domo_solicitado = next((d for d in domos_disponibles if d['domo'] == domo_especifico), None)
            if domo_solicitado:
                recomendaciones.append(f"Tu domo solicitado ({domo_solicitado['info']['nombre']}) está disponible")
            else:
                recomendaciones.append(f"El domo {domo_especifico} no está disponible, pero hay alternativas")
        
        # Recomendación general de mejor opción
        if len(domos_disponibles) > 0:
            mejor_opcion = max(domos_disponibles, key=lambda x: len(x['fechas_disponibles']))
            recomendaciones.append(f"Mayor disponibilidad: {mejor_opcion['info']['nombre']} ({len(mejor_opcion['fechas_disponibles'])} fechas)")
        
        return recomendaciones
    
    # ===== UTILIDADES =====
    
    def detectar_intencion_consulta(self, user_input: str) -> Dict[str, Any]:
        """
        Detecta si el usuario está consultando disponibilidades
        
        Args:
            user_input: Input del usuario
            
        Returns:
            Diccionario con análisis de intención
        """
        user_input_lower = user_input.lower()
        
        keywords_disponibilidad = [
            'disponible', 'disponibles', 'disponibilidad',
            'libre', 'libres', 'ocupado', 'ocupados',
            'fechas', 'calendario', 'cuando',
            'hay espacio', 'tienen cupo',
            'esta ocupado', 'estan ocupados',
            'esta libre', 'estan libres'
        ]
        
        keywords_encontradas = [kw for kw in keywords_disponibilidad if kw in user_input_lower]
        
        return {
            'es_consulta_disponibilidad': len(keywords_encontradas) > 0,
            'confianza': len(keywords_encontradas) / len(keywords_disponibilidad),
            'keywords_detectadas': keywords_encontradas
        }
    
    def get_availability_health(self) -> Dict[str, Any]:
        """
        Obtener estado de salud del servicio de disponibilidades
        
        Returns:
            Diccionario con información de salud
        """
        try:
            if not self._check_database_available():
                return {
                    "status": "unavailable",
                    "database_connected": False,
                    "service_available": False
                }
            
            # Probar consulta básica
            test_result = self.consultar_disponibilidades()
            
            return {
                "status": "healthy",
                "database_connected": True,
                "service_available": True,
                "domos_configurados": len(self.domos_info),
                "test_query_success": test_result.get('success', False),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_error(logger, e, {"component": "availability_health"})
            return {
                "status": "error",
                "database_connected": False,
                "service_available": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }