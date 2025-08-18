# Conversation state management - Enhanced user states
# This will improve the current user_states dictionary system

from typing import Dict, Any
from datetime import datetime

class ConversationState:
    """Enhanced conversation state management"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_flow = "none"
        self.step = 0
        self.context = {}
        self.session_data = {}
        self.last_activity = datetime.now()
        self.waiting_for_availability = False
        self.reserva_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility with current system"""
        return {
            "current_flow": self.current_flow,
            "reserva_step": self.step,
            "reserva_data": self.reserva_data,
            "waiting_for_availability": self.waiting_for_availability,
            "context": self.context,
            "session_data": self.session_data,
            "last_activity": self.last_activity.isoformat()
        }
    
    @classmethod
    def from_dict(cls, user_id: str, data: Dict[str, Any]):
        """Create from dictionary for compatibility with current system"""
        state = cls(user_id)
        state.current_flow = data.get("current_flow", "none")
        state.step = data.get("reserva_step", 0)
        state.reserva_data = data.get("reserva_data", {})
        state.waiting_for_availability = data.get("waiting_for_availability", False)
        state.context = data.get("context", {})
        state.session_data = data.get("session_data", {})
        
        # Handle last_activity
        last_activity = data.get("last_activity")
        if last_activity and isinstance(last_activity, str):
            try:
                state.last_activity = datetime.fromisoformat(last_activity)
            except:
                state.last_activity = datetime.now()
        else:
            state.last_activity = datetime.now()
            
        return state