# Imagen base
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código al contenedor
COPY . .

# Exponer el puerto usado por Railway (aunque solo es informativo)
EXPOSE 8080

# Usar shell para que $PORT se expanda correctamente
CMD gunicorn agente:app --bind 0.0.0.0:$PORT
