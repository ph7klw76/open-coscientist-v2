"""
Scientific hypothesis generation, review, and evolution tools.

Uses litellm to call DeepSeek V4 models for generating novel,
falsifiable scientific hypotheses based on literature and domain knowledge.
"""

import json
import logging
import os
from typing import Optional

import litellm

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("COSCIENTIST_MODEL", "deepseek/deepseek-v4-pro")
DEFAULT_CHEAP_MODEL = os.environ.get("COSCIENTIST_CHEAP_MODEL", "deepseek/deepseek-v4-flash")

GENERATION_PROMPT = """You are a senior research scientist in {field} tasked with generating a novel, falsifiable scientific hypothesis.

# Research Goal
{goal}

# Literature Review
{literature_review}

# Instructions
1. Generate ONE novel, specific, and falsifiable scientific hypothesis that advances the research goal.
2. The hypothesis MUST be mechanistic - explain HOW and WHY, not just WHAT.
3. Provide 2-4 specific, falsifiable predictions that would disprove the hypothesis if they fail.
4. List 3-6 assumptions (implicit or explicit) that the hypothesis depends on.
5. Be creative but scientifically rigorous. Avoid generic or obvious hypotheses.

# Output Format
Respond in the following markdown format:

# Hypothesis
[Your detailed mechanistic hypothesis statement]

# Falsifiable Predictions
- [Prediction 1]
- [Prediction 2]
- [Prediction 3]

# Assumptions
- [Assumption 1]
- [Assumption 2]
- [Assumption 3]
"""

REVIEW_PROMPT = """You are a rigorous scientific reviewer evaluating a research hypothesis.

# Research Goal
{goal}

# Hypothesis to Review
{hypothesis}

# Predictions
{predictions}

# Assumptions
{assumptions}

# Instructions
1. Identify the CAUSAL REASONING chain in this hypothesis.
2. For EACH assumption, research and evaluate whether it is supported by established scientific knowledge.
3. Verify whether the predictions genuinely test the hypothesis (are they falsifiable and specific?).
4. Classify the hypothesis as: PROMISING, NEEDS_REFINEMENT, or FLAWED.
5. If FLAWED, explain the specific fatal flaw.
6. If NEEDS_REFINEMENT, suggest specific improvements.

# Output Format
Respond in JSON with these fields:
{{
    "causal_reasoning": "string describing the causal chain",
    "assumption_evaluation": {{"assumption_1": "evaluation", ...}},
    "prediction_verification": "assessment of predictions",
    "classification": "PROMISING|NEEDS_REFINEMENT|FLAWED",
    "feedback": "detailed review feedback"
}}
"""

EVOLUTION_PROMPT = """You are a senior research scientist evolving a scientific hypothesis to address weaknesses.

# Research Goal
{goal}

# Original Hypothesis
{parent_hypothesis}

# Review Feedback
{feedback}

# Instructions
1. Address the weaknesses identified in the review feedback.
2. Generate an EVOLVED hypothesis that is stronger than the original.
3. You may:
   - Refine the mechanism to be more specific
   - Add constraints or boundary conditions
   - Explore a different but related mechanism
   - Combine with complementary pathways
4. The evolved hypothesis MUST still be falsifiable and novel.

# Output Format
Respond in the following markdown format:

# Evolved Hypothesis
[Your detailed mechanistic evolved hypothesis]

# Key Improvements
- [Improvement 1 over the original]
- [Improvement 2 over the original]

# Falsifiable Predictions
- [Prediction 1]
- [Prediction 2]
- [Prediction 3]

# Assumptions
- [Assumption 1]
- [Assumption 2]
"""


def _call_llm(prompt: str, model: Optional[str] = None, max_tokens: int = 8000) -> str:
    """Call litellm with error handling."""
    model = model or DEFAULT_MODEL
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.4,
        )
        content = response.choices[0].message.content
        if not content:
            return json.dumps({"error": "Empty response from LLM"})
        return content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return json.dumps({"error": str(e)})


def _parse_hypothesis_markdown(text: str) -> dict:
    """Parse hypothesis markdown into structured JSON."""
    result = {"hypothesis": "", "predictions": [], "assumptions": []}

    sections = text.split("#")
    for section in sections:
        section = section.strip()
        lower = section.lower()

        if lower.startswith("hypothesis"):
            result["hypothesis"] = section.split("\n", 1)[-1].strip()
        elif "prediction" in lower:
            predictions = []
            for line in section.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    predictions.append(line.lstrip("-* ").strip())
            result["predictions"] = predictions
        elif "assumption" in lower:
            assumptions = []
            for line in section.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    assumptions.append(line.lstrip("-* ").strip())
            result["assumptions"] = assumptions

    return result


def generate_hypothesis(
    goal: str,
    literature_review: str = "",
    field: str = "biology",
) -> str:
    """
    Generate a novel, falsifiable scientific hypothesis based on a research goal.

    Uses DeepSeek V4 Pro to generate mechanistic hypotheses with testable predictions
    and explicit assumptions. The hypothesis explains HOW and WHY, not just WHAT.

    Args:
        goal: The research goal (e.g., "Identify novel drug targets for Alzheimer's")
        literature_review: Summary of relevant scientific literature and background
        field: Scientific domain/field of expertise (default: "biology")

    Returns:
        JSON string with hypothesis, predictions, assumptions, and metadata
    """
    prompt = GENERATION_PROMPT.format(
        field=field,
        goal=goal,
        literature_review=literature_review or "Use your domain knowledge.",
    )
    response = _call_llm(prompt, DEFAULT_MODEL, max_tokens=16000)
    parsed = _parse_hypothesis_markdown(response)

    return json.dumps({
        "hypothesis": parsed["hypothesis"],
        "predictions": parsed["predictions"],
        "assumptions": parsed["assumptions"],
        "field": field,
        "model": DEFAULT_MODEL,
    }, indent=2)


def review_hypothesis(
    goal: str,
    hypothesis: str,
    predictions: str = "",
    assumptions: str = "",
) -> str:
    """
    Perform a rigorous scientific review of a hypothesis.

    Evaluates the causal reasoning chain, verifies assumptions against scientific
    knowledge, checks that predictions are falsifiable, and classifies the
    hypothesis as PROMISING, NEEDS_REFINEMENT, or FLAWED.

    Args:
        goal: The research goal this hypothesis addresses
        hypothesis: The hypothesis statement to review
        predictions: Comma-separated list of predictions
        assumptions: Comma-separated list of assumptions

    Returns:
        JSON string with causal reasoning, assumption evaluation, classification,
        and detailed feedback
    """
    prompt = REVIEW_PROMPT.format(
        goal=goal,
        hypothesis=hypothesis,
        predictions=predictions or "Not provided",
        assumptions=assumptions or "Not provided",
    )
    response = _call_llm(prompt, DEFAULT_CHEAP_MODEL, max_tokens=8000)

    try:
        return json.dumps(json.loads(response), indent=2)
    except json.JSONDecodeError:
        return json.dumps({
            "classification": "NEEDS_REFINEMENT",
            "feedback": response[:2000],
            "causal_reasoning": "",
            "parse_error": "Could not parse structured response",
        }, indent=2)


def evolve_hypothesis(
    goal: str,
    parent_hypothesis: str,
    feedback: str = "",
) -> str:
    """
    Evolve an existing hypothesis to address identified weaknesses.

    Takes an original hypothesis and review feedback, then generates an improved
    version that is more specific, constrained, or explores complementary mechanisms.

    Args:
        goal: The research goal being pursued
        parent_hypothesis: The original hypothesis to evolve from
        feedback: Review feedback or weaknesses to address

    Returns:
        JSON string with evolved hypothesis, key improvements, predictions, and assumptions
    """
    prompt = EVOLUTION_PROMPT.format(
        goal=goal,
        parent_hypothesis=parent_hypothesis,
        feedback=feedback or "Address any weaknesses in specificity, novelty, or mechanistic detail.",
    )
    response = _call_llm(prompt, DEFAULT_MODEL, max_tokens=16000)
    parsed = _parse_hypothesis_markdown(response)

    improvements = []
    for line in response.split("\n"):
        line = line.strip()
        if "improvement" in line.lower() and (line.startswith("-") or line.startswith("*")):
            improvements.append(line.lstrip("-* ").strip())

    return json.dumps({
        "evolved_hypothesis": parsed["hypothesis"],
        "key_improvements": improvements or ["See hypothesis for improvements"],
        "predictions": parsed["predictions"],
        "assumptions": parsed["assumptions"],
        "model": DEFAULT_MODEL,
    }, indent=2)
