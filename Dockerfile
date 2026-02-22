# Multi-stage Dockerfile for Manus Agent Pro

# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /app/client

# Copy package files
COPY client/package.json client/pnpm-lock.yaml ./

# Install dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy source files
COPY client/src ./src
COPY client/public ./public
COPY client/index.html ./
COPY client/vite.config.ts ./
COPY client/tsconfig.json ./
COPY client/postcss.config.js ./
COPY client/tailwind.config.js ./

# Build frontend
RUN pnpm build

# Stage 2: Build backend and final image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY server ./server
COPY shared ./shared
COPY drizzle ./drizzle

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/client/dist ./client/dist

# Create necessary directories
RUN mkdir -p /app/chroma_db /app/workspace /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Expose ports
EXPOSE 3000 5000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "3000"]
