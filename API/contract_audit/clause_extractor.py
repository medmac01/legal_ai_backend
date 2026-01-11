"""
Description:
    Clause Extractor for splitting contracts into individual clauses.
    Identifies and categorizes clauses based on common legal patterns.
    Enhanced to extract articles/sub-clauses and group them into thematics for auditing.

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
        category: Categorization of the clause type (thematic group)
        start_position: Character position where clause starts in original text
        end_position: Character position where clause ends in original text
        sub_clauses: List of sub-clause dictionaries within this clause
        parent_number: Parent clause number if this is a sub-clause
    """
    number: str
    title: str
    content: str
    category: str = "general"
    start_position: int = 0
    end_position: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_clauses: List[Dict[str, Any]] = field(default_factory=list)
    parent_number: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert clause to dictionary representation."""
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "metadata": self.metadata,
            "sub_clauses": self.sub_clauses,
            "parent_number": self.parent_number
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
    
    Groups clauses into thematic categories for auditing purposes.
    """
    
    # Thematic category patterns for contract auditing
    CATEGORY_PATTERNS = {
        "definitions": [
            r"\bdefinition", r"\binterpretation", r"\bmeaning\b",
            r'"[^"]+"\s+means\b'
        ],
        "confidentiality_obligations": [
            r"\bconfidentiality\s+obligation", r"\bconfidential",
            r"\bnon-disclosure", r"\bproprietary", r"\bsecret"
        ],
        "core_obligations": [
            r"\bobligation", r"\bduty\b", r"\bresponsibilit",
            r"\bshall\s+(?:not\s+)?(?:disclose|use|protect)",
            r"\bcovenants?\b", r"\bagrees?\s+to\b"
        ],
        "exclusions_exceptions": [
            r"\bexclusion", r"\bexcept(?:ion)?\b", r"\bshall\s+not\s+apply",
            r"\bdoes\s+not\s+(?:include|apply)", r"\bpublic\s+domain"
        ],
        "permitted_use": [
            r"\bpermitted\s+(?:use|disclosure)", r"\bauthorized\s+use"
        ],
        "legally_required_disclosure": [
            r"\blegal(?:ly)?\s+required", r"\bcompelled\s+(?:by\s+law|disclosure)",
            r"\bcourt\s+order", r"\bsubpoena", r"\bregulatory",
            r"\bbinding\s+law", r"\bjudicial"
        ],
        "intellectual_property": [
            r"\bintellectual\s+property", r"\bip\s+rights?\b", r"\bpatent",
            r"\btrademark", r"\bcopyright", r"\blicen[cs]e", r"\bownership",
            r"\bno\s+license", r"\bno\s+warranty"
        ],
        "return_of_information": [
            r"\breturn\s+(?:of\s+)?(?:confidential|information|materials)",
            r"\bdestruction", r"\bdestroy"
        ],
        "term_duration": [
            r"\bterm\b", r"\bduration", r"\beffective\s+(?:date|period)",
            r"\bremain\s+in\s+effect", r"\bmonths?\b.*\bfrom"
        ],
        "termination": [
            r"\btermination", r"\bexpir", r"\bcancellation",
            r"\bend\s+of\s+agreement"
        ],
        "liability": [
            r"\bliability", r"\bliable\b", r"\bdamage", r"\bloss\b",
            r"\bnegligence", r"\bbreach"
        ],
        "indemnification": [
            r"\bindemnif", r"\bhold\s+harmless"
        ],
        "dispute_resolution": [
            r"\bdispute", r"\barbitration", r"\bmediation",
            r"\blitigation", r"\bresolution", r"\bsettlement"
        ],
        "governing_law": [
            r"\bgoverning\s+law", r"\bjurisdiction", r"\bapplicable\s+law",
            r"\bvenue\b", r"\bchoice\s+of\s+law", r"\bconstrued\s+in\s+accordance"
        ],
        "notices": [
            r"\bnotice", r"\bnotification", r"\bcommunication"
        ],
        "assignment": [
            r"\bassignment", r"\btransfer", r"\bdelegation",
            r"\bnon-assignable"
        ],
        "amendment": [
            r"\bamendment", r"\bmodification", r"\bchange",
            r"\bsupplement"
        ],
        "severability": [
            r"\bseverability", r"\bseparability", r"\binvalid\s+provision",
            r"\bunenforceable"
        ],
        "entire_agreement": [
            r"\bentire\s+agreement", r"\bwhole\s+agreement",
            r"\bcomplete\s+agreement", r"\bsupersede"
        ],
        "waiver": [
            r"\bwaiver", r"\bfailure\s+to\s+enforce"
        ],
        "non_solicitation": [
            r"\bnon-solicitation", r"\bsolicit\s+for\s+employment"
        ],
        "warranty": [
            r"\bwarranty", r"\bguarantee", r"\brepresentation"
        ],
        "force_majeure": [
            r"\bforce\s+majeure", r"\bact\s+of\s+god", r"\bunforeseen"
        ],
        "data_protection": [
            r"\bdata\s+protection", r"\bpersonal\s+data", r"\bprivacy", r"\bgdpr"
        ],
        "general_provisions": [
            r"\bgeneral\s+provision", r"\bmiscellaneous"
        ]
    }
    
    # Thematic groupings that combine related categories for audit
    THEMATIC_GROUPS = {
        "definitions": ["definitions"],
        "core_obligations": [
            "confidentiality_obligations", "core_obligations"
        ],
        "exclusions_and_exceptions": ["exclusions_exceptions"],
        "permitted_disclosures": [
            "permitted_use", "legally_required_disclosure"
        ],
        "intellectual_property": ["intellectual_property"],
        "term_and_termination": [
            "term_duration", "termination", "return_of_information"
        ],
        "liability_and_indemnity": ["liability", "indemnification"],
        "dispute_resolution": ["dispute_resolution"],
        "governing_law": ["governing_law"],
        "general_provisions": [
            "notices", "assignment", "amendment", "severability",
            "entire_agreement", "waiver", "non_solicitation",
            "warranty", "force_majeure", "data_protection",
            "general_provisions"
        ]
    }
    
    # Patterns for detecting clause headers (articles/sections only, not sub-clauses)
    CLAUSE_HEADER_PATTERNS = [
        # ARTICLE X. TITLE or ARTICLE X: TITLE (must be at start of line)
        r"^[\s]*(?P<number>ARTICLE\s+\d+)[\.\:\s]+(?P<title>[A-Z][A-Z\s\-]+?)(?=\s*\n)",
        # Section X. TITLE (must be at start of line)
        r"^[\s]*(?P<number>SECTION\s+\d+)[\.\:\s]+(?P<title>[A-Z][A-Z\s\-]+?)(?=\s*\n)",
    ]
    
    # Sub-clause patterns
    SUB_CLAUSE_PATTERNS = [
        # X.Y format (e.g., 1.1, 2.3)
        re.compile(r"(\d+\.\d+)\s+(.+?)(?=\n\s*\d+\.\d+\s|\n\s*ARTICLE|\n\s*Article|\Z)", re.DOTALL),
        # (a), (b), (c) format
        re.compile(r"\(([a-z])\)\s+(.+?)(?=\s*\([a-z]\)|\n\s*\d+\.\d+|\n\s*ARTICLE|\Z)", re.DOTALL),
    ]
    
    # Special section markers
    RECITALS_PATTERN = re.compile(
        r"(RECITALS?|WHEREAS|BACKGROUND|PREAMBLE)\s*[\:\n](.+?)(?=NOW,?\s*THEREFORE|ARTICLE|SECTION|\d+\.)",
        re.IGNORECASE | re.DOTALL
    )
    
    SIGNATURE_PATTERN = re.compile(
        r"(IN\s+WITNESS\s+WHEREOF|EXECUTED\s+(?:AS\s+OF|BY)|SIGNATURES?)(.+)$",
        re.IGNORECASE | re.DOTALL
    )
    
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
        
        # Extract special sections
        preamble = self._extract_preamble(contract_text)
        recitals = self._extract_recitals(contract_text)
        signatures = self._extract_signatures(contract_text)
        
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
        
        # Find signature block start to exclude from last clause
        sig_match = self.SIGNATURE_PATTERN.search(contract_text)
        sig_start = sig_match.start() if sig_match else len(contract_text)
        
        # Extract clause content based on positions
        clauses = []
        
        # Add preamble as a clause if exists
        if preamble:
            clauses.append(Clause(
                number="PREAMBLE",
                title="Parties Identification",
                content=preamble,
                category="parties_and_recitals",
                start_position=0,
                end_position=len(preamble),
                metadata={"section_type": "preamble"}
            ))
        
        # Add recitals as a clause if exists
        if recitals:
            clauses.append(Clause(
                number="RECITALS",
                title="Recitals",
                content=recitals,
                category="parties_and_recitals",
                start_position=contract_text.find(recitals) if recitals in contract_text else 0,
                end_position=contract_text.find(recitals) + len(recitals) if recitals in contract_text else 0,
                metadata={"section_type": "recitals"}
            ))
        
        # Extract main clauses/articles
        for i, (start_pos, number, title) in enumerate(clause_positions):
            # Determine end position (start of next clause or signature block)
            if i + 1 < len(clause_positions):
                end_pos = clause_positions[i + 1][0]
            else:
                end_pos = sig_start
            
            content = contract_text[start_pos:end_pos].strip()
            category = self._categorize_text(content, title)
            
            # Extract sub-clauses
            sub_clauses = self._extract_sub_clauses(content, number)
            
            clause = Clause(
                number=number.strip(),
                title=title.strip() if title else "",
                content=content,
                category=category,
                start_position=start_pos,
                end_position=end_pos,
                sub_clauses=sub_clauses,
                metadata={"section_type": "article"}
            )
            clauses.append(clause)
        
        # Add signatures as a clause if exists
        if signatures:
            clauses.append(Clause(
                number="SIGNATURES",
                title="Execution",
                content=signatures,
                category="signatures",
                start_position=sig_start,
                end_position=len(contract_text),
                metadata={"section_type": "signatures"}
            ))
        
        logger.info(f"Extracted {len(clauses)} clauses from contract")
        return clauses
    
    def _extract_preamble(self, text: str) -> str:
        """Extract the preamble section (parties identification)."""
        markers = [
            re.search(r"RECITALS?|WHEREAS|BACKGROUND", text, re.IGNORECASE),
            re.search(r"ARTICLE\s+\d+", text, re.IGNORECASE),
            re.search(r"NOW,?\s*THEREFORE", text, re.IGNORECASE),
        ]
        
        end_pos = len(text)
        for marker in markers:
            if marker and marker.start() < end_pos:
                end_pos = marker.start()
        
        preamble = text[:end_pos].strip()
        return preamble if len(preamble) > 50 else ""  # Only return if substantial
    
    def _extract_recitals(self, text: str) -> str:
        """Extract the recitals/whereas section."""
        match = self.RECITALS_PATTERN.search(text)
        if match:
            return match.group(0).strip()
        return ""
    
    def _extract_signatures(self, text: str) -> str:
        """Extract the signature block."""
        match = self.SIGNATURE_PATTERN.search(text)
        if match:
            return match.group(0).strip()
        return ""
    
    def _extract_sub_clauses(self, clause_content: str, parent_number: str) -> List[Dict[str, Any]]:
        """
        Extract sub-clauses from a clause's content.
        
        Args:
            clause_content: Content of the parent clause
            parent_number: Number of the parent clause
            
        Returns:
            List of sub-clause dictionaries
        """
        sub_clauses = []
        
        # Extract X.Y format sub-clauses
        numbered_pattern = re.compile(
            r"(\d+\.\d+)\s+(.+?)(?=\n\s*\d+\.\d+\s|\n\s*ARTICLE|\n\s*Article|\Z)",
            re.DOTALL
        )
        
        for match in numbered_pattern.finditer(clause_content):
            number = match.group(1)
            content = match.group(2).strip()
            content = re.sub(r'\s+', ' ', content).strip()
            
            sub_clauses.append({
                "number": number,
                "content": content,
                "parent_number": parent_number,
                "type": "numbered"
            })
        
        # Extract lettered sub-clauses (a), (b), (c)
        lettered_pattern = re.compile(
            r"\(([a-z])\)\s+(.+?)(?=\s*\([a-z]\)|\n\s*\d+\.\d+|\n\s*ARTICLE|\Z)",
            re.DOTALL
        )
        
        for match in lettered_pattern.finditer(clause_content):
            letter = match.group(1)
            content = match.group(2).strip()
            content = re.sub(r'\s+', ' ', content).strip()
            
            sub_clauses.append({
                "number": f"({letter})",
                "content": content,
                "parent_number": parent_number,
                "type": "lettered"
            })
        
        return sub_clauses
    
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
        # Priority 1: Check title for direct category matches
        title_lower = title.lower().strip()
        
        # Direct title-to-category mapping (highest priority)
        title_category_map = {
            "definition": "definitions",
            "interpretation": "definitions",
            "confidentiality obligation": "confidentiality_obligations",
            "obligation": "core_obligations",
            "exclusion": "exclusions_exceptions",
            "exception": "exclusions_exceptions",
            "permitted use": "permitted_use",
            "permitted disclosure": "permitted_use",
            "legally required": "legally_required_disclosure",
            "required disclosure": "legally_required_disclosure",
            "intellectual property": "intellectual_property",
            "no license": "intellectual_property",
            "license": "intellectual_property",
            "warranty": "warranty",
            "no warranty": "intellectual_property",
            "return of": "return_of_information",
            "return of confidential": "return_of_information",
            "term": "term_duration",
            "duration": "term_duration",
            "termination": "termination",
            "liability": "liability",
            "responsibility": "liability",
            "indemnif": "indemnification",
            "dispute": "dispute_resolution",
            "arbitration": "dispute_resolution",
            "governing law": "governing_law",
            "applicable law": "governing_law",
            "jurisdiction": "governing_law",
            "notice": "notices",
            "notification": "notices",
            "assignment": "assignment",
            "amendment": "amendment",
            "modification": "amendment",
            "severability": "severability",
            "entire agreement": "entire_agreement",
            "waiver": "waiver",
            "non-solicitation": "non_solicitation",
            "solicitation": "non_solicitation",
            "general provision": "general_provisions",
            "miscellaneous": "general_provisions",
            "force majeure": "force_majeure",
            "data protection": "data_protection",
            "privacy": "data_protection",
        }
        
        for key, category in title_category_map.items():
            if key in title_lower:
                return category
        
        # Priority 2: Pattern-based scoring on combined text
        combined_text = f"{title} {text}".lower()
        
        scores: Dict[str, int] = {}
        for category, patterns in self._compiled_category_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(combined_text)
                score += len(matches)
            if score > 0:
                scores[category] = score
        
        # Return highest scoring category
        if scores:
            return max(scores, key=scores.get)
        
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
    
    def get_clauses_by_thematic_group(
        self,
        clauses: List[Clause],
        thematic_group: str
    ) -> List[Clause]:
        """
        Filter clauses by thematic group (combines related categories).
        
        Args:
            clauses: List of Clause objects
            thematic_group: Thematic group name
            
        Returns:
            Filtered list of clauses
        """
        categories = self.THEMATIC_GROUPS.get(thematic_group, [thematic_group])
        return [c for c in clauses if c.category in categories]
    
    def group_clauses_by_theme(
        self,
        clauses: List[Clause]
    ) -> Dict[str, List[Clause]]:
        """
        Group all clauses by their thematic groups.
        
        Args:
            clauses: List of Clause objects
            
        Returns:
            Dictionary mapping thematic group names to lists of clauses
        """
        # Build reverse mapping from category to thematic group
        category_to_theme = {}
        for theme, categories in self.THEMATIC_GROUPS.items():
            for cat in categories:
                category_to_theme[cat] = theme
        
        # Group clauses
        groups: Dict[str, List[Clause]] = {}
        for clause in clauses:
            theme = category_to_theme.get(clause.category, "uncategorized")
            if theme not in groups:
                groups[theme] = []
            groups[theme].append(clause)
        
        return groups
    
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
        
        # Count sub-clauses
        total_sub_clauses = sum(len(c.sub_clauses) for c in clauses)
        
        # Get thematic groupings
        thematic_groups = self.group_clauses_by_theme(clauses)
        thematic_coverage = {k: len(v) for k, v in thematic_groups.items()}
        
        return {
            "total_clauses": len(clauses),
            "total_sub_clauses": total_sub_clauses,
            "categories": categories,
            "thematic_coverage": thematic_coverage,
            "clause_numbers": [c.number for c in clauses]
        }
    
    def get_audit_summary(self, clauses: List[Clause]) -> Dict[str, Any]:
        """
        Generate an audit-focused summary of the extracted clauses.
        
        Args:
            clauses: List of Clause objects
            
        Returns:
            Dictionary with audit summary information
        """
        thematic_groups = self.group_clauses_by_theme(clauses)
        
        # Check for special sections
        has_preamble = any(c.metadata.get("section_type") == "preamble" for c in clauses)
        has_recitals = any(c.metadata.get("section_type") == "recitals" for c in clauses)
        has_signatures = any(c.metadata.get("section_type") == "signatures" for c in clauses)
        
        summary = {
            "total_clauses": len(clauses),
            "total_sub_clauses": sum(len(c.sub_clauses) for c in clauses),
            "has_preamble": has_preamble,
            "has_recitals": has_recitals,
            "has_signatures": has_signatures,
            "thematic_coverage": {k: len(v) for k, v in thematic_groups.items()},
            "articles_by_theme": {
                k: [{"number": c.number, "title": c.title} for c in v]
                for k, v in thematic_groups.items()
            },
            "potential_gaps": [],
            "audit_checklist": {}
        }
        
        # Identify potential gaps for NDA-specific audit
        required_themes = [
            "definitions",
            "core_obligations",
            "term_and_termination",
            "governing_law"
        ]
        
        for theme in required_themes:
            if theme not in thematic_groups or not thematic_groups[theme]:
                summary["potential_gaps"].append({
                    "theme": theme,
                    "issue": f"No clauses found for critical theme: {theme}"
                })
        
        # Build audit checklist
        summary["audit_checklist"] = {
            "definitions_present": "definitions" in thematic_groups and len(thematic_groups["definitions"]) > 0,
            "obligations_defined": "core_obligations" in thematic_groups and len(thematic_groups["core_obligations"]) > 0,
            "exceptions_specified": "exclusions_and_exceptions" in thematic_groups and len(thematic_groups["exclusions_and_exceptions"]) > 0,
            "term_specified": "term_and_termination" in thematic_groups and len(thematic_groups["term_and_termination"]) > 0,
            "governing_law_specified": "governing_law" in thematic_groups and len(thematic_groups["governing_law"]) > 0,
            "dispute_resolution_specified": "dispute_resolution" in thematic_groups and len(thematic_groups["dispute_resolution"]) > 0,
            "ip_provisions_present": "intellectual_property" in thematic_groups and len(thematic_groups["intellectual_property"]) > 0,
        }
        
        return summary