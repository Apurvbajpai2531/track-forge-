#!/bin/bash
set -e

echo "=================================="
echo "  TrackForge — Starting Project"
echo "=================================="

# 1. Check .env files exist, create with defaults if missing
if [ ! -f "backend/.env" ]; then
    echo "backend/.env not found — creating with default values..."
    cat > backend/.env << 'EOF'
SECRET_KEY=trackforge-backend-secret-key
EOF
fi

if [ ! -f "frontend/.env" ]; then
    echo "frontend/.env not found — creating with default values..."
    cat > frontend/.env << 'EOF'
FRONTEND_SECRET_KEY=trackforge-frontend-secret-key
EOF
fi

# 2. Check for port conflicts (80 and 5432) and warn
if command -v lsof >/dev/null 2>&1; then
    if sudo lsof -i :80 >/dev/null 2>&1; then
        echo "WARNING: Port 80 is already in use on this machine."
        echo "  Common causes: apache2 or nginx running locally."
        echo "  Fix with: sudo systemctl stop apache2   (or nginx)"
    fi
    if sudo lsof -i :5432 >/dev/null 2>&1; then
        echo "WARNING: Port 5432 is already in use on this machine."
        echo "  Common cause: a local Postgres service running."
        echo "  Fix with: sudo systemctl stop postgresql"
    fi
fi

# 3. Stop any existing containers from a previous run
echo "Stopping any existing containers..."
docker compose down 2>/dev/null || true

# 4. Build and start everything
echo "Building and starting all containers..."
docker compose up --build -d

# 5. Show status
echo ""
echo "=================================="
echo "  Container status:"
echo "=================================="
docker compose ps

echo ""
echo "TrackForge is starting up. Once all containers show 'healthy' or 'running',"
echo "open: http://localhost"
echo ""
echo "View logs with:   docker compose logs -f"
echo "Stop everything with:   docker compose down"
