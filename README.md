# Knowledge Graph Project

A comprehensive knowledge graph system that extracts structured information from text documents and provides intelligent querying capabilities using both traditional NLP and modern LLM approaches.

## 🎯 Project Overview

This project demonstrates multiple approaches to building knowledge graphs from text data:

1. **Traditional NLP Approach** - Uses spaCy for dependency parsing and named entity recognition
2. **LLM-Based Approach** - Uses Ollama (local LLM) for intelligent triple extraction
3. **Hybrid QA System** - Combines knowledge graphs with RAG (Retrieval Augmented Generation)
4. **Enterprise API** - FastAPI-based service for querying structured data with AI summaries

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Text Input    │───▶│  Triple Extract │───▶│  Knowledge      │
│   (.txt files)  │    │  (spaCy/LLM)    │    │  Graph (Neo4j)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐           │
│   Web UI        │◀───│   FastAPI       │◀──────────┘
│  (Streamlit)    │    │   (REST API)    │
└─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │  (Summaries)    │
                       └─────────────────┘
```

## 📁 Project Structure

```
knowledge_graph/
├── 📄 Core Scripts
│   ├── main.py                    # Original Ollama-based triple extraction
│   ├── main_demo.py               # spaCy-based extraction (no LLM required)
│   ├── main_ollama.py             # Enhanced Ollama extraction with HTML viz
│   ├── main_universal.py          # Universal spaCy + NER extraction
│   └── main_api.py                # FastAPI server for enterprise data
│
├── 🔧 Processing & QA
│   ├── qa_anydoc_v2.py            # Hybrid KG + RAG question answering
│   ├── employee_qna.py            # Streamlit UI for employee queries
│   ├── emb_index.py               # Vector embeddings for semantic search
│   └── ingest_concur.py           # CSV data ingestion to Neo4j
│
├── 🌐 Web Interface
│   ├── app.py                     # Streamlit KG + RAG demo
│   └── employee_qna.py            # Employee-specific Q&A interface
│
├── ⚙️ Configuration
│   ├── config.py                  # Environment configuration
│   ├── database.py                # Neo4j connection management
│   ├── models.py                  # Pydantic data models
│   └── ollama_service.py          # LLM service wrapper
│
├── 📊 Data Files
│   ├── input/                     # Sample text documents
│   ├── output/                    # Generated graphs and triples
│   ├── *.csv                      # Sample enterprise data
│   └── requirements.txt           # Python dependencies
│
└── 🐳 Deployment
    ├── Dockerfile                 # Container configuration
    ├── docker-compose.yml         # Multi-service orchestration
    ├── README_API.md              # API documentation
    └── README_DEPLOY.md           # Deployment guide
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Neo4j Database (local or Docker)
- Ollama (for LLM features) - Optional
- Docker & Docker Compose (for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd knowledge_graph
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Basic Usage

#### 1. Extract Knowledge Graph from Text (spaCy - No LLM Required)

```bash
# Process a single document
python main_demo.py --inputpath ./input/sample.txt --outlabel my_document

# Process multiple documents
python main_universal.py --inputpath ./input/ --outlabel all_docs --html
```

#### 2. Extract Knowledge Graph with LLM (Ollama)

```bash
# Install and start Ollama
ollama serve
ollama pull llama3.2

# Extract triples using LLM
python main_ollama.py --inputpath ./input/sample.txt --outlabel llm_doc --model llama3.2 --html
```

#### 3. Interactive Question Answering

```bash
# Start the Streamlit demo
streamlit run app.py

# Or use command-line QA
python qa_anydoc_v2.py --doc ./input/sample.txt --triples ./output/sample_triples.json --ask "Your question here"
```

#### 4. Enterprise API (with Neo4j)

```bash
# Start Neo4j (Docker)
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.15-community

# Load sample data
python ingest_concur.py

# Start API server
python main_api.py

# Access API docs at http://localhost:8000/docs
```

## 📚 Detailed Usage Guide

### 1. Text Processing Scripts

#### `main_demo.py` - Basic spaCy Extraction
- **Purpose**: Extract subject-verb-object triples using dependency parsing
- **Requirements**: Only spaCy (auto-downloads model)
- **Best for**: Quick prototyping, educational purposes
- **Output**: JSON, CSV, and HTML graph visualization

```bash
python main_demo.py --inputpath ./input/metamorphosis-kafka.txt --outlabel kafka_demo
```

#### `main_ollama.py` - LLM-Powered Extraction
- **Purpose**: Use local LLM for intelligent triple extraction
- **Requirements**: Ollama installed and running
- **Best for**: High-quality, context-aware extractions
- **Features**: Chunking, retry logic, HTML visualization

```bash
python main_ollama.py --inputpath ./input/ --outlabel llm_corpus --model llama3.2 --html --max_chars 2000
```

#### `main_universal.py` - Advanced spaCy + NER
- **Purpose**: Combines dependency parsing with named entity recognition
- **Features**: Prepositional objects, coordinated subjects/objects, NER-based relations
- **Best for**: Comprehensive extraction without LLM dependency

```bash
python main_universal.py --inputpath ./input/ --outlabel comprehensive --html --drop_pronouns
```

### 2. Question Answering System

#### `qa_anydoc_v2.py` - Hybrid KG + RAG
- **Purpose**: Answer questions using both knowledge graph and text retrieval
- **Features**: Confidence scoring, fallback mechanisms, Ollama integration
- **Workflow**: KG-first → RAG fallback → LLM composition

```bash
python qa_anydoc_v2.py \
  --doc ./input/complex_demo.txt \
  --triples ./output/complex_triples.json \
  --ask "Who does Priya Raman report to?" \
  --use_ollama --model llama3.2 \
  --verbose
```

#### `app.py` - Streamlit Web Interface
- **Purpose**: Interactive web interface for document Q&A
- **Features**: Document selection, model configuration, real-time answers
- **Access**: http://localhost:8501

### 3. Enterprise API System

#### Data Ingestion (`ingest_concur.py`)
- **Purpose**: Load CSV data into Neo4j graph database
- **Data Sources**: reports.csv, entries.csv, approvals.csv, payments.csv
- **Features**: Batch processing, constraint creation, relationship mapping

```bash
# Set CSV directory
export CONCUR_CSV_DIR="/path/to/csv/files"
python ingest_concur.py
```

#### API Server (`main_api.py`)
- **Purpose**: RESTful API for querying enterprise data
- **Features**: AI-powered summaries, structured queries, health monitoring
- **Endpoints**: Employee data, expense analysis, vendor insights

```bash
python main_api.py
# Access at http://localhost:8000/docs
```

#### Vector Search (`emb_index.py`)
- **Purpose**: Semantic search using embeddings
- **Features**: FAISS indexing, parallel processing, fact extraction
- **Integration**: Used by API for enhanced querying

```bash
python emb_index.py  # Build embedding index
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Ollama Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Data Processing
CONCUR_CSV_DIR=/path/to/csv/files
BATCH_SIZE=1000
EMB_MAX_FACTS=500
```

### Input Data Format

#### Text Documents
- Place `.txt` files in the `input/` directory
- UTF-8 encoding recommended
- Documents are automatically chunked for processing

#### CSV Data (Enterprise)
Required CSV files for enterprise features:
- `reports.csv` - Expense reports
- `entries.csv` - Individual expense entries
- `approvals.csv` - Approval workflow data
- `payments.csv` - Payment information

## 📊 Output Formats

### Triple Extraction Outputs
- **JSON**: `{outlabel}_triples.json` - Structured triple data
- **CSV**: `{outlabel}_triples.csv` - Tabular format for analysis
- **Pickle**: `{outlabel}_triples.pkl` - Python object for programmatic use
- **HTML**: `{outlabel}_graph.html` - Interactive graph visualization

### Graph Database Schema
```
Employee -[:SUBMITTED]-> Report -[:HAS_ENTRY]-> Expense -[:PAID_TO]-> Vendor
Report -[:APPROVED_BY]-> Employee
Report -[:SETTLED_BY]-> Payment
```

## 🎨 Visualization

### Interactive HTML Graphs
- Powered by PyVis network visualization
- Interactive node manipulation
- Relationship labeling
- Physics-based layout

### Neo4j Browser
- Access at http://localhost:7474
- Cypher query interface
- Graph exploration tools
- Data visualization

## 🚀 Deployment Options

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start services
python main_api.py
streamlit run app.py
```

### 2. Docker Compose
```bash
# Start all services
docker-compose up -d

# Load data
docker-compose exec api python ingest_concur.py

# Access services
# API: http://localhost:8000
# Neo4j: http://localhost:7474
```

### 3. Production Deployment
- Use the provided Dockerfile for containerization
- Configure environment variables for production
- Set up proper database credentials
- Enable SSL/TLS for API endpoints

## 🔍 Advanced Features

### 1. Custom Triple Extraction
- Modify system prompts in `input/system-prompt-2.txt`
- Adjust extraction parameters in `input/config.json`
- Add custom NER patterns in `main_universal.py`

### 2. Enhanced Question Answering
- Tune confidence thresholds in `qa_anydoc_v2.py`
- Add custom relation mappings
- Implement domain-specific reasoning

### 3. API Extensions
- Add new endpoints in `main_api.py`
- Create custom Pydantic models in `models.py`
- Implement authentication and authorization

## 🐛 Troubleshooting

### Common Issues

1. **spaCy Model Not Found**
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Ollama Connection Failed**
   ```bash
   # Check if Ollama is running
   ollama list
   # Pull required model
   ollama pull llama3.2
   ```

3. **Neo4j Connection Issues**
   ```bash
   # Check Neo4j status
   docker ps | grep neo4j
   # Test connection
   cypher-shell -u neo4j -p password "RETURN 1"
   ```

4. **Memory Issues with Large Documents**
   - Reduce `--max_chars` parameter
   - Process documents in smaller chunks
   - Increase system memory allocation

### Performance Optimization

1. **Parallel Processing**
   - Enable parallel embedding in `ollama_service.py`
   - Use batch processing for large datasets

2. **Caching**
   - Cache extracted triples to avoid reprocessing
   - Use Redis for API response caching

3. **Database Optimization**
   - Create appropriate Neo4j indexes
   - Use connection pooling for high-load scenarios

## 📈 Performance Metrics

### Triple Extraction Speed
- **spaCy**: ~1000 sentences/second
- **Ollama**: ~10-50 sentences/second (depends on model size)
- **Memory Usage**: 2-8GB depending on document size

### API Performance
- **Response Time**: 100-500ms for simple queries
- **Concurrent Users**: 50-100 (depending on hardware)
- **Database Queries**: Optimized with proper indexing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **spaCy** - Natural language processing library
- **Ollama** - Local LLM inference
- **Neo4j** - Graph database
- **FastAPI** - Modern web framework
- **Streamlit** - Data app framework
- **PyVis** - Network visualization

## 📞 Support

For questions, issues, or contributions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Examine the example scripts

---

**Happy Knowledge Graph Building! 🕸️**
