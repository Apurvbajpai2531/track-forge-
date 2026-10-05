#!/bin/bash
set -e

# ---------- Install Docker ----------
apt-get update -y
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker

# ---------- App directory ----------
mkdir -p /opt/trackforge
cd /opt/trackforge

# ---------- nginx.conf ----------
cat > nginx.conf << 'NGINX_EOF'
events {}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:5000;
    }

    server {
        listen 80;

        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /docs {
            proxy_pass http://backend/docs;
            proxy_set_header Host $host;
        }

        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
NGINX_EOF

# ---------- docker-compose.yml ----------
cat > docker-compose.yml << COMPOSE_EOF
services:
  backend:
    image: ${backend_image}
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg2://${db_username}:${db_password}@${db_host}:5432/${db_name}
      SECRET_KEY: ${backend_secret_key}
    expose:
      - "8000"

  frontend:
    image: ${frontend_image}
    restart: unless-stopped
    environment:
      API_BASE_URL: http://backend:8000/api
      API_TIMEOUT_SECONDS: "5"
      FRONTEND_SECRET_KEY: ${frontend_secret_key}
      GROQ_API_KEY: ${groq_api_key}
      AI_PROVIDER: groq
    expose:
      - "5000"
    depends_on:
      - backend

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend
COMPOSE_EOF

# ---------- Start the app ----------
docker compose up -d
