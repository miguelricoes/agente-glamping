# Servicio de estado persistente - Reemplaza diccionarios volátiles con PostgreSQL
# Mantiene compatibilidad total con el sistema existente

from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta
from utils.logger import get_logger, log_database_operation
from models.conversation_state_db import ConversationStateDB

# Inicializar logger para este módulo
logger = get_logger(__name__)

class PersistentStateService:
    """
    Servicio de estado persistente que reemplaza user_states y user_memories
    Mantiene compatibilidad total con la interfaz actual
    """
    
    def __init__(self, db, enable_caching: bool = True):
        """
        Inicializar servicio de estado persistente
        
        Args:
            db: Instancia de SQLAlchemy
            enable_caching: Si habilitar caché en memoria para performance
        """
        self.db = db
        self.enable_caching = enable_caching
        self.state_db = ConversationStateDB(db)
        
        # Cache en memoria para performance (opcional)
        self._state_cache: Dict[str, Dict[str, Any]] = {}
        self._memory_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutos TTL para cache
        
        logger.info("Servicio de estado persistente inicializado",
                   extra={"caching_enabled": enable_caching, "phase": "startup"})
    
    def _is_cache_valid(self, user_id: str) -> bool:
        """Verificar si el cache es válido para un usuario"""
        if not self.enable_caching:
            return False
        
        if user_id not in self._cache_timestamps:
            return False
        
        age = datetime.utcnow() - self._cache_timestamps[user_id]
        return age.total_seconds() < self._cache_ttl
    
    def _update_cache(self, user_id: str, state_data: Dict[str, Any], memory_data: Any = None):
        """Actualizar cache para un usuario"""
        if not self.enable_caching:
            return
        
        self._state_cache[user_id] = state_data.copy()
        if memory_data is not None:
            self._memory_cache[user_id] = memory_data
        self._cache_timestamps[user_id] = datetime.utcnow()
    
    def _clear_cache(self, user_id: str):
        """Limpiar cache para un usuario"""
        self._state_cache.pop(user_id, None)
        self._memory_cache.pop(user_id, None)
        self._cache_timestamps.pop(user_id, None)
    
    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener estado de usuario (reemplaza user_states[user_id])
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Diccionario con el estado del usuario
        """
        # Verificar cache primero
        if self._is_cache_valid(user_id) and user_id in self._state_cache:
            logger.debug(f"Estado obtenido desde cache: {user_id}",
                        extra={"user_id": user_id, "source": "cache", "phase": "state_retrieval"})
            return self._state_cache[user_id].copy()
        
        try:
            # Obtener desde base de datos
            state = self.state_db.get_or_create_state(user_id)
            state_dict = state.to_dict()
            
            # Formato compatible con sistema actual
            compatible_state = {
                "current_flow": state_dict["current_flow"],
                "reserva_step": state_dict["reserva_step"],
                "reserva_data": state_dict["reserva_data"],
                "waiting_for_availability": state_dict["waiting_for_availability"]
            }
            
            # Actualizar cache
            self._update_cache(user_id, compatible_state)
            
            logger.debug(f"Estado obtenido desde DB: {user_id}",
                        extra={"user_id": user_id, "source": "database", "phase": "state_retrieval"})
            
            return compatible_state
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de usuario: {e}",
                        extra={"user_id": user_id, "phase": "state_retrieval"})
            
            # Fallback a estado por defecto
            default_state = {
                "current_flow": "none",
                "reserva_step": 0,
                "reserva_data": {},
                "waiting_for_availability": False
            }
            return default_state
    
    def update_user_state(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualizar estado de usuario (reemplaza user_states[user_id] = ...)
        
        Args:
            user_id: Identificador del usuario
            updates: Diccionario con las actualizaciones
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            # Actualizar en base de datos
            success = self.state_db.update_state(user_id, {
                **updates,
                "increment_messages": True  # Incrementar contador
            })
            
            if success:
                # Limpiar cache para forzar reload
                self._clear_cache(user_id)
                
                log_database_operation(logger, "UPDATE", "user_conversation_states", True,
                                     f"Estado actualizado para {user_id}")
                return True
            else:
                log_database_operation(logger, "UPDATE", "user_conversation_states", False,
                                     f"Error actualizando estado para {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}",
                        extra={"user_id": user_id, "phase": "state_update"})
            return False
    
    def set_user_state_field(self, user_id: str, field: str, value: Any) -> bool:
        """
        Actualizar un campo específico del estado (compatibilidad con user_states[user_id][field] = value)
        
        Args:
            user_id: Identificador del usuario
            field: Campo a actualizar
            value: Nuevo valor
            
        Returns:
            True si se actualizó exitosamente
        """
        return self.update_user_state(user_id, {field: value})
    
    def get_user_memory(self, user_id: str) -> Any:
        """
        Obtener memoria conversacional (reemplaza user_memories[user_id])
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Objeto de memoria conversacional
        """
        # Verificar cache primero
        if self._is_cache_valid(user_id) and user_id in self._memory_cache:
            logger.debug(f"Memoria obtenida desde cache: {user_id}",
                        extra={"user_id": user_id, "source": "cache", "phase": "memory_retrieval"})
            return self._memory_cache[user_id]
        
        try:
            # Obtener desde base de datos
            memory_data = self.state_db.get_memory(user_id)
            
            # Si no hay memoria, devolver None para que el sistema cree una nueva
            if not memory_data:
                return None
            
            # Actualizar cache
            self._update_cache(user_id, {}, memory_data)
            
            logger.debug(f"Memoria obtenida desde DB: {user_id}",
                        extra={"user_id": user_id, "source": "database", "phase": "memory_retrieval"})
            
            return memory_data
            
        except Exception as e:
            logger.error(f"Error obteniendo memoria: {e}",
                        extra={"user_id": user_id, "phase": "memory_retrieval"})
            return None
    
    def set_user_memory(self, user_id: str, memory: Any) -> bool:
        """
        Guardar memoria conversacional (reemplaza user_memories[user_id] = ...)
        
        Args:
            user_id: Identificador del usuario
            memory: Objeto de memoria a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Convertir memoria a diccionario serializable
            if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                # Es un objeto ConversationBufferMemory de LangChain
                from langchain.schema import messages_to_dict
                memory_data = {
                    "messages": messages_to_dict(memory.chat_memory.messages),
                    "type": "ConversationBufferMemory"
                }
            elif isinstance(memory, dict):
                memory_data = memory
            else:
                # Fallback: convertir a string
                memory_data = {"raw": str(memory), "type": "raw"}
            
            # Guardar en base de datos
            success = self.state_db.update_memory(user_id, memory_data)
            
            if success:
                # Limpiar cache para forzar reload
                self._clear_cache(user_id)
                
                log_database_operation(logger, "UPDATE", "user_conversation_states", True,
                                     f"Memoria guardada para {user_id}")
                return True
            else:
                log_database_operation(logger, "UPDATE", "user_conversation_states", False,
                                     f"Error guardando memoria para {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error guardando memoria: {e}",
                        extra={"user_id": user_id, "phase": "memory_update"})
            return False
    
    def user_exists(self, user_id: str) -> bool:
        """
        Verificar si un usuario existe (reemplaza user_id in user_states)
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            True si el usuario existe
        """
        try:
            stats = self.state_db.get_user_stats(user_id)
            return stats.get("exists", False)
        except Exception as e:
            logger.error(f"Error verificando existencia de usuario: {e}",
                        extra={"user_id": user_id, "phase": "user_check"})
            return False
    
    def create_user_if_not_exists(self, user_id: str) -> Dict[str, Any]:
        """
        Crear usuario si no existe y devolver estado inicial
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Estado inicial del usuario
        """
        return self.get_user_state(user_id)  # get_or_create_state lo manejará
    
    def cleanup_old_users(self, days_old: int = 30) -> int:
        """
        Limpiar usuarios antiguos
        
        Args:
            days_old: Días de antigüedad para considerar un usuario como viejo
            
        Returns:
            Número de usuarios eliminados
        """
        try:
            deleted_count = self.state_db.cleanup_old_states(days_old)
            
            # Limpiar cache también
            if self.enable_caching:
                self._state_cache.clear()
                self._memory_cache.clear()
                self._cache_timestamps.clear()
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error en limpieza de usuarios: {e}",
                        extra={"phase": "cleanup"})
            return 0
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de un usuario
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Diccionario con estadísticas
        """
        return self.state_db.get_user_stats(user_id)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del sistema
        
        Returns:
            Diccionario con estadísticas globales
        """
        try:
            total_users = self.state_db.UserConversationState.query.count()
            active_users = self.state_db.UserConversationState.query.filter(
                self.state_db.UserConversationState.last_interaction >= 
                datetime.utcnow() - timedelta(days=7)
            ).count()
            
            cache_size = len(self._state_cache) if self.enable_caching else 0
            
            return {
                "total_users": total_users,
                "active_users_7d": active_users,
                "cache_enabled": self.enable_caching,
                "cache_size": cache_size,
                "cache_ttl_seconds": self._cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del sistema: {e}",
                        extra={"phase": "stats"})
            return {"error": str(e)}

# Clase de compatibilidad para migración gradual
class CompatibilityStateManager:
    """
    Manager de compatibilidad que permite migración gradual del sistema actual
    Actúa como un proxy entre los diccionarios antiguos y el nuevo sistema persistente
    """
    
    def __init__(self, persistent_service: PersistentStateService):
        self.persistent_service = persistent_service
        self.logger = get_logger(f"{__name__}.compatibility")
    
    def create_compatible_user_states(self) -> 'CompatibleUserStates':
        """Crear objeto compatible con user_states"""
        return CompatibleUserStates(self.persistent_service)
    
    def create_compatible_user_memories(self) -> 'CompatibleUserMemories':
        """Crear objeto compatible con user_memories"""
        return CompatibleUserMemories(self.persistent_service)

class CompatibleUserStates:
    """Objeto que se comporta como user_states pero usa el sistema persistente"""
    
    def __init__(self, persistent_service: PersistentStateService):
        self.persistent_service = persistent_service
    
    def __getitem__(self, user_id: str) -> Dict[str, Any]:
        return self.persistent_service.get_user_state(user_id)
    
    def __setitem__(self, user_id: str, state: Dict[str, Any]):
        self.persistent_service.update_user_state(user_id, state)
    
    def __contains__(self, user_id: str) -> bool:
        return self.persistent_service.user_exists(user_id)
    
    def get(self, user_id: str, default=None):
        if self.__contains__(user_id):
            return self.__getitem__(user_id)
        return default

class CompatibleUserMemories:
    """Objeto que se comporta como user_memories pero usa el sistema persistente"""
    
    def __init__(self, persistent_service: PersistentStateService):
        self.persistent_service = persistent_service
    
    def __getitem__(self, user_id: str):
        return self.persistent_service.get_user_memory(user_id)
    
    def __setitem__(self, user_id: str, memory):
        self.persistent_service.set_user_memory(user_id, memory)
    
    def __contains__(self, user_id: str) -> bool:
        return self.persistent_service.user_exists(user_id)
    
    def get(self, user_id: str, default=None):
        if self.__contains__(user_id):
            return self.__getitem__(user_id)
        return default