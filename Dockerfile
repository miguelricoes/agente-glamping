# 🔒 DOCKERFILE SEGURO PARA PRODUCCIÓN
# Usa imagen base oficial de Python con parches de seguridad
FROM python:3.11-slim

# Variables de entorno de seguridad
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Variables de entorno de seguridad adicionales
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 👥 Crear usuario no-root para seguridad (CRÍTICO)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Define el directorio de trabajo
WORKDIR /app

# 🔧 Instalar dependencias del sistema con limpieza de seguridad
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias necesarias
    libpq-dev \
    build-essential \
    python3-dev \
    pkg-config \
    # Herramientas de seguridad y health checks
    curl \
    ca-certificates \
    # Limpieza de seguridad
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    # Limpiar cache adicional
    && rm -rf /root/.cache

# 📦 Instalar dependencias Python con seguridad mejorada
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --no-deps -r requirements.txt \
    && pip check \
    # Limpiar cache de pip
    && rm -rf /root/.cache/pip

# 📁 Copiar código de aplicación
COPY . .

# 🔐 Configurar permisos de seguridad
# Cambiar propietario de archivos al usuario no-root
RUN chown -R appuser:appuser /app \
    # Remover permisos de escritura para otros usuarios en archivos críticos
    && chmod -R 755 /app \
    && chmod -R 644 /app/*.py /app/**/*.py 2>/dev/null || true \
    # Proteger archivos de configuración
    && chmod 600 /app/config/*.py 2>/dev/null || true

# 🔄 Cambiar a usuario no-root (CRÍTICO DE SEGURIDAD)
USER appuser

# 🌐 Exponer puerto (solo documentativo)
EXPOSE 8080

# 🏥 Health check para monitoreo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 🚀 Comando Gunicorn con configuración optimizada para concurrencia
# Usa archivo de configuración para configuración avanzada y adaptativa
CMD ["gunicorn", "--config", "gunicorn.conf.py", "agente_standalone:app"]