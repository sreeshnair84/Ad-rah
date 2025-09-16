# Adara Digital Signage Platform - Enterprise Deployment Guide

## Executive Summary

This comprehensive guide provides step-by-step instructions for deploying the Adara Digital Signage Platform in enterprise environments, including on-premises, cloud, and hybrid deployments with high availability, security, and scalability considerations.

**Deployment Guide Version**: 2.0
**Last Updated**: September 16, 2025
**Target Audience**: DevOps Engineers, System Administrators, Enterprise IT Teams
**Deployment Scope**: Production-ready enterprise deployments supporting 10,000+ devices

---

## 🎯 **Deployment Architectures**

### **Supported Deployment Models**

```yaml
Deployment Options:
  cloud_native:
    provider: Azure (Primary), AWS (Secondary)
    scalability: Auto-scaling to 10,000+ devices
    availability: 99.9% SLA
    management: Fully managed services

  hybrid_cloud:
    data_location: On-premises sensitive data
    compute: Cloud-based processing
    compliance: Industry-specific requirements
    connectivity: VPN/ExpressRoute

  on_premises:
    infrastructure: Customer data center
    control: Full infrastructure control
    compliance: Air-gapped environments
    maintenance: Customer managed

  edge_distributed:
    architecture: Edge computing nodes
    latency: <10ms response times
    offline: Full offline capability
    synchronization: Eventual consistency
```

### **Reference Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Internet / External Users                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                  Load Balancer / CDN                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Azure CDN     │  │ Application     │  │   WAF/DDoS      │ │
│  │   (Global)      │  │   Gateway       │  │  Protection     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 Container Orchestration                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  API Gateway    │  │   Web Frontend  │  │   Flutter App   │ │
│  │  (FastAPI)      │  │   (Next.js)     │  │   (Mobile)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   Data & Storage Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │    MongoDB      │  │   Redis Cache   │  │  Azure Blob     │ │
│  │   (Replica Set) │  │   (Cluster)     │  │   Storage       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## ☁️ **Cloud-Native Deployment (Azure)**

### **Azure Services Architecture**

```yaml
Azure Services Stack:
  compute:
    - Azure Kubernetes Service (AKS)
    - Azure Container Instances (ACI)
    - Azure Functions (serverless)

  storage:
    - Azure Blob Storage (content files)
    - Azure Files (shared storage)
    - Azure Disk (persistent volumes)

  database:
    - Azure Cosmos DB (MongoDB API)
    - Azure Cache for Redis
    - Azure SQL Database (analytics)

  networking:
    - Azure Application Gateway
    - Azure Load Balancer
    - Azure CDN
    - Azure Virtual Network

  security:
    - Azure Key Vault
    - Azure Active Directory
    - Azure Security Center
    - Azure Firewall

  monitoring:
    - Azure Monitor
    - Application Insights
    - Log Analytics
    - Azure Sentinel
```

### **Azure Resource Group Setup**

#### **1. Infrastructure Provisioning**

```bash
#!/bin/bash
# azure-setup.sh - Azure infrastructure deployment script

# Variables
RESOURCE_GROUP="adara-production-rg"
LOCATION="westeurope"
AKS_CLUSTER="adara-aks-cluster"
ACR_NAME="adaracontainerregistry"
STORAGE_ACCOUNT="adarastorageprod"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Azure Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Premium \
  --admin-enabled true

# Create AKS cluster with auto-scaling
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER \
  --node-count 3 \
  --min-count 3 \
  --max-count 20 \
  --enable-cluster-autoscaler \
  --node-vm-size Standard_D4s_v3 \
  --enable-addons monitoring,azure-keyvault-secrets-provider \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --encryption-services blob

# Create Cosmos DB with MongoDB API
az cosmosdb create \
  --resource-group $RESOURCE_GROUP \
  --name adara-cosmosdb \
  --kind MongoDB \
  --server-version 4.2 \
  --default-consistency-level Session \
  --enable-automatic-failover true \
  --locations regionName=$LOCATION failoverPriority=0 isZoneRedundant=false

# Create Azure Cache for Redis
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name adara-redis-cache \
  --location $LOCATION \
  --sku Premium \
  --vm-size P3 \
  --enable-non-ssl-port false \
  --redis-configuration maxmemory-policy=allkeys-lru

# Create Key Vault
az keyvault create \
  --resource-group $RESOURCE_GROUP \
  --name adara-keyvault \
  --location $LOCATION \
  --sku premium \
  --enable-rbac-authorization true

echo "Azure infrastructure provisioning completed!"
```

#### **2. Kubernetes Configuration**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: adara-production
  labels:
    name: adara-production
    environment: production
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: adara-config
  namespace: adara-production
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  MONGO_DATABASE: "adara_digital_signage"
  REDIS_DATABASE: "0"
  API_VERSION: "v2"
  MAX_UPLOAD_SIZE: "100MB"
  SESSION_TIMEOUT: "3600"
---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: adara-secrets
  namespace: adara-production
type: Opaque
data:
  # Base64 encoded values - replace with actual secrets
  MONGO_URI: <base64-encoded-mongo-connection-string>
  REDIS_URL: <base64-encoded-redis-connection-string>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  AZURE_STORAGE_CONNECTION_STRING: <base64-encoded-storage-connection>
```

#### **3. Application Deployment**

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adara-backend
  namespace: adara-production
  labels:
    app: adara-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: adara-backend
  template:
    metadata:
      labels:
        app: adara-backend
    spec:
      containers:
      - name: adara-backend
        image: adaracontainerregistry.azurecr.io/adara-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: adara-config
              key: ENVIRONMENT
        - name: MONGO_URI
          valueFrom:
            secretKeyRef:
              name: adara-secrets
              key: MONGO_URI
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: adara-secrets
              key: REDIS_URL
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
---
apiVersion: v1
kind: Service
metadata:
  name: adara-backend-service
  namespace: adara-production
spec:
  selector:
    app: adara-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adara-frontend
  namespace: adara-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: adara-frontend
  template:
    metadata:
      labels:
        app: adara-frontend
    spec:
      containers:
      - name: adara-frontend
        image: adaracontainerregistry.azurecr.io/adara-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "https://api.adara.com"
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: adara-frontend-service
  namespace: adara-production
spec:
  selector:
    app: adara-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP
```

#### **4. Auto-scaling Configuration**

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: adara-backend-hpa
  namespace: adara-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: adara-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: adara-frontend-hpa
  namespace: adara-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: adara-frontend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🏢 **On-Premises Deployment**

### **Infrastructure Requirements**

#### **Minimum Hardware Specifications**

```yaml
Production Environment (10,000 devices):
  application_servers:
    count: 3
    cpu: 16 cores (Intel Xeon or AMD EPYC)
    memory: 64GB RAM
    storage: 1TB NVMe SSD
    network: 10Gbps NIC

  database_servers:
    count: 3 (replica set)
    cpu: 24 cores
    memory: 128GB RAM
    storage: 2TB NVMe SSD (primary) + 4TB SAS (backup)
    network: 10Gbps NIC

  cache_servers:
    count: 3 (Redis cluster)
    cpu: 8 cores
    memory: 32GB RAM
    storage: 500GB SSD
    network: 10Gbps NIC

  load_balancer:
    count: 2 (HA pair)
    cpu: 8 cores
    memory: 16GB RAM
    storage: 500GB SSD
    network: 10Gbps NIC

  storage_servers:
    count: 2 (NAS/SAN)
    storage: 50TB (RAID 10)
    network: 10Gbps NIC
    backup: Additional 100TB capacity

Total Infrastructure Cost: $150,000 - $200,000
```

#### **Network Architecture**

```yaml
Network Design:
  dmz_network:
    subnet: 10.0.1.0/24
    components:
      - Load balancers
      - Web application firewall
      - Reverse proxy

  application_network:
    subnet: 10.0.2.0/24
    components:
      - Application servers
      - Container orchestration
      - API gateways

  database_network:
    subnet: 10.0.3.0/24
    components:
      - Database servers
      - Cache servers
      - Backup systems

  management_network:
    subnet: 10.0.4.0/24
    components:
      - Monitoring systems
      - Log aggregation
      - Administration tools

  storage_network:
    subnet: 10.0.5.0/24
    components:
      - File storage
      - Backup storage
      - Content delivery
```

### **Docker Compose Deployment**

#### **Production Docker Compose Setup**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:1.24-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - backend-1
      - backend-2
      - backend-3
      - frontend
    restart: unless-stopped
    networks:
      - adara-network

  # Backend Services (3 replicas for HA)
  backend-1:
    image: adara/backend:latest
    environment:
      - ENVIRONMENT=production
      - MONGO_URI=mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/adara_digital_signage?replicaSet=rs0
      - REDIS_URL=redis://redis-cluster:6379
      - INSTANCE_ID=backend-1
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      - mongo-1
      - redis-cluster
    restart: unless-stopped
    networks:
      - adara-network

  backend-2:
    image: adara/backend:latest
    environment:
      - ENVIRONMENT=production
      - MONGO_URI=mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/adara_digital_signage?replicaSet=rs0
      - REDIS_URL=redis://redis-cluster:6379
      - INSTANCE_ID=backend-2
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      - mongo-1
      - redis-cluster
    restart: unless-stopped
    networks:
      - adara-network

  backend-3:
    image: adara/backend:latest
    environment:
      - ENVIRONMENT=production
      - MONGO_URI=mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/adara_digital_signage?replicaSet=rs0
      - REDIS_URL=redis://redis-cluster:6379
      - INSTANCE_ID=backend-3
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      - mongo-1
      - redis-cluster
    restart: unless-stopped
    networks:
      - adara-network

  # Frontend Service
  frontend:
    image: adara/frontend:latest
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://your-domain.com/api
    restart: unless-stopped
    networks:
      - adara-network

  # MongoDB Replica Set
  mongo-1:
    image: mongo:7.0
    command: mongod --replSet rs0 --bind_ip_all
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
    volumes:
      - mongo1_data:/data/db
      - ./mongodb/mongod.conf:/etc/mongod.conf
    ports:
      - "27017:27017"
    restart: unless-stopped
    networks:
      - adara-network

  mongo-2:
    image: mongo:7.0
    command: mongod --replSet rs0 --bind_ip_all
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
    volumes:
      - mongo2_data:/data/db
      - ./mongodb/mongod.conf:/etc/mongod.conf
    ports:
      - "27018:27017"
    restart: unless-stopped
    networks:
      - adara-network

  mongo-3:
    image: mongo:7.0
    command: mongod --replSet rs0 --bind_ip_all
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
    volumes:
      - mongo3_data:/data/db
      - ./mongodb/mongod.conf:/etc/mongod.conf
    ports:
      - "27019:27017"
    restart: unless-stopped
    networks:
      - adara-network

  # Redis Cluster
  redis-cluster:
    image: redis:7-alpine
    command: redis-server /etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/etc/redis/redis.conf
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - adara-network

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - adara-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped
    networks:
      - adara-network

volumes:
  mongo1_data:
  mongo2_data:
  mongo3_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  adara-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### **Nginx Load Balancer Configuration**

```nginx
# nginx/nginx.conf
upstream adara_backend {
    least_conn;
    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;
}

upstream adara_frontend {
    server frontend:3000;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # API Routes
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://adara_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Authentication Routes (stricter rate limiting)
    location /api/auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://adara_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend Routes
    location / {
        proxy_pass http://adara_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health Check Endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # File Upload Size
    client_max_body_size 100M;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

---

## 🔧 **Configuration Management**

### **Environment Configuration**

#### **Production Environment Variables**

```bash
# .env.production
# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_VERSION=v2

# Database Configuration
MONGO_URI=mongodb://admin:${MONGO_PASSWORD}@mongo-1:27017,mongo-2:27017,mongo-3:27017/adara_digital_signage?replicaSet=rs0&authSource=admin
MONGO_DATABASE=adara_digital_signage
MONGO_MAX_POOL_SIZE=50
MONGO_MIN_POOL_SIZE=10

# Cache Configuration
REDIS_URL=redis://:${REDIS_PASSWORD}@redis-cluster:6379/0
REDIS_MAX_CONNECTIONS=100
REDIS_TIMEOUT=5

# Security Configuration
JWT_SECRET_KEY=${JWT_SECRET}
JWT_REFRESH_SECRET_KEY=${JWT_REFRESH_SECRET}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Azure Services (if using cloud storage)
AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION}
AZURE_CONTAINER_NAME=adara-content
AZURE_KEY_VAULT_URL=${AZURE_KEY_VAULT_URL}

# AI Services Configuration
GEMINI_API_KEY=${GEMINI_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Performance Configuration
MAX_UPLOAD_SIZE=100MB
SESSION_TIMEOUT=3600
RATE_LIMIT_REQUESTS_PER_MINUTE=100
CACHE_TTL_SECONDS=300

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# CORS Configuration
ALLOWED_ORIGINS=https://your-domain.com,https://admin.your-domain.com
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=*

# Email Configuration (for notifications)
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=587
SMTP_USERNAME=${SMTP_USERNAME}
SMTP_PASSWORD=${SMTP_PASSWORD}
SMTP_TLS=true
```

#### **Secrets Management**

```bash
#!/bin/bash
# scripts/setup-secrets.sh
# Script to set up production secrets

# Generate random secrets
JWT_SECRET=$(openssl rand -hex 32)
JWT_REFRESH_SECRET=$(openssl rand -hex 32)
MONGO_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Create secrets file
cat > .env.secrets << EOF
# Generated secrets - DO NOT COMMIT TO VERSION CONTROL
JWT_SECRET=${JWT_SECRET}
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}
MONGO_PASSWORD=${MONGO_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# API Keys - Replace with actual values
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Azure Configuration (if using)
AZURE_STORAGE_CONNECTION=your_azure_storage_connection_string
AZURE_KEY_VAULT_URL=your_azure_key_vault_url

# Email Configuration
SMTP_HOST=your_smtp_host
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
EOF

# Set secure permissions
chmod 600 .env.secrets

echo "Secrets generated in .env.secrets"
echo "Please update the placeholder values with actual API keys and configuration"
```

### **SSL/TLS Certificate Setup**

#### **Certificate Generation (Let's Encrypt)**

```bash
#!/bin/bash
# scripts/setup-ssl.sh
# SSL certificate setup with Let's Encrypt

DOMAIN="your-domain.com"
EMAIL="admin@your-domain.com"

# Install certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Create nginx directory
mkdir -p nginx/ssl

# Generate certificate
sudo certbot certonly \
  --standalone \
  --email $EMAIL \
  --agree-tos \
  --non-interactive \
  --domains $DOMAIN

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/certificate.crt
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/private.key

# Set appropriate permissions
sudo chown $(whoami):$(whoami) nginx/ssl/*
chmod 644 nginx/ssl/certificate.crt
chmod 600 nginx/ssl/private.key

# Setup auto-renewal
sudo crontab -e
# Add this line:
# 0 12 * * * /usr/bin/certbot renew --quiet

echo "SSL certificates installed for $DOMAIN"
echo "Certificates will auto-renew via cron job"
```

---

## 📊 **Monitoring & Observability**

### **Comprehensive Monitoring Setup**

#### **Prometheus Configuration**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  # Application metrics
  - job_name: 'adara-backend'
    static_configs:
      - targets: ['backend-1:9090', 'backend-2:9090', 'backend-3:9090']
    metrics_path: /metrics
    scrape_interval: 10s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # Database metrics
  - job_name: 'mongodb-exporter'
    static_configs:
      - targets: ['mongodb-exporter:9216']

  # Redis metrics
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Nginx metrics
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

#### **Alert Rules Configuration**

```yaml
# monitoring/alert_rules.yml
groups:
  - name: adara_alerts
    rules:
      # High API response time
      - alert: HighAPIResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High API response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"

      # Database connection issues
      - alert: MongoDBDown
        expr: up{job="mongodb-exporter"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MongoDB is down"
          description: "MongoDB has been down for more than 1 minute"

      # Redis connection issues
      - alert: RedisDown
        expr: up{job="redis-exporter"} == 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Redis is down"
          description: "Redis has been down for more than 1 minute"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"

      # High CPU usage
      - alert: HighCPUUsage
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80%"

      # Low disk space
      - alert: LowDiskSpace
        expr: node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"} < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk space is below 10%"
```

#### **Grafana Dashboard Configuration**

```json
{
  "dashboard": {
    "title": "Adara Digital Signage Platform",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors/sec"
          },
          {
            "expr": "rate(http_requests_total{status=~\"4..\"}[5m])",
            "legendFormat": "4xx errors/sec"
          }
        ]
      },
      {
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "mongodb_connections{state=\"current\"}",
            "legendFormat": "Active Connections"
          },
          {
            "expr": "rate(mongodb_op_counters_total[5m])",
            "legendFormat": "Operations/sec"
          }
        ]
      }
    ]
  }
}
```

---

## 🛡️ **Security Configuration**

### **Production Security Checklist**

#### **Network Security**

```yaml
Firewall Rules:
  inbound:
    - port: 80 (HTTP - redirect to HTTPS)
    - port: 443 (HTTPS)
    - port: 22 (SSH - restricted IPs only)
    - port: 3000 (Grafana - internal only)
    - port: 9090 (Prometheus - internal only)

  outbound:
    - port: 80, 443 (external APIs)
    - port: 25, 587 (email)
    - port: 53 (DNS)

  internal:
    - port: 8000 (API internal)
    - port: 27017-27019 (MongoDB cluster)
    - port: 6379 (Redis)

Security Groups:
  web_tier:
    - Allow: 80, 443 from 0.0.0.0/0
    - Allow: 22 from management IPs

  app_tier:
    - Allow: 8000 from web_tier
    - Allow: 22 from management IPs

  data_tier:
    - Allow: 27017-27019 from app_tier
    - Allow: 6379 from app_tier
    - Deny: all from external
```

#### **Application Security**

```python
# app/security/production_config.py
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets

class ProductionSecurityConfig:
    """Production security configuration"""

    # Password hashing
    password_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12  # Higher rounds for production
    )

    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "strict"

    # CSRF protection
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

    # Content Security Policy
    CSP_DIRECTIVES = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "frame-ancestors": ["'none'"],
    }

    # Rate limiting
    RATE_LIMITS = {
        "auth": "5 per minute",
        "api": "100 per minute",
        "upload": "10 per minute",
        "download": "50 per minute"
    }

    # Input validation
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_EXTENSIONS = {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "video": [".mp4", ".webm", ".mov"],
        "document": [".pdf", ".doc", ".docx"]
    }

    @staticmethod
    def generate_secure_key() -> str:
        """Generate cryptographically secure key"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        return ProductionSecurityConfig.password_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return ProductionSecurityConfig.password_context.verify(password, hashed)
```

#### **Database Security**

```yaml
# MongoDB Security Configuration
mongodb_security:
  authentication:
    enabled: true
    mechanism: SCRAM-SHA-256
    admin_user: admin
    app_user: adara_app
    readonly_user: adara_readonly

  authorization:
    enabled: true
    roles:
      - role: readWriteAnyDatabase
        db: admin
        user: adara_app
      - role: read
        db: adara_digital_signage
        user: adara_readonly

  encryption:
    at_rest: true
    in_transit: true
    key_management: external

  network:
    bind_ip: 0.0.0.0  # Restricted by firewall
    ssl_mode: requireSSL
    ssl_certificate: /etc/ssl/mongodb.pem

  auditing:
    enabled: true
    destination: file
    path: /var/log/mongodb/audit.log
    format: JSON
```

---

## 🚀 **Deployment Procedures**

### **Zero-Downtime Deployment Strategy**

#### **Blue-Green Deployment**

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh
# Zero-downtime deployment script

set -e

# Configuration
BLUE_ENV="adara-blue"
GREEN_ENV="adara-green"
CURRENT_ENV=$(kubectl get service adara-production -o jsonpath='{.spec.selector.version}')
NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new-version>"
    exit 1
fi

echo "Current environment: $CURRENT_ENV"

# Determine target environment
if [ "$CURRENT_ENV" = "blue" ]; then
    TARGET_ENV="green"
    TARGET_NAMESPACE="adara-green"
else
    TARGET_ENV="blue"
    TARGET_NAMESPACE="adara-blue"
fi

echo "Deploying version $NEW_VERSION to $TARGET_ENV environment"

# Step 1: Deploy to target environment
echo "1. Deploying application to $TARGET_ENV..."
kubectl apply -f k8s/namespaces/$TARGET_NAMESPACE.yaml
kubectl set image deployment/adara-backend adara-backend=adara/backend:$NEW_VERSION -n $TARGET_NAMESPACE
kubectl set image deployment/adara-frontend adara-frontend=adara/frontend:$NEW_VERSION -n $TARGET_NAMESPACE

# Step 2: Wait for deployment to be ready
echo "2. Waiting for deployment to be ready..."
kubectl rollout status deployment/adara-backend -n $TARGET_NAMESPACE --timeout=300s
kubectl rollout status deployment/adara-frontend -n $TARGET_NAMESPACE --timeout=300s

# Step 3: Run health checks
echo "3. Running health checks..."
TARGET_URL="http://adara-backend.$TARGET_NAMESPACE:8000/api/health"
for i in {1..30}; do
    if kubectl exec -n $TARGET_NAMESPACE deployment/adara-backend -- curl -f $TARGET_URL; then
        echo "Health check passed!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Health check failed after 30 attempts"
        exit 1
    fi
    sleep 5
done

# Step 4: Run smoke tests
echo "4. Running smoke tests..."
./scripts/smoke-tests.sh $TARGET_NAMESPACE

# Step 5: Switch traffic
echo "5. Switching traffic to $TARGET_ENV..."
kubectl patch service adara-production -p '{"spec":{"selector":{"version":"'$TARGET_ENV'"}}}'

# Step 6: Monitor for issues
echo "6. Monitoring for 60 seconds..."
sleep 60

# Step 7: Run post-deployment verification
echo "7. Running post-deployment verification..."
./scripts/post-deployment-tests.sh

echo "Deployment completed successfully!"
echo "New version $NEW_VERSION is now live on $TARGET_ENV"

# Optional: Clean up old environment after successful deployment
read -p "Clean up old environment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    OLD_NAMESPACE="adara-$CURRENT_ENV"
    kubectl delete namespace $OLD_NAMESPACE
    echo "Old environment cleaned up"
fi
```

#### **Database Migration Strategy**

```python
# scripts/database_migration.py
"""
Database migration script for production deployments
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, mongo_uri: str):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client.adara_digital_signage

    async def run_migrations(self):
        """Run all pending migrations"""
        try:
            # Get current migration version
            current_version = await self.get_migration_version()
            logger.info(f"Current migration version: {current_version}")

            # Run migrations
            migrations = [
                self.migration_001_add_indexes,
                self.migration_002_update_schema,
                self.migration_003_cleanup_data,
            ]

            for i, migration in enumerate(migrations, 1):
                if i > current_version:
                    logger.info(f"Running migration {i:03d}...")
                    await migration()
                    await self.update_migration_version(i)
                    logger.info(f"Migration {i:03d} completed")

            logger.info("All migrations completed successfully")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

    async def get_migration_version(self) -> int:
        """Get current migration version"""
        try:
            doc = await self.db.migrations.find_one({"_id": "version"})
            return doc["version"] if doc else 0
        except:
            return 0

    async def update_migration_version(self, version: int):
        """Update migration version"""
        await self.db.migrations.update_one(
            {"_id": "version"},
            {"$set": {"version": version, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    async def migration_001_add_indexes(self):
        """Migration 001: Add performance indexes"""
        # User indexes
        await self.db.users.create_index("email", unique=True)
        await self.db.users.create_index([("company_id", 1), ("is_active", 1)])

        # Content indexes
        await self.db.content.create_index([("company_id", 1), ("status", 1)])
        await self.db.content.create_index("uploaded_at")

        # Device indexes
        await self.db.devices.create_index([("company_id", 1), ("status", 1)])
        await self.db.devices.create_index("last_seen")

    async def migration_002_update_schema(self):
        """Migration 002: Update document schemas"""
        # Add new fields to existing documents
        await self.db.users.update_many(
            {"created_at": {"$exists": False}},
            {"$set": {"created_at": datetime.utcnow()}}
        )

        await self.db.content.update_many(
            {"view_count": {"$exists": False}},
            {"$set": {"view_count": 0}}
        )

    async def migration_003_cleanup_data(self):
        """Migration 003: Clean up old data"""
        # Remove old test data
        await self.db.content.delete_many({"filename": {"$regex": "^test_"}})

        # Clean up expired sessions
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        await self.db.sessions.delete_many({"created_at": {"$lt": cutoff_date}})

async def main():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable required")

    migration = DatabaseMigration(mongo_uri)
    await migration.run_migrations()

if __name__ == "__main__":
    asyncio.run(main())
```

#### **Rollback Procedures**

```bash
#!/bin/bash
# scripts/rollback.sh
# Emergency rollback script

set -e

PREVIOUS_VERSION=$1
REASON=$2

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Usage: $0 <previous-version> [reason]"
    exit 1
fi

echo "EMERGENCY ROLLBACK INITIATED"
echo "Rolling back to version: $PREVIOUS_VERSION"
echo "Reason: ${REASON:-'Not specified'}"

# Log rollback
echo "$(date): Rollback to $PREVIOUS_VERSION - $REASON" >> /var/log/adara/rollbacks.log

# Step 1: Scale down current deployment
echo "1. Scaling down current deployment..."
kubectl scale deployment adara-backend --replicas=0 -n adara-production
kubectl scale deployment adara-frontend --replicas=0 -n adara-production

# Step 2: Deploy previous version
echo "2. Deploying previous version $PREVIOUS_VERSION..."
kubectl set image deployment/adara-backend adara-backend=adara/backend:$PREVIOUS_VERSION -n adara-production
kubectl set image deployment/adara-frontend adara-frontend=adara/frontend:$PREVIOUS_VERSION -n adara-production

# Step 3: Scale up
echo "3. Scaling up previous version..."
kubectl scale deployment adara-backend --replicas=3 -n adara-production
kubectl scale deployment adara-frontend --replicas=2 -n adara-production

# Step 4: Wait for rollout
echo "4. Waiting for rollout to complete..."
kubectl rollout status deployment/adara-backend -n adara-production --timeout=300s
kubectl rollout status deployment/adara-frontend -n adara-production --timeout=300s

# Step 5: Health check
echo "5. Running health checks..."
for i in {1..10}; do
    if kubectl exec -n adara-production deployment/adara-backend -- curl -f http://localhost:8000/api/health; then
        echo "Health check passed!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "Health check failed - manual intervention required"
        exit 1
    fi
    sleep 10
done

# Step 6: Send notifications
echo "6. Sending notifications..."
./scripts/send-alert.sh "ROLLBACK COMPLETED" "Successfully rolled back to version $PREVIOUS_VERSION"

echo "ROLLBACK COMPLETED SUCCESSFULLY"
echo "Version $PREVIOUS_VERSION is now active"
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment Checklist**

```yaml
Infrastructure Preparation:
  - [ ] Hardware/cloud resources provisioned
  - [ ] Network configuration completed
  - [ ] SSL certificates installed
  - [ ] DNS records configured
  - [ ] Firewall rules applied
  - [ ] Load balancer configured

Security Setup:
  - [ ] Secrets generated and secured
  - [ ] Database authentication configured
  - [ ] API keys configured
  - [ ] HTTPS enforced
  - [ ] Security headers configured
  - [ ] Rate limiting enabled

Database Preparation:
  - [ ] MongoDB replica set configured
  - [ ] Database indexes created
  - [ ] Backup strategy implemented
  - [ ] Migration scripts tested
  - [ ] Performance tuning applied

Application Configuration:
  - [ ] Environment variables set
  - [ ] Configuration files validated
  - [ ] Docker images built and tested
  - [ ] Dependencies verified
  - [ ] Log levels configured

Monitoring Setup:
  - [ ] Prometheus configured
  - [ ] Grafana dashboards imported
  - [ ] Alert rules configured
  - [ ] Log aggregation setup
  - [ ] Health checks enabled
```

### **Post-Deployment Verification**

```yaml
Functional Testing:
  - [ ] User authentication working
  - [ ] Content upload functioning
  - [ ] Device registration working
  - [ ] API endpoints responding
  - [ ] Database connectivity verified

Performance Testing:
  - [ ] Response times within SLA
  - [ ] Load testing passed
  - [ ] Memory usage normal
  - [ ] CPU utilization optimal
  - [ ] Database performance verified

Security Verification:
  - [ ] HTTPS enforced
  - [ ] Authentication required
  - [ ] Authorization working
  - [ ] Rate limiting active
  - [ ] Input validation working

Monitoring Verification:
  - [ ] Metrics collection working
  - [ ] Alerts configured
  - [ ] Logs being generated
  - [ ] Health checks passing
  - [ ] Dashboards accessible

Business Verification:
  - [ ] User workflows functional
  - [ ] Content delivery working
  - [ ] Device communication active
  - [ ] Analytics data flowing
  - [ ] Admin functions working
```

---

## 🎯 **Conclusion**

### **Deployment Success Criteria**

```yaml
Technical Success Metrics:
  - API response time: <200ms (95th percentile)
  - System uptime: >99.9%
  - Error rate: <0.1%
  - Database performance: <50ms query time
  - Security scan: Zero critical vulnerabilities

Business Success Metrics:
  - User login success rate: >99%
  - Content upload success rate: >98%
  - Device connectivity: >99%
  - Customer satisfaction: >90%
  - Support ticket volume: <baseline

Operational Success Metrics:
  - Deployment time: <30 minutes
  - Rollback time: <5 minutes
  - Mean time to recovery: <15 minutes
  - Monitoring coverage: 100%
  - Documentation completeness: 100%
```

### **Support & Maintenance**

```yaml
Ongoing Support:
  - 24/7 monitoring and alerting
  - Weekly security updates
  - Monthly performance optimization
  - Quarterly disaster recovery testing
  - Annual security audits

Maintenance Windows:
  - Weekly: Sundays 2-4 AM UTC (low traffic)
  - Monthly: First Sunday 1-5 AM UTC (major updates)
  - Emergency: As needed with notifications

Escalation Procedures:
  - Level 1: Automated alerts and basic triage
  - Level 2: DevOps team response (15 minutes)
  - Level 3: Senior engineering team (30 minutes)
  - Level 4: Emergency response team (1 hour)

Documentation Updates:
  - Deployment procedures updated after each release
  - Runbooks updated monthly
  - Architecture documentation quarterly
  - Security procedures annually
```

---

**Document Prepared By**: DevOps & Infrastructure Team
**Deployment Testing**: Completed on staging environment
**Production Readiness**: Approved for enterprise deployment
**Next Review**: Monthly deployment process optimization

*This deployment guide is maintained as a living document and updated with each production deployment to reflect current best practices and lessons learned.*