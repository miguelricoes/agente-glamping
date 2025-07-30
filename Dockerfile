# Imagen base oficial
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto por defecto (Railway usará el que defina como PORT)
EXPOSE 8080

# Usar bash para evaluar correctamente la variable $PORT
CMD bash -c "gunicorn --bind 0.0.0.0:${PORT:-8080} agente:app"
