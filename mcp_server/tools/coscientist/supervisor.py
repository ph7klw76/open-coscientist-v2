"""
Supervisor decision-making and system status tools.

Provides the strategic decision-making layer of the coscientist
framework, along with system configuration introspection.
"""

import json
import logging
import os

from .hypothesis import _call_llm, DEFAULT_MODEL

logger = logging.getLogger(__name__)

SUPERVISOR_PROMPT = """You are the Supervisor Agent for the Coscientist multi-agent research system. Your role is to analyze the current state of the research process and decide what actions to take next to advance scientific hypothesis generation, evaluation, and refinement.

# Research Goal
{goal}

# Research Meta Review
{meta_review}

# System Statistics
- Total actions taken: {total_actions}
- Total hypotheses generated: {total_hypotheses}
- Number of meta-reviews completed: {num_meta_reviews}
- Recent actions: {latest_actions}
- Top ELO ratings: {top_elo_ratings}

# Available Actions
1. **generate_hypothesis** — Generate a new scientific hypothesis
2. **run_reflection** — Run deep verification on existing hypotheses
3. **run_tournament** — Rank hypotheses through pairwise comparison
4. **run_meta_review** — Perform meta-analysis of top hypotheses
5. **evolve_hypothesis** — Evolve the best hypothesis to address weaknesses
6. **expand_literature_review** — Expand literature search for new domains
7. **finish** — Conclude the research process and generate final report

# Decision Guidelines
- EARLY STAGE (<12 hypotheses): Prioritize **generate_hypothesis** and **expand_literature_review**
- MID STAGE (12-24 hypotheses): Balance generation with **run_reflection** and **run_tournament**
- LATE STAGE (>24 hypotheses): Prioritize **evolve_hypothesis** and **run_meta_review**
- When ELO ratings plateau or cosine similarity is high, diversify with **expand_literature_review**
- When top hypotheses have ELO >1500 and are diverse, consider **finish**

# Output Format
DECISION: [chosen_action]

REASONING:
- [Primary factors influencing this decision]
- [Key metrics that support this choice]
"""


def _get_available_models() -> dict:
    """Get available LLM models and their configuration."""
    return {
        "smart_models": [
            "deepseek/deepseek-v4-pro",
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-20250514",
            "google/gemini-2.5-pro",
        ],
        "cheap_models": [
            "deepseek/deepseek-v4-flash",
            "openai/gpt-4o-mini",
            "google/gemini-2.5-flash",
        ],
        "default_smart": "deepseek/deepseek-v4-pro",
        "default_cheap": "deepseek/deepseek-v4-flash",
        "provider": "litellm",
    }


def supervisor_decision(
    goal: str,
    meta_review: str,
    total_actions: int = 0,
    total_hypotheses: int = 0,
    num_meta_reviews: int = 0,
    latest_actions: str = "",
    top_elo_ratings: str = "[]",
) -> str:
    """
    Get a strategic decision from the coscientist supervisor on next research steps.

    Analyzes the current state of research and decides whether to generate new
    hypotheses, run verification, evolve existing hypotheses, or conclude.

    Args:
        goal: The research goal being pursued
        meta_review: Latest meta-review summary of the hypothesis set
        total_actions: Total number of actions taken so far
        total_hypotheses: Total hypotheses generated so far
        num_meta_reviews: Number of meta-reviews completed
        latest_actions: Comma-separated list of recent actions
        top_elo_ratings: JSON array of top ELO ratings (e.g., "[1520, 1480, 1450]")

    Returns:
        JSON string with the supervisor's decision action and detailed reasoning
    """
    prompt = SUPERVISOR_PROMPT.format(
        goal=goal,
        meta_review=meta_review or "No meta-review available yet.",
        total_actions=total_actions,
        total_hypotheses=total_hypotheses,
        num_meta_reviews=num_meta_reviews,
        latest_actions=latest_actions or "None yet",
        top_elo_ratings=top_elo_ratings,
    )
    response = _call_llm(prompt, DEFAULT_MODEL, max_tokens=16000)

    # Parse DECISION and REASONING from response
    decision = ""
    reasoning = ""
    for line in response.split("\n"):
        if line.upper().startswith("DECISION:"):
            decision = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("REASONING:"):
            reasoning_lines = []
            in_reasoning = True
            for line2 in response.split("\n"):
                if line2.upper().startswith("REASONING:"):
                    in_reasoning = True
                    reasoning_lines.append(line2.split(":", 1)[-1].strip())
                elif in_reasoning and line2.strip().startswith("-"):
                    reasoning_lines.append(line2.strip())
                elif in_reasoning and not line2.strip().startswith("-"):
                    if line2.strip() and not line2.upper().startswith("DECISION:"):
                        reasoning_lines.append(line2.strip())
            reasoning = "\n".join(reasoning_lines)
            break

    return json.dumps({
        "decision": decision or "generate_hypothesis",
        "reasoning": reasoning or response[:500],
        "model": DEFAULT_MODEL,
    }, indent=2)


def get_system_status() -> str:
    """
    Get the current status and configuration of the Open-Coscientist system.

    Returns information about available models, MCP tools, API key status,
    and system capabilities.

    Returns:
        JSON string with system status, available models, tools, and configuration
    """
    models = _get_available_models()

    api_keys = {
        "DEEPSEEK_API_KEY": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "ENTREZ_EMAIL": bool(os.environ.get("ENTREZ_EMAIL")),
    }

    return json.dumps({
        "framework": "Open-Coscientist",
        "version": "0.2.0",
        "protocol": "MCP (Model Context Protocol)",
        "provider": "litellm",
        "models": models,
        "api_keys_configured": api_keys,
        "coscientist_tools": [
            "generate_hypothesis",
            "review_hypothesis",
            "evolve_hypothesis",
            "meta_review_analysis",
            "generate_final_report",
            "supervisor_decision",
            "get_system_status",
        ],
        "literature_tools": [
            "check_pubmed_available",
            "search_pubmed",
            "pubmed_search_with_fulltext",
        ],
        "knowledge_graph_tools": [
            "query_gene_disease_network",
            "query_gene_codependents",
            "query_drug_info",
            "query_clinical_trials",
            "query_pathways",
            "query_causal_subnetwork",
            "query_mechanistic_statements",
            "run_enrichment_analysis",
        ],
    }, indent=2)
