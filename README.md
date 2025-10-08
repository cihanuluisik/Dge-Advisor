# DGE Policy RAG System

A production-ready RAG (Retrieval Augmented Generation) system for policy document Q&A. Built with LlamaIndex, CrewAI agents, and PostgreSQL vector storage.

## 📚 Documentation

- **[Full Documentation](docs/README.md)** - Complete setup guide, usage instructions, and configuration
- **[Architecture Diagrams](docs/ARCHITECTURE_DIAGRAMS.md)** - System and CrewAI architecture visualizations
- **[Cleanup Notes](docs/CLEANUP_SUGGESTIONS.md)** - Code quality improvements and refactoring history

## Quick Start

```bash
# Deploy all services
./deploy_all_to_local_docker.sh up

# Or manually
cd docker
docker-compose up -d
```

**Access Points:**
- UI: http://localhost:3000
- API: http://localhost:8008/v1
- Phoenix: http://localhost:6006
- pgAdmin: http://localhost:5050

## Performance

- **83% semantic accuracy** (0.830 similarity score)
- **68.4%** of responses are high quality (≥0.8)
- Optimized retrieval with 3 documents (2 semantic + 1 sparse)
- Zero context errors, zero low-performing queries
- ✅ **Production Ready**

## Architecture

- **API**: FastAPI with OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`)
- **Agents**: CrewAI multi-agent workflow (Guardrail → Memorized → LLM)
- **Storage**: PostgreSQL 16 + pgvector (HNSW index, hybrid search)
- **Embeddings**: Granite-embedding:30m (384-dim)
- **LLM**: Gemma3:12b
- **Monitoring**: Arize Phoenix (OpenTelemetry)
- **UI**: Open WebUI

See [Architecture Diagrams](docs/ARCHITECTURE_DIAGRAMS.md) for detailed visualizations.

## Prerequisites

1. Docker & Docker Compose
2. Python 3.9+ (Docker uses 3.12)
3. Ollama with models:
   ```bash
   ollama pull granite-embedding:30m
   ollama pull gemma3:12b
   ```

## Environment Variables

```bash
# Database
DHOST=localhost
DPORT=5432
DNAME=ragdb
DUSER=user
DPASSWORD=password

# Models
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=granite-embedding:30m
EMBEDDING_MODEL_DIM=384
LLM_MODEL=gemma3:12b

# API
RAG_API_PORT=8008
OPENAI_API_KEY=dummy-key

# Monitoring
PHOENIX_HOST=localhost
PHOENIX_PORT=6006
```

## Deployment Commands

```bash
./deploy_all_to_local_docker.sh [command]
  up       - Start all services (default)
  down     - Stop all services
  build    - Rebuild containers
  restart  - Restart services
  logs     - Follow logs
  rag      - Rebuild and deploy API only
  clean    - Remove all data (prompts confirmation)
```

## Local Development

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run API locally
./start_api.sh
```

For detailed setup instructions, testing, and troubleshooting, see the [full documentation](docs/README.md).

## Project Structure

```
Dge1/
├── src/
│   ├── agents/           # CrewAI agents (agents.yaml, tasks.yaml, crew.py)
│   ├── api/              # FastAPI service (service.py, request_response.py)
│   ├── config/           # Config (config.py, config_rag.py)
│   ├── indexer/          # Document ingestion & vector indexing
│   └── retriever/        # Hybrid search retriever
├── docker/
│   ├── docker-compose.yml    # Services: postgres, phoenix, openwebui, rag-api, pgadmin
│   ├── Dockerfile            # Python 3.12 + uv package manager
│   └── scripts/              # init-db.sql, pgadmin-servers.json
├── data/
│   ├── all/              # Source documents (PDF)
│   └── md/               # Converted markdown
├── tests/                # Tests & RAG evaluation (ragas)
├── deploy_all_to_local_docker.sh  # Deployment script
├── start_api.sh          # Local dev script
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
└── pytest.ini            # Test configuration
```

## RAG Configuration

**Vector Search (HNSW):**
- Index: `hnsw_m=24`, `ef_construction=128`, `ef_search=64`
- Distance: Cosine similarity
- Hybrid: Semantic + BM25 sparse search

**Retrieval:**
- Top-k: 3 documents (2 semantic + 1 sparse)
- Reranking: Enabled
- Conversation context: Last 3 messages

## License

Internal use only - DGE Organization