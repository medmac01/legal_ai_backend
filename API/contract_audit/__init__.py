"""
Contract Audit module for auditing contracts against Moroccan law.
Provides functionality for:
- Parsing contract documents (PDF, DOCX, TXT)
- Extracting individual clauses from contracts
- Retrieving relevant law articles from vector database
- Auditing clauses against Moroccan law using LLM
- Generating comprehensive audit reports
"""

from .contract_parser import ContractParser
from .clause_extractor import ClauseExtractor
from .law_retriever import LawRetriever
from .audit_service import AuditService
from .report_generator import ReportGenerator

__all__ = [
    "ContractParser",
    "ClauseExtractor", 
    "LawRetriever",
    "AuditService",
    "ReportGenerator"
]
