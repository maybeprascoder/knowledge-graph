# Knowledge Graph Deployment Guide

A comprehensive guide for deploying the Knowledge Graph system across different environments, from local development to production.

## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- 8GB+ RAM recommended
- CSV files: `reports.csv`, `entries.csv`, `approvals.csv`, `payments.csv`

### 1. Clone and Setup
```bash
git clone <repository-url>
cd knowledge_graph

# Copy your CSV files to the project root
cp /path/to/your/*.csv ./
```

### 2. Start the Stack
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Load Data
```bash
# Wait for services to be healthy, then load data
docker-compose exec api python ingest_concur.py

# Verify data loading
docker-compose exec neo4j cypher-shell -u neo4j -p kgdemo123 "MATCH (n) RETURN count(n) as total_nodes"
```

### 4. Access Services
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/kgdemo123)
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Configuration

### Services Overview

#### Neo4j Database
```yaml
neo4j:
  image: neo4j:5.15-community
  ports:
    - "7474:7474"  # HTTP
    - "7687:7687"  # Bolt
  environment:
    - NEO4J_AUTH=neo4j/kgdemo123
    - NEO4J_PLUGINS=["apoc"]
  volumes:
    - neo4j_data:/data
    - neo4j_logs:/logs
```

#### API Service
```yaml
api:
  build: .
  ports:
    - "8000:8000"
  environment:
    - NEO4J_URI=bolt://neo4j:7687
    - NEO4J_USERNAME=neo4j
    - NEO4J_PASSWORD=kgdemo123
    - OLLAMA_MODEL=llama3.2
    - OLLAMA_BASE_URL=http://host.docker.internal:11434
  depends_on:
    neo4j:
      condition: service_healthy
```

### Custom Configuration

#### Environment Variables
Create a `.env` file to override defaults:

```env
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

# Ollama Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Data Processing
CONCUR_CSV_DIR=/app/data
BATCH_SIZE=1000
EMB_MAX_FACTS=500
```

#### Custom Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for CSV data
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🖥️ Manual Setup (Local Development)

### Prerequisites
- Python 3.11+
- Neo4j Database (5.15+)
- Ollama (for AI features)
- 8GB+ RAM recommended

### 1. Install Neo4j

#### Option A: Docker (Recommended)
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS=["apoc"] \
  -v neo4j_data:/data \
  neo4j:5.15-community
```

#### Option B: Neo4j Desktop
1. Download Neo4j Desktop from https://neo4j.com/download/
2. Create a new project and database
3. Set password and start the database
4. Note the connection details

### 2. Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for development
pip install jupyter notebook ipykernel
```

### 3. Install Ollama (Optional)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required models (in another terminal)
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 4. Configure Environment
Create a `.env` file:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Ollama Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Data Configuration
CONCUR_CSV_DIR=/path/to/csv/files
BATCH_SIZE=1000
EMB_MAX_FACTS=500
```

### 5. Load Data
```bash
# Set CSV directory
export CONCUR_CSV_DIR="/path/to/your/csv/files"

# Load data into Neo4j
python ingest_concur.py

# Verify data loading
python -c "
from database import db
result = db.execute_query('MATCH (n) RETURN count(n) as total_nodes')
print(f'Total nodes: {result[0][\"total_nodes\"]}')
"
```

### 6. Start Services

#### API Server
```bash
# Development mode with auto-reload
uvicorn main_api:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn main_api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Streamlit UI (Optional)
```bash
# Start Streamlit demo
streamlit run app.py

# Start employee Q&A interface
streamlit run employee_qna.py
```

## ☁️ Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance Setup
```bash
# Launch EC2 instance (t3.large or larger)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Security Groups
Configure security groups to allow:
- Port 22 (SSH)
- Port 8000 (API)
- Port 7474 (Neo4j Browser)

#### 3. Deploy Application
```bash
# Clone repository
git clone <repository-url>
cd knowledge_graph

# Copy CSV files
scp -i your-key.pem /path/to/*.csv ec2-user@your-instance:/home/ec2-user/knowledge_graph/

# Start services
docker-compose up -d
```

### Google Cloud Platform

#### 1. Compute Engine Setup
```bash
# Create VM instance
gcloud compute instances create kg-server \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud

# Install Docker
gcloud compute ssh kg-server --command="
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
"
```

#### 2. Deploy with Cloud Run (Containerized)
```bash
# Build and push to Container Registry
docker build -t gcr.io/your-project/kg-api .
docker push gcr.io/your-project/kg-api

# Deploy to Cloud Run
gcloud run deploy kg-api \
  --image gcr.io/your-project/kg-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Deployment

#### 1. Container Instances
```bash
# Create resource group
az group create --name kg-rg --location eastus

# Deploy with Azure Container Instances
az container create \
  --resource-group kg-rg \
  --name kg-api \
  --image your-registry/kg-api:latest \
  --ports 8000 \
  --environment-variables \
    NEO4J_URI=bolt://your-neo4j:7687 \
    NEO4J_USERNAME=neo4j \
    NEO4J_PASSWORD=your-password
```

## 🔧 Production Configuration

### Security Hardening

#### 1. Environment Variables
```bash
# Use strong passwords
NEO4J_PASSWORD=$(openssl rand -base64 32)

# Use environment-specific URLs
NEO4J_URI=bolt://your-neo4j-cluster:7687
OLLAMA_BASE_URL=https://your-ollama-instance:11434
```

#### 2. SSL/TLS Configuration
```nginx
# Nginx reverse proxy configuration
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. Authentication (Optional)
```python
# Add to main_api.py
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

# Implement JWT authentication
jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=3600,
    tokenUrl="auth/jwt/login",
)
```

### Performance Optimization

#### 1. Database Optimization
```cypher
// Create indexes for better performance
CREATE INDEX employee_id_index FOR (e:Employee) ON (e.id);
CREATE INDEX report_id_index FOR (r:Report) ON (r.id);
CREATE INDEX expense_id_index FOR (x:Expense) ON (x.id);
CREATE INDEX vendor_name_index FOR (v:Vendor) ON (v.name);

// Create composite indexes for common queries
CREATE INDEX report_employee_date FOR (r:Report) ON (r.owner_id, r.submit_date);
```

#### 2. API Optimization
```python
# Add caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Configure Redis caching
FastAPICache.init(RedisBackend(), prefix="kg-cache")

# Add response caching
@cache(expire=300)  # 5 minutes
@app.get("/employee/{employee_id}/expenses")
async def get_employee_expenses(employee_id: str):
    # Implementation
    pass
```

#### 3. Load Balancing
```yaml
# docker-compose.yml with load balancer
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api1
      - api2
  
  api1:
    build: .
    environment:
      - NEO4J_URI=bolt://neo4j:7687
  
  api2:
    build: .
    environment:
      - NEO4J_URI=bolt://neo4j:7687
```

### Monitoring and Logging

#### 1. Health Checks
```python
# Enhanced health check
@app.get("/health")
async def health_check():
    checks = {
        "api": "healthy",
        "neo4j": check_neo4j_connection(),
        "ollama": check_ollama_connection(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage()
    }
    return checks
```

#### 2. Logging Configuration
```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

# Configure structured logging
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

#### 3. Metrics Collection
```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(process_time)
    
    return response
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Neo4j Connection Issues
```bash
# Check Neo4j status
docker-compose logs neo4j

# Test connection
docker-compose exec neo4j cypher-shell -u neo4j -p kgdemo123 "RETURN 1"

# Check Neo4j logs
docker-compose exec neo4j tail -f /var/log/neo4j/neo4j.log
```

#### 2. API Service Issues
```bash
# Check API logs
docker-compose logs api

# Test health endpoint
curl http://localhost:8000/health

# Check API container status
docker-compose exec api ps aux
```

#### 3. Data Loading Issues
```bash
# Check CSV file accessibility
docker-compose exec api ls -la /app/data/

# Verify CSV format
docker-compose exec api head -5 /app/data/reports.csv

# Re-run ingestion with verbose output
docker-compose exec api python ingest_concur.py --verbose
```

#### 4. Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

#### 5. Ollama Connection Issues
```bash
# Check Ollama status
ollama list

# Test Ollama connection
curl http://localhost:11434/api/tags

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Performance Issues

#### 1. Slow Query Performance
```cypher
// Analyze query performance
EXPLAIN MATCH (e:Employee)-[:SUBMITTED]->(r:Report) RETURN e.name, count(r);

// Create missing indexes
CREATE INDEX FOR (e:Employee) ON (e.id);
CREATE INDEX FOR (r:Report) ON (r.owner_id);
```

#### 2. High Memory Usage
```bash
# Monitor memory usage
docker stats --no-stream

# Optimize batch sizes
export BATCH_SIZE=500  # Reduce from 1000

# Use streaming for large files
python ingest_concur.py --streaming
```

#### 3. API Timeout Issues
```python
# Increase timeout in main_api.py
import uvicorn

uvicorn.run(
    app, 
    host="0.0.0.0", 
    port=8000,
    timeout_keep_alive=30,
    timeout_graceful_shutdown=30
)
```

## 📊 Monitoring Setup

### 1. Prometheus + Grafana
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 2. Application Metrics
```python
# Add to main_api.py
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 3. Log Aggregation
```yaml
# ELK Stack for log aggregation
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
```

## 🔄 Backup and Recovery

### 1. Database Backup
```bash
# Create Neo4j backup
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/var/lib/neo4j/backup/backup.dump

# Copy backup to host
docker cp kg_neo4j:/var/lib/neo4j/backup/backup.dump ./backup.dump
```

### 2. Data Export
```bash
# Export all data to CSV
docker-compose exec neo4j cypher-shell -u neo4j -p kgdemo123 "
  MATCH (e:Employee)
  RETURN e.id as employee_id, e.name as name
" > employees.csv
```

### 3. Disaster Recovery
```bash
# Restore from backup
docker-compose exec neo4j neo4j-admin load --from=/var/lib/neo4j/backup/backup.dump --database=neo4j --force

# Restart services
docker-compose restart neo4j api
```

## 🚀 Scaling Strategies

### 1. Horizontal Scaling
```yaml
# Scale API services
docker-compose up --scale api=3

# Use load balancer
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

### 2. Database Clustering
```yaml
# Neo4j cluster setup
version: '3.8'
services:
  neo4j-core1:
    image: neo4j:5.15-enterprise
    environment:
      - NEO4J_server_mode=CORE
      - NEO4J_causal__clustering_initial__discovery__members=neo4j-core1:5000,neo4j-core2:5000,neo4j-core3:5000
  
  neo4j-core2:
    image: neo4j:5.15-enterprise
    environment:
      - NEO4J_server_mode=CORE
      - NEO4J_causal__clustering_initial__discovery__members=neo4j-core1:5000,neo4j-core2:5000,neo4j-core3:5000
  
  neo4j-core3:
    image: neo4j:5.15-enterprise
    environment:
      - NEO4J_server_mode=CORE
      - NEO4J_causal__clustering_initial__discovery__members=neo4j-core1:5000,neo4j-core2:5000,neo4j-core3:5000
```

### 3. Caching Layer
```yaml
# Redis for caching
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data

# Update API service
api:
  environment:
    - REDIS_URL=redis://redis:6379
  depends_on:
    - redis
```

## 📋 Maintenance

### 1. Regular Maintenance Tasks
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up old containers
docker system prune -f
```

### 2. Database Maintenance
```cypher
// Analyze database statistics
CALL apoc.meta.stats();

// Check for orphaned nodes
MATCH (n) WHERE NOT (n)--() RETURN count(n) as orphaned_nodes;

// Clean up old data
MATCH (r:Report) 
WHERE r.create_date < datetime() - duration('P90D')
DETACH DELETE r;
```

### 3. Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# Monitor Neo4j performance
docker-compose exec neo4j cypher-shell -u neo4j -p kgdemo123 "CALL dbms.listQueries()"
```

This comprehensive deployment guide covers everything from local development to production scaling, ensuring your Knowledge Graph system runs smoothly in any environment.
