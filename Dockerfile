# Usa una imagen base de Python ligera
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc en el host
ENV PYTHONDONTWRITEBYTECODE 1
# Asegura que la salida de Python se envíe directamente al terminal
ENV PYTHONUNBUFFERED 1

# Define el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias para psycopg2
# libpq-dev: para conectarse a PostgreSQL
# build-essential: para compilar dependencias de Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos y descarga las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto que usará Gunicorn
EXPOSE 8080

# Comando para iniciar la aplicación con Gunicorn
# Gunicorn sirve la aplicación de Flask en el puerto definido por Railway ($PORT)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "agente:app"]