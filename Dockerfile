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

# Expone el puerto para Railway
EXPOSE 8080

# Comando correcto para iniciar gunicorn y usar la variable de entorno PORT
CMD sh -c "gunicorn --bind 0.0.0.0:${PORT:-8080} agente:app"
