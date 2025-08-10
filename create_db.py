# create_db.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

print("🚀 Iniciando creación de tabla 'reservas' en PostgreSQL...")

# Cargar variables de entorno
load_dotenv()

# Verificar que la variable DATABASE_URL existe
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ ERROR: No se encontró la variable de entorno DATABASE_URL")
    print("   Asegúrate de tener configurada la variable en tu archivo .env o en Railway")
    exit(1)

print(f"📍 Conectando a: {database_url}")

# Crear aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelo de datos para reservas (mismo que en agente.py)
class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    numero_whatsapp = db.Column(db.String(50), nullable=False)
    nombres_huespedes = db.Column(db.String(255), nullable=False)
    cantidad_huespedes = db.Column(db.Integer, nullable=False)
    domo = db.Column(db.String(50))
    fecha_entrada = db.Column(db.Date)
    fecha_salida = db.Column(db.Date)
    servicio_elegido = db.Column(db.String(100))
    adicciones = db.Column(db.String(255))
    numero_contacto = db.Column(db.String(50))
    email_contacto = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reserva {self.id}: {self.nombres_huespedes}>'

if __name__ == '__main__':
    with app.app_context():
        try:
            print("🔨 Creando tabla 'reservas'...")
            
            # Crear todas las tablas
            db.create_all()
            print("✅ Tabla 'reservas' creada exitosamente en PostgreSQL")
            
            # Verificar que la tabla existe
            from sqlalchemy import text
            print("🔍 Verificando que la tabla fue creada...")
            
            result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            
            if 'reservas' in tables:
                print("✅ Verificación exitosa: La tabla 'reservas' existe en la base de datos")
                
                # Mostrar estructura de la tabla
                print("\n📋 Estructura de la tabla 'reservas':")
                result = db.session.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'reservas' 
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print("┌─────────────────────┬────────────────┬──────────┬─────────────────┐")
                print("│ COLUMNA             │ TIPO           │ NULL     │ DEFAULT         │")
                print("├─────────────────────┼────────────────┼──────────┼─────────────────┤")
                
                for column_name, data_type, is_nullable, column_default in columns:
                    null_str = "SÍ" if is_nullable == "YES" else "NO"
                    default_str = str(column_default)[:15] if column_default else "-"
                    print(f"│ {column_name:<19} │ {data_type:<14} │ {null_str:<8} │ {default_str:<15} │")
                
                print("└─────────────────────┴────────────────┴──────────┴─────────────────┘")
                
                # Verificar que podemos insertar datos (prueba opcional)
                print("\n🧪 Realizando prueba de inserción...")
                
                # Crear una reserva de prueba
                reserva_test = Reserva(
                    numero_whatsapp="test_setup",
                    nombres_huespedes="Test Setup",
                    cantidad_huespedes=1,
                    domo="Test Domo",
                    fecha_entrada=datetime.now().date(),
                    fecha_salida=datetime.now().date(),
                    servicio_elegido="Ninguno",
                    adicciones="Test",
                    numero_contacto="000000000",
                    email_contacto="test@test.com"
                )
                
                # Insertar y eliminar inmediatamente
                db.session.add(reserva_test)
                db.session.commit()
                
                test_id = reserva_test.id
                print(f"✅ Inserción exitosa - ID generado: {test_id}")
                
                # Eliminar registro de prueba
                db.session.delete(reserva_test)
                db.session.commit()
                print("🗑️  Registro de prueba eliminado")
                
                print("\n🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
                print("   La tabla 'reservas' está lista para recibir datos desde tu chatbot.")
                print(f"   Total de tablas en la base de datos: {len(tables)}")
                
            else:
                print("❌ Error: La tabla 'reservas' no fue creada")
                print("   Tablas encontradas en la base de datos:")
                for table in tables:
                    print(f"   - {table}")
                
        except Exception as e:
            print(f"❌ Error al crear/verificar la tabla: {e}")
            print(f"   Tipo de error: {type(e).__name__}")
            
            # Información adicional para debugging
            if "connection" in str(e).lower():
                print("\n💡 Posibles soluciones:")
                print("   1. Verifica que DATABASE_URL esté configurada correctamente")
                print("   2. Asegúrate de que la base de datos PostgreSQL esté activa en Railway")
                print("   3. Revisa que las credenciales de conexión sean válidas")
            elif "permission" in str(e).lower():
                print("\n💡 Posibles soluciones:")
                print("   1. Verifica los permisos de la base de datos")
                print("   2. Asegúrate de que el usuario tenga permisos CREATE TABLE")
            
            print(f"\n🔧 DATABASE_URL configurada: {database_url}")