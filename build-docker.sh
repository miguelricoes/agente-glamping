#!/bin/bash
# 🔨 build-docker.sh - Script Robusto para Build de Docker
# Build optimizado con manejo avanzado de errores, cleanup y monitoring

set -euo pipefail  # Fail fast con pipe failure detection

# ===============================================================================
# CONFIGURACIÓN Y VARIABLES GLOBALES
# ===============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variables configurables
DOCKER_TAG="${1:-glamping-agent}"
BUILD_CONTEXT="${2:-.}"
BUILD_TARGET="${3:-}"
BUILD_MODE="${BUILD_MODE:-development}"  # development|production|test

# Variables de estado para cleanup
TEMP_FILES=()
INTERMEDIATE_IMAGES=()
BUILD_START_TIME=""
CLEANUP_ENABLED=true

# ===============================================================================
# FUNCIONES DE UTILIDAD Y LOGGING
# ===============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo -e "\n${PURPLE}🔍 $1${NC}"
    echo "==============================================================================="
}

log_build() {
    echo -e "${CYAN}🔨 $1${NC}"
}

# Función para mostrar progreso
show_progress() {
    local current=$1
    local total=$2
    local desc=$3
    local percent=$((current * 100 / total))
    printf "\r${BLUE}[%3d%%] %s${NC}" "$percent" "$desc"
}

# Función para calcular tiempo transcurrido
elapsed_time() {
    local start_time=$1
    local end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    printf "%dm %ds" "$minutes" "$seconds"
}

# ===============================================================================
# FUNCIONES DE CLEANUP Y MANEJO DE ERRORES
# ===============================================================================

# Función de limpieza completa
cleanup() {
    if [[ "$CLEANUP_ENABLED" != "true" ]]; then
        return 0
    fi

    log_section "LIMPIEZA DE RECURSOS"
    
    # Limpiar archivos temporales
    if [[ ${#TEMP_FILES[@]} -gt 0 ]]; then
        log_info "Eliminando archivos temporales..."
        for temp_file in "${TEMP_FILES[@]}"; do
            if [[ -f "$temp_file" ]]; then
                rm -f "$temp_file" && log_success "Eliminado: $temp_file" || log_warning "No se pudo eliminar: $temp_file"
            fi
        done
    fi

    # Limpiar imágenes intermedias huérfanas
    log_info "Limpiando imágenes intermedias huérfanas..."
    if docker image prune -f --filter "dangling=true" >/dev/null 2>&1; then
        log_success "Imágenes huérfanas eliminadas"
    else
        log_warning "No se pudieron eliminar algunas imágenes huérfanas"
    fi

    # Limpiar build cache si está muy lleno
    local cache_usage
    cache_usage=$(docker system df --format "table {{.Type}}\t{{.Size}}" | grep "Build Cache" | awk '{print $3}' | sed 's/[^0-9.]//g' || echo "0")
    if (( $(echo "$cache_usage > 1.0" | bc -l 2>/dev/null || echo 0) )); then
        log_info "Cache de build grande (${cache_usage}GB) - considerando limpieza..."
        log_warning "Ejecuta manualmente: docker builder prune -f"
    fi

    log_success "Limpieza completada"
}

# Función de cleanup en caso de error
cleanup_on_error() {
    local exit_code=$?
    log_error "Build falló con código de salida: $exit_code"
    
    if [[ -n "$BUILD_START_TIME" ]]; then
        local build_time
        build_time=$(elapsed_time "$BUILD_START_TIME")
        log_info "Tiempo transcurrido antes del error: $build_time"
    fi
    
    cleanup
    
    log_section "INFORMACIÓN DE DEBUG"
    log_info "Para debugging, puedes:"
    echo "  - Revisar logs de Docker: docker logs <container_id>"
    echo "  - Verificar espacio en disco: df -h"
    echo "  - Limpiar sistema Docker: docker system prune -f"
    echo "  - Ejecutar validación: ./validate-build.sh"
    
    exit $exit_code
}

# Configurar traps para manejo de errores
trap cleanup_on_error ERR INT TERM

# ===============================================================================
# VERIFICACIONES PRE-BUILD
# ===============================================================================

pre_build_checks() {
    log_section "VERIFICACIONES PRE-BUILD"
    
    # Verificar que Docker está disponible
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado o no está en PATH"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon no está corriendo"
        exit 1
    fi
    log_success "Docker está disponible y funcionando"

    # Verificar argumentos
    if [[ -z "$DOCKER_TAG" ]]; then
        log_error "Tag de Docker no puede estar vacío"
        exit 1
    fi
    log_success "Tag válido: $DOCKER_TAG"

    # Verificar contexto de build
    if [[ ! -d "$BUILD_CONTEXT" ]]; then
        log_error "Contexto de build no existe: $BUILD_CONTEXT"
        exit 1
    fi
    
    if [[ ! -f "$BUILD_CONTEXT/Dockerfile" ]]; then
        log_error "Dockerfile no encontrado en: $BUILD_CONTEXT"
        exit 1
    fi
    log_success "Contexto de build válido: $BUILD_CONTEXT"

    # Verificar espacio en disco
    local docker_root
    docker_root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo "/var/lib/docker")
    local available_space_kb
    available_space_kb=$(df "$docker_root" 2>/dev/null | awk 'NR==2 {print $4}' || echo "0")
    local available_space_gb=$((available_space_kb / 1024 / 1024))
    
    if [[ $available_space_kb -lt 2097152 ]]; then  # 2GB en KB
        log_warning "Espacio en disco bajo: ${available_space_gb}GB disponible (recomendado: >2GB)"
        log_info "Considera ejecutar: docker system prune -f"
    else
        log_success "Espacio en disco suficiente: ${available_space_gb}GB disponible"
    fi

    # Verificar memoria disponible
    if command -v free &> /dev/null; then
        local available_mem_mb
        available_mem_mb=$(free -m | awk 'NR==2{print $7}' || echo "0")
        if [[ $available_mem_mb -lt 512 ]]; then
            log_warning "Memoria disponible baja: ${available_mem_mb}MB (recomendado: >512MB)"
        else
            log_success "Memoria disponible: ${available_mem_mb}MB"
        fi
    fi

    # Ejecutar script de validación si existe
    if [[ -f "$BUILD_CONTEXT/validate-build.sh" ]]; then
        log_info "Ejecutando validación pre-build..."
        if bash "$BUILD_CONTEXT/validate-build.sh"; then
            log_success "Validación pre-build pasada"
        else
            log_error "Validación pre-build falló"
            exit 1
        fi
    else
        log_warning "Script de validación no encontrado (recomendado)"
    fi
}

# ===============================================================================
# ANÁLISIS DE CONTEXTO DE BUILD
# ===============================================================================

analyze_build_context() {
    log_section "ANÁLISIS DE CONTEXTO DE BUILD"
    
    # Calcular tamaño del contexto
    local context_size_kb
    context_size_kb=$(du -sk "$BUILD_CONTEXT" 2>/dev/null | cut -f1 || echo "0")
    local context_size_mb=$((context_size_kb / 1024))
    
    if [[ $context_size_kb -gt 524288 ]]; then  # 512MB
        log_warning "Contexto de build grande: ${context_size_mb}MB (puede ser lento)"
        log_info "Considera optimizar .dockerignore"
    else
        log_success "Tamaño de contexto: ${context_size_mb}MB"
    fi
    
    # Verificar .dockerignore
    if [[ -f "$BUILD_CONTEXT/.dockerignore" ]]; then
        local ignore_lines
        ignore_lines=$(wc -l < "$BUILD_CONTEXT/.dockerignore")
        log_success ".dockerignore encontrado ($ignore_lines reglas)"
    else
        log_warning ".dockerignore no encontrado - build puede incluir archivos innecesarios"
    fi
    
    # Contar archivos en contexto
    local file_count
    file_count=$(find "$BUILD_CONTEXT" -type f 2>/dev/null | wc -l || echo "0")
    log_info "Archivos en contexto: $file_count"
    
    # Identificar archivos grandes (>10MB)
    local large_files
    large_files=$(find "$BUILD_CONTEXT" -type f -size +10M 2>/dev/null | head -5 || echo "")
    if [[ -n "$large_files" ]]; then
        log_warning "Archivos grandes detectados (>10MB):"
        echo "$large_files" | while read -r file; do
            local size
            size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "  - $file ($size)"
        done
        log_info "Considera excluir en .dockerignore si no son necesarios"
    fi
}

# ===============================================================================
# CONFIGURACIÓN DE BUILD OPTIMIZADA
# ===============================================================================

configure_build_args() {
    log_section "CONFIGURACIÓN DE BUILD"
    
    # Configurar argumentos base
    BUILD_ARGS=(
        "--tag" "$DOCKER_TAG"
        "--progress=plain"
    )
    
    # Configurar BuildKit
    if docker buildx version >/dev/null 2>&1; then
        log_success "Usando Docker BuildKit para optimización"
        BUILD_ARGS+=("--build-arg" "BUILDKIT_INLINE_CACHE=1")
        export DOCKER_BUILDKIT=1
    else
        log_warning "BuildKit no disponible - usando builder clásico"
    fi
    
    # Configurar cache según el modo
    case "$BUILD_MODE" in
        "production")
            log_info "Modo producción: Build sin cache para imagen limpia"
            BUILD_ARGS+=("--no-cache")
            ;;
        "development")
            log_info "Modo desarrollo: Usando cache para build rápido"
            # No agregamos --no-cache
            ;;
        "test")
            log_info "Modo test: Build optimizado para testing"
            BUILD_ARGS+=("--target" "test")
            ;;
        *)
            log_warning "Modo desconocido: $BUILD_MODE, usando configuración por defecto"
            ;;
    esac
    
    # Configurar target si se especificó
    if [[ -n "$BUILD_TARGET" ]]; then
        BUILD_ARGS+=("--target" "$BUILD_TARGET")
        log_info "Target específico: $BUILD_TARGET"
    fi
    
    # Configurar plataforma si es necesario
    local arch
    arch=$(uname -m)
    if [[ "$arch" != "x86_64" ]]; then
        BUILD_ARGS+=("--platform" "linux/$arch")
        log_info "Plataforma específica: linux/$arch"
    fi
    
    # Agregar contexto al final
    BUILD_ARGS+=("$BUILD_CONTEXT")
    
    log_success "Configuración de build preparada"
}

# ===============================================================================
# EJECUCIÓN DEL BUILD
# ===============================================================================

execute_build() {
    log_section "EJECUTANDO BUILD DE DOCKER"
    
    BUILD_START_TIME=$(date +%s)
    
    log_build "Iniciando build con configuración:"
    echo "  Tag: $DOCKER_TAG"
    echo "  Contexto: $BUILD_CONTEXT"
    echo "  Modo: $BUILD_MODE"
    if [[ -n "$BUILD_TARGET" ]]; then
        echo "  Target: $BUILD_TARGET"
    fi
    echo ""
    
    # Ejecutar build con monitoreo
    log_build "Ejecutando: docker build ${BUILD_ARGS[*]}"
    echo ""
    
    if docker build "${BUILD_ARGS[@]}"; then
        local build_end_time
        build_end_time=$(date +%s)
        local total_build_time
        total_build_time=$(elapsed_time "$BUILD_START_TIME")
        
        log_success "Build completado en: $total_build_time"
    else
        log_error "Build falló"
        exit 1
    fi
}

# ===============================================================================
# VERIFICACIÓN POST-BUILD
# ===============================================================================

verify_build() {
    log_section "VERIFICACIÓN POST-BUILD"
    
    # Verificar que la imagen existe
    if ! docker image inspect "$DOCKER_TAG" &> /dev/null; then
        log_error "La imagen no se creó correctamente: $DOCKER_TAG"
        exit 1
    fi
    log_success "Imagen creada exitosamente: $DOCKER_TAG"
    
    # Obtener información de la imagen
    local image_id size_bytes created
    image_id=$(docker image inspect "$DOCKER_TAG" --format "{{.Id}}" | cut -d: -f2 | cut -c1-12)
    size_bytes=$(docker image inspect "$DOCKER_TAG" --format "{{.Size}}")
    created=$(docker image inspect "$DOCKER_TAG" --format "{{.Created}}")
    
    # Convertir tamaño a formato legible
    local size_mb=$((size_bytes / 1024 / 1024))
    
    log_success "ID de imagen: $image_id"
    log_success "Tamaño: ${size_mb}MB"
    log_success "Creada: $created"
    
    # Verificar tamaño de imagen
    if [[ $size_mb -gt 1024 ]]; then  # >1GB
        log_warning "Imagen grande: ${size_mb}MB - considera optimización"
    else
        log_success "Tamaño de imagen optimizado: ${size_mb}MB"
    fi
    
    # Test básico de la imagen
    log_info "Ejecutando test básico de la imagen..."
    if timeout 30 docker run --rm "$DOCKER_TAG" python -c "print('✅ Test básico pasado')" 2>/dev/null; then
        log_success "Test básico de imagen pasado"
    else
        log_warning "Test básico de imagen falló o tomó más de 30s"
    fi
}

# ===============================================================================
# REPORTE FINAL Y RECOMENDACIONES
# ===============================================================================

final_report() {
    log_section "REPORTE FINAL"
    
    local total_time
    total_time=$(elapsed_time "$BUILD_START_TIME")
    
    echo -e "${GREEN}🎉 BUILD COMPLETADO EXITOSAMENTE${NC}"
    echo ""
    echo -e "${BLUE}📊 Estadísticas:${NC}"
    echo "  • Tiempo total: $total_time"
    echo "  • Tag: $DOCKER_TAG"
    echo "  • Modo: $BUILD_MODE"
    echo "  • Contexto: $BUILD_CONTEXT"
    echo ""
    
    echo -e "${BLUE}🚀 Comandos de deployment:${NC}"
    echo ""
    echo -e "${CYAN}  # Desarrollo local:${NC}"
    echo "  docker run -p 8080:8080 --env-file .env $DOCKER_TAG"
    echo ""
    echo -e "${CYAN}  # Con docker-compose:${NC}"
    echo "  docker-compose up"
    echo ""
    echo -e "${CYAN}  # Producción:${NC}"
    echo "  docker run -d -p 8080:8080 --name glamping-agent $DOCKER_TAG"
    echo ""
    
    echo -e "${BLUE}🔧 Comandos útiles:${NC}"
    echo "  • Ver logs: docker logs $DOCKER_TAG"
    echo "  • Inspeccionar: docker image inspect $DOCKER_TAG"
    echo "  • Shell interactivo: docker run -it $DOCKER_TAG bash"
    echo "  • Cleanup: docker system prune -f"
    echo ""
    
    # Recomendaciones específicas del modo
    case "$BUILD_MODE" in
        "production")
            echo -e "${YELLOW}💡 Recomendaciones para producción:${NC}"
            echo "  • Usa un registry: docker tag $DOCKER_TAG your-registry.com/$DOCKER_TAG"
            echo "  • Configura health checks en tu orchestrator"
            echo "  • Considera usar secrets externos"
            ;;
        "development")
            echo -e "${YELLOW}💡 Para desarrollo:${NC}"
            echo "  • Usa docker-compose para servicios completos"
            echo "  • Monta volúmenes para desarrollo: -v \$(pwd):/app"
            ;;
    esac
    
    echo ""
    log_success "Build y verificación completados exitosamente"
}

# ===============================================================================
# FUNCIÓN PRINCIPAL
# ===============================================================================

main() {
    echo -e "${BLUE}"
    echo "🔨 SCRIPT DE BUILD ROBUSTO - AGENTE GLAMPING"
    echo "==============================================================================="
    echo "🎯 Build optimizado con manejo avanzado de errores y monitoring"
    echo -e "${NC}\n"
    
    # Mostrar configuración inicial
    log_info "Configuración de build:"
    echo "  • Tag: $DOCKER_TAG"
    echo "  • Contexto: $BUILD_CONTEXT"
    echo "  • Modo: $BUILD_MODE"
    if [[ -n "$BUILD_TARGET" ]]; then
        echo "  • Target: $BUILD_TARGET"
    fi
    echo ""
    
    # Ejecutar pipeline de build
    pre_build_checks
    analyze_build_context  
    configure_build_args
    execute_build
    verify_build
    final_report
    
    # Cleanup final
    cleanup
}

# ===============================================================================
# MANEJO DE ARGUMENTOS Y EJECUCIÓN
# ===============================================================================

# Mostrar ayuda si se solicita
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "🔨 Script de Build Robusto para Docker"
    echo ""
    echo "Uso: $0 [TAG] [CONTEXTO] [TARGET]"
    echo ""
    echo "Parámetros:"
    echo "  TAG      - Tag para la imagen Docker (default: glamping-agent)"
    echo "  CONTEXTO - Directorio de contexto de build (default: .)"
    echo "  TARGET   - Target específico del Dockerfile (opcional)"
    echo ""
    echo "Variables de entorno:"
    echo "  BUILD_MODE - Modo de build: development|production|test (default: development)"
    echo ""
    echo "Ejemplos:"
    echo "  $0                              # Build básico"
    echo "  $0 my-app ./src                 # Tag y contexto personalizados"
    echo "  BUILD_MODE=production $0        # Build para producción"
    echo ""
    exit 0
fi

# Ejecutar función principal
main "$@"