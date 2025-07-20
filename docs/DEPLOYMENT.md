# Deployment Guide

This guide covers deploying the PDF Viewer application in various environments, from development to production.

## Overview

The PDF Viewer application consists of two main components:
- **Backend**: FastAPI Python application
- **Frontend**: React TypeScript SPA

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Prerequisites
- Docker 20.0+
- Docker Compose 3.8+

#### Backend Dockerfile

```dockerfile
# Production Dockerfile for backend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install Python dependencies
RUN uv pip install --system -e .

# Copy application code
COPY backend/ ./backend/

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
# Multi-stage build for frontend
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
COPY frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY frontend/ .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - LOG_LEVEL=INFO
      - JSON_LOGS=true
      - ENVIRONMENT=production
      - MAX_FILE_SIZE=52428800
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api
    ports:
      - "80:80"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  # Optional: Redis for session storage
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: pdfviewer_network
```

#### Deployment Commands

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3

# Stop services
docker-compose down

# Update and restart
docker-compose pull
docker-compose up -d --build
```

### 2. Kubernetes Deployment

#### Backend Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdfviewer-backend
  labels:
    app: pdfviewer-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdfviewer-backend
  template:
    metadata:
      labels:
        app: pdfviewer-backend
    spec:
      containers:
      - name: backend
        image: pdfviewer/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: JSON_LOGS
          value: "true"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: pdfviewer-uploads
---
apiVersion: v1
kind: Service
metadata:
  name: pdfviewer-backend-service
spec:
  selector:
    app: pdfviewer-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Frontend Deployment

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdfviewer-frontend
  labels:
    app: pdfviewer-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pdfviewer-frontend
  template:
    metadata:
      labels:
        app: pdfviewer-frontend
    spec:
      containers:
      - name: frontend
        image: pdfviewer/frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: pdfviewer-frontend-service
spec:
  selector:
    app: pdfviewer-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

#### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pdfviewer-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
  - hosts:
    - pdfviewer.yourdomain.com
    secretName: pdfviewer-tls
  rules:
  - host: pdfviewer.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: pdfviewer-backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pdfviewer-frontend-service
            port:
              number: 80
```

### 3. Cloud Provider Deployments

#### AWS Deployment

**Using AWS ECS with Fargate:**

```yaml
# aws-ecs-task-definition.json
{
  "family": "pdfviewer",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/pdfviewer-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "JSON_LOGS", "value": "true"},
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pdfviewer",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Using AWS App Runner:**

```yaml
# apprunner.yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - echo "Installing dependencies..."
      - pip install uv
      - uv pip install -e .
run:
  runtime-version: 3.11
  command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
  env:
    - name: LOG_LEVEL
      value: INFO
    - name: JSON_LOGS
      value: "true"
    - name: ENVIRONMENT
      value: production
```

#### Google Cloud Run

```yaml
# gcp-cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: pdfviewer-backend
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/PROJECT_ID/pdfviewer-backend
        ports:
        - name: http1
          containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: INFO
        - name: JSON_LOGS
          value: "true"
        - name: ENVIRONMENT
          value: production
        resources:
          limits:
            cpu: 2000m
            memory: 2Gi
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
      volumes:
      - name: uploads
        emptyDir: {}
```

#### Azure Container Apps

```yaml
# azure-container-app.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdfviewer-config
data:
  LOG_LEVEL: "INFO"
  JSON_LOGS: "true"
  ENVIRONMENT: "production"
---
apiVersion: app.azure.com/v1
kind: ContainerApp
metadata:
  name: pdfviewer-backend
spec:
  managedEnvironmentId: /subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP/providers/Microsoft.App/managedEnvironments/ENVIRONMENT_NAME
  configuration:
    ingress:
      external: true
      targetPort: 8000
    secrets:
    - name: database-connection-string
      value: CONNECTION_STRING
  template:
    containers:
    - image: REGISTRY/pdfviewer-backend:latest
      name: backend
      env:
      - name: LOG_LEVEL
        value: INFO
      - name: JSON_LOGS
        value: "true"
      resources:
        cpu: 1.0
        memory: 2Gi
    scale:
      minReplicas: 1
      maxReplicas: 10
```

## Environment Configuration

### Production Environment Variables

**Backend (.env.production):**
```bash
# Application
LOG_LEVEL=INFO
JSON_LOGS=true
ENVIRONMENT=production

# File handling
MAX_FILE_SIZE=52428800
UPLOAD_DIR=/app/uploads

# Security
ALLOWED_HOSTS=["yourdomain.com", "www.yourdomain.com"]
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Database (if using)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis (if using)
REDIS_URL=redis://redis:6379/0

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
```

**Frontend (.env.production):**
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_NODE_ENV=production
VITE_SENTRY_DSN=https://your-frontend-sentry-dsn
```

### Staging Environment

**Backend (.env.staging):**
```bash
LOG_LEVEL=DEBUG
JSON_LOGS=true
ENVIRONMENT=staging
MAX_FILE_SIZE=52428800
UPLOAD_DIR=/app/uploads
```

**Frontend (.env.staging):**
```bash
VITE_API_BASE_URL=https://api-staging.yourdomain.com
VITE_NODE_ENV=staging
```

## Database Setup (Optional)

If you decide to add database persistence:

### PostgreSQL

```sql
-- database/init.sql
CREATE DATABASE pdfviewer;
CREATE USER pdfviewer_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE pdfviewer TO pdfviewer_user;

\c pdfviewer;

CREATE TABLE pdf_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pdf_files_upload_time ON pdf_files(upload_time);
CREATE INDEX idx_pdf_files_metadata ON pdf_files USING GIN(metadata);
```

### Redis Configuration

```redis
# redis.conf (production settings)
save 900 1
save 300 10
save 60 10000

maxmemory 2gb
maxmemory-policy allkeys-lru

appendonly yes
appendfsync everysec
```

## SSL/TLS Configuration

### Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server pdfviewer-backend:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
        ssl_certificate_key /etc/ssl/private/yourdomain.com.key;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        client_max_body_size 50M;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

## Monitoring and Observability

### Prometheus Metrics

```python
# backend/app/monitoring.py
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
FILE_UPLOADS = Counter('file_uploads_total', 'Total file uploads', ['status'])
FILE_SIZE = Histogram('file_size_bytes', 'Uploaded file sizes')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

```python
# backend/app/health.py
from fastapi import APIRouter
import psutil
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.1.0",
        "uptime": time.time() - start_time,
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }

@router.get("/ready")
async def readiness_check():
    # Check database connectivity, external services, etc.
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    # Basic liveness check
    return {"status": "alive"}
```

### Logging Configuration

```yaml
# logging-config.yaml
version: 1
disable_existing_loggers: false

formatters:
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    datefmt: '%Y-%m-%dT%H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    formatter: json
    filename: /app/logs/application.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

root:
  level: INFO
  handlers: [console, file]

loggers:
  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: false
```

## Security Considerations

### Security Headers

```python
# backend/app/security.py
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])
app.add_middleware(HTTPSRedirectMiddleware)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### File Upload Security

```python
# backend/app/security/file_validation.py
import magic
from pathlib import Path

ALLOWED_MIME_TYPES = {"application/pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_file_security(file_path: Path) -> bool:
    # Check file size
    if file_path.stat().st_size > MAX_FILE_SIZE:
        return False
    
    # Verify MIME type
    mime_type = magic.from_file(str(file_path), mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        return False
    
    # Additional PDF validation
    try:
        from pypdf import PdfReader
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            # Basic PDF structure validation
            len(reader.pages)
    except Exception:
        return False
    
    return True
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="pdfviewer"

# Create backup
pg_dump $DB_NAME | gzip > "$BACKUP_DIR/pdfviewer_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "pdfviewer_*.sql.gz" -mtime +30 -delete
```

### File Storage Backup

```bash
#!/bin/bash
# file-backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
UPLOAD_DIR="/app/uploads"
BACKUP_DIR="/backups/files"

# Sync files to backup location
rsync -av --delete "$UPLOAD_DIR/" "$BACKUP_DIR/current/"

# Create dated archive
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$UPLOAD_DIR" .

# Keep only last 7 days of archives
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +7 -delete
```

## Scaling Considerations

### Horizontal Scaling

1. **Stateless Design**: Application is stateless by design
2. **Load Balancing**: Use nginx or cloud load balancers
3. **File Storage**: Consider shared storage (NFS, S3) for multi-instance deployments
4. **Session Management**: Use Redis for session storage if needed

### Performance Optimization

1. **Caching**: Implement Redis caching for metadata
2. **CDN**: Use CDN for static assets and PDF delivery
3. **Database**: Add database connection pooling
4. **Async Processing**: Use Celery for heavy PDF processing

### Resource Requirements

**Minimum (Development):**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB+ (depending on file volume)

## Troubleshooting

### Common Issues

1. **File Upload Failures**
   - Check file size limits
   - Verify MIME type validation
   - Check disk space

2. **Memory Issues**
   - Monitor PDF processing memory usage
   - Implement file size limits
   - Add memory monitoring

3. **Performance Issues**
   - Enable query logging
   - Monitor request timing
   - Check resource utilization

### Log Analysis

```bash
# View recent errors
docker-compose logs --tail=100 backend | grep ERROR

# Monitor request performance
docker-compose logs backend | grep "Request completed" | tail -20

# Check memory usage
docker stats pdfviewer_backend_1
```

This deployment guide provides comprehensive instructions for deploying the PDF Viewer application in various environments. Choose the deployment method that best fits your infrastructure and requirements.