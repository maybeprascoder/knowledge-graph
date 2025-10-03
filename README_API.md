# Knowledge Graph API Documentation

A comprehensive FastAPI-based service that integrates Neo4j knowledge graph with Ollama for intelligent data querying and natural language processing.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CSV Data      │───▶│   Data          │───▶│   Neo4j         │
│   (Enterprise)  │    │   Ingestion     │    │   Graph DB      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐           │
│   Web UI        │◀───│   FastAPI       │◀──────────┘
│  (Streamlit)    │    │   (REST API)    │
└─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │  (AI Summaries) │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Neo4j Database (5.15+)
- Ollama (for AI features)
- CSV data files (reports, entries, approvals, payments)

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd knowledge_graph

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here

# Ollama Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Data Configuration
CONCUR_CSV_DIR=/path/to/csv/files
BATCH_SIZE=1000
EMB_MAX_FACTS=500
```

### 3. Start Services

```bash
# Start Neo4j (Docker)
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.15-community

# Start Ollama
ollama serve
ollama pull llama3.2

# Load data
python ingest_concur.py

# Start API server
python main_api.py
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Health Check**: http://localhost:8000/health

## 📊 Data Model

### Graph Schema

```
Employee -[:SUBMITTED]-> Report -[:HAS_ENTRY]-> Expense -[:PAID_TO]-> Vendor
Report -[:APPROVED_BY {step, decision, at}]-> Employee
Report -[:SETTLED_BY]-> Payment
```

### Node Properties

#### Employee
- `id`: Unique identifier (email)
- `name`: Full name

#### Report
- `id`: Report ID
- `name`: Report name
- `create_date`: Creation timestamp
- `submit_date`: Submission timestamp
- `approval_status`: Current approval status
- `payment_status`: Payment status
- `total_txn`: Total transaction amount
- `currency`: Currency code

#### Expense
- `id`: Expense ID
- `amount`: Transaction amount
- `currency`: Currency code
- `type_code`: Expense type code
- `type_name`: Expense type name
- `spend_category`: Spend category
- `description`: Expense description
- `transaction_date`: Transaction date

#### Vendor
- `name`: Vendor name

#### Payment
- `id`: Payment ID
- `method`: Payment method
- `status`: Payment status
- `payment_date`: Payment date
- `total_amount`: Total amount
- `company_paid`: Company paid amount
- `employee_due`: Employee due amount

## 🔌 API Endpoints

### Health & Status

#### `GET /`
Basic health check endpoint.

**Response:**
```json
{
  "message": "Knowledge Graph API is running",
  "status": "healthy"
}
```

#### `GET /health`
Detailed health check including database connectivity.

**Response:**
```json
{
  "api": "healthy",
  "neo4j": "connected",
  "ollama": "available"
}
```

### Employee Data

#### `GET /employees`
Get list of all employees in the database.

**Response:**
```json
{
  "employees": [
    {
      "employee_id": "john.doe@company.com",
      "name": "John Doe"
    }
  ]
}
```

#### `GET /employee/{employee_id}/expenses`
Get all expenses for a specific employee with AI-generated summary.

**Parameters:**
- `employee_id` (path): Employee identifier

**Response:**
```json
{
  "employee_id": "john.doe@company.com",
  "expenses": [
    {
      "expense_id": "EXP001",
      "amount": 150.0,
      "category": "Travel"
    }
  ],
  "total_amount": 425.5,
  "summary": "John Doe has submitted 5 expenses totaling $425.50...",
  "raw_data": [...]
}
```

#### `GET /employee/{employee_id}/approvals`
Get approval history for an employee's reports.

**Response:**
```json
{
  "employee_id": "john.doe@company.com",
  "approvals": [
    {
      "report_id": "RPT001",
      "step": 1.0,
      "step_name": "Manager Approval",
      "decision": "APPROVED",
      "decided_at": "2024-01-15T10:30:00Z",
      "approver_id": "manager@company.com",
      "approver_name": "Jane Manager"
    }
  ],
  "summary": "Approval summary...",
  "raw_data": [...]
}
```

#### `GET /employee/{employee_id}/payments`
Get payment history for an employee's reports.

**Response:**
```json
{
  "employee_id": "john.doe@company.com",
  "payments": [
    {
      "report_id": "RPT001",
      "payment_id": "PAY001",
      "method": "Direct Deposit",
      "status": "PAID",
      "payment_date": "2024-01-20T00:00:00Z",
      "total_amount": 425.5,
      "company_paid": 400.0,
      "employee_due": 25.5
    }
  ],
  "total_amount": 425.5,
  "summary": "Payment summary...",
  "raw_data": [...]
}
```

### Analytics & Insights

#### `GET /vendors/top`
Get top vendors by total spend.

**Parameters:**
- `limit` (query, optional): Number of vendors to return (default: 10)

**Response:**
```json
{
  "items": [
    {
      "vendor": "Acme Corp",
      "spend": 15000.0
    }
  ],
  "summary": "Top vendors analysis...",
  "raw_data": [...]
}
```

#### `GET /expenses/categories`
Get all unique expense categories.

**Response:**
```json
{
  "categories": ["Travel", "Meals", "Office Supplies", "Software"]
}
```

### Natural Language Querying

#### `GET /qa`
Answer natural language questions across the entire knowledge graph.

**Parameters:**
- `q` (query, required): Your question
- `limit` (query, optional): Maximum results to consider (default: 50)
- `mode` (query, optional): Answer mode - "precise", "conversational", or "auto" (default: "auto")

**Example:**
```bash
curl "http://localhost:8000/qa?q=What are the largest expenses and who approved them?&mode=conversational"
```

**Response:**
```json
{
  "question": "What are the largest expenses and who approved them?",
  "answer": "The largest expenses are...",
  "context": {
    "scope": "global",
    "expenses": [...],
    "approvals": [...],
    "facts": [...]
  }
}
```

#### `GET /qa/employee/{employee_id}`
Answer questions about a specific employee.

**Parameters:**
- `employee_id` (path): Employee identifier
- `q` (query, required): Your question

**Example:**
```bash
curl "http://localhost:8000/qa/employee/john.doe@company.com?q=What was my total travel expenses last month?"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.2` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_EMBED_MODEL` | Embedding model | `nomic-embed-text` |
| `CONCUR_CSV_DIR` | CSV files directory | Current directory |
| `BATCH_SIZE` | Batch processing size | `1000` |
| `EMB_MAX_FACTS` | Max facts for embedding | `500` |

### Data Ingestion

The API expects CSV files in the following format:

#### reports.csv
```csv
ID,Name,OwnerLoginID,OwnerName,CreateDate,SubmitDate,ApprovalStatus,PaymentStatus,TotalTransactionAmount
RPT001,January Expenses,john.doe@company.com,John Doe,2024-01-01,2024-01-15,APPROVED,PAID,425.50
```

#### entries.csv
```csv
ID,ReportID,TransactionDate,TransactionAmount,ExpenseTypeName,Description,VendorDescription
EXP001,RPT001,2024-01-10,150.00,Travel,Client meeting,Acme Corp
```

#### approvals.csv
```csv
ReportID,ApproverID,ApproverName,StepOrder,StepName,Decision,DecisionTimestamp
RPT001,manager@company.com,Jane Manager,1,Manager Approval,APPROVED,2024-01-12T10:30:00Z
```

#### payments.csv
```csv
PaymentID,ReportID,PaymentMethod,PaymentDate,TotalAmount,CompanyPaidAmount,EmployeeDueAmount,PaymentStatus
PAY001,RPT001,Direct Deposit,2024-01-20,425.50,400.00,25.50,PAID
```

## 🛠️ Development

### Adding New Endpoints

1. **Define the route in `main_api.py`:**
```python
@app.get("/custom/endpoint")
async def custom_endpoint(param: str):
    # Implementation
    pass
```

2. **Add Pydantic models in `models.py` if needed:**
```python
class CustomResponse(BaseModel):
    field1: str
    field2: int
```

3. **Test with the interactive docs at `/docs`**

### Database Queries

Use the database module for Neo4j queries:

```python
from database import db

# Execute a query
results = db.execute_query(
    "MATCH (e:Employee)-[:SUBMITTED]->(r:Report) RETURN e.name, count(r) as reports",
    {"limit": 10}
)
```

### Ollama Integration

Use the Ollama service for AI features:

```python
from ollama_service import ollama_service

# Generate summary
summary = ollama_service.generate_summary(data, "expense data")

# Answer question
answer = ollama_service.answer_question(question, context)

# Generate embeddings
embeddings = ollama_service.embed(["text1", "text2"])
```

### Error Handling

The API includes comprehensive error handling:

- **404**: Resource not found
- **500**: Internal server error
- **422**: Validation error
- **503**: Service unavailable

## 🚀 Deployment

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Load data
docker-compose exec api python ingest_concur.py

# Check status
docker-compose ps
```

### Production Considerations

1. **Security**
   - Set strong Neo4j passwords
   - Use environment variables for secrets
   - Enable HTTPS
   - Implement authentication

2. **Performance**
   - Use connection pooling
   - Enable Neo4j query caching
   - Monitor memory usage
   - Scale horizontally

3. **Monitoring**
   - Health check endpoints
   - Logging and metrics
   - Database performance monitoring
   - API response time tracking

## 🔍 Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   ```bash
   # Check Neo4j status
   docker ps | grep neo4j
   
   # Test connection
   cypher-shell -u neo4j -p password "RETURN 1"
   ```

2. **Ollama Not Responding**
   ```bash
   # Check Ollama status
   ollama list
   
   # Pull required model
   ollama pull llama3.2
   ```

3. **Data Loading Issues**
   ```bash
   # Check CSV files
   ls -la /path/to/csv/files/
   
   # Re-run ingestion
   python ingest_concur.py
   ```

4. **Memory Issues**
   - Reduce `BATCH_SIZE` for large datasets
   - Increase system memory
   - Use streaming for very large files

### Performance Optimization

1. **Database Indexing**
   ```cypher
   CREATE INDEX employee_id_index FOR (e:Employee) ON (e.id);
   CREATE INDEX report_id_index FOR (r:Report) ON (r.id);
   ```

2. **Query Optimization**
   - Use parameterized queries
   - Limit result sets
   - Use appropriate WHERE clauses

3. **Caching**
   - Cache frequently accessed data
   - Use Redis for session storage
   - Implement response caching

## 📈 Monitoring & Metrics

### Health Checks
- `/health` endpoint for service status
- Database connectivity monitoring
- Ollama service availability

### Logging
- Structured logging with timestamps
- Error tracking and alerting
- Performance metrics collection

### Metrics to Monitor
- API response times
- Database query performance
- Memory and CPU usage
- Error rates and types

## 🔮 Future Enhancements

- **Authentication & Authorization**: JWT-based auth system
- **Real-time Updates**: WebSocket support for live data
- **Advanced Analytics**: Machine learning insights
- **Data Validation**: Schema validation and data quality checks
- **API Versioning**: Support for multiple API versions
- **Rate Limiting**: Request throttling and quotas
- **Caching Layer**: Redis integration for performance
- **Monitoring Dashboard**: Real-time system metrics
