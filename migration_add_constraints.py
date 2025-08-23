#!/usr/bin/env python3
"""
Migration script to add database constraints and indexes for concurrency safety
Adds indexes, unique constraints, and check constraints to existing tables
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import get_logger

logger = get_logger(__name__)

def get_database_url():
    """Obtener URL de base de datos desde variables de entorno"""
    DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
    DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL') 
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL
    
    if not database_url:
        raise ValueError("No se encontró URL de base de datos configurada")
    
    return database_url

def add_reservas_constraints_and_indexes(engine):
    """Añadir constraints e índices a tabla reservas"""
    migrations = [
        # Añadir índices para campos frecuentemente consultados
        {
            'name': 'idx_reservas_numero_whatsapp',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_numero_whatsapp ON reservas(numero_whatsapp);'
        },
        {
            'name': 'idx_reservas_email_contacto', 
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_email_contacto ON reservas(email_contacto);'
        },
        {
            'name': 'idx_reservas_domo',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_domo ON reservas(domo);'
        },
        {
            'name': 'idx_reservas_fecha_entrada',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_fecha_entrada ON reservas(fecha_entrada);'
        },
        {
            'name': 'idx_reservas_fecha_salida',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_fecha_salida ON reservas(fecha_salida);'
        },
        {
            'name': 'idx_reservas_fecha_creacion',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_fecha_creacion ON reservas(fecha_creacion);'
        },
        
        # Índice compuesto para consultas de disponibilidad
        {
            'name': 'idx_disponibilidad_domo_fechas',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_disponibilidad_domo_fechas ON reservas(domo, fecha_entrada, fecha_salida);'
        },
        
        # Índice para búsquedas por usuario y fecha
        {
            'name': 'idx_reservas_usuario_fecha',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reservas_usuario_fecha ON reservas(numero_whatsapp, fecha_creacion);'
        },
        
        # Unique constraint para prevenir reservas duplicadas
        {
            'name': 'uq_reserva_usuario_domo_fechas',
            'sql': '''
                ALTER TABLE reservas 
                ADD CONSTRAINT uq_reserva_usuario_domo_fechas 
                UNIQUE (numero_whatsapp, domo, fecha_entrada, fecha_salida);
            ''',
            'ignore_error': True  # Puede fallar si ya existe o hay datos duplicados
        },
        
        # Check constraints para validación de datos
        {
            'name': 'chk_cantidad_huespedes_valida',
            'sql': '''
                ALTER TABLE reservas 
                ADD CONSTRAINT chk_cantidad_huespedes_valida 
                CHECK (cantidad_huespedes > 0 AND cantidad_huespedes <= 20);
            ''',
            'ignore_error': True
        },
        {
            'name': 'chk_fechas_validas',
            'sql': '''
                ALTER TABLE reservas 
                ADD CONSTRAINT chk_fechas_validas 
                CHECK (fecha_salida > fecha_entrada);
            ''',
            'ignore_error': True
        },
        {
            'name': 'chk_monto_no_negativo',
            'sql': '''
                ALTER TABLE reservas 
                ADD CONSTRAINT chk_monto_no_negativo 
                CHECK (monto_total >= 0);
            ''',
            'ignore_error': True
        }
    ]
    
    for migration in migrations:
        try:
            logger.info(f"Aplicando migración: {migration['name']}")
            engine.execute(text(migration['sql']))
            logger.info(f"✅ Migración aplicada exitosamente: {migration['name']}")
        except SQLAlchemyError as e:
            if migration.get('ignore_error', False):
                logger.warning(f"⚠️ Migración omitida (probablemente ya existe): {migration['name']} - {e}")
            else:
                logger.error(f"❌ Error aplicando migración: {migration['name']} - {e}")
                raise

def add_usuarios_constraints_and_indexes(engine):
    """Añadir constraints e índices a tabla usuarios"""
    migrations = [
        # Índices para campos frecuentemente consultados
        {
            'name': 'idx_usuarios_email',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_email ON usuarios(email);'
        },
        {
            'name': 'idx_usuarios_rol',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);'
        },
        {
            'name': 'idx_usuarios_fecha_creacion',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_fecha_creacion ON usuarios(fecha_creacion);'
        },
        {
            'name': 'idx_usuarios_activo',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_activo ON usuarios(activo);'
        },
        {
            'name': 'idx_usuarios_ultimo_acceso',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso);'
        },
        
        # Índices compuestos
        {
            'name': 'idx_usuarios_activos',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_activos ON usuarios(activo, fecha_creacion);'
        },
        {
            'name': 'idx_usuarios_auth',
            'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usuarios_auth ON usuarios(email, activo);'
        },
        
        # Check constraints para validación
        {
            'name': 'chk_rol_valido',
            'sql': '''
                ALTER TABLE usuarios 
                ADD CONSTRAINT chk_rol_valido 
                CHECK (rol IN ('admin', 'limitado'));
            ''',
            'ignore_error': True
        },
        {
            'name': 'chk_email_formato',
            'sql': '''
                ALTER TABLE usuarios 
                ADD CONSTRAINT chk_email_formato 
                CHECK (email LIKE '%@%');
            ''',
            'ignore_error': True
        },
        {
            'name': 'chk_nombre_longitud_minima',
            'sql': '''
                ALTER TABLE usuarios 
                ADD CONSTRAINT chk_nombre_longitud_minima 
                CHECK (LENGTH(nombre) >= 2);
            ''',
            'ignore_error': True
        }
    ]
    
    for migration in migrations:
        try:
            logger.info(f"Aplicando migración usuarios: {migration['name']}")
            engine.execute(text(migration['sql']))
            logger.info(f"✅ Migración usuarios aplicada: {migration['name']}")
        except SQLAlchemyError as e:
            if migration.get('ignore_error', False):
                logger.warning(f"⚠️ Migración usuarios omitida: {migration['name']} - {e}")
            else:
                logger.error(f"❌ Error migración usuarios: {migration['name']} - {e}")
                raise

def run_migration():
    """Ejecutar migración completa"""
    try:
        logger.info("🚀 Iniciando migración de constraints y índices")
        
        # Obtener URL de base de datos
        database_url = get_database_url()
        logger.info("✅ URL de base de datos obtenida")
        
        # Crear engine
        engine = create_engine(database_url)
        logger.info("✅ Engine de SQLAlchemy creado")
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Conexión a base de datos verificada")
        
        # Aplicar migraciones para reservas
        logger.info("📊 Aplicando migraciones para tabla reservas...")
        add_reservas_constraints_and_indexes(engine)
        
        # Aplicar migraciones para usuarios  
        logger.info("👥 Aplicando migraciones para tabla usuarios...")
        add_usuarios_constraints_and_indexes(engine)
        
        logger.info("🎉 Migración completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"💥 Error ejecutando migración: {e}")
        return False

def validate_constraints():
    """Validar que los constraints se aplicaron correctamente"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Verificar algunos índices clave
        with engine.connect() as conn:
            # Verificar índices en reservas
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'reservas' 
                AND indexname LIKE 'idx_%'
            """))
            
            indices_reservas = [row[0] for row in result.fetchall()]
            logger.info(f"Índices en reservas: {indices_reservas}")
            
            # Verificar constraints
            result = conn.execute(text("""
                SELECT conname FROM pg_constraint 
                WHERE conrelid = 'reservas'::regclass
                AND conname LIKE 'chk_%' OR conname LIKE 'uq_%'
            """))
            
            constraints = [row[0] for row in result.fetchall()]
            logger.info(f"Constraints en reservas: {constraints}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error validando constraints: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MIGRACIÓN DE CONSTRAINTS Y ÍNDICES PARA CONCURRENCIA")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        print("🔍 Validando constraints existentes...")
        if validate_constraints():
            print("✅ Validación completada")
        else:
            print("❌ Error en validación")
            sys.exit(1)
    else:
        print("🔧 Ejecutando migración...")
        if run_migration():
            print("✅ Migración completada exitosamente")
            print("\n🔍 Ejecuta con --validate para verificar los cambios")
        else:
            print("❌ Error en migración")
            sys.exit(1)