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
            "relevant_laws": self.relevant_laws
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
            "metadata": self.metadata
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
            logger.debug(f"Calling Ollama API at {url}")
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Failed to call Ollama API: {e}") from e
    
    def _parse_audit_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the structured response from clause audit.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed response dictionary
        """
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
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("COMPLIANCE:"):
                result["compliance_status"] = line.replace("COMPLIANCE:", "").strip()
            elif line.startswith("RISK_LEVEL:"):
                result["risk_level"] = line.replace("RISK_LEVEL:", "").strip()
            elif line.startswith("ISSUES:"):
                current_section = "issues"
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
            elif line.startswith("LEGAL_REFERENCES:"):
                current_section = "legal_references"
            elif line.startswith("ANALYSIS:"):
                current_section = "analysis"
            elif line.startswith("- ") and current_section in ["issues", "recommendations", "legal_references"]:
                result[current_section].append(line[2:].strip())
            elif current_section == "analysis" and line:
                result["analysis"] += line + " "
        
        result["analysis"] = result["analysis"].strip()
        
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
        # Get relevant laws if not provided
        if relevant_laws is None:
            relevant_laws = self.law_retriever.retrieve_relevant_laws(
                clause.content,
                clause_category=clause.category
            )
        
        # Format laws for prompt
        laws_text = self.law_retriever.format_laws_for_prompt(relevant_laws)
        
        # Build prompt
        prompt = CLAUSE_AUDIT_PROMPT.format(
            clause_number=clause.number,
            clause_title=clause.title or "Untitled",
            clause_content=clause.content[:3000],  # Limit content length
            relevant_laws=laws_text
        )
        
        logger.info(f"Auditing clause {clause.number}: {clause.title}")
        
        # Call LLM
        try:
            response = self._call_ollama(prompt)
            parsed = self._parse_audit_response(response)
            
            return AuditFinding(
                clause_number=clause.number,
                clause_title=clause.title,
                compliance_status=parsed["compliance_status"],
                risk_level=parsed["risk_level"],
                issues=parsed["issues"],
                recommendations=parsed["recommendations"],
                legal_references=parsed["legal_references"],
                analysis=parsed["analysis"],
                relevant_laws=relevant_laws
            )
        except Exception as e:
            logger.error(f"Error auditing clause {clause.number}: {e}")
            return AuditFinding(
                clause_number=clause.number,
                clause_title=clause.title,
                compliance_status="Error",
                risk_level="Unknown",
                issues=[f"Audit failed: {str(e)}"],
                recommendations=["Manual review required"],
                analysis="Automated audit could not be completed."
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
        logger.info(f"Starting full audit of contract: {filename}")
        
        # Parse contract
        contract_text = self.parser.extract_text(file_content, filename)
        
        # Extract clauses
        clauses = self.clause_extractor.extract_clauses(contract_text)
        
        logger.info(f"Extracted {len(clauses)} clauses for audit")
        
        # Audit each clause
        findings = []
        for clause in clauses:
            finding = self.audit_clause(clause)
            findings.append(finding)
        
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
        stats = report.get_summary_stats()
        if stats["non_compliant"] == 0 and stats["high_risk"] == 0:
            report.overall_compliance = "Good"
            report.overall_risk = "Low"
        elif stats["non_compliant"] <= 2 and stats["high_risk"] <= 1:
            report.overall_compliance = "Fair"
            report.overall_risk = "Medium"
        else:
            report.overall_compliance = "Poor"
            report.overall_risk = "High"
        
        # Generate executive summary
        if generate_summary and findings:
            report.executive_summary = self._generate_executive_summary(report)
        
        logger.info(f"Audit completed: {report.overall_compliance} compliance, "
                   f"{report.overall_risk} risk")
        
        return report
    
    def _generate_executive_summary(self, report: AuditReport) -> str:
        """
        Generate an executive summary for the audit report.
        
        Args:
            report: AuditReport object
            
        Returns:
            Executive summary text
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
            return self._call_ollama(prompt)
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return "Executive summary generation failed. Please review individual findings."
    
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
        logger.info(f"Starting quick audit of contract: {filename}")
        
        # Parse contract
        contract_text = self.parser.extract_text(file_content, filename)
        
        # Get relevant laws for the whole contract
        # Use first 2000 characters as representative sample
        sample_text = contract_text[:2000]
        relevant_laws = self.law_retriever.retrieve_relevant_laws(sample_text)
        laws_text = self.law_retriever.format_laws_for_prompt(relevant_laws)
        
        # Build prompt
        prompt = CLAUSE_AUDIT_ENHANCED.format(
            contract_text=contract_text[:5000],  # Limit for prompt
            relevant_laws=laws_text
        )
        
        try:
            response = self._call_ollama(prompt)
            
            return {
                "contract_name": filename,
                "audit_date": datetime.now().isoformat(),
                "audit_type": "quick",
                "assessment": response,
                "text_length": len(contract_text),
                "relevant_laws_count": len(relevant_laws)
            }
        except Exception as e:
            logger.error(f"Quick audit failed: {e}")
            return {
                "contract_name": filename,
                "audit_date": datetime.now().isoformat(),
                "audit_type": "quick",
                "error": str(e),
                "assessment": "Quick audit could not be completed. Please try full audit."
            }
