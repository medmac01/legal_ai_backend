# LightRAG + Qdrant Setup Guide

## Overview

Your system now supports **two indexing backends**:

1. **VectorDB** (ChromaDB/Pinecone) - Current default, simpler setup
2. **LightRAG** (with Qdrant) - Advanced graph-based RAG with better retrieval

## What Was Fixed

### 1. PDF Parsing Error
**Error**: `ImportError: partition_pdf() is not available`

**Solution**: Added `unstructured[pdf]` to requirements files
- Updated `/API/requirements.txt`
- Updated `/Archivist/requirements.txt`

### 2. Missing EMBEDDINGS_API_KEY
**Error**: `EMBEDDINGS_API_KEY is required but not set`

**Solution**: Added to `.env` file (using your existing Gemini API key)

## How to Use LightRAG + Qdrant

### Option 1: Using Official LightRAG (Recommended)

**Note**: LightRAG service needs to be set up separately. The docker-compose configuration is prepared but you need to either:
- Build your own LightRAG service container
- Use a compatible LightRAG server

### Option 2: Keep Using VectorDB (Current Setup)

Your current setup uses **ChromaDB** which works fine. To fix the PDF issue:

```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

## Configuration Files Updated

### 1. docker-compose.yml
Added two new services:
- **qdrant**: Vector database (port 6333)
- **lightrag**: Document indexing service (port 9621)

### 2. Archivist config.yaml
Updated LightRAG settings:
```yaml
indexers:
  lightrag:
    base_url: "http://lightrag:9621"
    clear_existing: true
    max_polling_time: 300
    polling_interval: 2
```

### 3. API .env
Added:
```bash
EMBEDDINGS_API_KEY=${GEMINI_API_KEY}
```

## Switching Between Indexers

### To Use ChromaDB (Current - Simpler)
In `API/tasks.py` line 220:
```python
archivist = Archivist(config = {
    "enable_vectordb": True,  # Use ChromaDB
    "enable_lightrag": False,
    "run_name": "Example Index"
})
```

### To Use LightRAG (Advanced)
In `API/tasks.py` line 220:
```python
archivist = Archivist(config = {
    "enable_vectordb": False,
    "enable_lightrag": True,  # Use LightRAG + Qdrant
    "run_name": "Example Index"
})
```

## Rebuild and Deploy

### Quick Fix (Just PDF Support)
```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API

# Rebuild containers with new dependencies
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d

# Check logs
sudo docker-compose logs -f multiagentframework_worker
```

### With LightRAG + Qdrant (Full Setup)

1. **Start Qdrant only first** (to test):
```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API
sudo docker-compose up -d qdrant
```

2. **Set up LightRAG server** (you'll need to configure this separately):
   - LightRAG needs to be configured to connect to Qdrant
   - See: https://github.com/HKUDS/LightRAG for setup details

3. **Update task configuration** in `API/tasks.py` (line 220):
```python
archivist = Archivist(config = {
    "enable_vectordb": False,
    "enable_lightrag": True,
    "run_name": "Example Index"
})
```

4. **Rebuild and start all services**:
```bash
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

## Testing

### Test PDF Upload
```bash
# Upload a PDF through your frontend or API
curl -X POST http://localhost:5001/api/documents/upload \
  -F "file=@test.pdf" \
  -F "metadata={\"title\":\"Test\",\"author\":\"User\"}"
```

### Check Qdrant Status
```bash
# Qdrant health check
curl http://localhost:6333/

# List collections
curl http://localhost:6333/collections
```

### Monitor Logs
```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f multiagentframework_worker
sudo docker-compose logs -f qdrant
sudo docker-compose logs -f lightrag
```

## Architecture Comparison

### ChromaDB (Current)
- ✅ Simpler setup
- ✅ Works out of the box
- ✅ Good for basic semantic search
- ❌ No graph-based relationships

### LightRAG + Qdrant
- ✅ Advanced graph-based RAG
- ✅ Better contextual understanding
- ✅ Scalable with Qdrant
- ❌ Requires additional LightRAG service
- ❌ More complex setup

## Recommended Approach

**For now (immediate fix)**:
1. Keep using ChromaDB (VectorDB)
2. Just rebuild to fix the PDF error
3. System will work immediately

**For future (better performance)**:
1. Research and set up LightRAG server properly
2. Configure it to use your Qdrant instance
3. Switch indexer configuration
4. Test thoroughly before production

## Current Status

✅ PDF parsing dependencies added
✅ EMBEDDINGS_API_KEY configured
✅ Qdrant service ready in docker-compose
⏸️ LightRAG service needs separate configuration
✅ ChromaDB works with current setup

## Need Help?

The main error you saw will be fixed by rebuilding with the updated requirements. Run:

```bash
cd /home/gpuadmin/threathunting/legal_ai_backend/API
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

Then try uploading your PDF again!
