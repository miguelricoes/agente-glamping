# migrate_password_fields.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

print("Migrando tabla usuarios para agregar campos de contraseña...")

load_dotenv()

DATABASE_PRIVATE_URL = os.getenv('DATABASE_PRIVATE_URL')
DATABASE_PUBLIC_URL = os.getenv('DATABASE_PUBLIC_URL')
DATABASE_URL = os.getenv('DATABASE_URL')

database_url = DATABASE_PRIVATE_URL or DATABASE_PUBLIC_URL or DATABASE_URL

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

if __name__ == '__main__':
    with app.app_context():
        try:
            print("Agregando campos temp_password y password_changed...")

            # Agregar columnas a la tabla existente
            from sqlalchemy import text

            # Verificar si las columnas ya existen
            result = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'usuarios' AND column_name IN ('temp_password', 'password_changed')
            """))
            existing_columns = [row[0] for row in result]

            if 'temp_password' not in existing_columns:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN temp_password VARCHAR(50)"))
                print("OK: Columna temp_password agregada")
            else:
                print("INFO: Columna temp_password ya existe")

            if 'password_changed' not in existing_columns:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN password_changed BOOLEAN DEFAULT FALSE"))
                print("OK: Columna password_changed agregada")
            else:
                print("INFO: Columna password_changed ya existe")

            db.session.commit()
            print("EXITO: Migracion completada exitosamente!")

        except Exception as e:
            print(f"ERROR: Error en migracion: {e}")
            db.session.rollback()