FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# 🔥 Este sí expande la variable PORT correctamente:
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "agente:app"]

