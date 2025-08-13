import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    metodo_pago = db.Column(db.String(50), default='Pendiente')
    monto_total = db.Column(db.Numeric(10, 2), default=0.00)
    comentarios_especiales = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

if __name__ == '__main__':
    with app.app_context():
        try:
            total_reservas = Reserva.query.count()
            print(f"Total de reservas: {total_reservas}")
            
            if total_reservas > 0:
                print("\nUltimas 5 reservas:")
                reservas = Reserva.query.order_by(Reserva.fecha_creacion.desc()).limit(5).all()
                for reserva in reservas:
                    print(f"ID: {reserva.id} | {reserva.nombres_huespedes} | {reserva.domo} | {reserva.fecha_creacion}")
                    
                # Buscar reserva especifica (ID 8)
                reserva_8 = Reserva.query.get(8)
                if reserva_8:
                    print(f"\nReserva ID 8 encontrada:")
                    print(f"Nombres: {reserva_8.nombres_huespedes}")
                    print(f"Domo: {reserva_8.domo}")
                    print(f"WhatsApp: {reserva_8.numero_whatsapp}")
                    print(f"Email: {reserva_8.email_contacto}")
                    print(f"Monto: {reserva_8.monto_total}")
                else:
                    print("\nReserva ID 8 NO encontrada")
            else:
                print("No hay reservas en la base de datos")
                
        except Exception as e:
            print(f"Error: {e}")