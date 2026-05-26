#!/usr/bin/env bash
# =============================================================================
# Festival Luciérnagas 2026 — Setup automatizado
# =============================================================================
# Uso:  ./setup.sh
# Compatible con: Ubuntu/Debian, Fedora, Arch, macOS, WSL2
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() { echo -e "\n${BLUE}▶ $1${NC}"; }
print_ok()   { echo -e "${GREEN}✔ $1${NC}"; }
print_warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_err()  { echo -e "${RED}✖ $1${NC}"; }

# -----------------------------------------------------------------------------
# 1. Detectar sistema operativo
# -----------------------------------------------------------------------------
print_step "Detectando sistema operativo..."

OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if grep -qi microsoft /proc/version 2>/dev/null; then
        OS="wsl"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
fi
print_ok "Sistema detectado: $OS"

# -----------------------------------------------------------------------------
# 2. Verificar que Docker esté instalado
# -----------------------------------------------------------------------------
print_step "Verificando Docker..."

if ! command -v docker &> /dev/null; then
    print_err "Docker no está instalado."
    echo ""
    echo "Instala Docker desde:"
    case $OS in
        linux|wsl) echo "  https://docs.docker.com/engine/install/" ;;
        mac)       echo "  https://docs.docker.com/desktop/install/mac-install/" ;;
        *)         echo "  https://docs.docker.com/get-docker/" ;;
    esac
    echo ""
    echo "Después de instalar, vuelve a correr ./setup.sh"
    exit 1
fi
print_ok "Docker instalado: $(docker --version)"

# -----------------------------------------------------------------------------
# 3. Verificar Docker Compose
# -----------------------------------------------------------------------------
print_step "Verificando Docker Compose..."

if docker compose version &> /dev/null; then
    print_ok "Docker Compose: $(docker compose version --short)"
else
    print_err "Docker Compose v2 no disponible. Actualiza Docker a una versión reciente."
    exit 1
fi

# -----------------------------------------------------------------------------
# 4. Verificar que el daemon de Docker esté corriendo
# -----------------------------------------------------------------------------
print_step "Verificando que el daemon de Docker esté corriendo..."

if ! docker info &> /dev/null; then
    if [[ "$OS" == "linux" || "$OS" == "wsl" ]]; then
        print_warn "Docker no responde. Intentando arrancarlo..."
        sudo systemctl start docker || true
        sleep 2
    elif [[ "$OS" == "mac" ]]; then
        print_err "Docker Desktop no está corriendo. Ábrelo desde Aplicaciones y vuelve a correr ./setup.sh"
        exit 1
    fi

    # Reintentar (puede ser problema de permisos)
    if ! docker info &> /dev/null 2>&1; then
        if [[ "$OS" == "linux" || "$OS" == "wsl" ]]; then
            print_warn "Docker no responde — probablemente es problema de permisos."
            print_step "Configurando grupo docker para tu usuario..."

            # Crear grupo docker si no existe
            if ! getent group docker > /dev/null 2>&1; then
                sudo groupadd docker
                print_ok "Grupo 'docker' creado."
            fi

            # Agregar usuario al grupo
            if ! groups | grep -q docker; then
                sudo usermod -aG docker "$USER"
                print_warn "Te agregué al grupo 'docker'."
                echo ""
                print_err "DEBES CERRAR SESIÓN Y VOLVER A ENTRAR (o reiniciar la computadora)"
                print_err "para que el cambio surta efecto."
                echo ""
                echo "Después de reiniciar sesión, vuelve a correr ./setup.sh"
                exit 1
            fi
        else
            print_err "No puedo conectar con Docker. Verifica que esté corriendo."
            exit 1
        fi
    fi
fi
print_ok "Docker daemon respondiendo correctamente."

# -----------------------------------------------------------------------------
# 5. Configurar permisos del entrypoint
# -----------------------------------------------------------------------------
print_step "Configurando permisos del entrypoint..."

if [[ -f "docker/entrypoint.sh" ]]; then
    chmod +x docker/entrypoint.sh
    # Quitar CRLF si el archivo viene con line endings de Windows
    if file docker/entrypoint.sh | grep -q CRLF; then
        print_warn "entrypoint.sh tiene line endings de Windows. Convirtiendo a LF..."
        sed -i 's/\r$//' docker/entrypoint.sh
    fi
    print_ok "Permisos OK en docker/entrypoint.sh"
else
    print_warn "No encontré docker/entrypoint.sh — saltando."
fi

# -----------------------------------------------------------------------------
# 6. Crear archivo .env si no existe
# -----------------------------------------------------------------------------
print_step "Verificando archivo .env..."

if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_ok "Archivo .env creado desde .env.example"
        print_warn "Revisa .env y ajusta las variables si es necesario."
    else
        print_warn "No hay .env ni .env.example. Si el proyecto los necesita, créalos manualmente."
    fi
else
    print_ok "Archivo .env ya existe."
fi

# -----------------------------------------------------------------------------
# 7. Construir imágenes
# -----------------------------------------------------------------------------
print_step "Construyendo imágenes Docker (esto puede tardar varios minutos la primera vez)..."

docker compose build
print_ok "Imágenes construidas."

# -----------------------------------------------------------------------------
# 8. Levantar contenedores
# -----------------------------------------------------------------------------
print_step "Levantando contenedores..."

docker compose up -d
print_ok "Contenedores levantados."

# Esperar a que la base de datos esté lista
print_step "Esperando a que PostgreSQL esté listo..."
sleep 5

# -----------------------------------------------------------------------------
# 9. Aplicar migraciones
# -----------------------------------------------------------------------------
print_step "Aplicando migraciones..."

if docker compose exec -T web python manage.py migrate; then
    print_ok "Migraciones aplicadas."
else
    print_err "Las migraciones automáticas fallaron."
    echo ""
    echo "Causas comunes:"
    echo "  • Falta un paquete en requirements.txt (revisa el traceback)"
    echo "  • Falta una app sin migraciones — intenta:"
    echo "      docker compose exec web python manage.py makemigrations"
    echo "      docker compose exec web python manage.py migrate"
    echo ""
    echo "Mira los logs con: docker compose logs web --tail=80"
    exit 1
fi

# -----------------------------------------------------------------------------
# 10. Resumen final
# -----------------------------------------------------------------------------
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✨ Setup completado — Festival Luciérnagas 2026 está listo${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "🌐 URLs disponibles:"
echo "   Admin Django:    http://localhost:8000/admin/"
echo "   API Parques:     http://localhost:8000/api/parques/"
echo "   API Reservas:    http://localhost:8000/api/reservaciones/"
echo "   API Auth:        http://localhost:8000/api/auth/"
echo ""
echo "🛠  Comandos útiles:"
echo "   Ver logs:        docker compose logs -f web"
echo "   Detener todo:    docker compose down"
echo "   Volver a iniciar:docker compose up -d"
echo "   Shell de la BD:  make dbshell"
echo "   Crear superuser: docker compose exec web python manage.py createsuperuser"
echo ""
echo "Si es la primera vez, crea un superusuario:"
echo "   docker compose exec web python manage.py createsuperuser"
echo ""