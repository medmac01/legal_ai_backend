"""
Description: 
    NDA Generator Service for generating Non-Disclosure Agreements using Google Gemini API.
    Provides functionality to generate NDA text and Word documents.
    
Author: Adapted from Streamlit app for FastAPI
Date  : 2025/01/07
"""

import os
import logging
from datetime import date
from io import BytesIO
from typing import Optional, Tuple

import google.generativeai as genai
from docx import Document

from .rules_engine import build_llm_prompt

# Get a logger instance - use a local logger to avoid circular imports
logger = logging.getLogger(__name__)


class NDAService:
    """
    Service class for generating Non-Disclosure Agreements using Google Gemini API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NDA Service.
        
        Args:
            api_key: Optional Gemini API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it as an environment variable or pass it to the constructor.")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Set up the model generation configuration
        self.generation_config = {
            "temperature": 0.3,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192,
        }
        
        # Initialize the Generative Model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite-preview-06-17",
            generation_config=self.generation_config
        )
        
        logger.info("NDAService initialized successfully")
    
    def generate_nda_text(self, user_inputs: dict) -> str:
        """
        Generate NDA text based on user inputs.
        
        Args:
            user_inputs: Dictionary containing NDA parameters:
                - client_name: Client company name (Party 1)
                - client_type_and_address: Client type and address
                - counterparty_name: Counterparty name (Party 2)
                - counterparty_type_and_address: Counterparty type and address
                - party_role: Which party is the client ("Receiving Party", "Disclosing Party", "Both (Bilateral)")
                - purpose: Purpose of disclosure
                - applicable_law: Governing law
                - language: Language of the contract
                - duration: Duration of confidentiality in months
                - effective_date: Effective date of the agreement
                - litigation: Dispute resolution mechanism
        
        Returns:
            Generated NDA text as a string.
        
        Raises:
            ValueError: If required fields are missing.
            Exception: If Gemini API call fails.
        """
        # Validate required fields
        required_fields = [
            "client_name", "client_type_and_address", 
            "counterparty_name", "counterparty_type_and_address",
            "party_role", "purpose", "applicable_law", 
            "language", "duration", "litigation"
        ]
        
        missing_fields = [field for field in required_fields if field not in user_inputs or not user_inputs[field]]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Determine nature of obligations based on party role
        if user_inputs["party_role"] != "Both (Bilateral)":
            user_inputs["nature_of_obligations"] = "Unilateral"
        else:
            user_inputs["nature_of_obligations"] = "Bilateral"
        
        # Set default effective date if not provided
        if "effective_date" not in user_inputs or not user_inputs["effective_date"]:
            user_inputs["effective_date"] = date.today().isoformat()
        
        # Build the prompt using the rules engine
        prompt = build_llm_prompt(user_inputs)
        
        logger.info(f"Generating NDA for client: {user_inputs['client_name']}, counterparty: {user_inputs['counterparty_name']}")
        
        try:
            response = self.model.generate_content(prompt)
            nda_text = response.text
            logger.info("NDA text generated successfully")
            return nda_text
        except Exception as e:
            logger.error(f"Error generating NDA text: {e}")
            raise Exception(f"Failed to generate NDA: {str(e)}")
    
    def create_docx(self, nda_text: str, client_name: str = "", counterparty_name: str = "") -> bytes:
        """
        Create a Word document from NDA text.
        
        Args:
            nda_text: The generated NDA text.
            client_name: Optional client name for filename generation.
            counterparty_name: Optional counterparty name for filename generation.
        
        Returns:
            Word document as bytes.
        """
        doc = Document()
        doc.add_heading('Non-Disclosure Agreement', 0)
        
        # Simple parsing: add paragraphs based on newlines
        for para in nda_text.split('\n'):
            # Check if the line is likely a heading (e.g., "Article 1. Definitions")
            stripped = para.strip()
            if stripped.lower().startswith(("article", "section")) or stripped.endswith(":"):
                doc.add_heading(stripped, level=2)
            elif stripped:  # Avoid adding empty paragraphs
                doc.add_paragraph(para)
        
        # Save the document to a byte stream
        bio = BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        logger.info("Word document created successfully")
        return bio.getvalue()
    
    def generate_nda_with_docx(self, user_inputs: dict) -> Tuple[str, bytes]:
        """
        Generate NDA text and create a Word document.
        
        Args:
            user_inputs: Dictionary containing NDA parameters.
        
        Returns:
            Tuple of (nda_text, docx_bytes).
        """
        nda_text = self.generate_nda_text(user_inputs)
        docx_bytes = self.create_docx(
            nda_text, 
            user_inputs.get("client_name", ""),
            user_inputs.get("counterparty_name", "")
        )
        return nda_text, docx_bytes
