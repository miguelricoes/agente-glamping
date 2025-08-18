# Migración para crear tabla de estado conversacional persistente
# Migra de diccionarios volátiles a PostgreSQL

import os
import sys
from datetime import datetime
from sqlalchemy import text

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger, log_database_operation

# Inicializar logger para migración
logger = get_logger(__name__)

def create_conversation_state_table(db):
    """
    Crear tabla user_conversation_states para estado persistente
    
    Args:
        db: Instancia de SQLAlchemy
    """
    
    logger.info("Iniciando migración: crear tabla user_conversation_states",
               extra={"phase": "migration", "operation": "create_table"})
    
    # SQL para crear la tabla
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_conversation_states (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(100) UNIQUE NOT NULL,
        current_flow VARCHAR(50) DEFAULT 'none' NOT NULL,
        reserva_step INTEGER DEFAULT 0 NOT NULL,
        waiting_for_availability BOOLEAN DEFAULT FALSE NOT NULL,
        reserva_data JSONB DEFAULT '{}',
        conversation_memory JSONB DEFAULT '{}',
        last_interaction TIMESTAMP DEFAULT NOW() NOT NULL,
        created_at TIMESTAMP DEFAULT NOW() NOT NULL,
        total_messages INTEGER DEFAULT 0 NOT NULL,
        last_endpoint VARCHAR(50)
    );
    """
    
    # SQL para crear índices
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_user_conversation_states_user_id ON user_conversation_states(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_conversation_states_current_flow ON user_conversation_states(current_flow);",
        "CREATE INDEX IF NOT EXISTS idx_user_conversation_states_last_interaction ON user_conversation_states(last_interaction);",
        "CREATE INDEX IF NOT EXISTS idx_user_conversation_states_created_at ON user_conversation_states(created_at);"
    ]
    
    try:
        # Ejecutar creación de tabla
        db.session.execute(text(create_table_sql))
        logger.info("Tabla user_conversation_states creada exitosamente",
                   extra={"phase": "migration", "operation": "create_table"})
        
        # Ejecutar creación de índices
        for idx, index_sql in enumerate(create_indexes_sql):
            db.session.execute(text(index_sql))
            logger.debug(f"Índice {idx + 1} creado exitosamente",
                        extra={"phase": "migration", "operation": "create_index"})
        
        # Confirmar cambios
        db.session.commit()
        
        log_database_operation(logger, "CREATE", "user_conversation_states", True,
                             "Tabla e índices creados exitosamente")
        
        logger.info("Migración completada exitosamente",
                   extra={"phase": "migration", "status": "completed"})
        
        return True
        
    except Exception as e:
        logger.error(f"Error en migración: {e}",
                    extra={"phase": "migration", "operation": "create_table"})
        db.session.rollback()
        
        log_database_operation(logger, "CREATE", "user_conversation_states", False,
                             f"Error: {e}")
        
        return False

def migrate_existing_data(db, user_states_dict=None, user_memories_dict=None):
    """
    Migrar datos existentes de diccionarios a la nueva tabla
    
    Args:
        db: Instancia de SQLAlchemy
        user_states_dict: Diccionario user_states actual (opcional)
        user_memories_dict: Diccionario user_memories actual (opcional)
    """
    
    if not user_states_dict and not user_memories_dict:
        logger.info("No hay datos existentes para migrar",
                   extra={"phase": "migration", "operation": "data_migration"})
        return True
    
    logger.info("Iniciando migración de datos existentes",
               extra={"phase": "migration", "operation": "data_migration"})
    
    try:
        migrated_count = 0
        
        # Migrar user_states
        if user_states_dict:
            for user_id, state_data in user_states_dict.items():
                # Preparar datos de memoria si existe
                memory_data = user_memories_dict.get(user_id, {}) if user_memories_dict else {}
                
                # Convertir memoria a formato serializable
                if hasattr(memory_data, 'chat_memory'):
                    from langchain.schema import messages_to_dict
                    if hasattr(memory_data.chat_memory, 'messages'):
                        serialized_memory = {
                            "messages": messages_to_dict(memory_data.chat_memory.messages),
                            "type": "ConversationBufferMemory"
                        }
                    else:
                        serialized_memory = {"type": "ConversationBufferMemory", "messages": []}
                else:
                    serialized_memory = memory_data if isinstance(memory_data, dict) else {}
                
                # Insertar en nueva tabla
                insert_sql = """
                INSERT INTO user_conversation_states 
                (user_id, current_flow, reserva_step, waiting_for_availability, 
                 reserva_data, conversation_memory, last_interaction, total_messages)
                VALUES (:user_id, :current_flow, :reserva_step, :waiting_for_availability,
                        :reserva_data, :conversation_memory, :last_interaction, :total_messages)
                ON CONFLICT (user_id) DO UPDATE SET
                    current_flow = EXCLUDED.current_flow,
                    reserva_step = EXCLUDED.reserva_step,
                    waiting_for_availability = EXCLUDED.waiting_for_availability,
                    reserva_data = EXCLUDED.reserva_data,
                    conversation_memory = EXCLUDED.conversation_memory,
                    last_interaction = EXCLUDED.last_interaction,
                    total_messages = EXCLUDED.total_messages
                """
                
                db.session.execute(text(insert_sql), {
                    'user_id': user_id,
                    'current_flow': state_data.get('current_flow', 'none'),
                    'reserva_step': state_data.get('reserva_step', 0),
                    'waiting_for_availability': state_data.get('waiting_for_availability', False),
                    'reserva_data': state_data.get('reserva_data', {}),
                    'conversation_memory': serialized_memory,
                    'last_interaction': datetime.utcnow(),
                    'total_messages': 1  # Asumir al menos 1 mensaje por existir el estado
                })
                
                migrated_count += 1
        
        # Confirmar migración
        db.session.commit()
        
        logger.info(f"Migración de datos completada: {migrated_count} usuarios migrados",
                   extra={"phase": "migration", "migrated_users": migrated_count})
        
        log_database_operation(logger, "MIGRATE", "user_conversation_states", True,
                             f"{migrated_count} usuarios migrados")
        
        return True
        
    except Exception as e:
        logger.error(f"Error migrando datos: {e}",
                    extra={"phase": "migration", "operation": "data_migration"})
        db.session.rollback()
        
        log_database_operation(logger, "MIGRATE", "user_conversation_states", False,
                             f"Error: {e}")
        
        return False

def verify_migration(db):
    """
    Verificar que la migración se completó correctamente
    
    Args:
        db: Instancia de SQLAlchemy
        
    Returns:
        True si la verificación es exitosa
    """
    
    logger.info("Verificando migración",
               extra={"phase": "migration", "operation": "verification"})
    
    try:
        # Verificar que la tabla existe
        result = db.session.execute(text("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_name = 'user_conversation_states'
        """)).fetchone()
        
        if result.table_count == 0:
            logger.error("Tabla user_conversation_states no existe",
                        extra={"phase": "migration", "operation": "verification"})
            return False
        
        # Verificar estructura de la tabla
        result = db.session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_conversation_states'
            ORDER BY ordinal_position
        """)).fetchall()
        
        expected_columns = {
            'id', 'user_id', 'current_flow', 'reserva_step', 'waiting_for_availability',
            'reserva_data', 'conversation_memory', 'last_interaction', 'created_at',
            'total_messages', 'last_endpoint'
        }
        
        actual_columns = {row.column_name for row in result}
        
        if not expected_columns.issubset(actual_columns):
            missing = expected_columns - actual_columns
            logger.error(f"Columnas faltantes en tabla: {missing}",
                        extra={"phase": "migration", "operation": "verification"})
            return False
        
        # Verificar índices
        result = db.session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'user_conversation_states'
        """)).fetchall()
        
        index_count = len(result)
        
        logger.info(f"Verificación exitosa: tabla con {len(actual_columns)} columnas y {index_count} índices",
                   extra={"phase": "migration", "operation": "verification", 
                          "columns": len(actual_columns), "indexes": index_count})
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando migración: {e}",
                    extra={"phase": "migration", "operation": "verification"})
        return False

def run_migration(db, user_states_dict=None, user_memories_dict=None):
    """
    Ejecutar migración completa
    
    Args:
        db: Instancia de SQLAlchemy
        user_states_dict: Diccionario user_states actual (opcional)
        user_memories_dict: Diccionario user_memories actual (opcional)
        
    Returns:
        True si la migración fue exitosa
    """
    
    logger.info("Iniciando migración completa de estado conversacional",
               extra={"phase": "migration", "operation": "full_migration"})
    
    try:
        # Paso 1: Crear tabla e índices
        if not create_conversation_state_table(db):
            return False
        
        # Paso 2: Migrar datos existentes
        if not migrate_existing_data(db, user_states_dict, user_memories_dict):
            return False
        
        # Paso 3: Verificar migración
        if not verify_migration(db):
            return False
        
        logger.info("Migración completa exitosa",
                   extra={"phase": "migration", "status": "completed"})
        
        return True
        
    except Exception as e:
        logger.error(f"Error en migración completa: {e}",
                    extra={"phase": "migration", "operation": "full_migration"})
        return False

if __name__ == "__main__":
    """Script para ejecutar migración desde línea de comandos"""
    
    print("Ejecutando migración de estado conversacional...")
    
    # Importar dependencias
    try:
        # Removida dependencia de agente.py - ahora recibe db como parámetro
        
        if db is None:
            print("ERROR: Base de datos no disponible")
            sys.exit(1)
        
        # Ejecutar migración
        success = run_migration(db)
        
        if success:
            print("✅ Migración completada exitosamente")
            sys.exit(0)
        else:
            print("❌ Error en migración")
            sys.exit(1)
            
    except ImportError as e:
        print(f"ERROR: No se pudieron importar dependencias: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)