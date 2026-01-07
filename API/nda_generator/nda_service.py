"""
Description: 
    NDA Generator Service for generating Non-Disclosure Agreements.
    Uses Jinja2 templates for initial NDA generation and Google Gemini API
    for NDA modification/customization.
    
Author: Adapted from Streamlit app for FastAPI
Date  : 2025/01/07
"""

import os
import logging
from datetime import date
from io import BytesIO
from typing import Optional, Tuple, List, Dict, Any

import google.generativeai as genai
from docx import Document

from .j2_engine import render_template

# Get a logger instance - use a local logger to avoid circular imports
logger = logging.getLogger(__name__)

# System prompt for the chat/modification phase
CHAT_SYSTEM_PROMPT = """
You are a precise legal contract editor. Your task is to modify the provided Non-Disclosure Agreement (NDA) based *only* on the user's explicit request.

**Your Core Directives:**
1.  **Strict Adherence:** Only make the change requested by the user. Do not add, remove, or alter any other part of the contract.
2.  **Maintain Professional Tone:** Ensure the wording of your modifications is formal, professional, and consistent with the existing legal language of the document.
3.  **Output the Full Document:** After making the requested change, you MUST return the entire, complete, and updated text of the NDA. Do not provide summaries, explanations, or confirmation messages. Your output should be only the contract text itself.
4.  **No Commentary:** Do not include phrases like "Here is the updated version:", "I have made the requested change:", or any other conversational text. The output must be ready to be copied and pasted directly into a legal document.
5.  **If Unclear, Ask:** If the user's request is ambiguous, ask for clarification instead of guessing. For example: "Could you please specify which clause you are referring to for the 'indemnity' change?"

Your role is to act as a silent, precise editing tool. The user provides an instruction, you provide the fully updated document.
"""


class NDAService:
    """
    Service class for generating Non-Disclosure Agreements.
    Uses Jinja2 templates for initial generation and Google Gemini API for modifications.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NDA Service.
        
        Args:
            api_key: Optional Gemini API key. If not provided, will try to get from environment.
                     API key is only required for modification features, not for template-based generation.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        
        # Only initialize Gemini if API key is available (for modification features)
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                
                # Set up the model generation configuration
                self.generation_config = {
                    "temperature": 0.2,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 8192,
                }
                
                # Initialize the Generative Model with system instruction for modifications
                self.model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash-lite-preview-06-17",
                    generation_config=self.generation_config,
                    system_instruction=CHAT_SYSTEM_PROMPT
                )
                
                logger.info("NDAService initialized with Gemini API for modifications")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini API: {e}. Modification features will be unavailable.")
                self.model = None
        else:
            logger.info("NDAService initialized without Gemini API (template-based generation only)")
    
    def generate_nda_text(self, user_inputs: dict) -> str:
        """
        Generate NDA text based on user inputs using Jinja2 templates.
        
        Args:
            user_inputs: Dictionary containing NDA parameters:
                - first_party: First party company name
                - first_party_address: Address of the first party
                - first_party_incorporation_state: Incorporation state of the first party
                - first_party_representative: Representative of the first party
                - first_party_registration_number: Registration number of the first party
                - first_party_role: Role of first party ("Receiving Party", "Disclosing Party", "Both (Bilateral)")
                - second_party: Second party company name
                - second_party_address: Address of the second party
                - second_party_incorporation_state: Incorporation state of the second party
                - second_party_representative: Representative of the second party
                - second_party_registration_number: Registration number of the second party
                - purpose: Purpose of disclosure
                - applicable_law: Governing law
                - language: Language of the contract
                - duration: Duration of confidentiality in months
                - date: Effective date of the agreement (ISO format)
                - litigation: Dispute resolution mechanism
        
        Returns:
            Generated NDA text as a string.
        
        Raises:
            ValueError: If required fields are missing.
        """
        # Set default date if not provided
        if "date" not in user_inputs or not user_inputs["date"]:
            user_inputs["date"] = date.today().strftime("%Y-%m-%d")
        
        logger.info(f"Generating NDA for first_party: {user_inputs.get('first_party', 'N/A')}, "
                   f"second_party: {user_inputs.get('second_party', 'N/A')}")
        
        try:
            nda_text = render_template(user_inputs)
            logger.info("NDA text generated successfully using Jinja2 template")
            return nda_text
        except ValueError as e:
            logger.error(f"Validation error generating NDA: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating NDA text: {e}")
            raise Exception(f"Failed to generate NDA: {str(e)}")
    
    def modify_nda(self, nda_text: str, modification_request: str, 
                   conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Modify an existing NDA using Google Gemini API.
        
        Args:
            nda_text: The current NDA text to modify.
            modification_request: User's request for how to modify the NDA.
            conversation_history: Optional list of previous conversation messages
                                  for context. Each message is a dict with 'role' and 'parts' keys.
        
        Returns:
            Modified NDA text as a string.
        
        Raises:
            ValueError: If Gemini API is not available.
            Exception: If Gemini API call fails.
        """
        if not self.model:
            raise ValueError("Gemini API is not available. Please provide GEMINI_API_KEY to enable modification features.")
        
        # Build conversation history if provided
        history = []
        if conversation_history:
            history = conversation_history
        else:
            # Initialize with the current NDA as the first model response
            history = [
                {"role": "user", "parts": ["Please review this NDA."]},
                {"role": "model", "parts": [nda_text]}
            ]
        
        logger.info(f"Modifying NDA with request: {modification_request[:100]}...")
        
        try:
            # Start a chat session with history
            chat_session = self.model.start_chat(history=history)
            
            # Send the modification request
            response = chat_session.send_message(modification_request)
            modified_text = response.text
            
            logger.info("NDA modified successfully")
            return modified_text
        except Exception as e:
            logger.error(f"Error modifying NDA: {e}")
            raise Exception(f"Failed to modify NDA: {str(e)}")
    
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
            user_inputs.get("first_party", ""),
            user_inputs.get("second_party", "")
        )
        return nda_text, docx_bytes
