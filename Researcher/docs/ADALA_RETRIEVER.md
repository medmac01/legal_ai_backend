# Adala Justice Retriever

## Overview

The `AdalaRetriever` is a specialized retriever for searching and retrieving Moroccan legal documents from the official Adala Justice website (https://adala.justice.gov.ma). It provides access to:

- **Laws (Lois)** - Legal statutes and acts
- **Decrees (Décrets)** - Administrative decrees
- **Regulations (Règlements)** - Official regulations
- **Other legal documents**

## Features

- ✅ Asynchronous search with 30-second timeout
- ✅ Structured document metadata extraction
- ✅ Support for both Arabic and French queries
- ✅ LangChain Document format compatibility
- ✅ LangGraph tool integration
- ✅ Comprehensive error handling and logging
- ✅ Configurable via YAML

## Configuration

The retriever is configured in `Researcher/src/Researcher/config.yaml`:

```yaml
retrievers:
  adala:
    base_url: "https://adala.justice.gov.ma"
    build_id: "THP5ZL1eNCinRAZ1hWfN0"  # May need updates if website is redeployed
    max_results: 5
```

### Configuration Parameters

- **`base_url`** (string): The base URL of the Adala Justice website
- **`build_id`** (string): The Next.js build ID for API endpoints. **Note**: This may change if the Adala website is redeployed
- **`max_results`** (int): Maximum number of search results to retrieve (default: 5)

## Usage

### Basic Usage with Researcher Agent

```python
from Researcher.agent import Researcher

# Create a researcher with Adala retriever enabled
researcher = Researcher(config={
    "enable_adala": True,
})

# Search for Moroccan legal documents
results = researcher.query("طلاق")  # Arabic: divorce laws
results = researcher.query("code civil")  # French: civil code
```

### Direct Usage

```python
from Researcher.retrievers import AdalaRetriever

# Initialize the retriever
retriever = AdalaRetriever()

# Search for legal documents
documents = retriever.retrieve("الزواج", max_results=10)  # Arabic: marriage

# Access document information
for doc in documents:
    print(f"Title: {doc.metadata['title']}")
    print(f"Type: {doc.metadata['type']}")
    print(f"Date: {doc.metadata['date']}")
    print(f"Download URL: {doc.metadata['source']}")
```

## Document Structure

Each retrieved document is returned as a LangChain `Document` object with the following structure:

### Page Content
```
Title: <document title>
Document Type: <type>
Law Type: <law_type>
Date: <date>
Download URL: <download_url>
```

### Metadata
```python
{
    "source": "<download_url>",          # Full URL to download the document
    "title": "<title>",                   # Document title
    "type": "<document_type>",            # Document type (Law, Decree, etc.)
    "law_type": "<law_type>",            # Specific law classification
    "date": "<date>",                     # Publication/enactment date
    "relative_path": "<relative_path>",   # Relative path on the Adala website
    "retriever": "adala_retriever"        # Retriever identifier
}
```

## API Details

### API Endpoint

The retriever queries the Adala Justice API:

```
https://adala.justice.gov.ma/_next/data/{build_id}/fr/search.json?term={query}
```

### Response Format

The API returns JSON in the following structure:

```json
{
  "pageProps": {
    "searchResult": {
      "data": [
        {
          "title": "Document Title",
          "type": "Law",
          "law_type": "Civil",
          "date": "2024-01-01",
          "relative_path": "/documents/example.pdf"
        }
      ]
    }
  }
}
```

## Error Handling

The retriever implements robust error handling:

- **HTTP Errors**: Logged and returns empty list
- **Request Errors**: Logged and returns empty list  
- **Timeout**: 30-second timeout with graceful failure
- **Invalid Responses**: Handled with empty list return

All errors are logged using the Researcher's logging system for debugging.

## Important Notes

### Build ID Updates

⚠️ **The `build_id` parameter is critical for API compatibility.**

If searches start failing, the Build ID may have changed due to website redeployment. To find the new Build ID:

1. Visit https://adala.justice.gov.ma/fr/search
2. Open browser developer tools (F12)
3. Go to the Network tab
4. Perform a search
5. Look for requests to `/_next/data/{BUILD_ID}/fr/search.json`
6. Copy the new BUILD_ID and update `config.yaml`

### Language Support

The retriever supports queries in:
- **Arabic**: Most legal documents are in Arabic
- **French**: Official translations and some documents

## Dependencies

- `httpx==0.27.0` - Async HTTP client for API requests
- `asyncio` - Async/await support
- `langchain-core` - Document objects
- `langchain` - Tool integration

## Testing

Unit tests are available in `Researcher/tests/test_adala_retriever.py`:

```bash
cd Researcher
python -m unittest tests.test_adala_retriever
```

## Troubleshooting

### Search Returns Empty Results

1. **Check Build ID**: The Build ID may have changed
2. **Check Network**: Ensure connectivity to https://adala.justice.gov.ma
3. **Check Logs**: Review logs for specific error messages

### Timeout Errors

- The 30-second timeout may be too short for slow connections
- Can be adjusted in the `_async_search()` method

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Ensure httpx is installed: `pip install httpx==0.27.0`

## Example Queries

### Arabic Queries
```python
retriever.retrieve("طلاق")           # Divorce
retriever.retrieve("الزواج")          # Marriage
retriever.retrieve("الميراث")         # Inheritance
retriever.retrieve("العقود التجارية") # Commercial contracts
```

### French Queries
```python
retriever.retrieve("divorce")         # Divorce
retriever.retrieve("code civil")      # Civil code
retriever.retrieve("droit du travail") # Labor law
retriever.retrieve("contrats")        # Contracts
```

## Contributing

When making changes to the AdalaRetriever:

1. Follow the existing `BaseRetriever` pattern
2. Maintain comprehensive error handling
3. Update documentation
4. Add unit tests for new features
5. Validate with both Arabic and French queries

## License

This implementation is part of the legal_ai_backend project. See the main repository license for details.
