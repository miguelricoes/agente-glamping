-- Migración para agregar columnas faltantes a user_conversation_states
-- Ejecutar en Railway PostgreSQL Dashboard

-- Agregar las tres columnas faltantes que el código necesita
ALTER TABLE user_conversation_states
ADD COLUMN previous_context VARCHAR(100) DEFAULT '',
ADD COLUMN last_action VARCHAR(100) DEFAULT '',
ADD COLUMN waiting_for_continuation BOOLEAN DEFAULT FALSE;

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_user_conversation_states_last_action ON user_conversation_states(last_action);
CREATE INDEX IF NOT EXISTS idx_user_conversation_states_waiting_continuation ON user_conversation_states(waiting_for_continuation);

-- Verificar que las columnas se crearon correctamente
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'user_conversation_states' 
AND column_name IN ('previous_context', 'last_action', 'waiting_for_continuation')
ORDER BY column_name;