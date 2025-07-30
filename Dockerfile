# Imagen base con Python
FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Copiar requerimientos e instalarlos
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto que Railway usa
EXPOSE 8080

# Usar script de arranque que expande $PORT correctamente
ENTRYPOINT ["./entrypoint.sh"]
