# Knowledge Graph API

A FastAPI-based service that integrates Neo4j knowledge graph with Ollama for natural language processing.

## Architecture

- **Neo4j**: Local graph database storing employee, expense, and report data
- **FastAPI**: REST API backend with automatic OpenAPI documentation
- **Ollama**: Local LLM for generating natural language summaries
- **Python**: Core application logic and data processing

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here

# Ollama Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Start Neo4j

Make sure Neo4j is running locally on the default port (7687).

### 4. Start Ollama

```bash
# Install and start Ollama
ollama serve

# Pull the model (in another terminal)
ollama pull llama3.2
```

### 5. Populate Sample Data

```bash
python sample_data.py
```

### 6. Start the API Server

```bash
python main_api.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health check including database connectivity

### Employee Data
- `GET /employee/{id}/expenses` - Get all expenses for an employee with AI summary
- `GET /employees` - List all employees
- `GET /expenses/categories` - Get all expense categories

## Example Usage

### Get Employee Expenses

```bash
curl "http://localhost:8000/employee/EMP001/expenses"
```

Response:
```json
{
  "employee_id": "EMP001",
  "expenses": [
    {
      "expense_id": "EXP001",
      "amount": 150.0,
      "category": "Travel"
    }
  ],
  "total_amount": 425.5,
  "summary": "John Smith has submitted 5 expenses totaling $425.50...",
  "raw_data": [...]
}
```

### List All Employees

```bash
curl "http://localhost:8000/employees"
```

## Data Model

The Neo4j graph contains:

- **Employee** nodes: `{id, name, department}`
- **Report** nodes: `{id, month, status}`
- **Expense** nodes: `{id, amount, category}`
- **Relationships**:
  - `Employee -[:SUBMITTED]-> Report`
  - `Report -[:HAS_ENTRY]-> Expense`
  - `Employee -[:REPORTS_TO]-> Employee`

## Development

### Adding New Endpoints

1. Add new route functions in `main_api.py`
2. Define Pydantic models in `models.py` if needed
3. Add corresponding Cypher queries
4. Test with the interactive API docs at `http://localhost:8000/docs`

### Database Queries

All Neo4j queries are executed through the `database.py` module:

```python
from database import db

# Execute a query
results = db.execute_query("MATCH (n) RETURN n LIMIT 5")
```

### Ollama Integration

The `ollama_service.py` module handles all LLM interactions:

```python
from ollama_service import ollama_service

summary = ollama_service.generate_summary(data, "expense data")
```

## Next Steps

- Add more complex queries (approval chains, policy violations)
- Implement authentication and authorization
- Add data validation and error handling
- Create a React frontend
- Add real-time updates with WebSockets
