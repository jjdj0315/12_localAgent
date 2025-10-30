"""
Multi-Agent System - Specialized agents for local government tasks

Agents:
- CitizenSupportAgent: Handle citizen inquiries
- DocumentWritingAgent: Draft official documents
- LegalResearchAgent: Search and interpret laws/regulations
- DataAnalysisAgent: Analyze statistical data
- ReviewAgent: Review and improve documents
"""

from .citizen_support import CitizenSupportAgent
from .document_writing import DocumentWritingAgent
from .legal_research import LegalResearchAgent
from .data_analysis import DataAnalysisAgent
from .review import ReviewAgent

__all__ = [
    "CitizenSupportAgent",
    "DocumentWritingAgent",
    "LegalResearchAgent",
    "DataAnalysisAgent",
    "ReviewAgent",
]
