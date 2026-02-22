# Manus Agent Pro - Setup Guide

Complete setup instructions for running Manus Agent Pro locally and in production.

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (with WSL2)
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for Docker images and data

### Required Software
- Docker 20.10+ and Docker Compose 2.0+
- Python 3.11+ (for local development)
- Node.js 22+ (for frontend development)
- Git 2.30+

### API Keys
- **DeepSeek API Key**: Get from https://platform.deepseek.com
- **Optional**: OpenAI API key for additional models

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/manus-agent-pro.git
cd manus-agent-pro
```

### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# LLM Configuration
LLM_API_KEY=sk-your-deepseek-api-key
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# Agent Configuration
AGENT_NAME=Manus Agent Pro
AGENT_VERSION=1.0.0
MAX_ITERATIONS=10

# Database
DATABASE_URL=mysql://root:root@localhost:3306/manus_agent
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=manus_agent

# Security
JWT_SECRET=your-secret-key-here
WORKSPACE_ROOT=./workspace

# Memory
CHROMA_DB_PATH=./chroma_db

# OAuth (if using Manus OAuth)
VITE_APP_ID=your-app-id
OAUTH_SERVER_URL=https://api.manus.im
VITE_OAUTH_PORTAL_URL=https://manus.im/login
```

### 3. Install Python Dependencies
```bash
# Create virtual environment (optional but recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies
```bash
cd client
pnpm install
cd ..
```

### 5. Initialize Database
```bash
# Create database tables
python -c "from server.main import app; print('Database initialized')"
```

### 6. Start Backend Server
```bash
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 3000
```

The backend will be available at `http://localhost:3000`

### 7. Start Frontend Server (in another terminal)
```bash
cd client
pnpm dev
```

The frontend will be available at `http://localhost:5173`

### 8. Access the Application
- **Web UI**: http://localhost:5173
- **API**: http://localhost:3000/api
- **Chat**: http://localhost:5173/chat
- **Dashboard**: http://localhost:5173/dashboard

## Docker Setup

### 1. Build Docker Image
```bash
docker build -t manus-agent-pro:latest .
```

### 2. Start with Docker Compose
```bash
# Create necessary directories
mkdir -p workspace chroma_db logs

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

### 3. Access Services
- **Web UI**: http://localhost
- **API**: http://localhost/api
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

### 4. Stop Services
```bash
docker-compose down
```

### 5. Clean Up
```bash
# Remove containers and volumes
docker-compose down -v

# Remove images
docker rmi manus-agent-pro:latest
```

## Configuration

### Agent Configuration
Edit `server/agent_config.py` to customize:
- Agent name and description
- System prompt and behavior
- Tool availability
- Memory settings
- Security policies

### LLM Settings
Modify `server/llm_client.py` for:
- Model selection
- Temperature and parameters
- Token limits
- Retry policies

### Memory Settings
Configure `server/memory_manager_advanced.py`:
- Collection names
- Embedding model
- Search parameters
- Retention policies

## Troubleshooting

### Issue: "Connection refused" on localhost:3000
**Solution**: Ensure the backend server is running
```bash
# Check if port 3000 is in use
lsof -i :3000

# Kill process if needed
kill -9 <PID>
```

### Issue: "Database connection error"
**Solution**: Verify MySQL is running and credentials are correct
```bash
# Test connection
mysql -h localhost -u root -p -e "SELECT 1"

# Check Docker container
docker-compose logs db
```

### Issue: "LLM API key invalid"
**Solution**: Verify your DeepSeek API key
```bash
# Test API key
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

### Issue: "Out of memory" errors
**Solution**: Increase Docker memory limits
```bash
# Edit docker-compose.yml
services:
  app:
    mem_limit: 4g
    memswap_limit: 4g
```

### Issue: "Port already in use"
**Solution**: Change port mappings in docker-compose.yml
```yaml
ports:
  - "8000:3000"  # Use 8000 instead of 3000
```

## Performance Tuning

### Database Optimization
```sql
-- Create indexes for faster queries
CREATE INDEX idx_conversation_user ON conversations(user_id);
CREATE INDEX idx_memory_type ON memories(memory_type);
CREATE INDEX idx_task_status ON tasks(status);
```

### Redis Caching
Enable Redis caching in `server/main.py`:
```python
from redis import Redis
redis_client = Redis(host='localhost', port=6379, db=0)
```

### Nginx Optimization
Adjust worker processes in `nginx.conf`:
```nginx
worker_processes auto;  # Use all available CPU cores
worker_connections 4096;  # Increase connection limit
```

## Security Hardening

### 1. Change Default Passwords
```bash
# Update MySQL password
docker-compose exec db mysql -u root -p -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'strong-password';"

# Update JWT secret
export JWT_SECRET=$(openssl rand -hex 32)
```

### 2. Enable SSL/TLS
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes

# Update nginx.conf to use SSL
```

### 3. Restrict API Access
```bash
# Add rate limiting in nginx.conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

### 4. Enable CORS
```python
# In server/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring

### View Logs
```bash
# Backend logs
docker-compose logs -f app

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

### Monitor Resources
```bash
# CPU and memory usage
docker stats

# Disk usage
docker system df
```

### Health Checks
```bash
# Check API health
curl http://localhost:3000/api/health

# Check database
docker-compose exec db mysqladmin ping -u root -p

# Check Redis
docker-compose exec redis redis-cli ping
```

## Backup and Restore

### Backup Database
```bash
# Backup MySQL
docker-compose exec db mysqldump -u root -p manus_agent > backup.sql

# Backup ChromaDB
tar -czf chroma_db_backup.tar.gz chroma_db/

# Backup workspace
tar -czf workspace_backup.tar.gz workspace/
```

### Restore Database
```bash
# Restore MySQL
docker-compose exec -T db mysql -u root -p manus_agent < backup.sql

# Restore ChromaDB
tar -xzf chroma_db_backup.tar.gz

# Restore workspace
tar -xzf workspace_backup.tar.gz
```

## Production Deployment

### 1. Prepare Production Environment
```bash
# Create production .env
cp .env.example .env.production
# Edit with production values
```

### 2. Build Production Image
```bash
docker build -f Dockerfile -t manus-agent-pro:1.0.0 .
docker tag manus-agent-pro:1.0.0 your-registry/manus-agent-pro:1.0.0
docker push your-registry/manus-agent-pro:1.0.0
```

### 3. Deploy with Docker Compose
```bash
# Update docker-compose.yml with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. Set Up SSL Certificate
```bash
# Using Let's Encrypt with Certbot
certbot certonly --standalone -d yourdomain.com
# Copy certificates to ssl/ directory
```

### 5. Configure Domain
```bash
# Update nginx.conf with your domain
server_name yourdomain.com;

# Update CORS in application
ALLOWED_ORIGINS=https://yourdomain.com
```

### 6. Monitor Production
```bash
# Set up log rotation
docker-compose exec app logrotate -f /etc/logrotate.d/app

# Monitor with Prometheus/Grafana
docker-compose -f docker-compose.monitoring.yml up -d
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 3
```

### Load Balancing
```nginx
# nginx.conf
upstream app_backend {
    least_conn;
    server app:3000 weight=1;
    server app:3001 weight=1;
    server app:3002 weight=1;
}
```

### Database Replication
```bash
# Set up MySQL replication for high availability
docker-compose -f docker-compose.replication.yml up -d
```

## Support and Troubleshooting

For more help:
1. Check logs: `docker-compose logs -f`
2. Read documentation: See README.md
3. Create GitHub issue: https://github.com/yourusername/manus-agent-pro/issues
4. Contact support: support@example.com

---

**Last Updated**: 2026-02-22
**Version**: 1.0.0
