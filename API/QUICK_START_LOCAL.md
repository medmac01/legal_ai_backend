# Quick Start - Minimal Local Setup

## What This Is
**The simplest possible setup - everything runs locally on your machine with NO external API calls needed.**

## What You Get
✅ PDF document upload and processing
✅ ChromaDB vector database (local storage)
✅ Local embeddings (no API keys required)
✅ All services in Docker
✅ Zero ongoing costs

## Architecture
```
Your Documents → PDF Parser → Local Embeddings → ChromaDB (local storage)
                                                           ↓
                            Your Questions → AI → Search ChromaDB → Answer
```

## One Command Setup

```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API

# Stop any running containers
sudo docker-compose down

# Rebuild with new configuration
sudo docker-compose build --no-cache

# Start everything
sudo docker-compose up -d
```

## What Changed

### 1. Local Embeddings (No API Key Needed!)
- **Before**: Required OpenAI API key ($$$)
- **Now**: Uses `sentence-transformers/all-MiniLM-L6-v2` (free, runs on your CPU)
- **Speed**: First run downloads model (~100MB), then fast

### 2. ChromaDB for Vector Storage
- **Fully local** - data stored in `/chroma_db` inside container
- **No external dependencies**
- **Automatic persistence** via Docker volumes

### 3. PDF Support Fixed
- Added `unstructured[pdf]` package
- PDFs will now parse correctly

## Services Running

After starting, you'll have:

| Service | Port | Purpose |
|---------|------|---------|
| API | 5001 | Main FastAPI application |
| RabbitMQ | 5672, 15672 | Task queue |
| Redis | 6379 | Result backend |
| PostgreSQL | 5432 | Conversation history |
| Worker | - | Background task processing |

## Verify It's Working

### 1. Check all services are up
```bash
sudo docker ps
```
You should see 5 containers running.

### 2. Check logs
```bash
# Watch worker logs
sudo docker-compose logs -f multiagentframework_worker

# Check for this success message:
# "VectorDBIndexer initialized successfully"
```

### 3. Test PDF upload
Upload a PDF through your frontend or:
```bash
curl -X POST http://localhost:5001/api/documents/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

## Configuration Details

### Embeddings: `config.yaml`
```yaml
indexers:
  vectordb:
    embedding_type: "local"  # No API needed
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

### Vector Store: `config.yaml`
```yaml
indexers:
  vectordb:
    use_vector_store: "chroma"
    chroma:
      INDEX_NAME: "test"
      persist_directory: "/chroma_db"
```

## Performance Notes

### First Document Upload
- Downloads embedding model (~100MB) - **one-time only**
- Takes 30-60 seconds
- Subsequent uploads are much faster

### Embedding Model Options

**Current (Fast & Small)**
```yaml
embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```
- Size: ~100MB
- Speed: Very fast
- Quality: Good for most use cases

**Better Quality (Slower)**
```yaml
embedding_model: "sentence-transformers/all-mpnet-base-v2"
```
- Size: ~400MB
- Speed: Slower
- Quality: Better semantic understanding

To change: Edit `Archivist/src/Archivist/config.yaml` and rebuild.

## Troubleshooting

### "Model not found" error
The model downloads automatically on first use. Wait 30-60 seconds.

### "Out of memory" error
The local embedding model needs ~2GB RAM. If you have limited RAM:
1. Keep using `all-MiniLM-L6-v2` (smaller)
2. Close other applications
3. Or switch back to API embeddings (set `embedding_type: "openai"`)

### PDF parsing still fails
```bash
# Check worker logs
sudo docker-compose logs multiagentframework_worker | grep -i error

# Rebuild without cache
sudo docker-compose build --no-cache multiagentframework_worker
sudo docker-compose up -d
```

## Monitoring

### RabbitMQ Dashboard
http://localhost:15672
- Username: `guest`
- Password: `guest`

### View ChromaDB Data
```bash
# Enter worker container
sudo docker exec -it multiagentframework_worker bash

# Python shell
python3
>>> from chromadb import Client
>>> from chromadb.config import Settings
>>> client = Client(Settings(persist_directory="/chroma_db"))
>>> client.list_collections()
```

## Costs

**Everything is FREE!**
- ✅ No OpenAI API costs
- ✅ No Pinecone costs  
- ✅ No external services
- ✅ Runs entirely on your hardware

## When to Upgrade

This minimal setup is great for:
- ✅ Testing and development
- ✅ Small document collections (< 10,000 docs)
- ✅ Personal use
- ✅ Privacy-sensitive data (everything stays local)

Consider API embeddings when:
- ❌ You need best-in-class semantic search
- ❌ Processing 10,000+ documents
- ❌ Your server has limited CPU/RAM

## Reverting to API Embeddings

If you want to use OpenAI embeddings later:

1. Edit `Archivist/src/Archivist/config.yaml`:
```yaml
embedding_type: "openai"
embedding_model: "text-embedding-3-large"
```

2. Set API key in `.env`:
```bash
EMBEDDINGS_API_KEY=your-openai-key
```

3. Rebuild:
```bash
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

## Summary

You now have a **fully local, zero-cost, production-ready** document processing system! 🎉

Just run:
```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

Then upload your PDFs and start asking questions!
