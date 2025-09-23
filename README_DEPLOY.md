# Knowledge Graph API Deployment

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- CSV files: `reports.csv`, `entries.csv`, `approvals.csv`, `payments.csv` in the parent directory

### 1. Start the stack
```bash
cd knowledge-graph-demo
docker-compose up -d
```

### 2. Wait for services to be healthy
```bash
docker-compose ps
```

### 3. Load your data
```bash
# Copy CSVs to the import volume
docker cp ../reports.csv kg_neo4j:/var/lib/neo4j/import/
docker cp ../entries.csv kg_neo4j:/var/lib/neo4j/import/
docker cp ../approvals.csv kg_neo4j:/var/lib/neo4j/import/
docker cp ../payments.csv kg_neo4j:/var/lib/neo4j/import/

# Run the ingestion script
docker-compose exec api python ingest_concur.py
```

### 4. Access the API
- API Docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474 (neo4j/kgdemo123)

## API Endpoints

### Core endpoints
- `GET /health` - Health check
- `GET /employees` - List all employees
- `GET /employee/{employee_id}/expenses` - Employee expenses with AI summary
- `GET /employee/{employee_id}/approvals` - Employee approval history
- `GET /employee/{employee_id}/payments` - Employee payment history
- `GET /vendors/top?limit=10` - Top vendors by spend
- `GET /expenses/categories` - All expense categories

### Example usage
```bash
# Get employee expenses
curl "http://localhost:8000/employee/john.doe@company.com/expenses"

# Top vendors
curl "http://localhost:8000/vendors/top?limit=5"

# Employee approvals
curl "http://localhost:8000/employee/john.doe@company.com/approvals"
```

## Manual Setup (without Docker)

### 1. Install Neo4j
- Download Neo4j Desktop or use Docker: `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.15-community`

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Create `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Load data
```bash
export CONCUR_CSV_DIR="/path/to/csv/files"
python ingest_concur.py
```

### 5. Start API
```bash
uvicorn main_api:app --host 0.0.0.0 --port 8000 --reload
```

## Data Schema

### Nodes
- `Employee` - {id, name}
- `Report` - {id, name, create_date, submit_date, approval_status, payment_status, ...}
- `Expense` - {id, amount, type_code, type_name, spend_category, ...}
- `Vendor` - {name}
- `Payment` - {id, method, status, payment_date, total_amount, ...}

### Relationships
- `(:Employee)-[:SUBMITTED]->(:Report)`
- `(:Report)-[:HAS_ENTRY]->(:Expense)`
- `(:Expense)-[:PAID_TO]->(:Vendor)`
- `(:Report)-[:APPROVED_BY {step, decision, at}]->(:Employee)`
- `(:Report)-[:SETTLED_BY]->(:Payment)`

## Troubleshooting

### Neo4j connection issues
```bash
# Check Neo4j is running
docker-compose logs neo4j

# Test connection
docker-compose exec neo4j cypher-shell -u neo4j -p kgdemo123 "RETURN 1"
```

### API issues
```bash
# Check API logs
docker-compose logs api

# Test health endpoint
curl http://localhost:8000/health
```

### Data loading issues
```bash
# Check if CSVs are accessible
docker-compose exec api ls -la /app/data/

# Re-run ingestion
docker-compose exec api python ingest_concur.py
```

## Stopping the stack
```bash
docker-compose down
```

## Data persistence
Neo4j data is persisted in Docker volumes. To reset:
```bash
docker-compose down -v
docker-compose up -d
```
