# LightRAG + Ollama Setup Guide

## What You're Getting

**The BEST local setup:**
- ✅ **LightRAG** - Advanced graph-based RAG (better than simple vector search)
- ✅ **Ollama embeddings** - Your existing Ollama server on the host
- ✅ **Docker** - Everything containerized and isolated
- ✅ **Zero API costs** - Fully local, no external calls

## Prerequisites

1. **Ollama running on your host machine**:
   ```bash
   # Check Ollama is running
   curl http://localhost:11434/api/tags
   ```

2. **Download embedding model in Ollama**:
   ```bash
   # Install nomic-embed-text (recommended for embeddings)
   ollama pull nomic-embed-text
   
   # Or use another embedding model you prefer
   # ollama pull mxbai-embed-large
   # ollama pull all-minilm
   ```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Host Machine                                   │
│  ┌───────────────┐                             │
│  │ Ollama Server │ :11434                      │
│  │ (embeddings)  │                             │
│  └───────┬───────┘                             │
│          │                                      │
│  ┌───────▼──────────────────────────────────┐  │
│  │  Docker Network                          │  │
│  │                                          │  │
│  │  ┌─────────────┐    ┌─────────────┐    │  │
│  │  │  LightRAG   │◄───│ API Worker  │    │  │
│  │  │  :9621      │    │             │    │  │
│  │  └─────────────┘    └─────────────┘    │  │
│  │                                          │  │
│  │  Your PDFs → LightRAG → Graph Index    │  │
│  │                     ↓                    │  │
│  │              [Ollama embeddings]        │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Configuration

### 1. Check Your Ollama Model

See what embedding models you have:
```bash
ollama list | grep embed
```

If you need one:
```bash
# Best for embeddings
ollama pull nomic-embed-text
```

### 2. Update Model Name (if different)

If you're using a different model, edit [config.yaml](../Archivist/src/Archivist/config.yaml):
```yaml
indexers:
  vectordb:
    embedding_type: "ollama"
    embedding_model: "your-model-name"  # Change this
```

And [docker-compose.yml](docker-compose.yml):
```yaml
lightrag:
  environment:
    EMBEDDING_MODEL: "your-model-name"  # Change this too
```

## Deploy

### Full Rebuild (Recommended First Time)

```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API

# Stop everything
sudo docker-compose down

# Remove old images (optional but clean)
sudo docker-compose down --rmi all

# Rebuild with new configuration
sudo docker-compose build --no-cache

# Start all services
sudo docker-compose up -d
```

### Quick Restart (After Config Changes)

```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API

sudo docker-compose restart
```

## Verify Setup

### 1. Check Ollama from Docker Container

```bash
# Enter the worker container
sudo docker exec -it multiagentframework_worker bash

# Test Ollama connection
curl http://host.docker.internal:11434/api/tags

# Should show your Ollama models
```

### 2. Check LightRAG Service

```bash
# Check LightRAG is running
sudo docker ps | grep lightrag

# Check LightRAG logs
sudo docker-compose logs lightrag

# Test LightRAG endpoint
curl http://localhost:9621/health
```

### 3. Watch Worker Logs

```bash
sudo docker-compose logs -f multiagentframework_worker

# Look for these success messages:
# "Using Ollama embeddings: nomic-embed-text"
# "LightRAG initialized successfully"
```

## Test Document Upload

Upload a PDF through your frontend or API:

```bash
curl -X POST http://localhost:5001/api/documents/upload \
  -F "file=@test.pdf" \
  -F "metadata={\"title\":\"Test Doc\",\"author\":\"User\"}"
```

### What Happens:

1. PDF uploaded to API
2. Worker receives task
3. LightRAG processes document
4. Calls your **host Ollama** for embeddings
5. Creates graph-based index
6. Stores in LightRAG's internal storage

## Monitoring

### Check Ollama Usage

On your **host machine**:
```bash
# Watch Ollama logs
journalctl -u ollama -f

# Or if running Ollama manually
ollama serve  # Watch the console
```

You should see embedding requests coming from Docker containers.

### Monitor All Services

```bash
# All services
sudo docker-compose logs -f

# Specific services
sudo docker-compose logs -f lightrag
sudo docker-compose logs -f multiagentframework_worker
```

## Troubleshooting

### "Cannot connect to Ollama"

**Check Ollama is accessible from Docker:**
```bash
sudo docker run --rm curlimages/curl curl http://host.docker.internal:11434/api/tags
```

**If it fails:**
- Ensure Ollama is running: `systemctl status ollama`
- Or start it: `ollama serve`

### "Model not found"

**Pull the embedding model:**
```bash
ollama pull nomic-embed-text
```

### "LightRAG container not starting"

**Check LightRAG logs:**
```bash
sudo docker-compose logs lightrag
```

**Common issues:**
- Port 9621 already in use: Change port in docker-compose.yml
- Invalid model name: Update EMBEDDING_MODEL in docker-compose.yml

### "Worker can't reach LightRAG"

**Test connection from worker:**
```bash
sudo docker exec -it multiagentframework_worker bash
curl http://lightrag:9621/health
```

## Performance

### Embedding Speed
- **Ollama on GPU**: Very fast (~100ms per document)
- **Ollama on CPU**: Moderate (~500ms per document)

### First Upload
- LightRAG initializes (~5-10 seconds)
- Documents processed incrementally
- Graph index built in real-time

### Scaling
- **Documents**: LightRAG handles 10,000+ documents efficiently
- **Memory**: ~2-4GB RAM for Ollama embeddings
- **Disk**: Grows with document collection

## Ollama Models for Embeddings

| Model | Size | Dimensions | Speed | Quality |
|-------|------|------------|-------|---------|
| `nomic-embed-text` | 274MB | 768 | Fast | Excellent |
| `mxbai-embed-large` | 670MB | 1024 | Medium | Best |
| `all-minilm` | 45MB | 384 | Fastest | Good |

**Recommendation**: Start with `nomic-embed-text` (best balance).

## Switching Between Backends

### Use LightRAG (Current)
In [tasks.py](tasks.py):
```python
archivist = Archivist(config = {
    "enable_vectordb": False,
    "enable_lightrag": True,
    "run_name": "Example Index"
})
```

### Use Simple ChromaDB (Fallback)
In [tasks.py](tasks.py):
```python
archivist = Archivist(config = {
    "enable_vectordb": True,
    "enable_lightrag": False,
    "run_name": "Example Index"
})
```

Then rebuild:
```bash
sudo docker-compose restart
```

## Benefits of This Setup

### LightRAG Advantages
- 🎯 **Graph-based retrieval** - Understands document relationships
- 🔍 **Better context** - Maintains semantic connections
- 📊 **Multi-hop reasoning** - Answers complex questions
- 🚀 **Scalable** - Handles large document collections

### Ollama Advantages
- 💰 **Free** - No API costs
- 🔒 **Private** - Data never leaves your machine
- ⚡ **Fast** - GPU acceleration (if available)
- 🎛️ **Control** - Choose your own models

## Next Steps

1. **Upload some documents** - Test the indexing pipeline
2. **Ask questions** - See the graph-based retrieval in action
3. **Monitor performance** - Watch Ollama and LightRAG logs
4. **Tune if needed** - Adjust models or settings

## Cost Comparison

| Setup | Monthly Cost | Performance |
|-------|--------------|-------------|
| **This (LightRAG+Ollama)** | $0 | Excellent |
| OpenAI Embeddings + Vector DB | ~$50-200 | Good |
| Pinecone + OpenAI | ~$100-500 | Good |

## Summary

You now have a **production-ready, fully local, advanced RAG system** using:
- 🎯 LightRAG for intelligent document understanding
- 🤖 Your existing Ollama for embeddings
- 🐳 Docker for easy deployment
- 💰 $0 ongoing costs

Just run:
```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

Then upload your PDFs and enjoy advanced RAG! 🚀
