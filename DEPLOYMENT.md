# 🚀 AGENT-V2 Deployment Guide

## Production Deployment

### Prerequisites

- Linux server (Ubuntu 20.04+)
- Node.js 18+, Python 3.9+
- 2GB+ RAM, 10GB+ disk space
- gh CLI configured with GitHub token

### Step 1: Clone & Install

```bash
git clone https://github.com/Irfan430/AGENT-V2.git
cd AGENT-V2

# Install dependencies
pnpm install
pip3 install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit with production settings
nano .env
```

**Important settings:**

```env
NODE_ENV=production
AUTH_DISABLED=false  # Enable authentication
PORT=3000
PYTHON_AGENT_PORT=8001

# LLM Configuration
DEFAULT_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_production_key

# Database (if using)
DATABASE_URL=mysql://user:pass@host/db

# OAuth (if enabling auth)
OAUTH_SERVER_URL=https://your-oauth-server.com
JWT_SECRET=your_secret_key
```

### Step 3: Build

```bash
pnpm build
```

### Step 4: Run with PM2 (Recommended)

```bash
# Install PM2 globally
npm install -g pm2

# Create ecosystem config
cat > ecosystem.config.js << 'EOFPM2'
module.exports = {
  apps: [
    {
      name: 'agent-v2-node',
      script: './dist/index.js',
      instances: 1,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: './logs/node-error.log',
      out_file: './logs/node-out.log'
    },
    {
      name: 'agent-v2-python',
      script: 'python3',
      args: 'server/main.py',
      instances: 1,
      env: {
        PYTHONUNBUFFERED: 1,
        PORT: 8001
      },
      error_file: './logs/python-error.log',
      out_file: './logs/python-out.log'
    }
  ]
};
EOFPM2

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Step 5: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install nginx

# Create config
sudo nano /etc/nginx/sites-available/agent-v2
```

**Nginx configuration:**

```nginx
upstream agent_node {
    server localhost:3000;
}

upstream agent_python {
    server localhost:8001;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend & tRPC
    location / {
        proxy_pass http://agent_node;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Python Agent API
    location /agent/ {
        proxy_pass http://agent_python/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://agent_python;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/agent-v2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

### Step 7: Monitoring & Logs

```bash
# View logs
pm2 logs

# Monitor processes
pm2 monit

# Save logs
pm2 save

# Auto-start on reboot
pm2 startup
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t agent-v2:latest .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

### Access

- Frontend: https://your-domain.com
- API: https://your-domain.com/api/trpc
- Agent: https://your-domain.com/agent

## Scaling

### Horizontal Scaling

1. **Load Balancer**: Use Nginx/HAProxy
2. **Multiple Instances**: Run multiple Node.js instances
3. **Shared Database**: Use MySQL/PostgreSQL
4. **Shared Memory**: Use Redis for session storage

### Performance Optimization

```bash
# Enable compression
gzip on;
gzip_types text/plain application/json;

# Cache static assets
location ~* \.(js|css|png|jpg|gif)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ {
    limit_req zone=api burst=20 nodelay;
}
```

## Backup & Recovery

### Database Backup

```bash
# MySQL backup
mysqldump -u user -p database > backup.sql

# Restore
mysql -u user -p database < backup.sql
```

### Application Backup

```bash
# Backup entire directory
tar -czf agent-v2-backup.tar.gz /path/to/AGENT-V2/

# Restore
tar -xzf agent-v2-backup.tar.gz
```

## Troubleshooting

### High CPU Usage

```bash
# Check process
top -p $(pgrep -f "node dist/index.js")

# Restart
pm2 restart agent-v2-node
```

### Memory Leaks

```bash
# Monitor memory
pm2 monit

# Restart if needed
pm2 restart all
```

### Connection Issues

```bash
# Check ports
netstat -tlnp | grep -E "3000|8001"

# Check logs
tail -f logs/node-error.log
tail -f logs/python-error.log
```

## Security Checklist

- ✅ Enable HTTPS/SSL
- ✅ Set strong JWT_SECRET
- ✅ Configure firewall
- ✅ Enable authentication (AUTH_DISABLED=false)
- ✅ Use environment variables for secrets
- ✅ Regular backups
- ✅ Monitor logs
- ✅ Update dependencies regularly
- ✅ Use strong database passwords
- ✅ Restrict API access with rate limiting

## Monitoring & Alerts

### Setup Monitoring

```bash
# Install monitoring tools
npm install -g pm2-monitoring

# Enable monitoring
pm2 monitor
```

### Key Metrics to Monitor

- CPU usage
- Memory usage
- Response time
- Error rate
- Active connections
- Database query time

---

**For more help**, check the main README or open an issue on GitHub.
