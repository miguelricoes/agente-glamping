# check_reservas.py - Script para verificar reservas en la base de datos
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

print("🔍 Verificando reservas en la base de datos...")

# Cargar variables de entorno
load_dotenv()

# Crear aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Mismo modelo que en agente.py
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
            # Contar total de reservas
            total_reservas = Reserva.query.count()
            print(f"📊 Total de reservas en la base de datos: {total_reservas}")
            
            if total_reservas > 0:
                print("\n📋 Reservas encontradas:")
                print("┌────┬─────────────────┬─────────────────────┬─────────────┬─────────────────────┐")
                print("│ ID │ WHATSAPP        │ HUÉSPEDES           │ DOMO        │ FECHA CREACIÓN      │")
                print("├────┼─────────────────┼─────────────────────┼─────────────┼─────────────────────┤")
                
                reservas = Reserva.query.order_by(Reserva.fecha_creacion.desc()).limit(10).all()
                
                for reserva in reservas:
                    fecha_str = reserva.fecha_creacion.strftime("%Y-%m-%d %H:%M") if reserva.fecha_creacion else "N/A"
                    print(f"│ {reserva.id:<2} │ {reserva.numero_whatsapp:<15} │ {reserva.nombres_huespedes[:19]:<19} │ {(reserva.domo or 'N/A')[:11]:<11} │ {fecha_str:<19} │")
                
                print("└────┴─────────────────┴─────────────────────┴─────────────┴─────────────────────┘")
                
                if total_reservas > 10:
                    print(f"   ... y {total_reservas - 10} reservas más")
            else:
                print("📝 No hay reservas registradas aún.")
                print("   Cuando los usuarios confirmen reservas a través del chatbot, aparecerán aquí.")
            
            print("\n✅ Verificación completada exitosamente")
            
        except Exception as e:
            print(f"❌ Error al consultar reservas: {e}")
            print("   Verifica que la tabla 'reservas' haya sido creada correctamente.")