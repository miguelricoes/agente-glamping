# migrate_new_fields.py
import os
import psycopg2
from dotenv import load_dotenv

print("Iniciando migracion para agregar nuevos campos a tabla reservas...")

# Cargar variables de entorno
load_dotenv()

# Obtener URL de base de datos
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("ERROR: No se encontro DATABASE_URL")
    exit(1)

print(f"Conectando a Railway PostgreSQL...")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Conexion exitosa")
    
    # Verificar columnas existentes
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'reservas'
        ORDER BY ordinal_position;
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    print(f"Columnas existentes: {existing_columns}")
    
    # Definir nuevas columnas a agregar
    new_columns = [
        ('metodo_pago', 'VARCHAR(50) DEFAULT \'Pendiente\''),
        ('monto_total', 'NUMERIC(10, 2) DEFAULT 0.00'),
        ('comentarios_especiales', 'TEXT')
    ]
    
    # Agregar cada columna si no existe
    for column_name, column_def in new_columns:
        if column_name not in existing_columns:
            print(f"Agregando columna: {column_name}")
            sql = f"ALTER TABLE reservas ADD COLUMN {column_name} {column_def};"
            cursor.execute(sql)
            print(f"  -> {column_name} agregada exitosamente")
        else:
            print(f"Columna {column_name} ya existe, saltando...")
    
    # Verificar resultado final
    cursor.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name = 'reservas'
        ORDER BY ordinal_position;
    """)
    
    final_columns = cursor.fetchall()
    print("\nEstructura final de la tabla reservas:")
    print("COLUMNA                 | TIPO           | DEFAULT")
    print("------------------------|----------------|------------------")
    
    for column_name, data_type, column_default in final_columns:
        default_str = str(column_default)[:15] if column_default else "-"
        print(f"{column_name:<23} | {data_type:<14} | {default_str}")
    
    # Probar inserción con nuevos campos
    print("\nProbando insercion con nuevos campos...")
    
    test_sql = """
        INSERT INTO reservas (
            numero_whatsapp, nombres_huespedes, cantidad_huespedes, 
            domo, fecha_entrada, fecha_salida, servicio_elegido, 
            adicciones, numero_contacto, email_contacto,
            metodo_pago, monto_total, comentarios_especiales
        ) VALUES (
            'test_migration', 'Test Migration', 2, 
            'antares', '2025-01-20', '2025-01-22', 'ninguno',
            'test', '+1234567890', 'test@test.com',
            'transferencia', 1300000.00, 'Prueba de migracion exitosa'
        ) RETURNING id;
    """
    
    cursor.execute(test_sql)
    test_id = cursor.fetchone()[0]
    print(f"Insercion de prueba exitosa - ID: {test_id}")
    
    # Verificar que se pueden leer los nuevos campos
    cursor.execute("""
        SELECT metodo_pago, monto_total, comentarios_especiales 
        FROM reservas WHERE id = %s
    """, (test_id,))
    
    result = cursor.fetchone()
    print(f"Datos leidos: metodo_pago='{result[0]}', monto_total={result[1]}, comentarios='{result[2][:30]}...'")
    
    # Limpiar: eliminar registro de prueba
    cursor.execute("DELETE FROM reservas WHERE id = %s", (test_id,))
    print("Registro de prueba eliminado")
    
    print("\n=== MIGRACION COMPLETADA EXITOSAMENTE ===")
    print("La base de datos en Railway ahora incluye:")
    print("- metodo_pago (VARCHAR 50)")
    print("- monto_total (NUMERIC 10,2)")  
    print("- comentarios_especiales (TEXT)")
    print("El agente puede ahora usar todos los nuevos campos!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error durante la migracion: {e}")
    print(f"Tipo de error: {type(e).__name__}")