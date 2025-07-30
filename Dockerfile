# Imagen base oficial con Python
FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer un puerto por defecto (Railway usa la variable PORT automáticamente)
EXPOSE 8080

# 👇 ¡Aquí está la corrección crítica!
ENTRYPOINT ["bash", "-c"]
CMD ["exec gunicorn --bind 0.0.0.0:${PORT:-8080} agente:app"]
