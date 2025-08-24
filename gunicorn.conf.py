# Configuración de Gunicorn optimizada para Railway - SIN DEPENDENCIAS EXTERNAS
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

# HOOKS DE CONFIGURACIÓN SIMPLE (SIN LOGGER EXTERNO)
def on_starting(server):
    """Hook ejecutado al iniciar Gunicorn - USA PRINT PARA EVITAR ERRORES"""
    print(f"Iniciando Gunicorn con {workers} workers")
    print(f"Concurrencia total: {workers} workers")
    print(f"Timeout: {timeout}s")
    print(f"Bind: {bind}")
    
    # Verificar configuración crítica
    if workers < 2:
        print("ADVERTENCIA: Solo 1 worker configurado - puede causar bloqueos")
    
    if timeout > 30:
        print("ADVERTENCIA: Timeout > 30s puede causar timeouts de WhatsApp")

def on_reload(server):
    """Hook ejecutado en reload"""
    print("Recargando configuracion de Gunicorn")

def worker_int(worker):
    """Hook ejecutado cuando worker recibe SIGINT"""
    print(f"Worker {worker.pid} interrumpido")

def on_exit(server):
    """Hook ejecutado al salir"""
    print("Cerrando Gunicorn")

def pre_fork(server, worker):
    """Hook antes de crear worker"""
    print(f"Creando worker {worker.age}")

def post_fork(server, worker):
    """Hook después de crear worker"""
    print(f"Worker {worker.pid} iniciado")

def when_ready(server):
    """Hook cuando server está listo"""
    print("Gunicorn listo para recibir requests")
    print(f"Worker class: {worker_class}")
    print(f"Workers activos: {workers}")

def worker_abort(worker):
    """Hook cuando worker es abortado"""
    print(f"Worker {worker.pid} abortado inesperadamente")

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
    timeout = 60  # Más tiempo para debugging
    reload = True  # Auto-reload en desarrollo
    
elif env == 'testing':
    # Configuración mínima para testing
    workers = 1
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
                print(f"Memoria limitada ({mem_total_mb:.0f}MB), reduciendo workers a {workers}")
            elif mem_total_mb < 1024:
                workers = min(workers, 2)
                print(f"Memoria detectada: {mem_total_mb:.0f}MB, usando {workers} workers")
                
    except Exception as e:
        print(f"No se pudo detectar memoria del sistema: {e}")

# LOG FINAL DE CONFIGURACIÓN (USA PRINT EN LUGAR DE LOGGER)
print("Configuracion de Gunicorn cargada:")
print(f"   Workers: {workers}")
print(f"   Worker class: {worker_class}")
print(f"   Timeout: {timeout}s")
print(f"   Bind: {bind}")
print(f"   Log level: {loglevel}")

# Validación final
if workers < 2:
    print("ADVERTENCIA: Configuracion de bajo rendimiento detectada")