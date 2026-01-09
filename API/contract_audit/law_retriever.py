"""
Description:
    Law Retriever for querying vector database for relevant Moroccan law articles.
    Reuses the existing VectorDBRetriever from the Researcher module.

Author: Contract Audit Module
Date: 2025/01/09
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LawRetriever:
    """
    Retriever for finding relevant Moroccan law articles from the vector database.
    
    Uses the existing vector database infrastructure to retrieve law articles
    that are relevant to contract clauses being audited.
    """
    
    def __init__(self, top_k: int = 5, similarity_threshold: float = 0.0):
        """
        Initialize the Law Retriever.
        
        Args:
            top_k: Maximum number of law articles to retrieve per query
            similarity_threshold: Minimum similarity score threshold
        """
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self._retriever = None
        
        logger.info(f"Initializing LawRetriever with top_k={top_k}, "
                   f"similarity_threshold={similarity_threshold}")
    
    def _get_retriever(self):
        """
        Lazy initialization of the vector database retriever.
        
        Returns:
            VectorDBRetriever instance
        """
        if self._retriever is None:
            try:
                from Researcher.retrievers import VectorDBRetriever
                self._retriever = VectorDBRetriever()
                logger.info("VectorDBRetriever initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to import VectorDBRetriever: {e}")
                raise ImportError(
                    "VectorDBRetriever not available. "
                    "Ensure Researcher module is properly installed."
                ) from e
            except Exception as e:
                logger.error(f"Failed to initialize VectorDBRetriever: {e}")
                raise
        
        return self._retriever
    
    def retrieve_relevant_laws(
        self, 
        clause_content: str,
        clause_category: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant law articles for a given clause.
        
        Args:
            clause_content: Text content of the clause to analyze
            clause_category: Optional category to help focus the search
            top_k: Override default top_k for this query
            
        Returns:
            List of dictionaries containing law article information:
            - content: The text of the law article
            - metadata: Associated metadata (law_name, article, etc.)
            - score: Similarity score
        """
        retriever = self._get_retriever()
        
        # Build query - optionally include category context
        query = clause_content
        if clause_category and clause_category != "general":
            # Add category context to improve retrieval
            category_context = f"[{clause_category.upper()} CLAUSE] "
            query = category_context + clause_content[:500]  # Limit query length
        
        k = top_k or self.top_k
        
        logger.info(f"Retrieving laws for clause (category: {clause_category})")
        logger.debug(f"Query length: {len(query)} characters")
        
        try:
            # Use the vectordb retriever to get relevant documents
            documents = retriever.retrieve(
                query, 
                k=k, 
                similarity_threshold=self.similarity_threshold
            )
            
            # Filter for law reference documents only
            law_results = []
            for doc in documents:
                metadata = doc.metadata or {}
                
                # Filter for law reference source type if available
                source_type = metadata.get("source_type", "")
                
                law_results.append({
                    "content": doc.page_content,
                    "metadata": metadata,
                    "score": metadata.get("vectordb_similarity_score", 0.0),
                    "law_name": metadata.get("law_name", "Unknown Law"),
                    "article": metadata.get("article", ""),
                    "article_number": metadata.get("article_number", ""),
                    "source_file": metadata.get("source_file", "")
                })
            
            logger.info(f"Retrieved {len(law_results)} relevant law articles")
            return law_results
            
        except Exception as e:
            logger.error(f"Error retrieving laws: {e}")
            return []
    
    def retrieve_laws_batch(
        self, 
        clauses: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant laws for multiple clauses.
        
        Args:
            clauses: List of clause dictionaries with 'content' and optionally 'category'
            top_k: Override default top_k for all queries
            
        Returns:
            Dictionary mapping clause index to list of relevant laws
        """
        results = {}
        
        for i, clause in enumerate(clauses):
            content = clause.get("content", "")
            category = clause.get("category", None)
            
            if not content:
                results[str(i)] = []
                continue
            
            laws = self.retrieve_relevant_laws(
                content, 
                clause_category=category,
                top_k=top_k
            )
            results[str(i)] = laws
        
        return results
    
    def format_laws_for_prompt(
        self, 
        laws: List[Dict[str, Any]],
        max_length: int = 2000
    ) -> str:
        """
        Format retrieved laws into a string suitable for LLM prompts.
        
        Args:
            laws: List of law article dictionaries
            max_length: Maximum total length of formatted output
            
        Returns:
            Formatted string of relevant laws
        """
        if not laws:
            return "No relevant Moroccan law articles found."
        
        formatted_parts = []
        current_length = 0
        
        for i, law in enumerate(laws):
            law_name = law.get("law_name", "Unknown Law")
            article = law.get("article", "")
            article_num = law.get("article_number", "")
            content = law.get("content", "")
            score = law.get("score", 0.0)
            
            # Build header
            header = f"**{law_name}"
            if article:
                header += f" - {article}"
            elif article_num:
                header += f" - Article {article_num}"
            header += f"** (relevance: {score:.2f})"
            
            # Truncate content if needed
            available_length = max_length - current_length - len(header) - 20
            if available_length <= 0:
                break
            
            if len(content) > available_length:
                content = content[:available_length] + "..."
            
            formatted = f"{header}\n{content}"
            formatted_parts.append(formatted)
            current_length += len(formatted) + 2
            
            if current_length >= max_length:
                break
        
        return "\n\n".join(formatted_parts)
