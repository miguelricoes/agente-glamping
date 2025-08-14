# reset_admin_password.py - Resetear contraseña del admin
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

print("Reseteando contraseña del usuario administrador...")

# Cargar variables de entorno
load_dotenv()

database_url = os.getenv('DATABASE_PRIVATE_URL') or os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')

if not database_url:
    print("ERROR: No se encontró ninguna DATABASE_URL")
    exit(1)

# Crear aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

if __name__ == '__main__':
    with app.app_context():
        try:
            # Buscar el usuario admin
            admin = Usuario.query.filter_by(email='juan@example.com').first()
            
            if admin:
                print(f"Admin encontrado: {admin.nombre}")
                print(f"Hash actual (primeros 50 chars): {admin.password_hash[:50]}...")
                print(f"Hash completo: {admin.password_hash}")
                
                # Verificar si es texto plano (problema de seguridad)
                if admin.password_hash == 'admin123':
                    print("PROBLEMA: Contraseña en texto plano detectada!")
                
                # Resetear contraseña a admin123 con hash seguro
                nueva_password = 'admin123'
                nuevo_hash = generate_password_hash(nueva_password)
                
                print(f"Nuevo hash generado: {nuevo_hash}")
                print(f"Verificando nuevo hash con 'admin123': {check_password_hash(nuevo_hash, nueva_password)}")
                
                # Actualizar en la base de datos
                admin.password_hash = nuevo_hash
                db.session.commit()
                
                print(f"OK: Contraseña del admin actualizada")
                print(f"   Email: juan@example.com")
                print(f"   Contraseña: admin123")
                
                # Verificar que funcione
                admin_updated = Usuario.query.filter_by(email='juan@example.com').first()
                if check_password_hash(admin_updated.password_hash, 'admin123'):
                    print("OK: Verificación exitosa - La contraseña funciona")
                    
                    # Probar login
                    print("Probando login con API...")
                    import requests
                    import json
                    
                    login_data = {
                        'email': 'juan@example.com',
                        'password': 'admin123'
                    }
                    
                    try:
                        response = requests.post(
                            'http://localhost:8080/api/auth/login',
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps(login_data),
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            print(f"OK: Login API exitoso!")
                            print(f"   Usuario: {result['user']['nombre']}")
                            print(f"   Rol: {result['user']['rol']}")
                        else:
                            print(f"ERROR: Login API falló - Código: {response.status_code}")
                            print(f"   Respuesta: {response.text}")
                    except Exception as e:
                        print(f"ERROR: No se pudo probar login API: {e}")
                        print("   (Asegúrate de que el servidor esté ejecutándose)")
                else:
                    print("ERROR: La verificación falló después de actualizar")
                    
            else:
                print("ERROR: Usuario administrador no encontrado")
                
        except Exception as e:
            print(f"ERROR: {e}")
            db.session.rollback()