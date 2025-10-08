# System Architecture Diagrams

## 1. Overall System Architecture

![Overall System Architecture](diagrams/overall_layers.png)

---

## 2. Detailed CrewAI Architecture

![CrewAI Architecture](diagrams/Crewai.png)

---

## 3. Conversation Example

![Conversation Example](diagrams/Conversation_example.png)

---

## Key Components Explained

### Overall System
- **Open WebUI**: Web-based chat interface for user interactions
- **RAG API**: FastAPI service providing OpenAI-compatible endpoints
- **CrewAI**: Agent orchestration framework managing workflow
- **PostgreSQL + pgvector**: Vector database for embeddings and chat history
- **Ollama**: Local LLM server hosting language models
- **Phoenix**: OpenTelemetry-based tracing and monitoring

### CrewAI Detailed Components

#### Agents (Sequential Process)
1. **Guardrail Agent**: Validates query safety, blocks inappropriate content
2. **Memorized Agent**: Retrieves relevant documents using RAG tools
3. **LLM Agent**: Synthesizes final answer with context from previous agents

#### Tools
- **RetrieverRerankerTool**: Handles document retrieval with chat history context
- **ConversationTool**: Manages conversation persistence

#### RAG Pipeline
- **Indexer**: Document ingestion, chunking, embedding generation
- **Retriever**: Vector similarity search with hybrid approach
- **Reranker**: Cross-encoder for relevance optimization

#### Hooks
- **@before_kickoff**: Prepare session data before agent execution
- **@after_kickoff**: Store assistant responses after completion
