"""
Open-Coscientist agent tools for MCP server.

Provides MCP-compatible tools for scientific hypothesis generation,
verification, evolution, and strategic decision-making, exposing the
multi-agent research framework via MCP.
"""

from .hypothesis import generate_hypothesis, review_hypothesis, evolve_hypothesis
from .analysis import meta_review_analysis, generate_final_report
from .supervisor import supervisor_decision, get_system_status

__all__ = [
    "generate_hypothesis",
    "review_hypothesis",
    "evolve_hypothesis",
    "meta_review_analysis",
    "generate_final_report",
    "supervisor_decision",
    "get_system_status",
]
