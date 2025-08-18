# Memory service - Enhanced memory management
# This will improve the current memory system

import os
from utils.logger import get_logger

logger = get_logger(__name__)

def create_memory_directory(memory_dir: str = "memory") -> bool:
    """
    Crea directorio de memoria si no existe
    
    Args:
        memory_dir: Directorio de memoria
        
    Returns:
        bool: True si se creó o ya existe
    """
    try:
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
            logger.info(f"Directorio de memoria creado: {memory_dir}")
        else:
            logger.info(f"Directorio de memoria ya existe: {memory_dir}")
        return True
    except Exception as e:
        logger.error(f"Error creando directorio de memoria: {e}")
        return False

# TODO: Move memory functions here from agente.py
# For now, keeping original memory functions in agente.py to maintain compatibility

def enhanced_save_user_memory(user_id: str, memory, state=None):
    """
    Future enhanced memory saving with state integration
    """
    # TODO: Implement enhanced memory saving
    pass

def enhanced_load_user_memory(user_id: str):
    """
    Future enhanced memory loading with state recovery
    """
    # TODO: Implement enhanced memory loading
    pass

def cleanup_old_memories(days_threshold: int = 30):
    """
    Future automatic cleanup of old memories
    """
    # TODO: Implement memory cleanup
    pass