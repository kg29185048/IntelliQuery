"""
Visualization Agent — suggests the best chart config for query results.

Refactored to use ChatPromptTemplate + JsonOutputParser LCEL chain.
"""

import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import get_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LCEL chain
# ---------------------------------------------------------------------------
_SYSTEM = """You are an expert Data Visualization Agent.

Analyze the user's query and the resulting JSON data sample, then determine the best
way to visualize it.

STRICT RULES:
1. Return ONLY a valid JSON object — no conversational text, no markdown.
2. You MUST TRY YOUR BEST to visualize the data. If there is ANY combination of a categorical/text field (for x_axis) and a numeric field (for y_axis), you MUST return {{"visualizable": true}}.
3. ONLY return {{"visualizable": false}} if the data is completely impossible to chart (e.g., just a single row/value, no numeric fields exist, or it's a flat list of strings).
4. If it CAN be visualized, return:
{{
  "visualizable": true,
  "chart_type": "bar",
  "x_axis": "exact_key_for_x",
  "y_axis": "exact_key_for_y",
  "title": "A short, descriptive title"
}}
5. chart_type MUST be one of: "bar", "line", "scatter", "pie", or "area".
   - For "pie", x_axis acts as the slice label, and y_axis acts as the numeric slice size.
6. CRITICAL: x_axis and y_axis MUST be exact dictionary keys present in the data sample below. Do not guess, format, or hallucinate keys.
   - IMPORTANT: If the categorical field is literally named "_id" in the JSON, you MUST output "_id" as the x_axis. Do NOT rename it to what it represents (e.g. do not output "genre" if the key is "_id").
7. y_axis MUST map to a numeric value in the data sample. If a field looks like a number but is a string (e.g., "10"), it counts as numeric.
8. HEURISTICS FOR CHART TYPE:
   - "pie": Use if the query asks for distribution, share, percentage, or if there are <= 7 categories representing parts of a whole (e.g., count by status/genre).
   - "line" or "area": Use for time-series data (e.g., when x_axis is a date, year, or month).
   - "scatter": Use if BOTH x_axis and y_axis are numeric.
   - "bar": Default fallback for comparing quantities across categories."""

_HUMAN = "User query: {user_query}\n\nData sample (first few rows):\n{data}"

_viz_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human",  _HUMAN),
])
_viz_chain = _viz_prompt | get_llm(json_mode=True) | JsonOutputParser()


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def generate_visualization_config(user_query: str, data: list) -> dict:
    """
    Returns a visualization config dict for the given query result data.
    Falls back to {{"visualizable": false}} on any failure.
    """
    data_sample = data[:10] if isinstance(data, list) else data

    try:
        return _viz_chain.invoke({
            "user_query": user_query,
            "data":       json.dumps(data_sample, default=str),
        })
    except Exception as exc:
        logger.error("[VisualizationAgent] Failed: %s", exc)
        return {"visualizable": False, "error": "Failed to generate visualization config."}