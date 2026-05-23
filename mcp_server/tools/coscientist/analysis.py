"""
Meta-review analysis and final report generation tools.

Provides tools for synthesizing multiple hypotheses into a coherent
meta-review and generating final research reports.
"""

import json
import logging

from .hypothesis import _call_llm, DEFAULT_MODEL, DEFAULT_CHEAP_MODEL

logger = logging.getLogger(__name__)

META_REVIEW_PROMPT = """You are a scientific meta-reviewer analyzing a collection of ranked hypotheses for a research project.

# Research Goal
{goal}

# Top Hypotheses
{top_hypotheses}

# Instructions
1. Identify COMMON STRENGTHS across the top hypotheses.
2. Identify COMMON WEAKNESSES and gaps in the hypothesis set.
3. Detect any SYSTEMATIC BIASES (e.g., all focusing on the same pathway).
4. Assess RESEARCH DIVERSITY - are the hypotheses exploring different mechanisms?
5. Provide ACTIONABLE RECOMMENDATIONS for the next research iteration.

# Output Format
Respond in JSON:
{{
    "common_strengths": ["strength 1", "strength 2"],
    "common_weaknesses": ["weakness 1", "weakness 2"],
    "systematic_biases": ["bias 1 if any"],
    "research_diversity": "HIGH|MODERATE|LOW",
    "recommendations": ["rec 1", "rec 2", "rec 3"],
    "summary": "brief overall assessment"
}}
"""

FINAL_REPORT_PROMPT = """You are a scientific research director writing a final report summarizing a multi-agent hypothesis generation project.

# Research Goal
{goal}

# Top Hypotheses Generated
{top_hypotheses}

# Instructions
1. Write an EXECUTIVE SUMMARY of the research findings.
2. For EACH top hypothesis, provide:
   - The core mechanistic claim
   - Key evidence and rationale
   - Falsifiable predictions
   - Potential impact if validated
3. Identify the most PROMISING DIRECTION for further investigation.
4. Discuss LIMITATIONS of the current approach.
5. Suggest NEXT STEPS for validation.

# Output Format
Write in professional scientific prose with clear section headings.
"""


def meta_review_analysis(
    goal: str,
    top_hypotheses: str,
) -> str:
    """
    Perform a meta-review analysis of the top-ranked scientific hypotheses.

    Analyzes multiple hypotheses to identify common strengths, weaknesses,
    systematic biases, and research diversity. Provides actionable
    recommendations for the next research iteration.

    Args:
        goal: The research goal being pursued
        top_hypotheses: Summary of top-ranked hypotheses with their rankings
                        (e.g., "1. (Elo: 1520) Hypothesis A... 2. (Elo: 1480) Hypothesis B...")

    Returns:
        JSON string with strengths, weaknesses, biases, diversity assessment,
        and recommendations
    """
    prompt = META_REVIEW_PROMPT.format(
        goal=goal,
        top_hypotheses=top_hypotheses,
    )
    response = _call_llm(prompt, DEFAULT_CHEAP_MODEL, max_tokens=8000)

    try:
        return json.dumps(json.loads(response), indent=2)
    except json.JSONDecodeError:
        return json.dumps({
            "summary": response[:2000],
            "common_strengths": [],
            "common_weaknesses": [],
            "recommendations": [],
            "parse_error": "Could not parse structured response",
        }, indent=2)


def generate_final_report(
    goal: str,
    top_hypotheses: str,
) -> str:
    """
    Generate a final scientific research report summarizing all findings.

    Produces a comprehensive report with executive summary, detailed
    hypothesis descriptions, evaluation of the most promising direction,
    limitations, and recommended next steps.

    Args:
        goal: The research goal that was pursued
        top_hypotheses: Summary of top-ranked hypotheses with ratings,
                       predictions, and key findings

    Returns:
        JSON string with the final report in markdown format
    """
    prompt = FINAL_REPORT_PROMPT.format(
        goal=goal,
        top_hypotheses=top_hypotheses,
    )
    response = _call_llm(prompt, DEFAULT_MODEL, max_tokens=16000)

    return json.dumps({
        "report": response,
        "goal": goal,
        "model": DEFAULT_MODEL,
    }, indent=2)
