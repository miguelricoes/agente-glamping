# Imagen base oficial de Python
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto para Railway
EXPOSE 8080

# ✅ Entrada correcta que expande la variable PORT
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["exec gunicorn --bind 0.0.0.0:${PORT:-8080} agente:app"]
