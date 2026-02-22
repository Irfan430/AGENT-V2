#!/bin/bash

# ============================================================
# AGENT-V2 Unified Development Server
# Starts both Node.js (frontend + tRPC) and Python (agent) servers
# Usage: ./dev.sh or pnpm dev:all
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           AGENT-V2 Development Server                      ║${NC}"
echo -e "${BLUE}║  Starting Node.js (3000) + Python Agent (8001)             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

# Load environment
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please configure .env with your API keys${NC}"
    exit 1
fi

export $(cat .env | grep -v '^#' | xargs)

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

echo -e "${YELLOW}Checking ports...${NC}"
check_port 3000 || exit 1
check_port 8001 || exit 1
echo -e "${GREEN}✓ Ports 3000 and 8001 are available${NC}\n"

# Function to handle cleanup
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $NODE_PID 2>/dev/null || true
    kill $PYTHON_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Node.js server (frontend + tRPC)
echo -e "${BLUE}Starting Node.js server on port 3000...${NC}"
NODE_ENV=development AUTH_DISABLED=true pnpm dev > /tmp/node-server.log 2>&1 &
NODE_PID=$!
echo -e "${GREEN}✓ Node.js server started (PID: $NODE_PID)${NC}"

# Wait for Node.js to be ready
sleep 3

# Start Python agent server
echo -e "${BLUE}Starting Python agent on port 8001...${NC}"
python3 server/main.py > /tmp/python-server.log 2>&1 &
PYTHON_PID=$!
echo -e "${GREEN}✓ Python agent started (PID: $PYTHON_PID)${NC}\n"

# Wait for both servers to be ready
sleep 2

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  ✓ Servers Running                         ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Frontend & API:  ${BLUE}http://localhost:3000${GREEN}                  ║${NC}"
echo -e "${GREEN}║  Chat Interface:  ${BLUE}http://localhost:3000/chat${GREEN}               ║${NC}"
echo -e "${GREEN}║  Python Agent:    ${BLUE}http://localhost:8001${GREEN}                  ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  Logs:                                                     ║${NC}"
echo -e "${GREEN}║    Node.js:  ${YELLOW}tail -f /tmp/node-server.log${GREEN}                ║${NC}"
echo -e "${GREEN}║    Python:   ${YELLOW}tail -f /tmp/python-server.log${GREEN}               ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  Press Ctrl+C to stop all servers                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

# Keep the script running
wait $NODE_PID $PYTHON_PID
