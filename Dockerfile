FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# 🔥 Este sí expande la variable PORT correctamente:
CMD sh -c "echo El puerto es: \$PORT && env && sleep 300"
