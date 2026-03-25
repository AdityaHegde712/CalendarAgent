#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}       Calendar Agent Launcher         ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── 1. Check .env ─────────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo -e "${YELLOW}[setup] .env not found. Copying from .env.example...${NC}"
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  echo -e "${RED}[action] Please edit .env and set your API key, then re-run this script.${NC}"
  exit 1
fi

# ── 2. Check credentials.json ─────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/credentials.json" ]; then
  echo -e "${RED}[error] credentials.json not found in the project root.${NC}"
  echo "  → Follow the README to download it from Google Cloud Console."
  exit 1
fi

# ── 3. Python venv ────────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  echo -e "${YELLOW}[setup] Creating Python virtual environment...${NC}"
  python -m venv "$VENV_DIR"
fi

echo -e "${YELLOW}[setup] Activating venv and installing backend dependencies...${NC}"
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$BACKEND_DIR/requirements.txt"
echo -e "${GREEN}[ok] Backend dependencies installed.${NC}"

# ── 4. Node / npm ─────────────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo -e "${RED}[error] Node.js is not installed. Please install it from https://nodejs.org${NC}"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo -e "${YELLOW}[setup] Installing frontend dependencies (npm install)...${NC}"
  cd "$FRONTEND_DIR" && npm install --silent
  cd "$PROJECT_DIR"
fi
echo -e "${GREEN}[ok] Frontend dependencies ready.${NC}"

# ── 5. Copy credentials into backend dir for easy access ──────────────────────
cp "$PROJECT_DIR/credentials.json" "$BACKEND_DIR/credentials.json"
[ -f "$PROJECT_DIR/token.json" ] && cp "$PROJECT_DIR/token.json" "$BACKEND_DIR/token.json"

# ── 6. Launch backend ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}[start] Launching backend on http://localhost:8000 ...${NC}"
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# ── 7. Launch frontend ────────────────────────────────────────────────────────
echo -e "${GREEN}[start] Launching frontend on http://localhost:3000 ...${NC}"
cd "$FRONTEND_DIR"
REACT_APP_API_URL=http://localhost:8000 npm start &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Backend  → ${GREEN}http://localhost:8000${NC}"
echo -e "  Frontend → ${GREEN}http://localhost:3000${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  On first run, a browser window will open for Google OAuth."
echo "  Press Ctrl+C to stop both servers."
echo ""

# ── 8. Cleanup on exit ────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "${YELLOW}[stop] Shutting down...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  # Sync token back to project root if updated
  [ -f "$BACKEND_DIR/token.json" ] && cp "$BACKEND_DIR/token.json" "$PROJECT_DIR/token.json"
  deactivate 2>/dev/null || true
}

trap cleanup EXIT INT TERM
wait
