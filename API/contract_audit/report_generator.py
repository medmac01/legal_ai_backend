"""
Description:
    Report Generator for creating Markdown and JSON audit reports.
    Formats audit findings into professional, readable reports.

Author: Contract Audit Module
Date: 2025/01/09
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generator for creating formatted audit reports.
    
    Supports output formats:
    - Markdown (for human-readable reports)
    - JSON (for programmatic access)
    """
    
    @staticmethod
    def generate_markdown_report(audit_report: Dict[str, Any]) -> str:
        """
        Generate a Markdown formatted audit report.
        
        Args:
            audit_report: Dictionary containing audit results
            
        Returns:
            Markdown formatted report string
        """
        contract_name = audit_report.get("contract_name", "Unknown Contract")
        audit_date = audit_report.get("audit_date", datetime.now().isoformat())
        total_clauses = audit_report.get("total_clauses", 0)
        findings = audit_report.get("findings", [])
        executive_summary = audit_report.get("executive_summary", "")
        overall_compliance = audit_report.get("overall_compliance", "Unknown")
        overall_risk = audit_report.get("overall_risk", "Unknown")
        summary_stats = audit_report.get("summary_stats", {})
        
        # Build report
        lines = []
        
        # Header
        lines.append(f"# Contract Audit Report")
        lines.append("")
        lines.append(f"**Contract:** {contract_name}")
        lines.append(f"**Audit Date:** {audit_date}")
        lines.append(f"**Overall Compliance:** {overall_compliance}")
        lines.append(f"**Overall Risk Level:** {overall_risk}")
        lines.append("")
        
        # Summary Statistics
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"- **Total Clauses Analyzed:** {total_clauses}")
        lines.append(f"- **Compliant:** {summary_stats.get('compliant', 0)}")
        lines.append(f"- **Non-Compliant:** {summary_stats.get('non_compliant', 0)}")
        lines.append(f"- **Needs Review:** {summary_stats.get('needs_review', 0)}")
        lines.append(f"- **High Risk:** {summary_stats.get('high_risk', 0)}")
        lines.append(f"- **Medium Risk:** {summary_stats.get('medium_risk', 0)}")
        lines.append(f"- **Low Risk:** {summary_stats.get('low_risk', 0)}")
        lines.append("")
        
        # Executive Summary
        if executive_summary:
            lines.append("## Executive Summary")
            lines.append("")
            lines.append(executive_summary)
            lines.append("")
        
        # Detailed Findings
        lines.append("## Detailed Findings")
        lines.append("")
        
        for i, finding in enumerate(findings, 1):
            clause_num = finding.get("clause_number", f"Clause {i}")
            clause_title = finding.get("clause_title", "")
            compliance = finding.get("compliance_status", "Unknown")
            risk = finding.get("risk_level", "Unknown")
            issues = finding.get("issues", [])
            recommendations = finding.get("recommendations", [])
            legal_refs = finding.get("legal_references", [])
            analysis = finding.get("analysis", "")
            
            # Compliance badge emoji
            if "compliant" in compliance.lower() and "non" not in compliance.lower():
                badge = "✅"
            elif "non" in compliance.lower():
                badge = "❌"
            else:
                badge = "⚠️"
            
            # Risk badge emoji
            risk_lower = risk.lower()
            if risk_lower == "high":
                risk_badge = "🔴"
            elif risk_lower == "medium":
                risk_badge = "🟡"
            else:
                risk_badge = "🟢"
            
            lines.append(f"### {badge} {clause_num}: {clause_title}")
            lines.append("")
            lines.append(f"**Compliance:** {compliance} | **Risk:** {risk_badge} {risk}")
            lines.append("")
            
            if issues:
                lines.append("**Issues Found:**")
                for issue in issues:
                    lines.append(f"- {issue}")
                lines.append("")
            
            if recommendations:
                lines.append("**Recommendations:**")
                for rec in recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            if legal_refs:
                lines.append("**Legal References:**")
                for ref in legal_refs:
                    lines.append(f"- {ref}")
                lines.append("")
            
            if analysis:
                lines.append("**Analysis:**")
                lines.append(analysis)
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Footer
        lines.append("## Disclaimer")
        lines.append("")
        lines.append("*This audit report is generated by an automated system and should be "
                    "reviewed by a qualified legal professional. The findings and recommendations "
                    "provided are based on automated analysis and may not capture all legal "
                    "nuances or jurisdiction-specific requirements.*")
        lines.append("")
        lines.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_report(
        audit_report: Dict[str, Any],
        indent: int = 2
    ) -> str:
        """
        Generate a JSON formatted audit report.
        
        Args:
            audit_report: Dictionary containing audit results
            indent: JSON indentation level
            
        Returns:
            JSON formatted report string
        """
        # Ensure all nested objects are serializable
        def make_serializable(obj):
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        serializable_report = make_serializable(audit_report)
        
        # Add report metadata
        serializable_report["_report_metadata"] = {
            "format": "json",
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "generator": "Contract Audit Module"
        }
        
        return json.dumps(serializable_report, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def generate_quick_audit_markdown(quick_audit: Dict[str, Any]) -> str:
        """
        Generate Markdown report for quick audit results.
        
        Args:
            quick_audit: Dictionary containing quick audit results
            
        Returns:
            Markdown formatted quick audit report
        """
        contract_name = quick_audit.get("contract_name", "Unknown Contract")
        audit_date = quick_audit.get("audit_date", datetime.now().isoformat())
        raw_response = quick_audit.get("raw_response", "No assessment available")
        parsed_assessment = quick_audit.get("parsed_assessment", {})
        text_length = quick_audit.get("text_length", 0)
        laws_count = quick_audit.get("relevant_laws_count", 0)
        error = quick_audit.get("error")
        
        lines = []
        
        lines.append("# Quick Contract Audit Report")
        lines.append("")
        lines.append(f"**Contract:** {contract_name}")
        lines.append(f"**Audit Date:** {audit_date}")
        lines.append(f"**Audit Type:** Quick Assessment")
        lines.append(f"**Contract Length:** {text_length:,} characters")
        lines.append(f"**Laws Referenced:** {laws_count}")
        lines.append("")
        
        if error:
            lines.append("## ⚠️ Error")
            lines.append("")
            lines.append(f"An error occurred during the audit: {error}")
            lines.append("")
        
        lines.append("## Assessment")
        lines.append("")
        lines.append(raw_response)
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*This is a quick assessment. For detailed clause-by-clause analysis, "
                    "use the full audit endpoint.*")
        lines.append("")
        lines.append("## Disclaimer")
        lines.append("")
        lines.append("*This audit report is generated by an automated system and should be "
                    "reviewed by a qualified legal professional.*")
        
        return "\n".join(lines)
    
    @classmethod
    def generate_report(
        cls,
        audit_result: Dict[str, Any],
        format: str = "markdown"
    ) -> str:
        """
        Generate an audit report in the specified format.
        
        Args:
            audit_result: Dictionary containing audit results
            format: Output format ("markdown" or "json")
            
        Returns:
            Formatted report string
            
        Raises:
            ValueError: If format is not supported
        """
        format = format.lower()
        
        if format == "markdown" or format == "md":
            # Check if it's a quick audit
            if audit_result.get("audit_type") == "quick":
                return cls.generate_quick_audit_markdown(audit_result)
            return cls.generate_markdown_report(audit_result)
        elif format == "json":
            return cls.generate_json_report(audit_result)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'markdown' or 'json'.")
