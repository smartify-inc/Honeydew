#!/bin/bash

# HoneyDew - Start Script
# Starts both backend and frontend servers
# Usage: ./start.sh [--docs] [--check-only] [--validate-config]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SERVE_DOCS=0
CHECK_ONLY=0
VALIDATE_CONFIG=0
for arg in "$@"; do
    case "$arg" in
        --docs) SERVE_DOCS=1 ;;
        --check-only) CHECK_ONLY=1 ;;
        --validate-config) VALIDATE_CONFIG=1 ;;
    esac
done

# Use project venv if present (created by install.sh)
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
    PIP="$SCRIPT_DIR/.venv/bin/pip"
else
    PYTHON=python3
    PIP="python3 -m pip"
fi

# Resolve the active config file: config.json if present, else config.example.json
CONFIG_FILE="$SCRIPT_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ] && [ -f "$SCRIPT_DIR/config.example.json" ]; then
    ACTIVE_CONFIG="$SCRIPT_DIR/config.example.json"
else
    ACTIVE_CONFIG="$CONFIG_FILE"
fi

# Validate a config file — used by both --validate-config and pre-flight checks
validate_config() {
    local cfg="$1"
    if [ ! -f "$cfg" ]; then
        echo "Error: Config file not found: $cfg"
        return 1
    fi
    "$PYTHON" -c "
import json, sys
try:
    d = json.load(open('$cfg'))
    for key in ('user', 'agent'):
        if key not in d:
            print(f'Missing required key: {key}', file=sys.stderr)
            sys.exit(1)
        if 'profile_id' not in d[key] or 'display_name' not in d[key]:
            print(f'Missing profile_id or display_name in {key}', file=sys.stderr)
            sys.exit(1)
except json.JSONDecodeError as e:
    print(f'Invalid JSON: {e}', file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f'Cannot read file: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1
}

# --validate-config: validate and exit without starting servers
if [ "$VALIDATE_CONFIG" -eq 1 ]; then
    echo "Validating config: $ACTIVE_CONFIG"
    if validate_config "$ACTIVE_CONFIG"; then
        echo "Config is valid."
        exit 0
    else
        echo "Config validation failed."
        exit 1
    fi
fi

# If config.json is missing, create it from the example
if [ ! -f "$CONFIG_FILE" ] && [ -f "$SCRIPT_DIR/config.example.json" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_FILE"
    echo "Created config.json from config.example.json — edit it to customize."
    ACTIVE_CONFIG="$CONFIG_FILE"
fi

# Pre-flight: validate config
if [ -f "$ACTIVE_CONFIG" ] && command -v "$PYTHON" &>/dev/null; then
    if ! validate_config "$ACTIVE_CONFIG" >/dev/null 2>&1; then
        echo "Error: $ACTIVE_CONFIG is invalid or missing required keys. Fix or remove it and run again."
        exit 1
    fi
fi

# Pre-flight: backend dependencies (uvicorn + app)
if ! (cd "$SCRIPT_DIR/backend" && "$PYTHON" -c "import uvicorn; from app.main import app" 2>/dev/null); then
    echo "Error: Backend dependencies not ready. Run ./install.sh first."
    echo "  (Checking with the same Python that will run the app...)"
    (cd "$SCRIPT_DIR/backend" && "$PYTHON" -c "import uvicorn; from app.main import app") || true
    exit 1
fi

# Pre-flight: frontend dependencies
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "Error: Frontend dependencies not installed. Run ./install.sh first."
    exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    echo "Pre-flight checks passed. Backend and frontend are ready to start."
    exit 0
fi

if [ -f "$CONFIG_FILE" ]; then
    USER_NAME=$("$PYTHON" -c "import json; print(json.load(open('$CONFIG_FILE'))['user']['display_name'])" 2>/dev/null || echo "User")
    AGENT_NAME=$("$PYTHON" -c "import json; print(json.load(open('$CONFIG_FILE'))['agent']['display_name'])" 2>/dev/null || echo "Agent")
    USER_PROFILE=$("$PYTHON" -c "import json; print(json.load(open('$CONFIG_FILE'))['user']['profile_id'])" 2>/dev/null || echo "user")
    AGENT_PROFILE=$("$PYTHON" -c "import json; print(json.load(open('$CONFIG_FILE'))['agent']['profile_id'])" 2>/dev/null || echo "agent")
else
    USER_NAME="User"
    AGENT_NAME="Agent"
    USER_PROFILE="user"
    AGENT_PROFILE="agent"
fi

# Colors for output
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       ${PURPLE}HoneyDew${CYAN} by Smartify              ║${NC}"
echo -e "${CYAN}║    Get things done, the smart way      ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

# Kill process and its children (e.g. uvicorn reloader + worker, npm + vite)
kill_tree() {
    local pid=$1
    [ -z "$pid" ] && return
    if command -v pkill &>/dev/null; then
        pkill -P "$pid" 2>/dev/null || true
    fi
    kill -9 "$pid" 2>/dev/null || true
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${PURPLE}Shutting down servers...${NC}"
    kill_tree "$BACKEND_PID"
    kill_tree "$FRONTEND_PID"
    [ -n "$DOCS_PID" ] && kill_tree "$DOCS_PID"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${CYAN}Starting backend server...${NC}"
cd backend
"$PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo -e "${CYAN}Waiting for backend to start...${NC}"
BACKEND_READY=0
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend ready at http://localhost:8000${NC}"
        BACKEND_READY=1
        break
    fi
    sleep 1
done
if [ "$BACKEND_READY" -eq 0 ]; then
    echo -e "${PURPLE}Warning: Backend did not respond in time. Check backend logs.${NC}"
fi

# Free frontend port in case a previous run left it bound
if command -v lsof &>/dev/null; then
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start frontend
echo -e "${CYAN}Starting frontend server...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready (Vite must be listening)
echo -e "${CYAN}Waiting for frontend to start...${NC}"
FRONTEND_READY=0
for i in {1..30}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ] || [ "$CODE" = "304" ]; then
        echo -e "${GREEN}✓ Frontend ready at http://localhost:5173${NC}"
        FRONTEND_READY=1
        break
    fi
    sleep 1
done
if [ "$FRONTEND_READY" -eq 0 ]; then
    echo -e "${PURPLE}Warning: Frontend did not respond in time. Check frontend logs.${NC}"
fi

# Optionally start the docs site
DOCS_PID=""
DOCS_LINE=""
if [ "$SERVE_DOCS" -eq 1 ]; then
    DOCS_URL="${SMARTIFY_DOCS_URL:-http://localhost:8001}"
    DOCS_BIND=$("$PYTHON" -c "
from urllib.parse import urlparse
u = urlparse('$DOCS_URL')
host = u.hostname or '127.0.0.1'
port = u.port or 8001
print(f'{host}:{port}')
" 2>/dev/null) || DOCS_BIND="127.0.0.1:8001"
    if ! "$PYTHON" -c "import mkdocs" 2>/dev/null; then
        echo -e "${CYAN}Installing docs dependencies...${NC}"
        "$PYTHON" -m pip install -r "$SCRIPT_DIR/docs/requirements.txt" -q 2>/dev/null || "$PYTHON" -m pip install -r "$SCRIPT_DIR/docs/requirements.txt"
    fi
    echo -e "${CYAN}Starting docs server...${NC}"
    "$PYTHON" -m mkdocs serve -a "$DOCS_BIND" --quiet &
    DOCS_PID=$!
    DOCS_READY=0
    for i in {1..15}; do
        CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOCS_URL/" 2>/dev/null || echo "000")
        if [ "$CODE" = "200" ] || [ "$CODE" = "304" ]; then
            echo -e "${GREEN}✓ Docs ready at $DOCS_URL${NC}"
            DOCS_READY=1
            break
        fi
        sleep 1
    done
    if [ "$DOCS_READY" -eq 0 ]; then
        echo -e "${PURPLE}Warning: Docs server did not respond in time.${NC}"
    fi
    DOCS_LINE="\n  ${CYAN}Docs:${NC}      $DOCS_URL"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Servers running! Press Ctrl+C to stop ${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:5173"
echo -e "  ${CYAN}Backend:${NC}   http://localhost:8000"
echo -e "  ${CYAN}API Docs:${NC}  http://localhost:8000/docs"
[ -n "$DOCS_LINE" ] && echo -e "$DOCS_LINE"
echo ""
echo -e "  ${PURPLE}${USER_NAME}:${NC}     http://localhost:5173/?profile=${USER_PROFILE}"
echo -e "  ${PURPLE}${AGENT_NAME}:${NC}     http://localhost:5173/?profile=${AGENT_PROFILE}"
echo ""
echo -e "  ${CYAN}Tip:${NC} Open the Frontend URL (5173) in your browser to use the app."
echo -e "       API endpoints (8000) are for the app; don't open /api/... in the browser on port 5173."
[ "$SERVE_DOCS" -eq 0 ] && echo -e "       Pass ${CYAN}--docs${NC} to start.sh to include the documentation site."
echo ""

# Wait for both processes
wait
