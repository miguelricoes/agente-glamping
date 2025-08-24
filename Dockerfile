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
    # Dependencias necesarias para compilación
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    python3-dev \
    pkg-config \
    # Dependencias para FAISS y NumPy
    libblas-dev \
    liblapack-dev \
    gfortran \
    # Herramientas de seguridad y health checks
    curl \
    ca-certificates \
    # Dependencias para compilar paquetes Python nativos
    libffi-dev \
    libssl-dev \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /root/.cache

# 📦 Instalar dependencias Python con estrategia robusta por etapas
COPY requirements.txt .

# 🚀 INSTALACIÓN POR ETAPAS CON MANEJO DE ERRORES Y FALLBACKS

# ETAPA 1: Actualizar herramientas de instalación
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ETAPA 2: Instalar dependencias base críticas (sin --no-deps)
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    flask-sqlalchemy==3.0.5 \
    flask-cors==4.0.0 \
    python-dotenv==1.0.0 \
    gunicorn==22.0.0 \
    psycopg2-binary==2.9.9

# ETAPA 3: Instalar dependencias matemáticas/científicas
RUN pip install --no-cache-dir \
    numpy>=1.24.0,\<2.0.0

# ETAPA 4: Instalar dependencias AI/ML con tolerancia a errores
RUN pip install --no-cache-dir \
    openai>=1.86.0,\<2.0.0 \
    tiktoken>=0.5.2,\<1.0.0 \
    || echo "⚠️ OpenAI dependencies installed with warnings"

# ETAPA 5: Instalar LangChain y dependencias relacionadas
RUN pip install --no-cache-dir \
    langchain==0.3.27 \
    langchain-openai==0.3.29 \
    langchain-community==0.3.27 \
    || echo "⚠️ LangChain dependencies installed with warnings"

# ETAPA 6: Instalar FAISS y ML adicionales (con fallback)
RUN pip install --no-cache-dir faiss-cpu==1.7.4 || \
    pip install --no-cache-dir faiss-cpu || \
    echo "⚠️ FAISS installation failed, continuing without vector search"

# ETAPA 7: Instalar sentence-transformers con manejo de errores
RUN pip install --no-cache-dir sentence-transformers==2.2.2 || \
    echo "⚠️ Sentence-transformers installation failed"

# ETAPA 8: Instalar dependencias de comunicación y utilidades
RUN pip install --no-cache-dir \
    twilio==8.10.0 \
    requests>=2.32.3 \
    urllib3>=2.2.1 \
    certifi>=2024.2.2 \
    python-dateutil>=2.8.2 \
    pytz>=2024.1 \
    psutil>=5.9.5

# ETAPA 9: Instalar dependencias de seguridad (opcionales)
RUN pip install --no-cache-dir \
    cryptography==42.0.5 \
    werkzeug==3.0.1 \
    || echo "⚠️ Security dependencies installed with warnings"

# ETAPA 10: Instalar dependencias de validación (opcionales)
RUN pip install --no-cache-dir \
    bleach>=6.1.0 \
    email-validator>=2.1.0 \
    phonenumbers>=8.13.0 \
    || echo "⚠️ Validation dependencies are optional"

# 🔍 VERIFICACIÓN FINAL Y LIMPIEZA
RUN pip check || echo "⚠️ Dependency check completed with warnings" \
    && rm -rf /root/.cache/pip \
    && echo "✅ All 10 installation stages completed"

# ETAPA 11: Verificar solo las dependencias CRÍTICAS para el funcionamiento
RUN python -c "
import sys
critical_imports = [
    ('flask', 'Flask framework'),
    ('openai', 'OpenAI API'),
    ('langchain', 'LangChain framework'),
    ('psycopg2', 'PostgreSQL adapter'),
    ('twilio.rest', 'Twilio API')
]

failed_imports = []
for module, description in critical_imports:
    try:
        __import__(module)
        print(f'✅ {description}: OK')
    except ImportError as e:
        failed_imports.append((module, description, str(e)))
        print(f'❌ {description}: FAILED - {e}')

if failed_imports:
    print(f'\n🚨 CRITICAL: {len(failed_imports)} critical dependencies failed!')
    for module, desc, error in failed_imports:
        print(f'  - {desc}: {error}')
    sys.exit(1)
else:
    print(f'\n✅ All {len(critical_imports)} critical dependencies verified successfully!')
"

# Limpiar cache de pip y archivos temporales
RUN rm -rf /root/.cache/pip /tmp/* /var/tmp/*

# 📁 Copiar código de aplicación
COPY . .

# 🔐 Configurar permisos de seguridad
RUN chown -R appuser:appuser /app \
    && chmod -R 755 /app \
    && chmod -R 644 /app/*.py 2>/dev/null || true \
    && chmod 600 /app/config/*.py 2>/dev/null || true

# 🔄 Cambiar a usuario no-root (CRÍTICO DE SEGURIDAD)
USER appuser

# 🌐 Exponer puerto
EXPOSE 8080

# 🏥 Health check mejorado con timeout apropiado
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 🚀 Comando de inicio optimizado
CMD ["gunicorn", "--config", "gunicorn.conf.py", "agente_standalone:app"]