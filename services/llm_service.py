# Servicio centralizado de LLM y agentes
# Extrae inicialización de LLM, Pinecone y agentes de agente.py

import os
import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from collections import deque
import threading
from utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiter inteligente para llamadas a LLM"""
    
    def __init__(self, max_calls_per_minute=60, max_calls_per_user_per_minute=1):
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_user_per_minute = max_calls_per_user_per_minute
        
        # Tracking global
        self.global_calls = deque()
        
        # Tracking por usuario
        self.user_calls = {}
        
        # Queue para requests en espera
        self.request_queue = deque()
        self.processing_queue = False
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        logger.info(f"RateLimiter inicializado: {max_calls_per_minute} global, {max_calls_per_user_per_minute} por usuario/min")
    
    def _cleanup_old_calls(self):
        """Limpia llamadas antiguas (más de 1 minuto)"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Limpiar llamadas globales
        while self.global_calls and self.global_calls[0] < cutoff:
            self.global_calls.popleft()
        
        # Limpiar llamadas por usuario
        for user_id in list(self.user_calls.keys()):
            user_calls = self.user_calls[user_id]
            while user_calls and user_calls[0] < cutoff:
                user_calls.popleft()
            
            # Remover usuarios sin llamadas recientes
            if not user_calls:
                del self.user_calls[user_id]
    
    def can_make_request(self, user_id: str = "anonymous") -> Tuple[bool, str, int]:
        """
        Verifica si se puede hacer un request
        
        Returns:
            Tuple[bool, str, int]: (can_proceed, reason, wait_seconds)
        """
        with self.lock:
            self._cleanup_old_calls()
            now = datetime.now()
            
            # Verificar límite global
            if len(self.global_calls) >= self.max_calls_per_minute:
                oldest_call = self.global_calls[0]
                wait_seconds = int((oldest_call + timedelta(minutes=1) - now).total_seconds()) + 1
                return False, "Límite global de llamadas excedido", wait_seconds
            
            # Verificar límite por usuario
            user_calls = self.user_calls.get(user_id, deque())
            if len(user_calls) >= self.max_calls_per_user_per_minute:
                oldest_call = user_calls[0]
                wait_seconds = int((oldest_call + timedelta(minutes=1) - now).total_seconds()) + 1
                return False, f"Límite de usuario excedido (máx {self.max_calls_per_user_per_minute}/min)", wait_seconds
            
            return True, "", 0
    
    def record_request(self, user_id: str = "anonymous"):
        """Registra una nueva llamada"""
        with self.lock:
            now = datetime.now()
            
            # Registrar llamada global
            self.global_calls.append(now)
            
            # Registrar llamada por usuario
            if user_id not in self.user_calls:
                self.user_calls[user_id] = deque()
            self.user_calls[user_id].append(now)
            
            logger.debug(f"Request registrado para usuario {user_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del rate limiter"""
        with self.lock:
            self._cleanup_old_calls()
            
            return {
                'global_calls_last_minute': len(self.global_calls),
                'max_calls_per_minute': self.max_calls_per_minute,
                'active_users': len(self.user_calls),
                'user_limits': {
                    user_id: len(calls) for user_id, calls in self.user_calls.items()
                },
                'queue_size': len(self.request_queue)
            }

class RequestThrottler:
    """Throttling automático para requests LLM"""
    
    def __init__(self):
        self.consecutive_errors = 0
        self.last_error_time = None
        self.throttle_until = None
        self.base_delay = 1.0  # segundos
        self.max_delay = 60.0  # segundos máximo
        
        logger.info("RequestThrottler inicializado")
    
    def record_success(self):
        """Registra una llamada exitosa"""
        self.consecutive_errors = 0
        self.throttle_until = None
        logger.debug("Request exitoso - throttle resetado")
    
    def record_error(self, error_code: int = None):
        """Registra un error y ajusta throttling"""
        self.consecutive_errors += 1
        self.last_error_time = datetime.now()
        
        # Calcular delay exponencial
        delay = min(self.base_delay * (2 ** (self.consecutive_errors - 1)), self.max_delay)
        self.throttle_until = self.last_error_time + timedelta(seconds=delay)
        
        logger.warning(f"Error {error_code} registrado - throttling por {delay}s (errores consecutivos: {self.consecutive_errors})")
    
    def should_throttle(self) -> Tuple[bool, float]:
        """
        Verifica si debe hacer throttling
        
        Returns:
            Tuple[bool, float]: (should_wait, wait_seconds)
        """
        if not self.throttle_until:
            return False, 0.0
        
        now = datetime.now()
        if now < self.throttle_until:
            wait_seconds = (self.throttle_until - now).total_seconds()
            return True, wait_seconds
        
        return False, 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del throttler"""
        should_throttle, wait_time = self.should_throttle()
        
        return {
            'consecutive_errors': self.consecutive_errors,
            'is_throttling': should_throttle,
            'wait_seconds': wait_time,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None
        }

class ResponseCache:
    """Cache inteligente para respuestas de LLM"""
    
    def __init__(self, cache_duration_minutes=10):
        self.cache = {}
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        logger.info(f"ResponseCache inicializado con duración {cache_duration_minutes} minutos")
    
    def _generate_key(self, query: str) -> str:
        """Genera clave de cache normalizando la query"""
        # Normalizar query: minúsculas, sin espacios extra, sin signos
        normalized = query.lower().strip()
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())  # Espacios únicos
        
        # Generar hash MD5 para clave corta
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:12]
    
    def _is_similar_query(self, query1: str, query2: str) -> bool:
        """Detecta si dos queries son similares"""
        # Normalizar ambas - remover palabras comunes como artículos
        stop_words = {'el', 'la', 'los', 'las', 'de', 'del', 'un', 'una', 'son', 'es', 'que', 'como', 'para', 'con', 'en'}
        
        words1 = set(word for word in query1.lower().split() if len(word) > 2 and word not in stop_words)
        words2 = set(word for word in query2.lower().split() if len(word) > 2 and word not in stop_words)
        
        # Calcular similitud por palabras comunes
        if not words1 or not words2:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / min(len(words1), len(words2))  # Cambiar a min para ser más permisivo
        
        return similarity >= 0.5  # 50% similitud
    
    def get(self, query: str) -> Optional[str]:
        """Obtiene respuesta del cache si existe y es válida"""
        cache_key = self._generate_key(query)
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if datetime.now() < cached_item['expires_at']:
                logger.info(f"Cache HIT para query: {query[:50]}...")
                return cached_item['response']
            else:
                # Cache expirado, remover
                del self.cache[cache_key]
                logger.debug(f"Cache EXPIRED removido para: {query[:50]}...")
        
        # Buscar queries similares
        for existing_key, cached_item in self.cache.items():
            if datetime.now() < cached_item['expires_at']:
                if self._is_similar_query(query, cached_item['original_query']):
                    logger.info(f"Cache SIMILAR HIT: '{query[:30]}...' similar a '{cached_item['original_query'][:30]}...'")
                    return cached_item['response']
        
        logger.debug(f"Cache MISS para query: {query[:50]}...")
        return None
    
    def set(self, query: str, response: str):
        """Almacena respuesta en cache"""
        cache_key = self._generate_key(query)
        
        self.cache[cache_key] = {
            'original_query': query,
            'response': response,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + self.cache_duration
        }
        
        logger.debug(f"Cache SET para query: {query[:50]}...")
        
        # Limpiar cache expirado periódicamente
        self._cleanup_expired()
    
    def _cleanup_expired(self):
        """Limpia entradas expiradas del cache"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self.cache.items() 
            if now >= item['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cache cleanup: {len(expired_keys)} entradas expiradas removidas")
    
    def clear(self):
        """Limpia todo el cache"""
        self.cache.clear()
        logger.info("Cache completamente limpiado")
    
    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del cache"""
        now = datetime.now()
        active_entries = sum(1 for item in self.cache.values() if now < item['expires_at'])
        expired_entries = len(self.cache) - active_entries
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries
        }

class LLMService:
    """Servicio centralizado para LLM y agentes Consolida toda la inicialización de IA de agente.py """
    def __init__(self):
        """Inicializar servicio de LLM"""
        self.llm = None
        self.qa_chains = {}
        self.tools = []
        self.response_cache = ResponseCache(cache_duration_minutes=10)  # Cache de 10 minutos
        self.rate_limiter = RateLimiter(max_calls_per_minute=60, max_calls_per_user_per_minute=1)
        self.throttler = RequestThrottler()
        
        logger.info("LLMService inicializado con cache inteligente, rate limiting y throttling", 
                   extra={"component": "llm_service", "phase": "startup"})
    
    
    def initialize_llm(self) -> bool:
        """
        Inicializa el modelo de lenguaje (extraído de agente.py líneas 648-701)
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando LLM", 
                       extra={"component": "llm_service", "action": "init_llm"})
            
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.error("OPENAI_API_KEY no configurada", 
                            extra={"component": "llm_service"})
                return False
            
            try:
                # Intentar inicializar con ChatOpenAI más reciente
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    temperature=0, 
                    model="gpt-3.5-turbo",
                    max_tokens=500,         # Límite de tokens de respuesta
                    openai_api_key=openai_api_key
                )
                logger.info("LLM inicializado con ChatOpenAI (gpt-4)", 
                           extra={"component": "llm_service", "model": "gpt-4"})
                return True
                
            except ImportError:
                try:
                    # Fallback a la versión anterior
                    from langchain.chat_models import ChatOpenAI
                    self.llm = ChatOpenAI(
                        temperature=0, 
                        model="gpt-3.5-turbo",
                        max_tokens=500,         # Límite de tokens de respuesta
                        openai_api_key=openai_api_key
                    )
                    logger.info("LLM inicializado con ChatOpenAI fallback (gpt-3.5-turbo)", 
                               extra={"component": "llm_service", "model": "gpt-3.5-turbo"})
                    return True
                    
                except ImportError:
                    logger.error("No se pudo importar ChatOpenAI", 
                                extra={"component": "llm_service"})
                    return False
                    
        except Exception as e:
            logger.error(f"Error inicializando LLM: {e}", 
                        extra={"component": "llm_service"})
            return False
    
    def initialize_qa_chains(self, vector_store_configs: Optional[Dict[str, Any]] = None) -> bool:
        """
        Inicializa cadenas de QA para RAG
        
        Args:
            vector_store_configs: Configuraciones de vectorstore
            
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando cadenas QA", 
                       extra={"component": "llm_service", "action": "init_qa_chains"})
            
            if not self.llm:
                logger.warning("LLM no inicializado, no se pueden crear cadenas QA", 
                              extra={"component": "llm_service"})
                return False
            
            # Configuraciones por defecto de cadenas
            default_chains = [
                "concepto_glamping",
                "ubicacion_contacto", 
                "domos_info",
                "servicios_incluidos",
                "actividades_adicionales",
                "politicas_glamping",
                "accesibilidad",
                "requisitos_reserva",
                "domos_precios",
                "que_es_brillo_luna",
                "servicios_externos",
                "sugerencias_movilidad_reducida",
                "politicas_privacidad",
                "politicas_cancelacion",
                "links_imagenes"
            ]
            
            # Intentar cargar cadenas QA reales desde rag_engine
            try:
                import rag_engine
                
                # Usar las cadenas QA que ya están cargadas con datos reales
                if hasattr(rag_engine, 'qa_chains') and rag_engine.qa_chains:
                    self.qa_chains = rag_engine.qa_chains.copy()
                    successful_chains = len([chain for chain in self.qa_chains.values() if chain is not None])
                    
                    logger.info(f"Cadenas QA cargadas desde rag_engine con datos reales: {successful_chains}/{len(self.qa_chains)}", 
                               extra={"component": "llm_service", "source": "rag_engine"})
                else:
                    logger.warning("rag_engine.qa_chains no disponible, creando cadenas básicas", 
                                  extra={"component": "llm_service"})
                    raise ImportError("qa_chains no disponible")
                    
            except (ImportError, Exception) as e:
                logger.warning(f"No se pudo cargar rag_engine ({e}), usando cadenas básicas", 
                              extra={"component": "llm_service"})
                
                # Fallback: Crear cadenas QA básicas (sin vectorstore)
                for chain_name in default_chains:
                    try:
                        # Crear cadena QA simple
                        from langchain.chains import LLMChain
                        from langchain.prompts import PromptTemplate
                        
                        prompt = PromptTemplate(
                            input_variables=["question"],
                            template=f"Responde la siguiente pregunta sobre {chain_name}: {{question}}"
                        )
                        
                        chain = LLMChain(
                            llm=self.llm,
                            prompt=prompt
                        )
                        
                        self.qa_chains[chain_name] = chain
                        
                    except Exception as e:
                        logger.warning(f"No se pudo crear cadena {chain_name}: {e}", 
                                      extra={"component": "llm_service", "chain": chain_name})
                        continue
            
            logger.info(f"Cadenas QA inicializadas: {len(self.qa_chains)}/{len(default_chains)}", 
                       extra={"component": "llm_service", "chains_count": len(self.qa_chains)})
            
            return len(self.qa_chains) > 0
            
        except Exception as e:
            logger.error(f"Error inicializando cadenas QA: {e}", 
                        extra={"component": "llm_service"})
            return False
    
    def call_llm_with_retry(self, prompt: str, max_retries: int = 3, temperature: float = 0) -> Tuple[bool, str, str]:
        """
        Llama al LLM con reintentos (extraído de agente.py líneas 1861-1905)
        
        Args:
            prompt: Prompt a enviar
            max_retries: Número máximo de reintentos
            temperature: Temperatura para el modelo
            
        Returns:
            Tuple[bool, str, str]: (success, response, error_message)
        """
        try:
            if not self.llm:
                return False, "", "LLM no inicializado"
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Llamando LLM (intento {attempt + 1}/{max_retries})", 
                               extra={"component": "llm_service", "attempt": attempt + 1})
                    
                    # Crear LLM temporal con temperatura específica si es diferente
                    llm_to_use = self.llm
                    if temperature != 0:
                        try:
                            from langchain_openai import ChatOpenAI
                            llm_to_use = ChatOpenAI(
                                temperature=temperature,
                                model="gpt-4" if "gpt-4" in str(self.llm) else "gpt-3.5-turbo",
                                openai_api_key=os.getenv("OPENAI_API_KEY")
                            )
                        except:
                            llm_to_use = self.llm
                    
                    response = llm_to_use.predict(prompt)
                    
                    logger.info("LLM respondió exitosamente", 
                               extra={"component": "llm_service", "response_length": len(response)})
                    
                    return True, response, ""
                    
                except Exception as e:
                    logger.warning(f"Error en intento {attempt + 1}: {e}", 
                                  extra={"component": "llm_service", "attempt": attempt + 1})
                    
                    if attempt == max_retries - 1:
                        error_msg = f"LLM falló después de {max_retries} intentos: {e}"
                        logger.error(error_msg, extra={"component": "llm_service"})
                        return False, "", error_msg
                    
                    # Esperar antes del siguiente intento
                    time.sleep(2 ** attempt)
            
            return False, "", "Máximo número de reintentos alcanzado"
            
        except Exception as e:
            error_msg = f"Error llamando LLM: {e}"
            logger.error(error_msg, extra={"component": "llm_service"})
            return False, "", error_msg
    
    def generate_simple_response(self, prompt: str) -> str:
        """
        Genera una respuesta simple usando el LLM directamente sin agente completo
        Útil para manejo de errores donde no queremos activar el agente completo
        """
        try:
            if not self.llm:
                logger.warning("LLM no inicializado para respuesta simple")
                return ""
            
            # Usar call_llm_with_retry que ya tiene manejo de errores
            success, response, error = self.call_llm_with_retry(prompt, max_retries=2, temperature=0.3)
            
            if success and response:
                return response.strip()
            else:
                logger.error(f"Error generando respuesta simple: {error}")
                return ""
                
        except Exception as e:
            logger.error(f"Error inesperado en generate_simple_response: {e}")
            return ""
    
    def initialize_agent_safe(self, tools: List[Any], memory: Any, max_retries: int = 3) -> Tuple[bool, Any, str]:
        """
        Inicializa agente de forma segura (extraído de agente.py líneas 1950-1993)
        
        Args:
            tools: Lista de herramientas
            memory: Memoria conversacional
            max_retries: Máximo de reintentos
            
        Returns:
            Tuple[bool, Any, str]: (success, agent, error_message)
        """
        try:
            if not self.llm:
                return False, None, "LLM no inicializado"
            
            logger.info("Inicializando agente conversacional", 
                       extra={"component": "llm_service", "tools_count": len(tools)})
            
            for attempt in range(max_retries):
                try:
                    from langchain.agents import initialize_agent, AgentType
                    
                    # Integrar PromptService para optimización del agente
                    from services.prompt_service import get_prompt_service

                    prompt_service = get_prompt_service()
                    system_prompt = prompt_service.get_main_system_prompt()

                    agent = initialize_agent(
                        tools=tools,
                        llm=self.llm,
                        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                        memory=memory,
                        verbose=False,
                        handle_parsing_errors=True,
                        max_iterations=3,
                        early_stopping_method="generate",
                        agent_kwargs={
                            'system_message': system_prompt,
                            'human_message': "Usuario: {input}\n\nAsistente:",
                            'format_instructions': "Usa las herramientas disponibles cuando sea necesario. Responde como el asistente especializado de Glamping Brillo de Luna."
                        }
                    )
                    
                    logger.info("Agente inicializado exitosamente", 
                               extra={"component": "llm_service", "attempt": attempt + 1})
                    
                    return True, agent, ""
                    
                except Exception as e:
                    logger.warning(f"Error inicializando agente (intento {attempt + 1}): {e}", 
                                  extra={"component": "llm_service", "attempt": attempt + 1})
                    
                    if attempt == max_retries - 1:
                        error_msg = f"Fallo inicializando agente después de {max_retries} intentos: {e}"
                        logger.error(error_msg, extra={"component": "llm_service"})
                        return False, None, error_msg
                    
                    time.sleep(1)
            
            return False, None, "Máximo número de reintentos alcanzado"
            
        except Exception as e:
            error_msg = f"Error inicializando agente: {e}"
            logger.error(error_msg, extra={"component": "llm_service"})
            return False, None, error_msg
    
    def run_agent_safe(self, agent: Any, user_input: str, max_retries: int = 2, user_id: str = "anonymous") -> Tuple[bool, str, str]:
        """
        Ejecuta agente de forma segura con cache inteligente, rate limiting y throttling
        
        Args:
            agent: Agente a ejecutar
            user_input: Input del usuario
            max_retries: Máximo de reintentos
            user_id: ID del usuario para rate limiting
            
        Returns:
            Tuple[bool, str, str]: (success, response, error_message)
        """
        try:
            if not agent:
                return False, "", "Agente no disponible"
            
            # Intentar obtener respuesta del cache primero
            cached_response = self.response_cache.get(user_input)
            if cached_response:
                logger.info("Respuesta servida desde cache", 
                           extra={"component": "llm_service", "input_length": len(user_input), "user_id": user_id})
                return True, cached_response, ""
            
            # Verificar throttling automático
            should_throttle, throttle_wait = self.throttler.should_throttle()
            if should_throttle:
                logger.warning(f"Request throttled - esperando {throttle_wait:.1f}s", 
                             extra={"component": "llm_service", "user_id": user_id})
                # Esperar o devolver mensaje de throttling
                if throttle_wait < 5:  # Si es poco tiempo, esperar
                    time.sleep(throttle_wait)
                else:  # Si es mucho tiempo, devolver mensaje
                    return False, "", f"Sistema temporalmente limitado. Intenta en {throttle_wait:.0f} segundos."
            
            # Verificar rate limiting por usuario
            can_proceed, limit_reason, wait_seconds = self.rate_limiter.can_make_request(user_id)
            if not can_proceed:
                logger.warning(f"Rate limit exceeded para {user_id}: {limit_reason}", 
                             extra={"component": "llm_service", "user_id": user_id})
                return False, "", f"Has alcanzado el límite de consultas. {limit_reason}. Intenta en {wait_seconds} segundos."
            
            # Registrar la llamada en el rate limiter
            self.rate_limiter.record_request(user_id)
            
            logger.info("Ejecutando agente (cache miss)", 
                       extra={"component": "llm_service", "input_length": len(user_input), "user_id": user_id})
            
            for attempt in range(max_retries):
                try:
                    response = agent.run(input=user_input)
                    
                    logger.info("Agente ejecutado exitosamente", 
                               extra={"component": "llm_service", "response_length": len(response), "user_id": user_id})
                    
                    # Registrar éxito en throttler
                    self.throttler.record_success()
                    
                    # Almacenar respuesta en cache
                    self.response_cache.set(user_input, response)
                    
                    return True, response, ""
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # Extraer código de error si es posible
                    error_code = None
                    if "429" in error_str:
                        error_code = 429
                    elif "401" in error_str:
                        error_code = 401
                    elif "403" in error_str:
                        error_code = 403
                    elif "500" in error_str:
                        error_code = 500
                    
                    # Registrar error en throttler
                    self.throttler.record_error(error_code)
                    
                    logger.warning(f"Error ejecutando agente (intento {attempt + 1}): {e}", 
                                  extra={"component": "llm_service", "attempt": attempt + 1, "user_id": user_id, "error_code": error_code})
                    
                    if attempt == max_retries - 1:
                        error_msg = f"Agente falló después de {max_retries} intentos: {e}"
                        logger.error(error_msg, extra={"component": "llm_service", "user_id": user_id})
                        return False, "", error_msg
                    
                    # Delay progresivo entre reintentos
                    delay = min(2 ** attempt, 10)  # Exponencial hasta 10s max
                    time.sleep(delay)
            
            return False, "", "Máximo número de reintentos alcanzado"
            
        except Exception as e:
            error_msg = f"Error ejecutando agente: {e}"
            logger.error(error_msg, extra={"component": "llm_service"})
            return False, "", error_msg
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud del servicio LLM
        
        Returns:
            Dict[str, Any]: Estado de salud
        """
        try:
            health_status = {
                'service_name': 'LLMService',
                'llm_initialized': self.llm is not None,
                'qa_chains_count': len(self.qa_chains),
                'tools_count': len(self.tools),
                'openai_api_key_configured': bool(os.getenv('OPENAI_API_KEY')),
                'timestamp': time.time()
            }
            
            # Test básico de LLM si está disponible
            if self.llm:
                try:
                    test_response = self.llm.predict("Test")
                    health_status['llm_test'] = 'ok'
                except Exception as e:
                    health_status['llm_test'] = f'error: {str(e)}'
            
            health_status['status'] = 'healthy' if health_status['llm_initialized'] else 'degraded'
            
            return health_status
            
        except Exception as e:
            return {
                'service_name': 'LLMService',
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def create_contextual_prompt(self, user_input: str, context: dict) -> str:
        """
        Crea prompt con contexto específico, personalidad y optimización LLM
        
        Args:
            user_input: Entrada del usuario
            context: Contexto previo del usuario
            
        Returns:
            str: Prompt optimizado contextualizado
        """
        try:
            # Usar PromptService para crear prompt optimizado
            from services.prompt_service import get_prompt_service
            prompt_service = get_prompt_service()
            
            # Crear prompt dinámico basado en análisis del input y contexto
            optimized_prompt = prompt_service.create_dynamic_prompt(user_input, context)
            
            logger.info(f"Prompt optimizado creado con PromptService", 
                       extra={"component": "llm_service", "with_prompt_optimization": True})
            
            return optimized_prompt
            
        except Exception as e:
            logger.error(f"Error creando prompt optimizado: {e}", 
                        extra={"component": "llm_service"})
            
            # Fallback usando PersonalityService si PromptService falla
            try:
                from services.personality_service import get_personality_service
                personality_service = get_personality_service()
                fallback_prompt = personality_service.create_contextual_prompt(user_input, context)
                
                logger.info("Using PersonalityService fallback for prompt creation")
                return fallback_prompt
                
            except Exception as fallback_error:
                logger.error(f"Error en fallback de personalidad: {fallback_error}")
                
                # Último recurso: prompt básico robusto
                return f"""Eres el asistente virtual de Glamping Brillo de Luna en Guatavita, Colombia.

PERSONALIDAD: Cálido, profesional y entusiasta sobre la experiencia de glamping.

MISIÓN: Ayudar con información sobre domos, servicios, actividades y reservas.

Usuario pregunta: {user_input}

Responde de manera completa y útil usando las herramientas RAG disponibles."""
    
    def initialize_all(self) -> bool:
        """
        Inicializa todos los componentes del servicio LLM
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando todos los componentes LLM", 
                       extra={"component": "llm_service", "action": "init_all"})
            
            # Inicializar LLM
            llm_ok = self.initialize_llm()
            
            # Inicializar cadenas QA
            qa_ok = self.initialize_qa_chains()
            
            success = llm_ok  # LLM es crítico, QA es opcional
            
            logger.info(f"Inicialización completa - LLM: {llm_ok}, QA: {qa_ok}", 
                       extra={"component": "llm_service", "llm": llm_ok, "qa": qa_ok})
            
            return success
            
        except Exception as e:
            logger.error(f"Error en inicialización completa: {e}", 
                        extra={"component": "llm_service"})
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del sistema LLM"""
        return {
            'cache': {
                'cache_enabled': True,
                'cache_duration_minutes': 10,
                **self.response_cache.get_stats()
            },
            'rate_limiting': self.rate_limiter.get_stats(),
            'throttling': self.throttler.get_stats()
        }
    
    def clear_cache(self):
        """Limpia el cache de respuestas"""
        self.response_cache.clear()
        logger.info("Cache de respuestas limpiado", extra={"component": "llm_service"})


def get_llm_service() -> LLMService:
    """
    Factory function para crear instancia de LLMService
    
    Returns:
        LLMService: Instancia del servicio
    """
    return LLMService()


def initialize_llm_service() -> LLMService:
    """
    Inicializa completamente el servicio LLM
    
    Returns:
        LLMService: Servicio LLM inicializado
    """
    service = LLMService()
    service.initialize_all()
    return service