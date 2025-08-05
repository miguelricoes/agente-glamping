# Imagen base liviana de Python
FROM python:3.12-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código fuente
COPY . .

# Exponer el puerto que usará Gunicorn
EXPOSE 8080

# Comando que inicia tu app (usa el puerto 8080 fijo)
CMD ["gunicorn", "agente:app", "--bind", "0.0.0.0:8080"]
