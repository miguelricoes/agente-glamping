# Imagen base con Python
FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Copia dependencias
COPY requirements.txt .

# Instala dependencias
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Exponer el puerto (opcional, para Railway)
EXPOSE 8080

# Comando para iniciar la app (Railway expandirá ${PORT})
ENTRYPOINT ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} agente:app"]