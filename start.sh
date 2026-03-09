#!/usr/bin/env bash
#
# DocBot — Docker infrastructure startup script
#
# Usage:
#   ./start.sh              # Build and start all services
#   ./start.sh build        # Rebuild images then start
#   ./start.sh stop         # Stop all services
#   ./start.sh restart      # Restart all services
#   ./start.sh logs         # Tail logs from all services
#   ./start.sh status       # Show running containers
#   ./start.sh down         # Stop and remove containers, networks
#   ./start.sh clean        # Stop, remove containers, networks AND volumes
#

set -euo pipefail

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="docbot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ─── Pre-flight checks ───────────────────────────────────────────────

check_prerequisites() {
    if ! command -v docker &>/dev/null; then
        err "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker compose version &>/dev/null 2>&1; then
        if ! command -v docker-compose &>/dev/null; then
            err "Docker Compose is not installed. Please install Docker Compose."
            exit 1
        fi
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    if ! docker info &>/dev/null 2>&1; then
        err "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# ─── .env guard ───────────────────────────────────────────────────────

ensure_env_file() {
    if [ ! -f .env ]; then
        warn ".env file not found. Creating a template..."
        cat > .env <<'EOF'
# Gemini
GEMINI_API_KEY=your-gemini-api-key-here

# MinIO (defaults match docker-compose)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
EOF
        warn "Please edit .env and set your GEMINI_API_KEY, then re-run this script."
        exit 1
    fi
}

# ─── Commands ─────────────────────────────────────────────────────────

cmd_build() {
    info "Building Docker images..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build "$@"
    ok "Build complete."
}

cmd_up() {
    info "Starting all services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --build "$@"
    ok "All services are up."
    echo ""
    info "Service endpoints:"
    echo "  Frontend  : http://localhost:3000"
    echo "  Backend   : http://localhost:8000"
    echo "  MinIO     : http://localhost:9003  (console)"
    echo ""
    info "Run './start.sh logs' to follow container logs."
}

cmd_stop() {
    info "Stopping services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" stop
    ok "Services stopped."
}

cmd_restart() {
    info "Restarting services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart
    ok "Services restarted."
}

cmd_down() {
    info "Stopping and removing containers..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    ok "Done."
}

cmd_clean() {
    warn "This will remove containers, networks AND volumes (data will be lost)."
    read -rp "Continue? [y/N] " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v
        ok "Cleaned up."
    else
        info "Cancelled."
    fi
}

cmd_logs() {
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$@"
}

cmd_status() {
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
}

# ─── Main ─────────────────────────────────────────────────────────────

main() {
    cd "$(dirname "$0")"

    check_prerequisites
    ensure_env_file

    local action="${1:-up}"
    shift 2>/dev/null || true

    case "$action" in
        build)   cmd_build "$@" ;;
        up)      cmd_up "$@" ;;
        start)   cmd_up "$@" ;;
        stop)    cmd_stop ;;
        restart) cmd_restart ;;
        down)    cmd_down ;;
        clean)   cmd_clean ;;
        logs)    cmd_logs "$@" ;;
        status)  cmd_status ;;
        *)
            echo "Usage: $0 {build|up|start|stop|restart|down|clean|logs|status}"
            exit 1
            ;;
    esac
}

main "$@"
