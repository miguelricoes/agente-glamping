# Servicio centralizado de LLM y agentes
# Extrae inicialización de LLM, Pinecone y agentes de agente.py

import os
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    """
    Servicio centralizado para LLM, Pinecone y agentes
    Consolida toda la inicialización de IA de agente.py
    """
    
    def __init__(self):
        """Inicializar servicio de LLM"""
        self.llm = None
        self.pinecone_initialized = False
        self.qa_chains = {}
        self.tools = []
        
        logger.info("LLMService inicializado", 
                   extra={"component": "llm_service", "phase": "startup"})
    
    def initialize_pinecone(self) -> bool:
        """
        Inicializa Pinecone (extraído de agente.py líneas 122-192)
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando Pinecone", 
                       extra={"component": "llm_service", "action": "init_pinecone"})
            
            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT")
            
            if not api_key or not environment:
                logger.warning("Credenciales de Pinecone no configuradas", 
                              extra={"component": "llm_service"})
                return False
            
            try:
                import pinecone
                
                # Inicializar Pinecone
                pinecone.init(
                    api_key=api_key,
                    environment=environment
                )
                
                # Verificar conexión
                indexes = pinecone.list_indexes()
                logger.info(f"Pinecone inicializado exitosamente. Índices disponibles: {len(indexes)}", 
                           extra={"component": "llm_service", "indexes_count": len(indexes)})
                
                self.pinecone_initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Error inicializando Pinecone: {e}", 
                            extra={"component": "llm_service"})
                return False
                
        except ImportError:
            logger.warning("Biblioteca Pinecone no disponible", 
                          extra={"component": "llm_service"})
            return False
        except Exception as e:
            logger.error(f"Error en inicialización de Pinecone: {e}", 
                        extra={"component": "llm_service"})
            return False
    
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
                    model="gpt-4",
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
            
            # Crear cadenas QA básicas (sin vectorstore por ahora)
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
                    
                    agent = initialize_agent(
                        tools=tools,
                        llm=self.llm,
                        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                        memory=memory,
                        verbose=False,
                        handle_parsing_errors=True,
                        max_iterations=3,
                        early_stopping_method="generate"
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
    
    def run_agent_safe(self, agent: Any, user_input: str, max_retries: int = 2) -> Tuple[bool, str, str]:
        """
        Ejecuta agente de forma segura (extraído de agente.py líneas 1994-2066)
        
        Args:
            agent: Agente a ejecutar
            user_input: Input del usuario
            max_retries: Máximo de reintentos
            
        Returns:
            Tuple[bool, str, str]: (success, response, error_message)
        """
        try:
            if not agent:
                return False, "", "Agente no disponible"
            
            logger.info("Ejecutando agente", 
                       extra={"component": "llm_service", "input_length": len(user_input)})
            
            for attempt in range(max_retries):
                try:
                    response = agent.run(input=user_input)
                    
                    logger.info("Agente ejecutado exitosamente", 
                               extra={"component": "llm_service", "response_length": len(response)})
                    
                    return True, response, ""
                    
                except Exception as e:
                    logger.warning(f"Error ejecutando agente (intento {attempt + 1}): {e}", 
                                  extra={"component": "llm_service", "attempt": attempt + 1})
                    
                    if attempt == max_retries - 1:
                        error_msg = f"Agente falló después de {max_retries} intentos: {e}"
                        logger.error(error_msg, extra={"component": "llm_service"})
                        return False, "", error_msg
                    
                    time.sleep(1)
            
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
                'pinecone_initialized': self.pinecone_initialized,
                'qa_chains_count': len(self.qa_chains),
                'tools_count': len(self.tools),
                'openai_api_key_configured': bool(os.getenv('OPENAI_API_KEY')),
                'pinecone_api_key_configured': bool(os.getenv('PINECONE_API_KEY')),
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
    
    def initialize_all(self) -> bool:
        """
        Inicializa todos los componentes del servicio LLM
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando todos los componentes LLM", 
                       extra={"component": "llm_service", "action": "init_all"})
            
            # Inicializar Pinecone
            pinecone_ok = self.initialize_pinecone()
            
            # Inicializar LLM
            llm_ok = self.initialize_llm()
            
            # Inicializar cadenas QA
            qa_ok = self.initialize_qa_chains()
            
            success = llm_ok  # LLM es crítico, Pinecone y QA son opcionales
            
            logger.info(f"Inicialización completa - LLM: {llm_ok}, Pinecone: {pinecone_ok}, QA: {qa_ok}", 
                       extra={"component": "llm_service", "llm": llm_ok, "pinecone": pinecone_ok, "qa": qa_ok})
            
            return success
            
        except Exception as e:
            logger.error(f"Error en inicialización completa: {e}", 
                        extra={"component": "llm_service"})
            return False


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