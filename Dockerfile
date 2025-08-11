# Imagen base liviana de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias del sistema necesarias para PostgreSQL y otras librerías
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias de Python
COPY requirements.txt .

# Actualiza pip e instala las dependencias sin caché
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código fuente
COPY . .

# Exponer el puerto que usará Gunicorn
EXPOSE 8080

# Comando que inicia tu app
# Se usa gunicorn con el puerto de Railway ($PORT) si está disponible, sino usa 8080.
CMD ["sh", "-c", "gunicorn agente:app --bind 0.0.0.0:${PORT:-8080}"]