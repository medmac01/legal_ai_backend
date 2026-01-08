"""
Description:
Adala Justice website retriever implementation for searching and retrieving Moroccan legal 
documents (laws, decrees, regulations) from https://adala.justice.gov.ma. Integrates with
the Adala Justice API to fetch structured legal content and converts results into 
LangChain Document objects.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10

Technical Implementation:
Adala Retriever

### Theoretical Background:
The **Adala retriever** enables AI models to **fetch Moroccan legal documents** from the 
official Adala Justice website by integrating with their API. This provides access to:
- Laws (Lois)
- Decrees (Décrets)
- Regulations (Règlements)
- Other official legal documents

### How Adala Retrieval Works:
1. **User Query**:
   - The user provides a query (e.g., "طلاق" or "divorce laws").
   
2. **API Integration**:
   - The retriever sends the query to the Adala Justice API endpoint.
   - The API performs a search and retrieves **matching legal documents**.

3. **Processing Search Results**:
   - The retriever extracts **title, type, law_type, date, download_url** from results.
   - Converts them into **LangChain Document objects** for structured retrieval.

4. **Use Cases**:
   - **Legal research** (e.g., "Find laws about family court procedures").
   - **Document retrieval** (e.g., "Get the latest labor law decree").
   - **AI-powered legal assistance** (e.g., "What regulations cover commercial contracts?").

This module implements **Adala Justice retrieval**, allowing **real-time legal document 
retrieval** from Morocco's official justice website.

Author: Petros Raptopoulos (petrosrapto@gmail.com)
Date: 2026/01/08
"""

import asyncio
import traceback
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
import httpx

from .base import BaseRetriever
from Researcher.utils import logger  # Import the logger
from Researcher.utils import config  # Import the Config loader

from langchain.tools import Tool


class AdalaRetriever(BaseRetriever):
    """
    A retriever that searches the Adala Justice website for Moroccan legal documents.

    Instead of relying on **general web search**, this retriever **fetches legal documents** 
    from Morocco's official justice portal to provide accurate and authoritative legal information.

    Features:
    - **Supports Adala Justice API** for legal document search.
    - **Configurable maximum results** for fine-tuned retrieval.
    - **Structured Output**: Converts legal documents into LangChain Document objects.
    - **Supports both Arabic and French** search terms.

    Attributes:
        base_url (str): The base URL of the Adala Justice website.
        build_id (str): The Next.js build ID for API endpoints (may need updates on site redeployment).
        max_results (int): The maximum number of search results to retrieve.
    """

    def __init__(self):
        """
        Initializes the **Adala retriever** using parameters from `config.yaml`.

        - **API Configuration**: Uses Adala Justice API endpoint.
        - **Configurable Settings**: Allows customization of search behavior.
        - **Build ID Handling**: Manages Next.js build ID for API compatibility.

        Raises:
            ValueError: If required configuration is missing.
            Exception: If an error occurs during initialization.
        """
        try:
            # Load Adala retriever settings
            adala_config = config.get("retrievers.adala", {})

            self.base_url = adala_config.get("base_url", "https://adala.justice.gov.ma")
            self.build_id = adala_config.get("build_id", "THP5ZL1eNCinRAZ1hWfN0")
            self.max_results = adala_config.get("max_results", 5)

            # Log retriever configuration
            logger.info("Initializing AdalaRetriever with config: %s", adala_config)
            logger.warning(
                "Note: The build_id may change if the Adala website is redeployed. "
                "If searches fail, the build_id in config.yaml may need to be updated."
            )

        except Exception as e:
            logger.error("Error initializing AdalaRetriever: %s", str(e))
            logger.debug(traceback.format_exc())

    @property
    def name(self) -> str:
        """
        Returns the unique name identifier of this retriever.

        Returns:
            str: The retriever's name identifier.
        """
        return "adala_retriever"

    async def _async_search(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Performs an asynchronous search to the Adala Justice API.

        Args:
            keyword (str): The search term (supports Arabic and French).
            limit (int): Maximum number of results to retrieve.

        Returns:
            List[Dict[str, Any]]: List of search result dictionaries.
        """
        try:
            # Construct the API endpoint URL
            api_url = f"{self.base_url}/_next/data/{self.build_id}/fr/search.json"
            
            # Prepare search parameters
            params = {
                "term": keyword,
            }
            
            # Make async HTTP request with timeout
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Sending request to Adala API: %s with params: %s", api_url, params)
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Extract search results from nested structure
                search_results = (
                    data.get("pageProps", {})
                    .get("searchResult", {})
                    .get("data", [])
                )
                
                # Limit results
                limited_results = search_results[:limit]
                
                logger.info("Retrieved %d results from Adala API", len(limited_results))
                return limited_results
                
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error from Adala API: %s", str(e))
            logger.debug(traceback.format_exc())
            return []
        except httpx.RequestError as e:
            logger.error("Request error to Adala API: %s", str(e))
            logger.debug(traceback.format_exc())
            return []
        except Exception as e:
            logger.error("Unexpected error in Adala API search: %s", str(e))
            logger.debug(traceback.format_exc())
            return []

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieves **Moroccan legal documents** from the Adala Justice website.

        This method:
        - Sends the **query** to the Adala Justice API.
        - Retrieves **legal documents** with metadata (title, type, date, download URL).
        - Converts results into **LangChain Document objects** for structured retrieval.

        Args:
            query (str): The input search query (Arabic or French).
            **kwargs: Additional parameters, such as `max_results` for limiting results.

        Returns:
            List[Document]: A **list of retrieved legal documents**.

        Logs:
            - Logs query execution and retrieval success.
            - Logs the number of documents retrieved.
        """
        try:
            # Override max results if provided
            max_results = kwargs.get("max_results", self.max_results)

            logger.info("Retrieving Adala documents for query: %s", query)

            # Handle async search in sync context
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async search
            search_results = asyncio.run(self._async_search(query, max_results))

            logger.info("Successfully retrieved %d Adala documents", len(search_results))

            # Convert search results to LangChain Document format
            documents = []
            for result in search_results:
                # Extract document fields
                title = result.get("title", "")
                document_type = result.get("type", "")
                law_type = result.get("law_type", "")
                date = result.get("date", "")
                relative_path = result.get("relative_path", "")
                
                # Construct download URL
                download_url = ""
                if relative_path:
                    download_url = f"{self.base_url}{relative_path}"
                
                # Create page content with structured information
                page_content_parts = []
                if title:
                    page_content_parts.append(f"Title: {title}")
                if document_type:
                    page_content_parts.append(f"Document Type: {document_type}")
                if law_type:
                    page_content_parts.append(f"Law Type: {law_type}")
                if date:
                    page_content_parts.append(f"Date: {date}")
                if download_url:
                    page_content_parts.append(f"Download URL: {download_url}")
                
                page_content = "\n".join(page_content_parts)
                
                # Create Document object
                doc = Document(
                    page_content=page_content,
                    metadata={
                        "source": download_url,
                        "title": title,
                        "type": document_type,
                        "law_type": law_type,
                        "date": date,
                        "relative_path": relative_path,
                        "retriever": self.name
                    }
                )
                documents.append(doc)

            logger.info("Documents retrieved: %s", str(documents))
            
            return documents

        except Exception as e:
            logger.error("Error retrieving from Adala: %s", str(e))
            logger.debug(traceback.format_exc())
            return []

    @property
    def tool(self) -> Tool:
        """
        Returns the AdalaRetriever as a LangChain Tool.

        This tool allows agents to search for Moroccan legal documents from the official 
        Adala Justice website. Use it when:
        
        - A query requires information about Moroccan laws, decrees, or regulations.
        - You need to retrieve official legal documents from Morocco's justice system.
        - The model needs authoritative legal information specific to Morocco.
        - A user asks about Moroccan legal topics (in Arabic or French).

        This tool helps bridge knowledge gaps by searching official legal documents 
        whenever Moroccan legal information is needed.
        """
        return Tool(
            name="AdalaSearch",
            func=lambda query: self.retrieve(query),
            description=(
                "Searches the Adala Justice website for Moroccan legal documents "
                "(laws, decrees, regulations). Use this when you need official legal "
                "information from Morocco's justice system. Supports Arabic and French queries."
            )
        )
