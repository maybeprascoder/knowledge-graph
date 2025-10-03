# Knowledge Graph Script Reference

A comprehensive reference guide for all scripts in the Knowledge Graph project, explaining their purpose, usage, and parameters.

## 📋 Script Overview

| Script | Purpose | Complexity | Dependencies |
|--------|---------|------------|--------------|
| `main_demo.py` | Basic spaCy extraction | Beginner | spaCy only |
| `main_ollama.py` | AI-powered extraction | Intermediate | Ollama + spaCy |
| `main_universal.py` | Advanced NLP extraction | Intermediate | spaCy + NER |
| `main_api.py` | Enterprise API server | Advanced | Neo4j + Ollama |
| `qa_anydoc_v2.py` | Question answering | Intermediate | spaCy + Ollama |
| `app.py` | Web interface | Beginner | Streamlit |
| `employee_qna.py` | Employee Q&A UI | Intermediate | Streamlit + API |
| `ingest_concur.py` | Data ingestion | Advanced | Neo4j |
| `emb_index.py` | Vector search | Advanced | FAISS + Ollama |

## 🔧 Core Processing Scripts

### 1. `main_demo.py` - Basic Text Processing

**Purpose:** Extract subject-verb-object relationships using dependency parsing

**Best for:**
- Quick prototyping
- Educational purposes
- Simple text analysis
- When you don't have AI models

**Usage:**
```bash
python main_demo.py --inputpath ./input/sample.txt --outlabel my_graph
```

**Parameters:**
- `--inputpath`: Path to text file (required)
- `--outlabel`: Output file prefix (required)

**Outputs:**
- `{outlabel}_triples.json` - Structured relationship data
- `{outlabel}_triples.csv` - Spreadsheet format
- `{outlabel}_nx_graph.pkl` - NetworkX graph object
- `{outlabel}_graph.html` - Interactive visualization

**How it works:**
1. Loads text file
2. Uses spaCy to parse sentences
3. Finds subject-verb-object patterns
4. Creates knowledge graph
5. Saves in multiple formats

**Example:**
```bash
# Create sample text
echo "John works at Acme Corp. Jane manages the team. The team is located in New York." > sample.txt

# Process it
python main_demo.py --inputpath sample.txt --outlabel company

# Results in:
# - company_triples.json
# - company_triples.csv  
# - company_nx_graph.pkl
# - company_graph.html
```

### 2. `main_ollama.py` - AI-Powered Extraction

**Purpose:** Use local LLM for intelligent relationship extraction

**Best for:**
- Complex documents
- High-quality extractions
- When you have AI models available
- Research papers and technical documents

**Usage:**
```bash
python main_ollama.py --inputpath ./input/sample.txt --outlabel ai_graph --model llama3.2 --html
```

**Parameters:**
- `--inputpath`: File, folder, or glob pattern (required)
- `--outlabel`: Output prefix (required)
- `--model`: Ollama model name (default: llama3.1:8b)
- `--max_chars`: Chunk size in characters (default: 1800)
- `--html`: Generate HTML visualization
- `--min_edges`: Minimum edges for HTML (default: 0)
- `--retry`: Retries on JSON parse failure (default: 2)

**Prerequisites:**
```bash
# Install and start Ollama
ollama serve

# Pull required model
ollama pull llama3.2
```

**Outputs:**
- `{outlabel}_triples.pkl` - Pickle format
- `{outlabel}_triples.json` - JSON format
- `{outlabel}_triples.csv` - CSV format
- `{outlabel}_nx_graph.pkl` - NetworkX graph
- `{outlabel}_graph.html` - Interactive visualization (if --html)

**How it works:**
1. Chunks text into manageable pieces
2. Sends each chunk to Ollama with extraction prompt
3. Parses JSON response for relationships
4. Normalizes and deduplicates triples
5. Creates knowledge graph
6. Optionally generates HTML visualization

**Example:**
```bash
# Process single file
python main_ollama.py --inputpath ./input/research_paper.txt --outlabel research --model llama3.2 --html

# Process multiple files
python main_ollama.py --inputpath ./input/*.txt --outlabel all_docs --model mistral --max_chars 2000
```

### 3. `main_universal.py` - Advanced NLP Extraction

**Purpose:** Comprehensive extraction using multiple NLP techniques

**Best for:**
- High-quality extraction without AI
- Complex documents with various entity types
- When you need comprehensive coverage
- Production systems without AI dependency

**Usage:**
```bash
python main_universal.py --inputpath ./input/sample.txt --outlabel universal --html
```

**Parameters:**
- `--inputpath`: File, folder, or glob pattern (required)
- `--outlabel`: Output prefix (required)
- `--min_edges`: Minimum edges for HTML (default: 0)
- `--max_docs`: Maximum documents to process (default: 0 = no limit)
- `--html`: Generate HTML visualization
- `--drop_pronouns`: Remove edges with pronoun subjects

**Features:**
- Subject-verb-object extraction
- Prepositional object handling
- Coordinated subjects and objects
- Named entity recognition
- Relationship templates
- Pronoun filtering

**Outputs:**
- `{outlabel}_triples.pkl` - Pickle format
- `{outlabel}_triples.json` - JSON format
- `{outlabel}_triples.csv` - CSV format
- `{outlabel}_nx_graph.pkl` - NetworkX graph
- `{outlabel}_graph.html` - Interactive visualization (if --html)

**How it works:**
1. Loads spaCy model (auto-downloads if missing)
2. Processes each document
3. Extracts SVO triples using dependency parsing
4. Handles prepositional objects and coordination
5. Applies NER-based relationship templates
6. Deduplicates and normalizes triples
7. Creates knowledge graph

**Example:**
```bash
# Process with pronoun filtering
python main_universal.py --inputpath ./input/ --outlabel clean --html --drop_pronouns

# Process limited number of documents
python main_universal.py --inputpath ./input/*.txt --outlabel sample --max_docs 5 --html
```

## 🌐 Web Interface Scripts

### 4. `app.py` - Streamlit Demo Interface

**Purpose:** Interactive web interface for document analysis

**Best for:**
- Demonstrations
- Interactive exploration
- Non-technical users
- Quick experiments

**Usage:**
```bash
streamlit run app.py
```

**Features:**
- Document selection dropdown
- Triples file selection
- Ollama integration toggle
- Model selection
- Verbose scoring option
- Real-time question answering
- Support information display

**Interface Components:**
1. **Sidebar:**
   - Document selection
   - Triples file selection
   - Ollama settings
   - Load button

2. **Main Area:**
   - Question input
   - Answer display
   - Support information (triples and snippets)

**How to use:**
1. Start the interface: `streamlit run app.py`
2. Open browser to http://localhost:8501
3. Select document and triples file
4. Configure Ollama settings if needed
5. Click "Load" to load data
6. Type your question
7. Click "Answer" to get results

### 5. `employee_qna.py` - Employee Q&A Interface

**Purpose:** Specialized interface for employee data queries

**Best for:**
- Enterprise data exploration
- Employee-specific queries
- API integration
- Business users

**Usage:**
```bash
streamlit run employee_qna.py
```

**Prerequisites:**
- API server running (`main_api.py`)
- Neo4j database with employee data

**Features:**
- Global vs employee-specific queries
- Employee ID input
- Question text area
- Context display
- Error handling

**How to use:**
1. Start API server: `python main_api.py`
2. Start interface: `streamlit run employee_qna.py`
3. Choose query scope (All data or By employee)
4. Enter employee ID if needed
5. Type your question
6. Click "Ask" to get results

## 🤖 AI and Processing Scripts

### 6. `qa_anydoc_v2.py` - Question Answering System

**Purpose:** Answer questions using knowledge graph and RAG

**Best for:**
- Document analysis
- Knowledge extraction
- Research assistance
- Information retrieval

**Usage:**
```bash
python qa_anydoc_v2.py --doc ./input/sample.txt --triples ./output/sample_triples.json --ask "Your question"
```

**Parameters:**
- `--doc`: Original text document (required)
- `--triples`: Triples JSON file (required)
- `--ask`: Your question (required)
- `--use_ollama`: Use Ollama for answer composition
- `--model`: Ollama model name (default: llama3.2)
- `--verbose`: Show detailed scoring information

**Features:**
- Knowledge graph-first answering
- RAG fallback mechanism
- Confidence scoring
- Support information
- Multiple answer modes

**How it works:**
1. Loads document and triples
2. Attempts KG-based answering first
3. Falls back to RAG if KG fails
4. Uses Ollama for answer composition (optional)
5. Returns answer with confidence scores

**Example:**
```bash
# Basic usage
python qa_anydoc_v2.py \
  --doc ./input/company_doc.txt \
  --triples ./output/company_triples.json \
  --ask "Who does John report to?"

# With AI enhancement
python qa_anydoc_v2.py \
  --doc ./input/company_doc.txt \
  --triples ./output/company_triples.json \
  --ask "What is the organizational structure?" \
  --use_ollama \
  --model llama3.2 \
  --verbose
```

### 7. `emb_index.py` - Vector Search System

**Purpose:** Semantic search using embeddings

**Best for:**
- Semantic similarity search
- Large-scale fact retrieval
- API integration
- Advanced querying

**Usage:**
```bash
python emb_index.py  # Build index
```

**Prerequisites:**
- Neo4j database with data
- Ollama with embedding model

**Features:**
- FAISS indexing
- Parallel embedding
- Fact extraction
- Semantic search
- Configurable limits

**How it works:**
1. Extracts facts from Neo4j database
2. Generates embeddings using Ollama
3. Builds FAISS index
4. Provides semantic search functionality

**Integration:**
```python
from emb_index import search_facts

# Search for similar facts
results = search_facts("expense approval process", k=10)
```

## 🏢 Enterprise Scripts

### 8. `main_api.py` - FastAPI Server

**Purpose:** RESTful API for enterprise data querying

**Best for:**
- Production systems
- Application integration
- Enterprise data analysis
- Professional deployments

**Usage:**
```bash
python main_api.py
```

**Prerequisites:**
- Neo4j database
- Ollama service
- CSV data files

**Features:**
- RESTful API endpoints
- AI-powered summaries
- Structured data queries
- Health monitoring
- CORS support
- OpenAPI documentation

**Endpoints:**
- `GET /` - Health check
- `GET /health` - Detailed health check
- `GET /employees` - List employees
- `GET /employee/{id}/expenses` - Employee expenses
- `GET /employee/{id}/approvals` - Employee approvals
- `GET /employee/{id}/payments` - Employee payments
- `GET /vendors/top` - Top vendors
- `GET /expenses/categories` - Expense categories
- `GET /qa` - Global Q&A
- `GET /qa/employee/{id}` - Employee Q&A

**Configuration:**
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### 9. `ingest_concur.py` - Data Ingestion

**Purpose:** Load CSV data into Neo4j graph database

**Best for:**
- Enterprise data integration
- CSV to graph conversion
- Data migration
- Production data loading

**Usage:**
```bash
python ingest_concur.py
```

**Prerequisites:**
- Neo4j database running
- CSV files in correct format
- Python environment with Neo4j driver

**Required CSV files:**
- `reports.csv` - Expense reports
- `entries.csv` - Individual expenses
- `approvals.csv` - Approval workflow
- `payments.csv` - Payment information

**Features:**
- Batch processing
- Constraint creation
- Relationship mapping
- Error handling
- Progress tracking

**Configuration:**
```env
CONCUR_CSV_DIR=/path/to/csv/files
BATCH_SIZE=1000
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

**How it works:**
1. Connects to Neo4j database
2. Creates constraints and indexes
3. Processes CSV files in batches
4. Maps data to graph structure
5. Creates relationships between entities

## 🔧 Utility Scripts

### 10. `config.py` - Configuration Management

**Purpose:** Centralized configuration management

**Features:**
- Environment variable loading
- Default value handling
- Settings validation
- Easy configuration access

**Usage:**
```python
from config import settings

# Access configuration
neo4j_uri = settings.NEO4J_URI
ollama_model = settings.OLLAMA_MODEL
```

### 11. `database.py` - Database Connection

**Purpose:** Neo4j database connection management

**Features:**
- Connection pooling
- Error handling
- Session management
- Query execution

**Usage:**
```python
from database import db

# Execute query
results = db.execute_query("MATCH (n) RETURN n LIMIT 5")
```

### 12. `models.py` - Data Models

**Purpose:** Pydantic models for API responses

**Features:**
- Type validation
- Serialization
- Documentation
- Error handling

**Models:**
- `Expense` - Expense data
- `EmployeeExpensesResponse` - Employee expenses response
- `Approval` - Approval data
- `Payment` - Payment data
- `VendorSpend` - Vendor spending data

### 13. `ollama_service.py` - AI Service

**Purpose:** Ollama integration service

**Features:**
- Model management
- Embedding generation
- Summary generation
- Question answering
- Parallel processing

**Usage:**
```python
from ollama_service import ollama_service

# Generate summary
summary = ollama_service.generate_summary(data, "expense data")

# Answer question
answer = ollama_service.answer_question(question, context)

# Generate embeddings
embeddings = ollama_service.embed(["text1", "text2"])
```

## 📊 Output Formats

### JSON Format
```json
[
  {
    "head_entity": {
      "entity": "John Smith",
      "attribute": "PERSON"
    },
    "relation": {
      "relation": "works_at"
    },
    "tail_entity": {
      "entity": "Acme Corp",
      "attribute": "ORG"
    }
  }
]
```

### CSV Format
```csv
head,head_attr,relation,tail,tail_attr
John Smith,PERSON,works_at,Acme Corp,ORG
Acme Corp,ORG,located_in,New York,GPE
```

### NetworkX Graph
```python
import networkx as nx
import pickle

# Load graph
with open('output/graph.pkl', 'rb') as f:
    G = pickle.load(f)

# Use graph
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
```

## 🎯 Choosing the Right Script

### For Beginners
1. **Start with:** `main_demo.py` + `app.py`
2. **Learn:** Basic concepts and visualization
3. **Progress to:** `main_universal.py` for better extraction

### For Intermediate Users
1. **Use:** `main_ollama.py` for AI-powered extraction
2. **Try:** `qa_anydoc_v2.py` for question answering
3. **Explore:** `employee_qna.py` for enterprise features

### For Advanced Users
1. **Deploy:** `main_api.py` for production
2. **Integrate:** `ingest_concur.py` for data loading
3. **Customize:** Modify scripts for specific needs

### For Enterprise
1. **Setup:** Neo4j + Ollama infrastructure
2. **Load:** Data using `ingest_concur.py`
3. **Deploy:** API using `main_api.py`
4. **Monitor:** Health and performance

## 🔍 Troubleshooting Scripts

### Common Issues

1. **Import errors:** Check if all dependencies are installed
2. **File not found:** Verify file paths and permissions
3. **Memory errors:** Reduce batch sizes or chunk sizes
4. **Connection errors:** Check service status and configuration
5. **Empty results:** Verify input data quality and format

### Debug Tips

1. **Use verbose mode:** Add `--verbose` to see detailed output
2. **Check logs:** Look at console output for error messages
3. **Test with sample data:** Use provided sample files first
4. **Verify prerequisites:** Ensure all services are running
5. **Check file formats:** Verify input files are in correct format

This reference guide provides comprehensive information about all scripts in the Knowledge Graph project, helping you choose the right tool for your specific needs and use case.
