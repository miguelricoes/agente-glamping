# verificar_admin_password.py - Verificar contraseña del admin existente
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

print("Verificando contraseña del usuario administrador...")

# Cargar variables de entorno
load_dotenv()

# Usar misma configuración que reservas
DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL

if not database_url:
    print("ERROR: No se encontró ninguna DATABASE_URL")
    exit(1)

print(f"Conectando a: {database_url}")

# Crear aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelo de usuario
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='limitado', nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    creado_por = db.Column(db.String(100), default='juan@example.com')
    activo = db.Column(db.Boolean, default=True)
    ultimo_acceso = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Usuario {self.id}: {self.nombre}>'

if __name__ == '__main__':
    with app.app_context():
        try:
            # Buscar el usuario admin
            admin = Usuario.query.filter_by(email='juan@example.com').first()
            
            if admin:
                print(f"\nAdmin encontrado:")
                print(f"  ID: {admin.id}")
                print(f"  Nombre: {admin.nombre}")
                print(f"  Email: {admin.email}")
                print(f"  Rol: {admin.rol}")
                print(f"  Activo: {admin.activo}")
                print(f"  Fecha creación: {admin.fecha_creacion}")
                print(f"  Creado por: {admin.creado_por}")
                print(f"  Hash password: {admin.password_hash[:50]}...")
                
                # Probar contraseñas comunes
                print(f"\nProbando contraseñas comunes:")
                passwords_to_test = [
                    'admin123',
                    'password123',
                    'admin',
                    '123456',
                    'password',
                    'glamping123',
                    'juan123'
                ]
                
                for password in passwords_to_test:
                    if check_password_hash(admin.password_hash, password):
                        print(f"OK: CONTRASENA ENCONTRADA: '{password}'")
                        
                        # Probar login con esta contraseña
                        print(f"\nProbando login con contraseña encontrada...")
                        import requests
                        import json
                        
                        login_data = {
                            'email': 'juan@example.com',
                            'password': password
                        }
                        
                        try:
                            response = requests.post(
                                'http://localhost:8080/api/auth/login',
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps(login_data),
                                timeout=5
                            )
                            
                            if response.status_code == 200:
                                print(f"OK: Login exitoso con contrasena: {password}")
                                result = response.json()
                                print(f"  Usuario: {result['user']['nombre']}")
                                print(f"  Rol: {result['user']['rol']}")
                            else:
                                print(f"ERROR: Login fallo con codigo: {response.status_code}")
                        except Exception as e:
                            print(f"ERROR: Error al probar login: {e}")
                        
                        break
                    else:
                        print(f"ERROR: '{password}' - No coincide")
                else:
                    print(f"\nERROR: Ninguna contrasena comun funciono")
                    print(f"   El admin puede tener una contraseña personalizada")
                    
                    # Ofrecer resetear la contraseña
                    print(f"\n¿Quieres resetear la contraseña del admin a 'admin123'? (y/n)")
                    
            else:
                print("ERROR: Usuario administrador no encontrado")
                
        except Exception as e:
            print(f"ERROR: Error: {e}")