#!/bin/bash
# 🧪 test-docker.sh - Script para Manejo del Entorno de Testing Local
# Facilita el setup, ejecución y cleanup del entorno de testing completo

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables
COMPOSE_FILE="docker-compose.test.yml"
ENV_FILE=".env.test"
ENV_EXAMPLE=".env.test.example"

# Funciones de logging
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_section() { echo -e "\n${PURPLE}🔍 $1${NC}\n$(printf '=%.0s' {1..79})"; }

# ===============================================================================
# FUNCIONES DE VERIFICACIÓN Y SETUP
# ===============================================================================

check_prerequisites() {
    log_section "VERIFICANDO PREREQUISITOS"
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    log_success "Docker está disponible"
    
    # Verificar Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose no está disponible"
        log_info "Instala Docker Compose v2: https://docs.docker.com/compose/install/"
        exit 1
    fi
    log_success "Docker Compose está disponible"
    
    # Verificar archivos necesarios
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Archivo de compose no encontrado: $COMPOSE_FILE"
        exit 1
    fi
    log_success "Archivo de compose encontrado: $COMPOSE_FILE"
}

setup_env_file() {
    log_section "CONFIGURANDO ARCHIVO DE ENTORNO"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE" ]]; then
            log_info "Creando $ENV_FILE desde ejemplo..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_success "Archivo $ENV_FILE creado desde ejemplo"
            log_warning "IMPORTANTE: Configura las APIs necesarias en $ENV_FILE"
            log_info "Al menos necesitas configurar OPENAI_API_KEY"
        else
            log_error "No se encontró archivo de ejemplo: $ENV_EXAMPLE"
            exit 1
        fi
    else
        log_success "Archivo de entorno encontrado: $ENV_FILE"
    fi
    
    # Verificar variables críticas
    if ! grep -q "OPENAI_API_KEY=sk-" "$ENV_FILE" 2>/dev/null; then
        log_warning "OPENAI_API_KEY no configurada o vacía en $ENV_FILE"
        log_info "La aplicación necesita una API key válida de OpenAI para funcionar"
    fi
}

check_ports() {
    log_section "VERIFICANDO PUERTOS DISPONIBLES"
    
    # Puertos por defecto a verificar
    local ports=(8080 5432 6379 8081 8082)
    local port_conflicts=()
    
    for port in "${ports[@]}"; do
        if command -v netstat &> /dev/null; then
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                port_conflicts+=("$port")
            fi
        elif command -v lsof &> /dev/null; then
            if lsof -i ":$port" >/dev/null 2>&1; then
                port_conflicts+=("$port")
            fi
        fi
    done
    
    if [[ ${#port_conflicts[@]} -gt 0 ]]; then
        log_warning "Puertos en uso detectados: ${port_conflicts[*]}"
        log_info "Puedes cambiar los puertos en $ENV_FILE o detener los servicios conflictivos"
    else
        log_success "Todos los puertos están disponibles"
    fi
}

# ===============================================================================
# FUNCIONES DE CONTROL DE SERVICIOS
# ===============================================================================

start_services() {
    log_section "INICIANDO SERVICIOS DE TESTING"
    
    log_info "Iniciando servicios en background..."
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d; then
        log_success "Servicios iniciados exitosamente"
        
        # Mostrar estado de servicios
        show_services_status
        
        # Mostrar URLs de acceso
        show_access_urls
        
    else
        log_error "Error iniciando servicios"
        exit 1
    fi
}

stop_services() {
    log_section "DETENIENDO SERVICIOS DE TESTING"
    
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down; then
        log_success "Servicios detenidos exitosamente"
    else
        log_warning "Algunos servicios no se pudieron detener correctamente"
    fi
}

restart_services() {
    log_section "REINICIANDO SERVICIOS DE TESTING"
    
    stop_services
    sleep 2
    start_services
}

build_and_start() {
    log_section "CONSTRUYENDO Y INICIANDO SERVICIOS"
    
    log_info "Construyendo imágenes..."
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache; then
        log_success "Imágenes construidas exitosamente"
    else
        log_error "Error construyendo imágenes"
        exit 1
    fi
    
    start_services
}

show_services_status() {
    log_section "ESTADO DE SERVICIOS"
    
    echo ""
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo ""
    
    # Verificar health checks
    local services=("glamping-agent" "postgres-test" "redis-test")
    local healthy_count=0
    
    for service in "${services[@]}"; do
        local health_status
        health_status=$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --format "table {{.Service}}\t{{.Status}}" | grep "$service" | awk '{print $2}' || echo "unknown")
        
        if [[ "$health_status" == *"healthy"* ]]; then
            log_success "Servicio saludable: $service"
            ((healthy_count++))
        elif [[ "$health_status" == *"starting"* ]]; then
            log_info "Servicio iniciando: $service"
        else
            log_warning "Servicio con problemas: $service ($health_status)"
        fi
    done
    
    if [[ $healthy_count -eq ${#services[@]} ]]; then
        log_success "Todos los servicios críticos están saludables"
    else
        log_warning "Algunos servicios aún están iniciando o tienen problemas"
        log_info "Espera unos momentos y verifica con: $0 status"
    fi
}

show_access_urls() {
    log_section "URLS DE ACCESO"
    
    echo ""
    echo -e "${CYAN}🌐 Servicios disponibles:${NC}"
    echo "  • Aplicación principal:    http://localhost:8080"
    echo "  • Health check:           http://localhost:8080/health"
    echo "  • Adminer (PostgreSQL):   http://localhost:8081"
    echo "  • Redis Commander:        http://localhost:8082"
    echo ""
    echo -e "${CYAN}🔌 Acceso directo a bases de datos:${NC}"
    echo "  • PostgreSQL: localhost:5432 (glamping_test/glamping_user/glamping_pass)"
    echo "  • Redis:      localhost:6379"
    echo ""
    echo -e "${CYAN}📊 Comandos útiles:${NC}"
    echo "  • Ver logs aplicación:     docker compose -f $COMPOSE_FILE logs -f glamping-agent"
    echo "  • Ver logs PostgreSQL:     docker compose -f $COMPOSE_FILE logs -f postgres-test"  
    echo "  • Ver logs Redis:          docker compose -f $COMPOSE_FILE logs -f redis-test"
    echo "  • Shell en aplicación:     docker compose -f $COMPOSE_FILE exec glamping-agent bash"
    echo ""
}

show_logs() {
    local service="${1:-}"
    
    if [[ -z "$service" ]]; then
        log_info "Mostrando logs de todos los servicios..."
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
    else
        log_info "Mostrando logs de: $service"
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "$service"
    fi
}

run_tests() {
    log_section "EJECUTANDO TESTS AUTOMATIZADOS"
    
    # Verificar que los servicios estén corriendo
    if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps glamping-agent | grep -q "Up"; then
        log_error "Los servicios no están corriendo. Ejecuta: $0 start"
        exit 1
    fi
    
    log_info "Ejecutando suite de tests..."
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up test-runner; then
        log_success "Tests ejecutados. Revisa los resultados en ./test_results/"
    else
        log_warning "Algunos tests fallaron. Revisa los logs para más detalles."
    fi
}

cleanup_all() {
    log_section "LIMPIEZA COMPLETA DEL ENTORNO"
    
    log_info "Deteniendo y eliminando servicios..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v
    
    log_info "Eliminando imágenes relacionadas..."
    docker images | grep glamping | awk '{print $3}' | xargs -r docker rmi -f || true
    
    log_info "Limpiando recursos Docker..."
    docker system prune -f
    
    log_success "Limpieza completa finalizada"
}

# ===============================================================================
# FUNCIÓN PRINCIPAL Y MANEJO DE COMANDOS
# ===============================================================================

show_help() {
    echo -e "${BLUE}🧪 Script de Manejo del Entorno de Testing Local${NC}"
    echo ""
    echo "Uso: $0 <comando> [opciones]"
    echo ""
    echo -e "${CYAN}Comandos disponibles:${NC}"
    echo "  setup     - Configurar entorno inicial"
    echo "  start     - Iniciar servicios de testing"
    echo "  stop      - Detener servicios"  
    echo "  restart   - Reiniciar servicios"
    echo "  build     - Construir imágenes y iniciar servicios"
    echo "  status    - Mostrar estado de servicios"
    echo "  logs      - Mostrar logs [servicio]"
    echo "  test      - Ejecutar tests automatizados"
    echo "  urls      - Mostrar URLs de acceso"
    echo "  cleanup   - Limpieza completa del entorno"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo -e "${CYAN}Ejemplos:${NC}"
    echo "  $0 setup              # Configuración inicial"
    echo "  $0 start              # Iniciar todos los servicios"
    echo "  $0 logs glamping-agent # Ver logs de la aplicación"
    echo "  $0 test               # Ejecutar tests"
    echo "  $0 cleanup            # Limpieza completa"
    echo ""
    echo -e "${YELLOW}Notas:${NC}"
    echo "  • Asegúrate de configurar OPENAI_API_KEY en .env.test"
    echo "  • Los servicios tardan ~60s en estar completamente listos"
    echo "  • Usa 'Ctrl+C' para interrumpir logs en tiempo real"
    echo ""
}

main() {
    local command="${1:-help}"
    
    case "$command" in
        "setup")
            check_prerequisites
            setup_env_file
            check_ports
            log_success "Setup completado. Ejecuta '$0 start' para iniciar servicios"
            ;;
        "start")
            check_prerequisites
            setup_env_file
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "build")
            check_prerequisites
            setup_env_file
            build_and_start
            ;;
        "status")
            show_services_status
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "test")
            run_tests
            ;;
        "urls")
            show_access_urls
            ;;
        "cleanup")
            cleanup_all
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Comando desconocido: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"