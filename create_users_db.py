# create_users_db.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

print("Iniciando creación de tabla 'usuarios' en Railway PostgreSQL...")

# Cargar variables de entorno
load_dotenv()

# Usar misma configuración que reservas
DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL

if not database_url:
    print("ERROR: No se encontró ninguna DATABASE_URL")
    print("   Railway debería configurar esto automáticamente")
    exit(1)

print(f"Conectando a: {database_url}")

# Crear aplicación Flask (mismo patrón que create_db.py)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelo de datos para usuarios
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='limitado', nullable=False)  # 'completo' o 'limitado'
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.String(100), default='juan@example.com')
    activo = db.Column(db.Boolean, default=True)
    ultimo_acceso = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Usuario {self.id}: {self.nombre} ({self.email})>'

if __name__ == '__main__':
    with app.app_context():
        try:
            print("Creando tabla 'usuarios'...")

            # Crear tabla
            db.create_all()
            print("OK: Tabla 'usuarios' creada exitosamente en Railway PostgreSQL")

            # Verificar que la tabla existe
            from sqlalchemy import text
            result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]

            if 'usuarios' in tables:
                print("OK: Verificacion exitosa: La tabla 'usuarios' existe")

                # Crear usuario administrador principal
                admin_exists = Usuario.query.filter_by(email='juan@example.com').first()
                if not admin_exists:
                    admin_user = Usuario(
                        nombre="Juan Administrador",
                        email="juan@example.com",
                        password_hash=generate_password_hash("admin123"),  # CAMBIAR EN PRODUCCIÓN
                        rol="completo",
                        creado_por="sistema"
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    print(f"OK: Usuario administrador creado - ID: {admin_user.id}")
                    print("Credenciales: juan@example.com / admin123")
                    print("IMPORTANTE: CAMBIAR CONTRASENA EN PRODUCCION")
                else:
                    print("INFO: Usuario administrador ya existe")

                # Mostrar estructura de la tabla
                print("\nEstructura de la tabla 'usuarios':")
                result = db.session.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'usuarios'
                    ORDER BY ordinal_position
                """))

                print("+---------------------+----------------+----------+")
                print("| COLUMNA             | TIPO           | NULL     |")
                print("+---------------------+----------------+----------+")

                for column_name, data_type, is_nullable in result:
                    null_str = "SÍ" if is_nullable == "YES" else "NO"
                    print(f"| {column_name:<19} | {data_type:<14} | {null_str:<8} |")

                print("+---------------------+----------------+----------+")
                print("\nSistema de usuarios listo!")
                print(f"   Tablas en Railway: {len(tables)}")

        except Exception as e:
            print(f"ERROR: {e}")
            print("TIP: Verifica que Railway PostgreSQL este activo")