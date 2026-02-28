#!/bin/bash

# HoneyDew - Installer
# Run once to install dependencies and create config.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CYAN='\033[0;36m'
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       ${PURPLE}HoneyDew${CYAN} by Smartify.ai           ║${NC}"
echo -e "${CYAN}║            Installer                   ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

# ── Config ───────────────────────────────────────────────────────────

DEFAULT_COLUMNS='["To Do", "In Progress", "Done", "Blocked"]'

if [ -f config.json ]; then
    echo -e "${GREEN}✓${NC} config.json already exists — skipping setup prompts."
else
    echo -e "${CYAN}Let's set up your profile and get your board configured!.${NC}"
    echo ""

    # User name
    printf "  Your name: "
    read -r USER_NAME
    USER_NAME="${USER_NAME:-User}"
    USER_ID=$(echo "$USER_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

    # Agent name
    printf "  Your agent's name: "
    read -r AGENT_NAME
    AGENT_NAME="${AGENT_NAME:-Agent}"
    AGENT_ID=$(echo "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

    echo ""
    echo -e "  Default columns: ${PURPLE}To Do, In Progress, Done, Blocked${NC}"
    printf "  Use defaults? (Y/n): "
    read -r COL_CHOICE

    if [ -z "$COL_CHOICE" ] || [[ "$COL_CHOICE" =~ ^[Yy] ]]; then
        COLUMNS_JSON="$DEFAULT_COLUMNS"
    else
        printf "  Enter column names (comma or space separated): "
        read -r COL_INPUT
        COLUMNS_JSON=$(python3 -c "
import re, json
raw = '''$COL_INPUT'''
parts = [c.strip() for c in re.split(r'[,]+', raw) if c.strip()]
if not parts:
    parts = ['To Do', 'In Progress', 'Done', 'Blocked']
print(json.dumps(parts))
")
    fi

    python3 -c "
import json
user_name = '''$USER_NAME'''
agent_name = '''$AGENT_NAME'''
user_id = '''$USER_ID'''
agent_id = '''$AGENT_ID'''
columns = json.loads('''$COLUMNS_JSON''')
config = {
    'user': {'profile_id': user_id, 'display_name': user_name},
    'agent': {'profile_id': agent_id, 'display_name': agent_name},
    'boards': [
        {'name': user_name + \"'s Board\", 'columns': columns},
        {'name': agent_name + \"'s Board\", 'columns': columns},
    ],
}
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
"
    echo ""
    echo -e "${GREEN}✓${NC} Created config.json"
    echo -e "  User:    ${PURPLE}$USER_NAME${NC} ($USER_ID)"
    echo -e "  Agent:   ${PURPLE}$AGENT_NAME${NC} ($AGENT_ID)"
    echo -e "  Columns: ${PURPLE}$(echo "$COLUMNS_JSON" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin)))")${NC}"
fi
echo ""

# ── Backend dependencies (use project venv to avoid PEP 668) ───────────

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${CYAN}Creating project virtual environment...${NC}"
    if ! python3 -m venv "$VENV_DIR" 2>&1; then
        echo -e "${YELLOW}Error: Could not create a virtual environment.${NC}"
        echo "  Your Python may be externally managed (PEP 668). Install venv and try again:"
        echo "    macOS:   brew install python-tk  (or ensure python@3.x has venv)"
        echo "    Linux:   sudo apt install python3-venv  (or equivalent)"
        echo "  Or run with a Python that includes venv:  python3 -m venv .venv"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Created .venv"
fi
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo -e "${CYAN}Installing backend dependencies...${NC}"
if ! "$PIP" install -r backend/requirements.txt -q 2>/dev/null; then
    "$PIP" install -r backend/requirements.txt
    exit 1
fi
echo -e "${GREEN}✓${NC} Backend dependencies installed"
echo ""

# ── Frontend dependencies ────────────────────────────────────────────

echo -e "${CYAN}Installing frontend dependencies...${NC}"
cd frontend
npm install --silent 2>/dev/null
cd ..
echo -e "${GREEN}✓${NC} Frontend dependencies installed"
echo ""

# ── Done ─────────────────────────────────────────────────────────────

echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  Next steps:"
echo -e "  1. Run ${CYAN}./start.sh${NC} to launch the app."
echo -e "  2. ${YELLOW}Edit config.json${NC} any time to change names, boards, or columns."
echo ""
