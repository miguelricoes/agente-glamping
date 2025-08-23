# Modelo de base de datos para estado conversacional persistente
# Reemplaza los diccionarios volátiles user_states y user_memories con PostgreSQL

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import json
from typing import Dict, Any, Optional
from utils.logger import get_logger

# Inicializar logger para este módulo
logger = get_logger(__name__)

class ConversationStateDB:
    """
    Modelo de base de datos para estado conversacional persistente
    Almacena tanto el estado del flujo como la memoria conversacional en PostgreSQL
    """
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self._create_model()
    
    def _create_model(self):
        """Crear el modelo de SQLAlchemy"""
        
        class UserConversationState(self.db.Model):
            __tablename__ = 'user_conversation_states'
            
            # Identificadores
            id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.String(100), unique=True, nullable=False, index=True)
            
            # Estado del flujo conversacional
            current_flow = self.db.Column(self.db.String(50), default='none', nullable=False)
            reserva_step = self.db.Column(self.db.Integer, default=0, nullable=False)
            waiting_for_availability = self.db.Column(self.db.Boolean, default=False, nullable=False)
            
            # NUEVOS CAMPOS para manejo de contexto
            previous_context = self.db.Column(self.db.String(100), default='', nullable=True)
            last_action = self.db.Column(self.db.String(100), default='', nullable=True)
            waiting_for_continuation = self.db.Column(self.db.Boolean, default=False, nullable=False)
            
            # Datos de reserva en progreso (JSON)
            reserva_data = self.db.Column(self.db.JSON, default=dict, nullable=True)
            
            # Memoria conversacional (JSON)
            conversation_memory = self.db.Column(self.db.JSON, default=dict, nullable=True)
            
            # Metadatos
            last_interaction = self.db.Column(self.db.DateTime, default=datetime.utcnow, nullable=False)
            created_at = self.db.Column(self.db.DateTime, default=datetime.utcnow, nullable=False)
            
            # Campos adicionales para analytics
            total_messages = self.db.Column(self.db.Integer, default=0, nullable=False)
            last_endpoint = self.db.Column(self.db.String(50), nullable=True)
            
            def __repr__(self):
                return f'<UserConversationState {self.user_id}: {self.current_flow}>'
            
            def to_dict(self) -> Dict[str, Any]:
                """Convertir a diccionario compatible con el sistema actual"""
                return {
                    'current_flow': self.current_flow,
                    'reserva_step': self.reserva_step,
                    'reserva_data': self.reserva_data or {},
                    'waiting_for_availability': self.waiting_for_availability,
                    'previous_context': self.previous_context or '',  # NUEVO
                    'last_action': self.last_action or '',           # NUEVO
                    'waiting_for_continuation': self.waiting_for_continuation,  # NUEVO
                    'conversation_memory': self.conversation_memory or {},
                    'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None,
                    'total_messages': self.total_messages
                }
            
            def update_from_dict(self, state_dict: Dict[str, Any]):
                """Actualizar desde diccionario compatible"""
                self.current_flow = state_dict.get('current_flow', 'none')
                self.reserva_step = state_dict.get('reserva_step', 0)
                self.reserva_data = state_dict.get('reserva_data', {})
                self.waiting_for_availability = state_dict.get('waiting_for_availability', False)
                self.previous_context = state_dict.get('previous_context', '')  # NUEVO
                self.last_action = state_dict.get('last_action', '')           # NUEVO
                self.waiting_for_continuation = state_dict.get('waiting_for_continuation', False)  # NUEVO
                self.last_interaction = datetime.utcnow()
        
        self.UserConversationState = UserConversationState
    
    def get_or_create_state(self, user_id: str) -> 'UserConversationState':
        """
        Obtener o crear estado conversacional para un usuario
        
        Args:
            user_id: Identificador único del usuario (phone/session_id)
            
        Returns:
            Instancia del estado conversacional
        """
        try:
            # Buscar estado existente
            state = self.UserConversationState.query.filter_by(user_id=user_id).first()
            
            if not state:
                # Crear nuevo estado
                state = self.UserConversationState(
                    user_id=user_id,
                    current_flow='none',
                    reserva_step=0,
                    waiting_for_availability=False,
                    previous_context='',  # NUEVO
                    last_action='',       # NUEVO
                    waiting_for_continuation=False,  # NUEVO
                    reserva_data={},
                    conversation_memory={}
                )
                self.db.session.add(state)
                self.db.session.commit()
                
                logger.info(f"Nuevo estado conversacional creado para usuario: {user_id}",
                          extra={"user_id": user_id, "phase": "state_creation"})
            
            return state
            
        except Exception as e:
            logger.error(f"Error obteniendo estado conversacional: {e}",
                        extra={"user_id": user_id, "phase": "state_retrieval"})
            self.db.session.rollback()
            raise
    
    def update_state(self, user_id: str, state_updates: Dict[str, Any]) -> bool:
        """
        Actualizar estado conversacional
        
        Args:
            user_id: Identificador del usuario
            state_updates: Diccionario con las actualizaciones
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            state = self.get_or_create_state(user_id)
            
            # Actualizar campos
            if 'current_flow' in state_updates:
                state.current_flow = state_updates['current_flow']
            if 'reserva_step' in state_updates:
                state.reserva_step = state_updates['reserva_step']
            if 'waiting_for_availability' in state_updates:
                state.waiting_for_availability = state_updates['waiting_for_availability']
            if 'reserva_data' in state_updates:
                state.reserva_data = state_updates['reserva_data']
            if 'last_endpoint' in state_updates:
                state.last_endpoint = state_updates['last_endpoint']
            
            # Incrementar contador de mensajes si es una interacción
            if state_updates.get('increment_messages', False):
                state.total_messages += 1
            
            # Actualizar timestamp
            state.last_interaction = datetime.utcnow()
            
            self.db.session.commit()
            
            logger.debug(f"Estado actualizado para usuario: {user_id}",
                        extra={"user_id": user_id, "updates": list(state_updates.keys()), "phase": "state_update"})
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}",
                        extra={"user_id": user_id, "phase": "state_update"})
            self.db.session.rollback()
            return False
    
    def update_memory(self, user_id: str, memory_data: Dict[str, Any]) -> bool:
        """
        Actualizar memoria conversacional
        
        Args:
            user_id: Identificador del usuario
            memory_data: Datos de memoria a guardar
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            state = self.get_or_create_state(user_id)
            state.conversation_memory = memory_data
            state.last_interaction = datetime.utcnow()
            
            self.db.session.commit()
            
            logger.debug(f"Memoria actualizada para usuario: {user_id}",
                        extra={"user_id": user_id, "memory_size": len(str(memory_data)), "phase": "memory_update"})
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando memoria: {e}",
                        extra={"user_id": user_id, "phase": "memory_update"})
            self.db.session.rollback()
            return False
    
    def get_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener memoria conversacional
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Diccionario con la memoria conversacional
        """
        try:
            state = self.get_or_create_state(user_id)
            return state.conversation_memory or {}
            
        except Exception as e:
            logger.error(f"Error obteniendo memoria: {e}",
                        extra={"user_id": user_id, "phase": "memory_retrieval"})
            return {}
    
    def cleanup_old_states(self, days_old: int = 30) -> int:
        """
        Limpiar estados conversacionales antiguos
        
        Args:
            days_old: Días de antigüedad para considerar un estado como viejo
            
        Returns:
            Número de estados eliminados
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_states = self.UserConversationState.query.filter(
                self.UserConversationState.last_interaction < cutoff_date
            ).all()
            
            count = len(old_states)
            
            for state in old_states:
                self.db.session.delete(state)
            
            self.db.session.commit()
            
            logger.info(f"Limpieza de estados: {count} estados eliminados",
                       extra={"deleted_count": count, "cutoff_days": days_old, "phase": "cleanup"})
            
            return count
            
        except Exception as e:
            logger.error(f"Error en limpieza de estados: {e}",
                        extra={"phase": "cleanup"})
            self.db.session.rollback()
            return 0
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de un usuario
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            state = self.UserConversationState.query.filter_by(user_id=user_id).first()
            
            if not state:
                return {"exists": False}
            
            return {
                "exists": True,
                "total_messages": state.total_messages,
                "current_flow": state.current_flow,
                "last_interaction": state.last_interaction.isoformat() if state.last_interaction else None,
                "created_at": state.created_at.isoformat() if state.created_at else None,
                "last_endpoint": state.last_endpoint
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}",
                        extra={"user_id": user_id, "phase": "stats"})
            return {"exists": False, "error": str(e)}