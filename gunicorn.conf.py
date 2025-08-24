# Configuración de Gunicorn optimizada para Railway
import os
import multiprocessing

# CONFIGURACIÓN BÁSICA PARA RAILWAY
bind = f"0.0.0.0:{os.getenv('PORT', 8080)}"
workers = min(int(os.getenv('WEB_CONCURRENCY', 2)), 4)  # Railway recomienda 2-4
worker_class = "sync"  # Cambiar de gthread a sync para Railway
timeout = 30  # Railway timeout
keepalive = 2

# CONFIGURACIÓN DE RECURSOS PARA RAILWAY
max_requests = 1000
max_requests_jitter = 50
worker_connections = 1000
preload_app = True

# CONFIGURACIÓN DE LOGS PARA RAILWAY
loglevel = os.getenv('LOG_LEVEL', 'info')
accesslog = '-'  # STDOUT para Railway logs
errorlog = '-'   # STDERR para Railway logs
capture_output = True

# RAILWAY OPTIMIZATIONS
worker_tmp_dir = '/dev/shm'  # Usar memoria compartida
tmp_upload_dir = '/tmp'

# CONFIGURACIÓN DE DESARROLLO VS PRODUCCIÓN
if os.getenv('RAILWAY_ENVIRONMENT_NAME') == 'production':
    workers = min(4, multiprocessing.cpu_count() * 2 + 1)
    loglevel = 'warning'
else:
    workers = 2
    loglevel = 'info'

# CONFIGURACIÓN DE SEGURIDAD
# Limitar tamaño de headers y requests
limit_request_line = 0  # No limit (manejado por Flask)
limit_request_fields = 100
limit_request_field_size = 8190

# CONFIGURACIÓN DE MONITOREO
# Enable stats para monitoreo externo
statsd_host = os.getenv('STATSD_HOST')
statsd_prefix = 'glamping.gunicorn'

# HOOKS DE CONFIGURACIÓN AVANZADA
def on_starting(server):
    """Hook ejecutado al iniciar Gunicorn"""
    logger.info(f"🚀 Iniciando Gunicorn con {workers} workers, {threads} threads cada uno")
    logger.info(f"📊 Concurrencia total: {workers * threads} conexiones simultáneas")
    logger.info(f"⏱️ Timeouts: request={timeout}s, keepalive={keepalive}s, graceful={graceful_timeout}s")
    logger.info(f"🔄 Reciclado de workers cada {max_requests}±{max_requests_jitter} requests")
    
    # Verificar configuración crítica
    if workers < 2:
        logger.warning("⚠️ ADVERTENCIA: Solo 1 worker configurado - puede causar bloqueos")
    
    if timeout > 30:
        logger.warning("⚠️ ADVERTENCIA: Timeout > 30s puede causar timeouts de WhatsApp")

def on_reload(server):
    """Hook ejecutado en reload"""
    logger.info("🔄 Recargando configuración de Gunicorn")

def worker_int(worker):
    """Hook ejecutado cuando worker recibe SIGINT"""
    logger.info(f"👷 Worker {worker.pid} interrumpido")

def on_exit(server):
    """Hook ejecutado al salir"""
    logger.info("🛑 Cerrando Gunicorn")

def pre_fork(server, worker):
    """Hook antes de crear worker"""
    logger.debug(f"👷 Creando worker {worker.age}")

def post_fork(server, worker):
    """Hook después de crear worker"""
    logger.info(f"✅ Worker {worker.pid} iniciado")

def pre_exec(server):
    """Hook antes de exec"""
    logger.info("🔧 Pre-exec: preparando nueva configuración")

def when_ready(server):
    """Hook cuando server está listo"""
    logger.info("✅ Gunicorn listo para recibir requests")
    
    # Log configuración final
    logger.info(f"🌐 Escuchando en {bind}")
    logger.info(f"🏭 Worker class: {worker_class}")
    logger.info(f"📈 Max workers: {workers}, Threads: {threads}")

def worker_abort(worker):
    """Hook cuando worker es abortado"""
    logger.error(f"💥 Worker {worker.pid} abortado inesperadamente")

# CONFIGURACIÓN ESPECÍFICA PARA DIFERENTES ENTORNOS
env = os.getenv('ENV', 'development')

if env == 'production':
    # Configuración de producción más conservadora
    workers = min(workers, 3)  # Limitar en producción
    preload_app = True
    max_requests = 800  # Reciclar más frecuentemente
    
elif env == 'development':
    # Configuración de desarrollo para debugging
    workers = 1
    threads = 2
    timeout = 60  # Más tiempo para debugging
    reload = True  # Auto-reload en desarrollo
    
elif env == 'testing':
    # Configuración mínima para testing
    workers = 1
    threads = 1
    timeout = 10

# CONFIGURACIÓN ADICIONAL PARA CONTENEDORES
# Detectar si estamos en un contenedor con recursos limitados
if os.path.exists('/.dockerenv'):
    # Ajustes para Docker
    worker_tmp_dir = '/dev/shm'  # Usar memoria compartida para mejor performance
    
    # Verificar memoria disponible (básico)
    try:
        with open('/proc/meminfo', 'r') as f:
            mem_info = f.read()
            mem_total_line = [line for line in mem_info.split('\n') if 'MemTotal' in line][0]
            mem_total_kb = int(mem_total_line.split()[1])
            mem_total_mb = mem_total_kb / 1024
            
            # Si hay poca memoria, reducir workers
            if mem_total_mb < 512:
                workers = 1
                threads = 2
                logger.warning(f"⚠️ Memoria limitada ({mem_total_mb:.0f}MB), reduciendo workers a {workers}")
            elif mem_total_mb < 1024:
                workers = min(workers, 2)
                logger.info(f"💾 Memoria detectada: {mem_total_mb:.0f}MB, usando {workers} workers")
                
    except Exception as e:
        logger.warning(f"No se pudo detectar memoria del sistema: {e}")

# LOG RESUMEN DE CONFIGURACIÓN
logger.info("📋 Configuración de Gunicorn cargada:")
logger.info(f"   Workers: {workers}")
logger.info(f"   Threads: {threads}")
logger.info(f"   Worker class: {worker_class}")
logger.info(f"   Timeout: {timeout}s")
logger.info(f"   Max requests: {max_requests}")
logger.info(f"   Bind: {bind}")
logger.info(f"   Environment: {env}")
logger.info(f"   Preload app: {preload_app}")

# Validación final
if workers * threads < 4:
    logger.error("🚨 CONFIGURACIÓN CRÍTICA: Concurrencia total < 4 puede causar bloqueos severos")
    
if timeout < 20:
    logger.warning("⚠️ Timeout muy bajo para operaciones LLM complejas")