"""
Description:
    Clause Extractor for splitting contracts into individual clauses.
    Identifies and categorizes clauses based on common legal patterns.

Author: Contract Audit Module
Date: 2025/01/09
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Clause:
    """
    Represents an individual clause extracted from a contract.
    
    Attributes:
        number: Clause number/identifier (e.g., "1", "1.1", "Article 1")
        title: Clause title/heading if available
        content: Full text content of the clause
        category: Categorization of the clause type
        start_position: Character position where clause starts in original text
        end_position: Character position where clause ends in original text
    """
    number: str
    title: str
    content: str
    category: str = "general"
    start_position: int = 0
    end_position: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert clause to dictionary representation."""
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "metadata": self.metadata
        }


class ClauseExtractor:
    """
    Extracts and categorizes clauses from contract text.
    
    Supports various clause numbering formats:
    - Article X
    - Section X
    - X. (numbered)
    - X.Y (sub-numbered)
    - Roman numerals (I, II, III)
    """
    
    # Common clause category patterns
    CATEGORY_PATTERNS = {
        "confidentiality": [
            r"confidential", r"non-disclosure", r"proprietary", r"secret"
        ],
        "definitions": [
            r"definition", r"interpretation", r"meaning"
        ],
        "obligations": [
            r"obligation", r"duty", r"shall", r"must", r"responsibility"
        ],
        "termination": [
            r"termination", r"expir", r"end of agreement", r"cancellation"
        ],
        "liability": [
            r"liability", r"indemnif", r"damage", r"loss", r"negligence"
        ],
        "intellectual_property": [
            r"intellectual property", r"ip", r"patent", r"trademark", 
            r"copyright", r"license"
        ],
        "dispute_resolution": [
            r"dispute", r"arbitration", r"mediation", r"litigation", 
            r"jurisdiction", r"governing law"
        ],
        "payment": [
            r"payment", r"fee", r"compensation", r"remuneration", r"price"
        ],
        "warranty": [
            r"warranty", r"guarantee", r"representation"
        ],
        "force_majeure": [
            r"force majeure", r"act of god", r"unforeseen"
        ],
        "assignment": [
            r"assignment", r"transfer", r"delegation"
        ],
        "notice": [
            r"notice", r"notification", r"communication"
        ],
        "amendment": [
            r"amendment", r"modification", r"change"
        ],
        "severability": [
            r"severability", r"separability", r"invalid provision"
        ],
        "entire_agreement": [
            r"entire agreement", r"whole agreement", r"complete agreement"
        ],
        "data_protection": [
            r"data protection", r"personal data", r"privacy", r"gdpr"
        ]
    }
    
    # Patterns for detecting clause headers
    CLAUSE_HEADER_PATTERNS = [
        # Article X: Title or Article X. Title
        r"(?P<number>Article\s+\d+[\.\:]?\s*(?:\d+[\.\:]?)*)\s*[:\-]?\s*(?P<title>[^\n]+)?",
        # Section X: Title or Section X. Title  
        r"(?P<number>Section\s+\d+[\.\:]?\s*(?:\d+[\.\:]?)*)\s*[:\-]?\s*(?P<title>[^\n]+)?",
        # X. Title (numbered sections)
        r"(?P<number>\d+(?:\.\d+)*[\.\)])\s+(?P<title>[A-Z][^\n]+)",
        # Roman numerals (I., II., III., etc.)
        r"(?P<number>(?:X{0,3})(?:IX|IV|V?I{0,3})[\.\)])\s+(?P<title>[A-Z][^\n]+)",
        # Clause X: Title
        r"(?P<number>Clause\s+\d+[\.\:]?\s*(?:\d+[\.\:]?)*)\s*[:\-]?\s*(?P<title>[^\n]+)?",
    ]
    
    def __init__(self):
        """Initialize the clause extractor."""
        self._compiled_header_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
            for pattern in self.CLAUSE_HEADER_PATTERNS
        ]
        self._compiled_category_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in self.CATEGORY_PATTERNS.items()
        }
    
    def extract_clauses(self, contract_text: str) -> List[Clause]:
        """
        Extract clauses from contract text.
        
        Args:
            contract_text: Full text of the contract
            
        Returns:
            List of Clause objects
        """
        if not contract_text or not contract_text.strip():
            logger.warning("Empty contract text provided")
            return []
        
        logger.info("Extracting clauses from contract text")
        
        # Find all clause headers with their positions
        clause_positions = self._find_clause_positions(contract_text)
        
        if not clause_positions:
            logger.info("No structured clauses found, treating entire text as single clause")
            return [Clause(
                number="1",
                title="Full Contract",
                content=contract_text.strip(),
                category=self._categorize_text(contract_text),
                start_position=0,
                end_position=len(contract_text)
            )]
        
        # Extract clause content based on positions
        clauses = []
        for i, (start_pos, number, title) in enumerate(clause_positions):
            # Determine end position (start of next clause or end of document)
            if i + 1 < len(clause_positions):
                end_pos = clause_positions[i + 1][0]
            else:
                end_pos = len(contract_text)
            
            content = contract_text[start_pos:end_pos].strip()
            category = self._categorize_text(content, title)
            
            clause = Clause(
                number=number.strip(),
                title=title.strip() if title else "",
                content=content,
                category=category,
                start_position=start_pos,
                end_position=end_pos
            )
            clauses.append(clause)
        
        logger.info(f"Extracted {len(clauses)} clauses from contract")
        return clauses
    
    def _find_clause_positions(self, text: str) -> List[tuple]:
        """
        Find positions of all clause headers in text.
        
        Returns:
            List of tuples (position, number, title)
        """
        positions = []
        
        for pattern in self._compiled_header_patterns:
            for match in pattern.finditer(text):
                number = match.group("number")
                title = match.group("title") if "title" in match.groupdict() else ""
                positions.append((match.start(), number, title or ""))
        
        # Sort by position and remove duplicates
        positions = sorted(set(positions), key=lambda x: x[0])
        
        # Remove overlapping matches (keep earliest)
        cleaned_positions = []
        last_end = -1
        for pos, number, title in positions:
            if pos >= last_end:
                cleaned_positions.append((pos, number, title))
                # Estimate end position based on header length
                last_end = pos + len(number) + len(title) + 10
        
        return cleaned_positions
    
    def _categorize_text(self, text: str, title: str = "") -> str:
        """
        Categorize clause based on content and title.
        
        Args:
            text: Clause content
            title: Clause title
            
        Returns:
            Category string
        """
        combined_text = f"{title} {text}".lower()
        
        for category, patterns in self._compiled_category_patterns.items():
            for pattern in patterns:
                if pattern.search(combined_text):
                    return category
        
        return "general"
    
    def get_clauses_by_category(
        self, 
        clauses: List[Clause], 
        category: str
    ) -> List[Clause]:
        """
        Filter clauses by category.
        
        Args:
            clauses: List of Clause objects
            category: Category to filter by
            
        Returns:
            Filtered list of clauses
        """
        return [c for c in clauses if c.category == category]
    
    def get_clause_summary(self, clauses: List[Clause]) -> Dict[str, Any]:
        """
        Generate summary statistics for extracted clauses.
        
        Args:
            clauses: List of Clause objects
            
        Returns:
            Dictionary with summary statistics
        """
        categories = {}
        for clause in clauses:
            categories[clause.category] = categories.get(clause.category, 0) + 1
        
        return {
            "total_clauses": len(clauses),
            "categories": categories,
            "clause_numbers": [c.number for c in clauses]
        }
