"""
Description: 
    Celery task definitions for asynchronous processing of PAKTON framework operations.
    Includes tasks for interrogation, research, and document indexing with retry logic
    and error handling for distributed task execution.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

from .config import Config
from celery import Celery
import asyncio
import os
import tempfile
import traceback
from .response_template import create_task_response
from .database import get_db_session, ConversationRepository

from .logger import logger
logger.info("Celery Worker initialized.")

# Initialize Celery
celery_app = Celery(
    Config.SERVICE_NAME,
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

celery_app.conf.task_routes = Config.TASK_ROUTES

# Ensure Celery does not override the root logger and uses the custom log format
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_log_format = "[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s"

# Global Archivist instance - initialized once per worker
archivist = None

def get_archivist():
    """Get or create the global Archivist instance"""
    global archivist
    if archivist is None:
        from Archivist import Archivist
        archivist = Archivist()
        logger.info("Archivist instance created")
    return archivist

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.interrogation', bind=True, default_retry_delay=5, max_retries=3)
def async_interrogation(self, userQuery: str, userContext: str = "", userInstructions: str = ""):
    """Asynchronous interrogation for given query."""
    logger.debug(f"Task started: async_interrogation - userQuery: {userQuery}, userContext: {userContext}, userInstructions: {userInstructions}")
    try:
        from Interrogator import Interrogator

        interrogator = Interrogator(config = {"run_name": "Example Interrogation"})
        results = interrogator.interrogation(userQuery=userQuery, userContext=userContext, userInstructions=userInstructions)
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Interrogation completed",
            data={"report": results["report"], "conclusion": results["conclusion"]}
        )
    except Exception as e:
        logger.error(f"Error in async_interrogation: {e}")

        if self.request.retries < self.max_retries:  # Check retry limit
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)  # Retry after 5 seconds

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to interrogate: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.process_query', bind=True, default_retry_delay=5, max_retries=3)
def async_process_query(self, query: str, thread_id: str = None, config: dict = None, user_email: str = None):
    """
    Asynchronous query processing using Archivist.

    Args:
        query (str): The user query to process.
        thread_id (str, optional): Thread ID for conversation continuity.
        config (dict, optional): Configuration dictionary containing model/agent settings.
        user_email (str, optional): User's email for conversation tracking.

    Returns:
        dict: JSON response with query result.

        **Success Response:**
        ```json
        {
            "status": "SUCCESS",
            "task_id": "<celery_task_id>",
            "message": "Query processed successfully",
            "data": {
                "thread_id": "<thread_id>",
                "response": "<response_content>",
                "messages": [...]
            }
        }
        ```

        **Failure Response:**
        ```json
        {
            "status": "FAILURE",
            "task_id": "<celery_task_id>",
            "message": "Failed to process query: <error_message>"
        }
        ```
    """
    logger.debug(f"Task started: async_process_query - query: {query}, thread_id: {thread_id}, user_email: {user_email}")
    
    try:
        archivist = get_archivist()
        
        async def process_query_async():
            async with archivist:
                result = await archivist.process_query(query, thread_id, config)
                logger.debug(f"Task completed: process_query_async - result: {result}")
                return result
        
        # Run the async function synchronously
        result = asyncio.run(process_query_async())

        logger.debug(f"Task completed: async_process_query run - result: {result}")
        
        # Track conversation in database if user is authenticated
        if user_email and result.get('thread_id'):
            try:
                with get_db_session() as db:
                    thread_id = result['thread_id']
                    
                    # Get or create conversation
                    conversation = ConversationRepository.get_by_thread_id(db, thread_id)
                    if not conversation:
                        # Use the first 500 characters of the query as the title
                        title = query[:500] if len(query) <= 500 else query[:497] + "..."
                        ConversationRepository.create(
                            db=db,
                            thread_id=thread_id,
                            user_email=user_email,
                            title=title
                        )
                    
                    # Update message count and timestamp (count only human and AI messages)
                    messages = result['response']['messages']
                    message_count = ConversationRepository.count_human_and_ai_messages(messages)
                    ConversationRepository.update_message_count_and_timestamp(
                        db=db,
                        thread_id=thread_id,
                        message_count=message_count
                    )
                    
                    logger.info(f"Conversation tracked for user {user_email}, thread {thread_id}")
            except Exception as db_error:
                logger.error(f"Failed to track conversation: {str(db_error)}")
                # Continue despite database error
        
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Query processed successfully",
            data={
                "thread_id": result['thread_id'],
                "response_content": result['response']['messages'][-1].content,
            }
        )
        
    except Exception as e:
        logger.error(f"Error in async_process_query: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to process query: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.index_document', bind=True, default_retry_delay=5, max_retries=3)
def async_index_document(self, file_content: bytes, metadata: dict):
    """
    Asynchronous indexing of a document using Archivist.

    Args:
        file_content (bytes): The binary content of the document.
        metadata (dict): Metadata including the filename.

    Returns:
        dict: JSON response indicating indexing status.

        **Success Response:**
        ```json
        {
            "status": "SUCCESS",
            "task_id": "<celery_task_id>",
            "message": "Indexing Document completed"
        }
        ```

        **Failure Response:**
        ```json
        {
            "status": "FAILURE",
            "task_id": "<celery_task_id>",
            "message": "Failed to index document: <error_message>"
        }
        ```
    """
    logger.debug(f"Task started: index_document - metadata: {metadata}")
    try:
        from Archivist import Archivist

        # Use VectorDB with Ollama embeddings for document indexing
        archivist = Archivist(config = {
            "enable_vectordb": True,   # Using ChromaDB with Ollama embeddings
            "enable_lightrag": False,  # LightRAG disabled (no Docker service)
            "run_name": "Example Index"
        })
        # Validate filename exists in metadata
        if 'filename' not in metadata:
            raise ValueError("Filename must be provided in metadata")
        
        filename = metadata['filename']
        file_extension = os.path.splitext(filename)[-1].lower()

        if file_extension not in ['.docx', '.pdf', '.txt']:
            raise ValueError("Unsupported file type. Only .docx , .pdf and .txt are allowed.")

        fd, temp_file_path = tempfile.mkstemp(suffix=file_extension)

        try:
            
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(file_content)
                temp_file.flush()  # Ensure file is written to disk before using it
                logger.info(f"Temporary file created: {temp_file_path}")

                archivist.index(filePath=temp_file_path)

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Temporary file deleted: {temp_file_path}")

        logger.info(f"Indexing complete for matadata: {metadata}")
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Indexing Document completed"
        )
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=str(ve)
        )
    except Exception as e:
        logger.error(f"Error in index_document: {e}")

        if self.request.retries < self.max_retries:  
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5) 
        
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to index document: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.research', bind=True, default_retry_delay=5, max_retries=3)
def async_research(self, query: str, instructions: str = "", agent_config: dict = None, search_config: dict = None):
    """Asynchronous research for given query using the Researcher agent."""
    logger.debug(f"Task started: async_research - query: {query}, instructions: {instructions}, agent_config: {agent_config}, search_config: {search_config}")
    try:
        from Researcher import Researcher

        researcher = Researcher(config=agent_config or {})
        results = researcher.search(query=query, instructions=instructions, config=search_config or {})
        
        # Convert Document objects to dictionaries
        chunks = []
        if search_config and search_config.get("return_chunks", False) and "responseContext" in results:
            for doc in results.get("responseContext", []):
                # Extract the page_content and metadata from each Document
                if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                    chunks.append({
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    })
                else:
                    # If the structure is different, try to convert the entire object to dict
                    try:
                        chunks.append(dict(doc))
                    except (TypeError, ValueError):
                        # Last resort: convert to string
                        chunks.append({"content": str(doc)})
        
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Research completed",
            data={"response": results.get("response", ""), "chunks": chunks}
        )
    except Exception as e:
        logger.error(f"Error in async_research: {e}")

        if self.request.retries < self.max_retries:  # Check retry limit
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)  # Retry after 5 seconds

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to research: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.ingest_law_chunks', bind=True, default_retry_delay=5, max_retries=3)
def async_ingest_law_chunks(self, chunks_file_path: str = None):
    """
    Asynchronous ingestion of pre-chunked law data from a JSON file into the vector database.

    This task reads chunks from a JSON file (default: API/docs/chunks.json) and ingests them
    into the vector database for later retrieval during interrogation. Each chunk contains
    legal text with metadata (law_name, article, article_number, source_file).

    Args:
        chunks_file_path (str, optional): Path to the JSON file containing law chunks.
            Defaults to '/app/API/docs/chunks.json' in Docker or 'API/docs/chunks.json' locally.

    Returns:
        dict: JSON response indicating ingestion status.

        **Success Response:**
        ```json
        {
            "status": "SUCCESS",
            "task_id": "<celery_task_id>",
            "message": "Law chunks ingested successfully",
            "data": {
                "chunks_count": 100
            }
        }
        ```

        **Failure Response:**
        ```json
        {
            "status": "FAILURE",
            "task_id": "<celery_task_id>",
            "message": "Failed to ingest law chunks: <error_message>"
        }
        ```
    """
    import json
    from langchain_core.documents import Document
    
    logger.debug(f"Task started: ingest_law_chunks - chunks_file_path: {chunks_file_path}")
    
    try:
        from Archivist import Archivist
        from Archivist.indexers import VectorDBIndexer
        
        # Default path - check both Docker and local paths
        if chunks_file_path is None:
            # Try Docker path first, then local path
            docker_path = '/app/API/docs/chunks.json'
            local_path = os.path.join(os.path.dirname(__file__), 'docs', 'chunks.json')
            
            if os.path.exists(docker_path):
                chunks_file_path = docker_path
            elif os.path.exists(local_path):
                chunks_file_path = local_path
            else:
                raise FileNotFoundError(f"Chunks file not found at {docker_path} or {local_path}")
        
        logger.info(f"Loading law chunks from: {chunks_file_path}")
        
        # Load chunks from JSON file
        with open(chunks_file_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        logger.info(f"Loaded {len(chunks_data)} chunks from file")
        
        # Convert chunks to LangChain Documents
        documents = []
        for chunk in chunks_data:
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            # Add source type to distinguish law documents from user documents
            metadata['source_type'] = 'law_reference'
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        logger.info(f"Converted {len(documents)} chunks to Documents")
        
        # Initialize VectorDB indexer and ingest documents
        # Note: We initialize a new indexer to ensure we're using the correct configuration
        indexer = VectorDBIndexer()
        
        # Index the documents (this will add to the existing collection)
        # We need to modify the index method to not delete all existing documents
        indexer.index_without_delete(documents)
        
        logger.info(f"Successfully ingested {len(documents)} law chunks into vector database")
        
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Law chunks ingested successfully",
            data={"chunks_count": len(documents)}
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=str(e)
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Invalid JSON format in chunks file: {e}"
        )
    except Exception as e:
        logger.error(f"Error in ingest_law_chunks: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to ingest law chunks: {e}"
        )

# Celery worker startup hook
@celery_app.on_after_configure.connect
def setup_worker_initialization(sender, **kwargs):
    """Initialize the archivist instance when a worker starts"""
    logger.info("Setting up worker initialization...")
    try:
        get_archivist()
        logger.info("Worker initialized successfully with archivist instance")
    except Exception as e:
        logger.error(f"Failed to initialize worker: {e}")