"""
Description:
    Audit Service for orchestrating contract auditing against Moroccan law.
    Uses Ollama-based LLM for clause analysis and compliance checking.

Author: Contract Audit Module
Date: 2025/01/09
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

import requests

from .contract_parser import ContractParser
from .clause_extractor import ClauseExtractor, Clause
from .law_retriever import LawRetriever

logger = logging.getLogger(__name__)


# Prompt templates for LLM interactions
CLAUSE_AUDIT_PROMPT = """You are a legal expert specializing in Moroccan law. Analyze the following contract clause for compliance with Moroccan law.

## Contract Clause
**Clause {clause_number}**: {clause_title}
{clause_content}

## Relevant Moroccan Law Articles
{relevant_laws}

## Instructions
Analyze this clause and provide:
1. **Compliance Status**: Is this clause compliant with Moroccan law? (Compliant / Non-Compliant / Needs Review)
2. **Risk Level**: Assess the risk level (Low / Medium / High)
3. **Issues Found**: List any legal issues or concerns
4. **Recommendations**: Suggest improvements or modifications
5. **Legal References**: Cite specific laws that apply

Format your response as follows:
COMPLIANCE: [Compliant/Non-Compliant/Needs Review]
RISK_LEVEL: [Low/Medium/High]
ISSUES:
- [Issue 1]
- [Issue 2]
RECOMMENDATIONS:
- [Recommendation 1]
- [Recommendation 2]
LEGAL_REFERENCES:
- [Reference 1]
- [Reference 2]
ANALYSIS:
[Detailed analysis paragraph]
"""

EXECUTIVE_SUMMARY_PROMPT = """You are a senior legal counsel preparing an executive summary of a contract audit report.

## Audit Results
{audit_results}

## Contract Overview
- Total Clauses Analyzed: {total_clauses}
- Compliant Clauses: {compliant_count}
- Non-Compliant Clauses: {non_compliant_count}
- Needs Review: {needs_review_count}

## Instructions
Write a professional executive summary that:
1. Summarizes the overall compliance status
2. Highlights critical issues that require immediate attention
3. Provides actionable recommendations
4. Assesses overall contract risk

Keep the summary concise but comprehensive (300-500 words).
"""

QUICK_AUDIT_PROMPT = """You are a legal expert specializing in Moroccan law. Perform a rapid assessment of the following contract.

## Contract Text
{contract_text}

## Relevant Moroccan Law References
{relevant_laws}

## Instructions
Provide a quick assessment covering:
1. **Overall Compliance**: General compliance with Moroccan law (Good / Fair / Poor)
2. **Key Concerns**: Top 3-5 areas of concern
3. **Critical Issues**: Any provisions that may be legally problematic
4. **Recommendations**: Priority actions to address issues

Be concise but thorough. Focus on the most important legal considerations.
"""

CLAUSE_AUDIT_ENHANCED = """
You are a legal expert in Moroccan law (DOC). Perform a clause-by-clause audit of the following contract.

## Contract
{contract_text}

## Legal References
{relevant_laws}

---

# THE 7 RISK AXES

For EACH clause, assess these 7 risks (HIGH/MODERATE/LOW/NONE):

**1. VALIDITY** — Contrary to public order or mandatory rules? (DOC Art. 2, 62, 109, 230)
Indicators: total exclusion of liability, waiver of mandatory rights

**2. IMBALANCE** — Creates a significant imbalance between parties? (DOC Art. 231, 264)
Indicators: unilateral termination, asymmetric penalties, unilateral modification

**3. INCOMPLETENESS** — Necessary clause absent or insufficient?
Check: force majeure, termination, disputes, confidentiality, liability cap

**4. AMBIGUITY** — Vague or imprecise clause? (DOC Art. 461-473)
Indicators: "reasonable time", undefined terms, unclear references

**5. FINANCIAL EXPOSURE** — Excessive financial risk? (DOC Art. 263-264)
Indicators: penalties without cap, unlimited indemnification, disproportionate amounts

**6. APPLICABILITY** — Difficult to enforce in practice? (DOC Art. 259-260)
Indicators: vague obligations, unrealistic deadlines, impossible proof

**7. JURISDICTIONAL RISK** — Inappropriate forum or applicable law?
Indicators: inaccessible foreign court, difficult enforcement in Morocco

---

# REPORT FORMAT
Write in English:

## EXECUTIVE SUMMARY
- Overall Health: [CRITICAL/INSUFFICIENT/FAIR/GOOD/EXCELLENT]
- Number of Clauses Analyzed
- Top 3 Major Issues
- Priority Actions

## CLAUSE-BY-CLAUSE ANALYSIS

### Clause [Number]: [Title]
**Text:** [citation]
**Type:** [TERMINATION/LIABILITY/PENALTIES/CONFIDENTIALITY/etc.]

**Identified Risks:**
| Axis | Level | Analysis | Legal Basis |
|-----|--------|---------|---------------------|

**Recommendations:** [corrective actions]
**Human Review Required:** [YES/NO]
[Repeat for each clause]

## MISSING CLAUSES
[List missing clauses that should be included]

## PRIORITY RECOMMENDATIONS
1. Immediate Actions (High Risks)
2. Improvements (Moderate Risks)

## CONCLUSION
[Final Recommendation: sign/modify/negotiate/reject]

---

RULES:
- High Risk → Human Review = YES
- A clause can have multiple risks
- Always cite the legal basis
- When in doubt, escalate the risk

Start the analysis.
"""


@dataclass
class AuditFinding:
    """
    Represents a finding from clause audit.
    """
    clause_number: str
    clause_title: str
    compliance_status: str  # Compliant, Non-Compliant, Needs Review
    risk_level: str  # Low, Medium, High
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    legal_references: List[str] = field(default_factory=list)
    analysis: str = ""
    relevant_laws: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: str = ""  # Always include raw LLM response
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_number": self.clause_number,
            "clause_title": self.clause_title,
            "compliance_status": self.compliance_status,
            "risk_level": self.risk_level,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "legal_references": self.legal_references,
            "analysis": self.analysis,
            "relevant_laws": self.relevant_laws,
            "raw_response": self.raw_response
        }


@dataclass
class AuditReport:
    """
    Complete audit report for a contract.
    """
    contract_name: str
    audit_date: str
    total_clauses: int
    findings: List[AuditFinding]
    executive_summary: str = ""
    overall_compliance: str = ""  # Good, Fair, Poor
    overall_risk: str = ""  # Low, Medium, High
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""  # Always include raw LLM response for executive summary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_name": self.contract_name,
            "audit_date": self.audit_date,
            "total_clauses": self.total_clauses,
            "findings": [f.to_dict() for f in self.findings],
            "executive_summary": self.executive_summary,
            "overall_compliance": self.overall_compliance,
            "overall_risk": self.overall_risk,
            "summary_stats": self.get_summary_stats(),
            "metadata": self.metadata,
            "raw_response": self.raw_response
        }
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics of findings."""
        stats = {
            "compliant": 0,
            "non_compliant": 0,
            "needs_review": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0
        }
        
        for finding in self.findings:
            status = finding.compliance_status.lower().replace("-", "_").replace(" ", "_")
            if "compliant" in status and "non" not in status:
                stats["compliant"] += 1
            elif "non" in status:
                stats["non_compliant"] += 1
            else:
                stats["needs_review"] += 1
            
            risk = finding.risk_level.lower()
            if risk == "high":
                stats["high_risk"] += 1
            elif risk == "medium":
                stats["medium_risk"] += 1
            else:
                stats["low_risk"] += 1
        
        return stats


class AuditService:
    """
    Main service for conducting contract audits.
    
    Orchestrates the parsing, clause extraction, law retrieval,
    and LLM-based analysis of contracts.
    """
    
    def __init__(
        self,
        ollama_model: str = "gpt-oss:20b",
        ollama_base_url: Optional[str] = None,
        law_retrieval_top_k: int = 5
    ):
        """
        Initialize the Audit Service.
        
        Args:
            ollama_model: Ollama model to use for analysis
            ollama_base_url: Base URL for Ollama API (defaults to env var or localhost)
            law_retrieval_top_k: Number of law articles to retrieve per clause
        """
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url or os.getenv(
            "OLLAMA_BASE_URL", 
            "http://host.docker.internal:11434"
        )
        
        self.parser = ContractParser()
        self.clause_extractor = ClauseExtractor()
        self.law_retriever = LawRetriever(top_k=law_retrieval_top_k)
        
        logger.info(f"AuditService initialized with model: {ollama_model}")
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API for text generation.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            Generated text response
        """
        url = f"{self.ollama_base_url}/api/generate"
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 8192
            }
        }
        
        try:
            logger.info(f"[OLLAMA] Calling Ollama API at {url} with model {self.ollama_model}")
            logger.debug(f"[OLLAMA] Prompt length: {len(prompt)} chars")
            logger.debug(f"[OLLAMA] First 300 chars of prompt: {prompt[:300]}")
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            llm_response = result.get("response", "")
            
            logger.info(f"[OLLAMA] Successfully received response. Length: {len(llm_response)} chars")
            logger.debug(f"[OLLAMA] First 500 chars of response: {llm_response[:500]}")
            
            return llm_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[OLLAMA] API error: {e}")
            raise RuntimeError(f"Failed to call Ollama API: {e}") from e
    
    def _parse_audit_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the structured response from clause audit (old format).
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed response dictionary
        """
        logger.debug(f"[PARSER] Starting to parse audit response. Response length: {len(response)}")
        logger.debug(f"[PARSER] First 500 chars of response: {response[:500]}")
        
        result = {
            "compliance_status": "Needs Review",
            "risk_level": "Medium",
            "issues": [],
            "recommendations": [],
            "legal_references": [],
            "analysis": ""
        }
        
        lines = response.strip().split("\n")
        current_section = None
        
        logger.debug(f"[PARSER] Processing {len(lines)} lines")
        
        for idx, line in enumerate(lines):
            line = line.strip()
            
            if line.startswith("COMPLIANCE:"):
                result["compliance_status"] = line.replace("COMPLIANCE:", "").strip()
                logger.debug(f"[PARSER] Line {idx}: Found COMPLIANCE = {result['compliance_status']}")
            elif line.startswith("RISK_LEVEL:"):
                result["risk_level"] = line.replace("RISK_LEVEL:", "").strip()
                logger.debug(f"[PARSER] Line {idx}: Found RISK_LEVEL = {result['risk_level']}")
            elif line.startswith("ISSUES:"):
                current_section = "issues"
                logger.debug(f"[PARSER] Line {idx}: Entering ISSUES section")
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
                logger.debug(f"[PARSER] Line {idx}: Entering RECOMMENDATIONS section")
            elif line.startswith("LEGAL_REFERENCES:"):
                current_section = "legal_references"
                logger.debug(f"[PARSER] Line {idx}: Entering LEGAL_REFERENCES section")
            elif line.startswith("ANALYSIS:"):
                current_section = "analysis"
                logger.debug(f"[PARSER] Line {idx}: Entering ANALYSIS section")
            elif line.startswith("- ") and current_section in ["issues", "recommendations", "legal_references"]:
                item = line[2:].strip()
                result[current_section].append(item)
                logger.debug(f"[PARSER] Line {idx}: Added to {current_section}: {item[:50]}...")
            elif current_section == "analysis" and line:
                result["analysis"] += line + " "
        
        result["analysis"] = result["analysis"].strip()
        
        logger.info(f"[PARSER] Parsing complete. Found {len(result['issues'])} issues, "
                   f"{len(result['recommendations'])} recommendations, "
                   f"{len(result['legal_references'])} legal references")
        logger.debug(f"[PARSER] Final result: compliance={result['compliance_status']}, "
                    f"risk={result['risk_level']}, analysis_length={len(result['analysis'])}")
        
        return result
    
    def _parse_enhanced_audit_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the enhanced audit response format from CLAUSE_AUDIT_ENHANCED prompt.
        
        This format includes:
        - EXECUTIVE SUMMARY with Overall Health
        - CLAUSE-BY-CLAUSE ANALYSIS with risk tables
        - MISSING CLAUSES
        - PRIORITY RECOMMENDATIONS
        
        Args:
            response: Raw LLM response from enhanced prompt
            
        Returns:
            Parsed response dictionary with structured findings
        """
        import re
        
        logger.debug(f"[ENHANCED_PARSER] Starting to parse enhanced audit response. Response length: {len(response)}")
        logger.debug(f"[ENHANCED_PARSER] First 800 chars: {response[:800]}")
        
        result = {
            "overall_health": "FAIR",
            "total_clauses_analyzed": 0,
            "top_issues": [],
            "priority_actions": [],
            "clause_findings": [],
            "missing_clauses": [],
            "priority_recommendations": [],
            "conclusion": "",
            "executive_summary": ""
        }
        
        lines = response.strip().split("\n")
        current_section = None
        current_clause = None
        
        logger.debug(f"[ENHANCED_PARSER] Processing {len(lines)} lines")
        
        for idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Parse Executive Summary section
            if line_stripped.startswith("## EXECUTIVE SUMMARY"):
                current_section = "executive_summary"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering EXECUTIVE SUMMARY")
            elif "Overall Health:" in line_stripped:
                # Extract health status: CRITICAL/INSUFFICIENT/FAIR/GOOD/EXCELLENT
                # Look for patterns like **FAIR** or [FAIR] or just FAIR
                health_match = re.search(r'\*\*([A-Z]+)\*\*|\[([A-Z]+)\]|:\s*([A-Z]+)', line_stripped)
                if health_match:
                    result["overall_health"] = (health_match.group(1) or health_match.group(2) or health_match.group(3)).strip()
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Found Overall Health = {result['overall_health']}")
            elif "Number of Clauses Analyzed" in line_stripped:
                # Try to extract number
                numbers = re.findall(r'\d+', line_stripped)
                if numbers:
                    result["total_clauses_analyzed"] = int(numbers[0])
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Found {result['total_clauses_analyzed']} clauses")
            elif "Top 3 Major Issues" in line_stripped or "Top Major Issues" in line_stripped:
                current_section = "top_issues"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering Top Issues section")
            elif "Priority Actions" in line_stripped and current_section != "priority_recommendations":
                current_section = "priority_actions"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering Priority Actions section")
            
            # Parse Clause-by-Clause Analysis
            elif line_stripped.startswith("## CLAUSE-BY-CLAUSE ANALYSIS"):
                current_section = "clause_analysis"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering CLAUSE-BY-CLAUSE ANALYSIS")
            elif line_stripped.startswith("### Clause"):
                # Save previous clause if exists
                if current_clause:
                    result["clause_findings"].append(current_clause)
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Saved clause {current_clause.get('number', '?')}")
                
                # Start new clause - handle various formats like "### Clause 1.1: Title" or "### Clause 1: Title"
                clause_match = re.match(r'###\s+Clause\s+([^:]+?):\s*(.+)', line_stripped)
                if clause_match:
                    current_clause = {
                        "number": clause_match.group(1).strip(),
                        "title": clause_match.group(2).strip(),
                        "text": "",
                        "type": "",
                        "risks": [],
                        "recommendations": [],
                        "human_review_required": False
                    }
                    current_section = "clause_analysis"
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Started new clause {current_clause['number']}: {current_clause['title']}")
                else:
                    logger.warning(f"[ENHANCED_PARSER] Line {idx}: Failed to parse clause header: {line_stripped}")
            elif line_stripped.startswith("**Text:**") and current_clause:
                current_clause["text"] = line_stripped.replace("**Text:**", "").strip()
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Set clause text: {current_clause['text'][:50]}...")
            elif line_stripped.startswith("**Type:**") and current_clause:
                current_clause["type"] = line_stripped.replace("**Type:**", "").strip().strip("[]")
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Set clause type: {current_clause['type']}")
            elif (line_stripped.startswith("**Identified Risks:**") or 
                  line_stripped.startswith("**Risks:**")) and current_clause:
                current_section = "clause_risks"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering clause risks section")
            elif line_stripped.startswith("**Recommendations:**") and current_clause:
                current_section = "clause_recommendations"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering clause recommendations section")
            elif line_stripped.startswith("**Human Review Required:**") and current_clause:
                current_clause["human_review_required"] = "YES" in line_stripped.upper()
                current_section = "clause_analysis"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Human review required: {current_clause['human_review_required']}")
            
            # Parse Missing Clauses section
            elif line_stripped.startswith("## MISSING CLAUSES"):
                current_section = "missing_clauses"
                if current_clause:  # Save last clause
                    result["clause_findings"].append(current_clause)
                    current_clause = None
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering MISSING CLAUSES")
            
            # Parse Priority Recommendations
            elif line_stripped.startswith("## PRIORITY RECOMMENDATIONS"):
                current_section = "priority_recommendations"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering PRIORITY RECOMMENDATIONS")
            
            # Parse Conclusion
            elif line_stripped.startswith("## CONCLUSION"):
                current_section = "conclusion"
                logger.debug(f"[ENHANCED_PARSER] Line {idx}: Entering CONCLUSION")
            
            # Collect items based on current section
            elif line_stripped and (line_stripped.startswith("-") or line_stripped.startswith("•") or 
                  re.match(r'^\d+\.', line_stripped)):  # Handle numbered items like "1.", "2."
                # Extract the item text, removing leading markers
                item = re.sub(r'^[-•]\s*|^\d+\.\s*', '', line_stripped).strip()
                # Also remove markdown bold markers at the start
                item = re.sub(r'^\*\*(.+?)\*\*', r'\1', item)
                
                if current_section == "top_issues" and item:
                    result["top_issues"].append(item)
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Added top issue: {item[:60]}...")
                elif current_section == "priority_actions" and item:
                    result["priority_actions"].append(item)
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Added priority action: {item[:60]}...")
                elif current_section == "missing_clauses" and item:
                    result["missing_clauses"].append(item)
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Added missing clause: {item[:60]}...")
                elif current_section == "priority_recommendations" and item:
                    result["priority_recommendations"].append(item)
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Added priority recommendation: {item[:60]}...")
                elif current_section == "clause_recommendations" and current_clause and item:
                    current_clause["recommendations"].append(item)
                    logger.debug(f"[ENHANCED_PARSER] Line {idx}: Added clause recommendation: {item[:60]}...")
            elif current_section == "conclusion" and line_stripped and not line_stripped.startswith("#"):
                result["conclusion"] += line_stripped + " "
        
        # Don't forget to save the last clause
        if current_clause:
            result["clause_findings"].append(current_clause)
            logger.debug(f"[ENHANCED_PARSER] Saved final clause {current_clause.get('number', '?')}")
        
        result["conclusion"] = result["conclusion"].strip()
        
        logger.info(f"[ENHANCED_PARSER] Parsing complete. Found {len(result['clause_findings'])} clauses, "
                   f"{len(result['top_issues'])} top issues, {len(result['missing_clauses'])} missing clauses")
        logger.debug(f"[ENHANCED_PARSER] Overall health: {result['overall_health']}, "
                    f"Clauses analyzed: {result['total_clauses_analyzed']}")
        
        return result
    
    def audit_clause(
        self, 
        clause: Clause,
        relevant_laws: Optional[List[Dict[str, Any]]] = None
    ) -> AuditFinding:
        """
        Audit a single clause against Moroccan law.
        
        Args:
            clause: Clause object to audit
            relevant_laws: Pre-retrieved laws (if None, will be retrieved)
            
        Returns:
            AuditFinding object
        """
        logger.info(f"[AUDIT_CLAUSE] Starting audit of clause {clause.number}: {clause.title}")
        
        # Get relevant laws if not provided
        if relevant_laws is None:
            logger.debug(f"[AUDIT_CLAUSE] Retrieving laws for clause {clause.number}")
            relevant_laws = self.law_retriever.retrieve_relevant_laws(
                clause.content,
                clause_category=clause.category
            )
            logger.debug(f"[AUDIT_CLAUSE] Retrieved {len(relevant_laws)} relevant laws")
        else:
            logger.debug(f"[AUDIT_CLAUSE] Using {len(relevant_laws)} pre-retrieved laws")
        
        # Format laws for prompt
        laws_text = self.law_retriever.format_laws_for_prompt(relevant_laws)
        logger.debug(f"[AUDIT_CLAUSE] Formatted laws text: {len(laws_text)} chars")
        
        # Build prompt
        clause_content_truncated = clause.content[:3000]
        logger.debug(f"[AUDIT_CLAUSE] Clause content: {len(clause.content)} chars (truncated to {len(clause_content_truncated)})")
        
        prompt = CLAUSE_AUDIT_PROMPT.format(
            clause_number=clause.number,
            clause_title=clause.title or "Untitled",
            clause_content=clause_content_truncated,
            relevant_laws=laws_text
        )
        logger.debug(f"[AUDIT_CLAUSE] Built prompt: {len(prompt)} chars")
        
        # Call LLM
        try:
            logger.debug(f"[AUDIT_CLAUSE] Calling LLM for clause {clause.number}")
            response = self._call_ollama(prompt)
            logger.debug(f"[AUDIT_CLAUSE] Parsing response for clause {clause.number}")
            parsed = self._parse_audit_response(response)
            logger.info(f"[AUDIT_CLAUSE] Successfully audited clause {clause.number}: "
                       f"{parsed['compliance_status']} / {parsed['risk_level']}")
            
            return AuditFinding(
                clause_number=clause.number,
                clause_title=clause.title,
                compliance_status=parsed["compliance_status"],
                risk_level=parsed["risk_level"],
                issues=parsed["issues"],
                recommendations=parsed["recommendations"],
                legal_references=parsed["legal_references"],
                analysis=parsed["analysis"],
                relevant_laws=relevant_laws,
                raw_response=response  # Always include raw LLM response
            )
        except Exception as e:
            logger.error(f"[AUDIT_CLAUSE] Error auditing clause {clause.number}: {e}", exc_info=True)
            # Try to capture response if it exists
            raw_response = ""
            try:
                if 'response' in locals():
                    raw_response = response
            except:
                pass
            
            return AuditFinding(
                clause_number=clause.number,
                clause_title=clause.title,
                compliance_status="Error",
                risk_level="Unknown",
                issues=[f"Audit failed: {str(e)}"],
                recommendations=["Manual review required"],
                analysis="Automated audit could not be completed.",
                raw_response=raw_response  # Include raw response even on error
            )
    
    def audit_contract(
        self,
        file_content: bytes,
        filename: str,
        generate_summary: bool = True
    ) -> AuditReport:
        """
        Perform a full audit of a contract document.
        
        Args:
            file_content: Binary content of the contract file
            filename: Name of the file
            generate_summary: Whether to generate executive summary
            
        Returns:
            AuditReport object
        """
        logger.info(f"[AUDIT_CONTRACT] Starting full audit of contract: {filename}")
        
        # Parse contract
        logger.debug(f"[AUDIT_CONTRACT] Parsing contract text")
        contract_text = self.parser.extract_text(file_content, filename)
        logger.info(f"[AUDIT_CONTRACT] Extracted {len(contract_text)} characters of text")
        
        # Extract clauses
        logger.debug(f"[AUDIT_CONTRACT] Extracting clauses from contract")
        clauses = self.clause_extractor.extract_clauses(contract_text)
        logger.info(f"[AUDIT_CONTRACT] Extracted {len(clauses)} clauses for audit")
        
        # Audit each clause
        findings = []
        for idx, clause in enumerate(clauses, 1):
            logger.info(f"[AUDIT_CONTRACT] Auditing clause {idx}/{len(clauses)}: {clause.number}")
            finding = self.audit_clause(clause)
            findings.append(finding)
        
        logger.info(f"[AUDIT_CONTRACT] Completed auditing all {len(findings)} clauses")
        
        # Create report
        report = AuditReport(
            contract_name=filename,
            audit_date=datetime.now().isoformat(),
            total_clauses=len(clauses),
            findings=findings,
            metadata={
                "text_length": len(contract_text),
                "clause_categories": self.clause_extractor.get_clause_summary(clauses)
            }
        )
        
        # Calculate overall status
        logger.debug(f"[AUDIT_CONTRACT] Calculating overall compliance status")
        stats = report.get_summary_stats()
        logger.debug(f"[AUDIT_CONTRACT] Stats: {stats}")
        
        if stats["non_compliant"] == 0 and stats["high_risk"] == 0:
            report.overall_compliance = "Good"
            report.overall_risk = "Low"
        elif stats["non_compliant"] <= 2 and stats["high_risk"] <= 1:
            report.overall_compliance = "Fair"
            report.overall_risk = "Medium"
        else:
            report.overall_compliance = "Poor"
            report.overall_risk = "High"
        
        logger.info(f"[AUDIT_CONTRACT] Overall status: {report.overall_compliance} compliance, "
                   f"{report.overall_risk} risk")
        
        # Generate executive summary
        if generate_summary and findings:
            logger.debug(f"[AUDIT_CONTRACT] Generating executive summary")
            summary_result = self._generate_executive_summary(report)
            report.executive_summary = summary_result["summary"]
            report.raw_response = summary_result["raw_response"]
            logger.info(f"[AUDIT_CONTRACT] Executive summary generated: {len(report.executive_summary)} chars")
        else:
            logger.debug(f"[AUDIT_CONTRACT] Skipping executive summary generation")
        
        logger.info(f"[AUDIT_CONTRACT] Audit completed successfully")
        
        return report
    
    def _generate_executive_summary(self, report: AuditReport) -> Dict[str, str]:
        """
        Generate an executive summary for the audit report.
        
        Args:
            report: AuditReport object
            
        Returns:
            Dictionary with 'summary' and 'raw_response' keys
        """
        # Summarize audit results for prompt
        audit_results = []
        for finding in report.findings[:10]:  # Limit to first 10 for prompt
            result = f"Clause {finding.clause_number}: {finding.compliance_status} ({finding.risk_level} risk)"
            if finding.issues:
                result += f" - Issues: {', '.join(finding.issues[:2])}"
            audit_results.append(result)
        
        stats = report.get_summary_stats()
        
        prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            audit_results="\n".join(audit_results),
            total_clauses=report.total_clauses,
            compliant_count=stats["compliant"],
            non_compliant_count=stats["non_compliant"],
            needs_review_count=stats["needs_review"]
        )
        
        try:
            raw_response = self._call_ollama(prompt)
            return {
                "summary": raw_response,
                "raw_response": raw_response
            }
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            error_msg = "Executive summary generation failed. Please review individual findings."
            return {
                "summary": error_msg,
                "raw_response": f"ERROR: {str(e)}"
            }
    
    def quick_audit(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Perform a quick audit of the entire contract.
        
        This provides a faster, high-level assessment without
        detailed clause-by-clause analysis.
        
        Args:
            file_content: Binary content of the contract file
            filename: Name of the file
            
        Returns:
            Dictionary with quick audit results
        """
        logger.info(f"[QUICK_AUDIT] Starting quick audit of contract: {filename}")
        
        # Parse contract
        logger.debug(f"[QUICK_AUDIT] Extracting text from file")
        contract_text = self.parser.extract_text(file_content, filename)
        logger.info(f"[QUICK_AUDIT] Extracted {len(contract_text)} characters of text")
        
        # Get relevant laws for the whole contract
        # Use first 2000 characters as representative sample
        sample_text = contract_text[:2000]
        logger.debug(f"[QUICK_AUDIT] Retrieving relevant laws using {len(sample_text)} char sample")
        relevant_laws = self.law_retriever.retrieve_relevant_laws(sample_text)
        logger.info(f"[QUICK_AUDIT] Retrieved {len(relevant_laws)} relevant law articles")
        
        laws_text = self.law_retriever.format_laws_for_prompt(relevant_laws)
        logger.debug(f"[QUICK_AUDIT] Formatted laws text: {len(laws_text)} chars")
        
        # Build prompt
        contract_snippet = contract_text[:5000]  # Limit for prompt
        logger.debug(f"[QUICK_AUDIT] Using contract snippet: {len(contract_snippet)} chars")
        
        prompt = CLAUSE_AUDIT_ENHANCED.format(
            contract_text=contract_snippet,
            relevant_laws=laws_text
        )
        logger.info(f"[QUICK_AUDIT] Built prompt with total length: {len(prompt)} chars")
        
        try:
            logger.info(f"[QUICK_AUDIT] Sending request to LLM")
            response = self._call_ollama(prompt)
            logger.info(f"[QUICK_AUDIT] Received LLM response: {len(response)} chars")
            
            # Parse the enhanced response
            logger.debug(f"[QUICK_AUDIT] Parsing enhanced audit response")
            parsed_response = self._parse_enhanced_audit_response(response)
            logger.info(f"[QUICK_AUDIT] Parsed response: {len(parsed_response.get('clause_findings', []))} clauses found")
            
            return {
                "contract_name": filename,
                "audit_date": datetime.now().isoformat(),
                "audit_type": "quick",
                "raw_response": response,  # Always include raw LLM response
                "parsed_assessment": parsed_response,  # Structured parsed data
                "text_length": len(contract_text),
                "relevant_laws_count": len(relevant_laws)
            }
        except Exception as e:
            logger.error(f"[QUICK_AUDIT] Quick audit failed: {e}", exc_info=True)
            return {
                "contract_name": filename,
                "audit_date": datetime.now().isoformat(),
                "audit_type": "quick",
                "error": str(e),
                "raw_response": "Quick audit could not be completed. Please try full audit."
            }
