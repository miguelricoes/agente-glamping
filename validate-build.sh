#!/bin/bash
# 🔍 validate-build.sh - Script de Validación Pre-Build Completo
# Valida entorno, archivos y configuración antes del build de Docker

set -euo pipefail  # Fail fast en errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Contadores para estadísticas
CHECKS_PASSED=0
CHECKS_TOTAL=0
WARNINGS=0

# Función para logging con colores
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo -e "\n${PURPLE}🔍 $1${NC}"
    echo "==============================================================================="
}

# Incrementar contador total de checks
check_total() {
    ((CHECKS_TOTAL++))
}

# ===============================================================================
# VERIFICACIONES DE SISTEMA Y ENTORNO
# ===============================================================================

check_docker_environment() {
    log_section "VERIFICANDO ENTORNO DOCKER"
    
    # Verificar instalación de Docker
    check_total
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        log_info "Instala Docker desde: https://docs.docker.com/get-docker/"
        exit 1
    fi
    log_success "Docker está instalado"

    # Verificar daemon Docker
    check_total
    if ! docker info &> /dev/null; then
        log_error "Docker daemon no está corriendo"
        log_info "Inicia Docker daemon: sudo systemctl start docker"
        exit 1
    fi
    log_success "Docker daemon está corriendo"

    # Verificar versión Docker
    check_total
    DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    log_success "Docker versión: $DOCKER_VERSION"

    # Verificar BuildKit (opcional pero recomendado)
    check_total
    if docker buildx version &> /dev/null; then
        log_success "Docker BuildKit disponible (optimización habilitada)"
    else
        log_warning "Docker BuildKit no disponible (build puede ser más lento)"
    fi

    # Verificar espacio en disco
    check_total
    DISK_SPACE=$(df -h . | awk 'NR==2 {print $4}')
    DISK_SPACE_NUM=$(df . | awk 'NR==2 {print $4}')
    if [[ $DISK_SPACE_NUM -lt 2097152 ]]; then  # 2GB en KB
        log_warning "Espacio en disco bajo: $DISK_SPACE disponible (recomendado: >2GB)"
    else
        log_success "Espacio en disco: $DISK_SPACE disponible"
    fi
}

# ===============================================================================
# VERIFICACIÓN DE ARCHIVOS CRÍTICOS
# ===============================================================================

check_critical_files() {
    log_section "VERIFICANDO ARCHIVOS CRÍTICOS"

    # Archivos absolutamente necesarios
    critical_files=(
        "Dockerfile"
        "requirements.txt" 
        "agente_standalone.py"
        "gunicorn.conf.py"
        ".dockerignore"
    )

    for file in "${critical_files[@]}"; do
        check_total
        if [[ ! -f "$file" ]]; then
            log_error "Archivo crítico faltante: $file"
            exit 1
        fi
        log_success "Archivo encontrado: $file"
    done

    # Archivos opcionales pero recomendados
    optional_files=(
        "docker-compose.yml"
        "docker-compose.prod.yml"
        ".env.example"
        "README.md"
    )

    for file in "${optional_files[@]}"; do
        check_total
        if [[ -f "$file" ]]; then
            log_success "Archivo opcional encontrado: $file"
        else
            log_warning "Archivo opcional faltante: $file (recomendado para producción)"
        fi
    done
}

# ===============================================================================
# VERIFICACIÓN DE DIRECTORIOS ESENCIALES
# ===============================================================================

check_directory_structure() {
    log_section "VERIFICANDO ESTRUCTURA DE DIRECTORIOS"

    # Directorios necesarios para la aplicación
    required_dirs=(
        "config"
        "models"
        "routes"
        "services"
        "utils"
        "security"
    )

    for dir in "${required_dirs[@]}"; do
        check_total
        if [[ ! -d "$dir" ]]; then
            log_error "Directorio crítico faltante: $dir"
            exit 1
        fi
        
        # Verificar que no esté vacío
        if [[ -z "$(ls -A "$dir")" ]]; then
            log_warning "Directorio vacío: $dir"
        else
            log_success "Directorio encontrado y poblado: $dir"
        fi
    done
}

# ===============================================================================
# VALIDACIÓN DE SINTAXIS PYTHON
# ===============================================================================

check_python_syntax() {
    log_section "VALIDANDO SINTAXIS PYTHON"

    # Verificar que Python está disponible
    check_total
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        log_error "Python no está instalado"
        exit 1
    fi

    # Determinar comando Python correcto
    PYTHON_CMD="python3"
    if ! command -v python3 &> /dev/null; then
        PYTHON_CMD="python"
    fi
    log_success "Python disponible: $($PYTHON_CMD --version)"

    # Archivos Python críticos para validar
    python_files=(
        "agente_standalone.py"
        "gunicorn.conf.py"
    )

    for file in "${python_files[@]}"; do
        check_total
        if ! $PYTHON_CMD -m py_compile "$file" 2>/dev/null; then
            log_error "Error de sintaxis en: $file"
            $PYTHON_CMD -m py_compile "$file"  # Mostrar error específico
            exit 1
        fi
        log_success "Sintaxis válida: $file"
    done

    # Validar archivos Python en directorios críticos
    for dir in config models routes services utils security; do
        if [[ -d "$dir" ]]; then
            python_count=$(find "$dir" -name "*.py" | wc -l)
            if [[ $python_count -gt 0 ]]; then
                check_total
                if find "$dir" -name "*.py" -exec $PYTHON_CMD -m py_compile {} \; 2>/dev/null; then
                    log_success "Sintaxis válida en directorio: $dir ($python_count archivos)"
                else
                    log_error "Errores de sintaxis en directorio: $dir"
                    exit 1
                fi
            fi
        fi
    done
}

# ===============================================================================
# VALIDACIÓN DE REQUIREMENTS.TXT
# ===============================================================================

check_requirements() {
    log_section "VALIDANDO REQUIREMENTS.TXT"

    # Dependencias críticas que deben estar presentes
    critical_deps=(
        "Flask"
        "gunicorn"
        "psycopg2-binary"
        "openai"
        "langchain"
        "numpy"
    )

    for dep in "${critical_deps[@]}"; do
        check_total
        if ! grep -qi "$dep" requirements.txt; then
            log_error "Dependencia crítica faltante en requirements.txt: $dep"
            exit 1
        fi
        log_success "Dependencia crítica encontrada: $dep"
    done

    # Verificar formato y versiones
    check_total
    if grep -q "==.*==\|>=.*>=" requirements.txt; then
        log_warning "Posibles versiones duplicadas o malformadas en requirements.txt"
    else
        log_success "Formato de versiones correcto en requirements.txt"
    fi

    # Contar total de dependencias
    check_total
    TOTAL_DEPS=$(grep -c "^[^#].*==" requirements.txt || echo "0")
    if [[ $TOTAL_DEPS -lt 10 ]]; then
        log_warning "Pocas dependencias definidas: $TOTAL_DEPS (¿archivo incompleto?)"
    else
        log_success "Total de dependencias: $TOTAL_DEPS"
    fi
}

# ===============================================================================
# VALIDACIÓN DE DOCKERFILE
# ===============================================================================

check_dockerfile() {
    log_section "VALIDANDO DOCKERFILE"

    # Verificar estructura básica
    check_total
    if ! grep -q "FROM python" Dockerfile; then
        log_error "Dockerfile no usa imagen base Python"
        exit 1
    fi
    log_success "Imagen base Python encontrada"

    # Verificar etapas críticas
    docker_checks=(
        "WORKDIR"
        "COPY requirements.txt"
        "RUN pip install"
        "COPY \."
        "EXPOSE"
        "CMD"
    )

    for check in "${docker_checks[@]}"; do
        check_total
        if ! grep -q "$check" Dockerfile; then
            log_error "Instrucción Dockerfile faltante: $check"
            exit 1
        fi
        log_success "Instrucción Dockerfile encontrada: $check"
    done

    # Verificar usuario no-root
    check_total
    if grep -q "USER.*appuser\|USER.*[^root]" Dockerfile; then
        log_success "Usuario no-root configurado (seguridad)"
    else
        log_warning "No se encontró configuración de usuario no-root"
    fi

    # Verificar health check
    check_total
    if grep -q "HEALTHCHECK" Dockerfile; then
        log_success "Health check configurado"
    else
        log_warning "Health check no configurado (recomendado para producción)"
    fi
}

# ===============================================================================
# ANÁLISIS DE CONTEXTO DE BUILD
# ===============================================================================

analyze_build_context() {
    log_section "ANALIZANDO CONTEXTO DE BUILD"

    # Calcular tamaño del contexto
    check_total
    if command -v du &> /dev/null; then
        CONTEXT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
        CONTEXT_SIZE_KB=$(du -sk . 2>/dev/null | cut -f1)
        
        log_success "Tamaño del contexto de build: $CONTEXT_SIZE"
        
        # Advertencia si el contexto es muy grande
        if [[ $CONTEXT_SIZE_KB -gt 524288 ]]; then  # 512MB
            log_warning "Contexto de build grande (>512MB) - considera optimizar .dockerignore"
        fi
    else
        log_warning "Comando 'du' no disponible - no se puede calcular tamaño del contexto"
    fi

    # Verificar .dockerignore
    check_total
    if [[ -f ".dockerignore" ]]; then
        DOCKERIGNORE_LINES=$(wc -l < .dockerignore)
        log_success ".dockerignore encontrado ($DOCKERIGNORE_LINES líneas)"
        
        # Verificar patrones críticos en .dockerignore
        critical_ignores=(".env" "__pycache__" "*.log" ".git")
        for pattern in "${critical_ignores[@]}"; do
            if grep -q "$pattern" .dockerignore; then
                log_success "Patrón de exclusión encontrado: $pattern"
            else
                log_warning "Patrón recomendado faltante en .dockerignore: $pattern"
            fi
        done
    else
        log_warning ".dockerignore faltante - el build puede incluir archivos innecesarios"
    fi

    # Identificar archivos grandes
    check_total
    if command -v find &> /dev/null; then
        LARGE_FILES=$(find . -type f -size +10M 2>/dev/null | head -5)
        if [[ -n "$LARGE_FILES" ]]; then
            log_warning "Archivos grandes detectados (>10MB):"
            echo "$LARGE_FILES" | while read -r file; do
                SIZE=$(du -h "$file" 2>/dev/null | cut -f1)
                echo "  - $file ($SIZE)"
            done
            log_info "Considera excluir archivos grandes en .dockerignore"
        else
            log_success "No se detectaron archivos grandes (>10MB)"
        fi
    fi
}

# ===============================================================================
# VERIFICACIONES DE SEGURIDAD
# ===============================================================================

check_security() {
    log_section "VERIFICACIONES DE SEGURIDAD"

    # Verificar que no hay archivos .env en el directorio
    check_total
    ENV_FILES=$(find . -name ".env*" -not -path "./.git/*" 2>/dev/null || echo "")
    if [[ -n "$ENV_FILES" ]]; then
        log_warning "Archivos .env detectados (pueden contener secretos):"
        echo "$ENV_FILES" | while read -r file; do
            echo "  - $file"
        done
        log_info "Asegúrate de que están excluidos en .dockerignore"
    else
        log_success "No se detectaron archivos .env en el contexto"
    fi

    # Verificar permisos de archivos críticos
    check_total
    if [[ -f "agente_standalone.py" ]]; then
        PERMS=$(stat -c "%a" agente_standalone.py 2>/dev/null || stat -f "%A" agente_standalone.py 2>/dev/null || echo "???")
        if [[ "$PERMS" =~ ^[67][0-4][0-4]$ ]]; then
            log_success "Permisos seguros en agente_standalone.py: $PERMS"
        else
            log_warning "Permisos potencialmente inseguros en agente_standalone.py: $PERMS"
        fi
    fi

    # Verificar que no hay claves o tokens hardcodeados
    check_total
    HARDCODED_SECRETS=$(grep -r -i "api_key\|token\|password\|secret" --include="*.py" . 2>/dev/null | grep -v "example\|template" | head -3 || echo "")
    if [[ -n "$HARDCODED_SECRETS" ]]; then
        log_warning "Posibles secretos hardcodeados detectados:"
        echo "$HARDCODED_SECRETS" | while read -r line; do
            echo "  - ${line:0:80}..."
        done
        log_info "Revisa que no haya secretos reales en el código"
    else
        log_success "No se detectaron secretos hardcodeados obvios"
    fi
}

# ===============================================================================
# VERIFICACIONES DE COMPATIBILIDAD
# ===============================================================================

check_compatibility() {
    log_section "VERIFICACIONES DE COMPATIBILIDAD"

    # Verificar compatibilidad de plataforma
    check_total
    PLATFORM=$(uname -s)
    log_success "Plataforma detectada: $PLATFORM"

    # Verificar arquitectura
    check_total
    ARCH=$(uname -m)
    log_success "Arquitectura: $ARCH"
    
    if [[ "$ARCH" != "x86_64" && "$ARCH" != "amd64" ]]; then
        log_warning "Arquitectura no estándar: $ARCH (puede requerir imágenes específicas)"
    fi

    # Verificar versión de Python en requirements vs sistema
    check_total
    if command -v python3 &> /dev/null; then
        SYSTEM_PYTHON=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
        log_success "Python del sistema: $SYSTEM_PYTHON"
        
        # Verificar compatibilidad con imagen Docker (Python 3.11)
        if [[ "$SYSTEM_PYTHON" < "3.8" ]]; then
            log_warning "Python del sistema muy antiguo ($SYSTEM_PYTHON) - Docker usará Python 3.11"
        fi
    fi
}

# ===============================================================================
# FUNCIÓN PRINCIPAL Y REPORTE FINAL
# ===============================================================================

main() {
    echo -e "${BLUE}"
    echo "🔍 SCRIPT DE VALIDACIÓN PRE-BUILD - AGENTE GLAMPING"
    echo "==============================================================================="
    echo "🎯 Validando entorno completo antes del build de Docker..."
    echo -e "${NC}\n"

    # Ejecutar todas las verificaciones
    check_docker_environment
    check_critical_files
    check_directory_structure
    check_python_syntax
    check_requirements
    check_dockerfile
    analyze_build_context
    check_security
    check_compatibility

    # Reporte final
    log_section "REPORTE FINAL"
    
    SUCCESS_RATE=$((CHECKS_PASSED * 100 / CHECKS_TOTAL))
    
    echo -e "${GREEN}✅ Checks pasados: $CHECKS_PASSED/$CHECKS_TOTAL ($SUCCESS_RATE%)${NC}"
    
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Advertencias: $WARNINGS${NC}"
    fi

    echo ""
    if [[ $SUCCESS_RATE -ge 90 && $WARNINGS -le 5 ]]; then
        echo -e "${GREEN}🚀 VALIDACIÓN EXITOSA - LISTO PARA BUILD${NC}"
        echo -e "${BLUE}💡 Comandos recomendados:${NC}"
        echo "   docker build -t glamping-agent ."
        echo "   docker-compose up --build"
        echo ""
        exit 0
    elif [[ $SUCCESS_RATE -ge 80 ]]; then
        echo -e "${YELLOW}⚠️  VALIDACIÓN CON ADVERTENCIAS - BUILD POSIBLE PERO NO ÓPTIMO${NC}"
        echo -e "${BLUE}💡 Considera resolver las advertencias antes del build de producción${NC}"
        echo ""
        exit 0
    else
        echo -e "${RED}❌ VALIDACIÓN FALLIDA - NO RECOMENDADO HACER BUILD${NC}"
        echo -e "${BLUE}💡 Resuelve los errores críticos antes de continuar${NC}"
        echo ""
        exit 1
    fi
}

# Ejecutar función principal
main "$@"