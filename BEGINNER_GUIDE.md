# Knowledge Graph Beginner's Guide

A step-by-step guide for beginners to understand and use the Knowledge Graph system effectively.

## 🎯 What is a Knowledge Graph?

A knowledge graph is a way to represent information as a network of connected entities and their relationships. Think of it like a family tree, but for any type of information - people, places, events, concepts, etc.

**Example:**
- John works at Acme Corp
- Acme Corp is located in New York
- John reports to Jane
- Jane manages the Engineering team

This creates a graph where:
- **Nodes** (circles) = entities (John, Acme Corp, New York, Jane, Engineering team)
- **Edges** (lines) = relationships (works at, located in, reports to, manages)

## 🚀 Getting Started

### Prerequisites

Before you begin, make sure you have:

1. **Python 3.11 or higher** installed
2. **Basic understanding of command line** (Terminal/Command Prompt)
3. **Text editor** (VS Code, Notepad++, or any editor you prefer)
4. **8GB+ RAM** (for smooth operation)

### Installation Steps

#### Step 1: Download the Project
```bash
# If you have Git installed
git clone <repository-url>
cd knowledge_graph

# Or download as ZIP and extract
```

#### Step 2: Install Python Dependencies
```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

#### Step 3: Verify Installation
```bash
python --version  # Should show Python 3.11+
pip list | grep spacy  # Should show spacy package
```

## 📚 Understanding the Scripts

### 1. Basic Text Processing (`main_demo.py`)

**What it does:** Extracts relationships from text using traditional NLP (no AI required)

**When to use:** 
- Quick experiments
- When you don't have AI models
- Educational purposes

**How to use:**
```bash
# Basic usage
python main_demo.py --inputpath ./input/sample.txt --outlabel my_first_graph

# What happens:
# 1. Reads your text file
# 2. Finds subject-verb-object relationships
# 3. Creates a knowledge graph
# 4. Saves results in multiple formats
```

**Example with sample text:**
```bash
# Create a sample text file
echo "John works at Acme Corp. Acme Corp is located in New York. John reports to Jane." > sample.txt

# Process it
python main_demo.py --inputpath sample.txt --outlabel company_graph

# Check outputs
ls output/
# You'll see:
# - company_graph_triples.json (structured data)
# - company_graph_triples.csv (spreadsheet format)
# - company_graph_nx_graph.pkl (Python object)
# - company_graph_graph.html (visualization)
```

### 2. AI-Powered Processing (`main_ollama.py`)

**What it does:** Uses AI to understand text and extract more sophisticated relationships

**When to use:**
- Complex documents
- When you want better relationship extraction
- When you have AI models available

**Prerequisites:**
```bash
# Install Ollama (AI model runner)
# Visit https://ollama.ai and download for your system

# Start Ollama service
ollama serve

# Download AI model (in another terminal)
ollama pull llama3.2
```

**How to use:**
```bash
# Basic usage
python main_ollama.py --inputpath ./input/sample.txt --outlabel ai_graph --model llama3.2 --html

# Advanced usage
python main_ollama.py \
  --inputpath ./input/ \
  --outlabel all_documents \
  --model llama3.2 \
  --max_chars 2000 \
  --html \
  --retry 3
```

**Parameters explained:**
- `--inputpath`: File or folder to process
- `--outlabel`: Name for output files
- `--model`: AI model to use (llama3.2, mistral, phi3, etc.)
- `--max_chars`: Maximum characters per AI request
- `--html`: Generate interactive visualization
- `--retry`: Number of retries if AI fails

### 3. Universal Processing (`main_universal.py`)

**What it does:** Combines multiple NLP techniques for comprehensive extraction

**When to use:**
- When you want the best of both worlds
- Complex documents with various entity types
- When you need high-quality extraction without AI

**How to use:**
```bash
# Basic usage
python main_universal.py --inputpath ./input/sample.txt --outlabel universal_graph --html

# Advanced usage
python main_universal.py \
  --inputpath ./input/ \
  --outlabel comprehensive \
  --html \
  --drop_pronouns \
  --max_docs 10
```

**Parameters explained:**
- `--drop_pronouns`: Remove unclear references (he, she, it)
- `--max_docs`: Limit number of documents to process
- `--html`: Generate visualization

### 4. Question Answering (`qa_anydoc_v2.py`)

**What it does:** Answers questions about your documents using the knowledge graph

**When to use:**
- When you want to query your data
- For document analysis
- To test if your graph is working

**How to use:**
```bash
# Basic usage
python qa_anydoc_v2.py \
  --doc ./input/sample.txt \
  --triples ./output/sample_triples.json \
  --ask "Who works at Acme Corp?"

# With AI enhancement
python qa_anydoc_v2.py \
  --doc ./input/sample.txt \
  --triples ./output/sample_triples.json \
  --ask "What is the organizational structure?" \
  --use_ollama \
  --model llama3.2 \
  --verbose
```

**Parameters explained:**
- `--doc`: Original text document
- `--triples`: JSON file with extracted relationships
- `--ask`: Your question
- `--use_ollama`: Use AI to improve answers
- `--verbose`: Show detailed processing information

### 5. Web Interface (`app.py`)

**What it does:** Provides a user-friendly web interface for document analysis

**When to use:**
- When you prefer clicking over typing commands
- For demonstrations
- When you want to experiment interactively

**How to use:**
```bash
# Start the web interface
streamlit run app.py

# Open your browser to http://localhost:8501
```

**Using the interface:**
1. Select a document from the dropdown
2. Select the corresponding triples file
3. Choose whether to use AI for answers
4. Type your question
5. Click "Answer" to get results

### 6. Enterprise API (`main_api.py`)

**What it does:** Provides a professional API for structured data querying

**When to use:**
- When you have structured data (CSV files)
- For building applications
- For integration with other systems

**Prerequisites:**
```bash
# Install Neo4j database
# Option 1: Docker (recommended)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15-community

# Option 2: Neo4j Desktop
# Download from https://neo4j.com/download/
```

**How to use:**
```bash
# 1. Load your data
python ingest_concur.py

# 2. Start the API
python main_api.py

# 3. Access the API documentation
# Open http://localhost:8000/docs in your browser
```

## 📊 Understanding the Outputs

### File Types Explained

#### 1. JSON Files (`*_triples.json`)
**What it contains:** Structured relationship data
**How to read:** Open in any text editor or JSON viewer
**Example:**
```json
[
  {
    "head_entity": {"entity": "John", "attribute": "PERSON"},
    "relation": {"relation": "works_at"},
    "tail_entity": {"entity": "Acme Corp", "attribute": "ORG"}
  }
]
```

#### 2. CSV Files (`*_triples.csv`)
**What it contains:** Spreadsheet-friendly data
**How to read:** Open in Excel, Google Sheets, or any spreadsheet program
**Columns:**
- `head`: Source entity
- `head_attr`: Type of source entity
- `relation`: Relationship type
- `tail`: Target entity
- `tail_attr`: Type of target entity

#### 3. HTML Files (`*_graph.html`)
**What it contains:** Interactive graph visualization
**How to read:** Open in any web browser
**Features:**
- Click and drag nodes
- Zoom in/out
- Search for specific entities
- View relationship details

#### 4. Pickle Files (`*_nx_graph.pkl`)
**What it contains:** Python graph object
**How to read:** Use in Python scripts
**Example:**
```python
import pickle
import networkx as nx

# Load the graph
with open('output/sample_nx_graph.pkl', 'rb') as f:
    G = pickle.load(f)

# Use the graph
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
```

## 🎯 Common Use Cases

### 1. Document Analysis

**Scenario:** You have a company document and want to understand the relationships between people and departments.

**Steps:**
```bash
# 1. Prepare your document
cp your_company_doc.txt ./input/

# 2. Extract relationships
python main_universal.py --inputpath ./input/your_company_doc.txt --outlabel company_analysis --html

# 3. Ask questions
python qa_anydoc_v2.py \
  --doc ./input/your_company_doc.txt \
  --triples ./output/company_analysis_triples.json \
  --ask "Who reports to whom in the company?"
```

### 2. Research Paper Analysis

**Scenario:** You want to extract key relationships from academic papers.

**Steps:**
```bash
# 1. Use AI for better understanding
python main_ollama.py --inputpath ./input/research_paper.txt --outlabel research --model llama3.2 --html

# 2. Query specific information
python qa_anydoc_v2.py \
  --doc ./input/research_paper.txt \
  --triples ./output/research_triples.json \
  --ask "What are the main findings of this research?" \
  --use_ollama \
  --model llama3.2
```

### 3. News Article Analysis

**Scenario:** You want to track relationships between people, organizations, and events in news.

**Steps:**
```bash
# 1. Process multiple articles
python main_universal.py --inputpath ./input/news/ --outlabel news_analysis --html --max_docs 20

# 2. Use web interface for exploration
streamlit run app.py
# Select news_analysis_triples.json and ask questions
```

### 4. Financial Data Analysis

**Scenario:** You have expense reports and want to analyze spending patterns.

**Steps:**
```bash
# 1. Prepare CSV files (reports.csv, entries.csv, approvals.csv, payments.csv)
# 2. Load into Neo4j
python ingest_concur.py

# 3. Start API
python main_api.py

# 4. Query via API
curl "http://localhost:8000/employee/john.doe@company.com/expenses"
```

## 🔧 Troubleshooting Common Issues

### Issue 1: "spaCy model not found"
**Error:** `OSError: [E050] Can't find model 'en_core_web_sm'`

**Solution:**
```bash
python -m spacy download en_core_web_sm
```

### Issue 2: "Ollama connection failed"
**Error:** `ConnectionError: Failed to connect to Ollama`

**Solution:**
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# Pull required model
ollama pull llama3.2
```

### Issue 3: "No triples extracted"
**Problem:** Empty or very few relationships found

**Solutions:**
1. **Check your text quality:**
   - Ensure sentences are complete
   - Avoid very short or fragmented text
   - Include clear subject-verb-object structures

2. **Try different approaches:**
   ```bash
   # Try AI-based extraction
   python main_ollama.py --inputpath your_file.txt --outlabel test --model llama3.2
   
   # Try universal extraction
   python main_universal.py --inputpath your_file.txt --outlabel test --html
   ```

3. **Adjust parameters:**
   ```bash
   # For AI extraction, try different models
   python main_ollama.py --inputpath your_file.txt --outlabel test --model mistral
   
   # For universal extraction, try different settings
   python main_universal.py --inputpath your_file.txt --outlabel test --drop_pronouns
   ```

### Issue 4: "Memory error"
**Error:** `MemoryError` or system becomes slow

**Solutions:**
1. **Process smaller chunks:**
   ```bash
   # Split large files
   split -l 1000 large_file.txt chunk_
   
   # Process each chunk
   for file in chunk_*; do
     python main_demo.py --inputpath "$file" --outlabel "chunk_${file}"
   done
   ```

2. **Use streaming for large datasets:**
   ```bash
   # For CSV data
   export BATCH_SIZE=500
   python ingest_concur.py
   ```

### Issue 5: "Graph visualization not working"
**Problem:** HTML file opens but graph doesn't display

**Solutions:**
1. **Check if PyVis is installed:**
   ```bash
   pip install pyvis
   ```

2. **Try different browsers:**
   - Chrome usually works best
   - Disable ad blockers
   - Allow JavaScript

3. **Check file size:**
   - Very large graphs may not render well
   - Try processing smaller documents first

## 📈 Tips for Better Results

### 1. Text Preparation
- **Use complete sentences:** "John works at Acme Corp" not "John Acme Corp"
- **Be specific:** "John Smith works as a manager at Acme Corp" is better than "John works there"
- **Include context:** "In 2023, John Smith was promoted to manager at Acme Corp"

### 2. Choosing the Right Script
- **For simple text:** Use `main_demo.py`
- **For complex documents:** Use `main_ollama.py` with AI
- **For comprehensive analysis:** Use `main_universal.py`
- **For interactive exploration:** Use `app.py` (Streamlit)

### 3. Parameter Tuning
- **Chunk size:** Smaller chunks (500-1000 chars) for better AI processing
- **Model selection:** Try different AI models (llama3.2, mistral, phi3)
- **Retry count:** Increase retries (3-5) for unreliable AI responses

### 4. Question Formulation
- **Be specific:** "Who does John report to?" not "Who does he report to?"
- **Use entity names:** "What is Acme Corp's location?" not "Where is it located?"
- **Ask one thing at a time:** "Who are the managers?" not "Who are the managers and what do they do?"

## 🎓 Learning Path

### Beginner (Week 1-2)
1. **Start with simple text:**
   - Create a short paragraph about your family
   - Use `main_demo.py` to extract relationships
   - View the HTML graph

2. **Try the web interface:**
   - Use `streamlit run app.py`
   - Experiment with different questions
   - Compare different documents

3. **Learn the basics:**
   - Understand nodes and edges
   - Learn about different relationship types
   - Practice with sample data

### Intermediate (Week 3-4)
1. **Work with real documents:**
   - Process news articles or company documents
   - Use `main_universal.py` for better extraction
   - Analyze the results

2. **Experiment with AI:**
   - Install Ollama
   - Try `main_ollama.py` with different models
   - Compare AI vs non-AI results

3. **Advanced querying:**
   - Use `qa_anydoc_v2.py` for complex questions
   - Learn to formulate better questions
   - Understand confidence scores

### Advanced (Week 5-6)
1. **Work with structured data:**
   - Set up Neo4j database
   - Use `main_api.py` for enterprise features
   - Process CSV data

2. **Customize the system:**
   - Modify extraction parameters
   - Add custom relationship types
   - Create your own questions

3. **Build applications:**
   - Integrate with other systems
   - Create custom visualizations
   - Deploy for production use

## 🔍 Understanding the Results

### Reading the Graph Visualization

1. **Nodes (circles):**
   - Size often indicates importance
   - Color may indicate entity type
   - Click to see details

2. **Edges (lines):**
   - Thickness may indicate relationship strength
   - Arrows show direction
   - Hover to see relationship type

3. **Layout:**
   - Related entities cluster together
   - Central nodes are often important
   - Isolated nodes may be outliers

### Interpreting Confidence Scores

- **High scores (0.7+):** Very confident about the relationship
- **Medium scores (0.4-0.7):** Somewhat confident, may need verification
- **Low scores (<0.4):** Low confidence, may be incorrect

### Common Relationship Types

- **Hierarchical:** reports_to, manages, supervises
- **Spatial:** located_in, works_at, lives_in
- **Temporal:** happened_before, occurred_during
- **Causal:** caused_by, results_in, leads_to
- **Functional:** uses, produces, consumes

## 🚀 Next Steps

### After Mastering the Basics

1. **Explore advanced features:**
   - Custom entity recognition
   - Relationship weighting
   - Temporal analysis

2. **Integrate with other tools:**
   - Database systems
   - Visualization tools
   - Machine learning pipelines

3. **Build your own applications:**
   - Document analysis tools
   - Knowledge management systems
   - Research assistants

4. **Contribute to the project:**
   - Report bugs
   - Suggest improvements
   - Add new features

### Resources for Further Learning

1. **Graph Theory:** Learn about networks and relationships
2. **Natural Language Processing:** Understand how text is processed
3. **Knowledge Graphs:** Study advanced graph techniques
4. **Machine Learning:** Explore AI-powered extraction

### Community and Support

- **GitHub Issues:** Report problems and ask questions
- **Documentation:** Read the full API documentation
- **Examples:** Study the sample scripts and data
- **Tutorials:** Follow online tutorials for specific use cases

Remember: The best way to learn is by doing! Start with simple examples and gradually work your way up to more complex scenarios. Don't be afraid to experiment and make mistakes - that's how you learn!
