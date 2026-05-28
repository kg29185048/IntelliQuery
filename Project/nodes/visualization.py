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

Analyze the user's query and the resulting data sample, then determine the best
way to visualize it.

STRICT RULES:
1. Return ONLY a valid JSON object — no conversational text, no markdown.
2. If the data cannot be visualized (e.g., a single string, list of names only,
   or no numeric y-axis values), return {{"visualizable": false}}.
3. If it CAN be visualized, return:
{{
  "visualizable": true,
  "chart_type": "bar",
  "x_axis": "field_name_for_x",
  "y_axis": "field_name_for_y",
  "title": "A short, descriptive title"
}}
4. chart_type must be one of: "bar", "line", "scatter".
5. y_axis MUST be a numeric field present in the data sample."""

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
    data_sample = data[:5] if isinstance(data, list) else data

    try:
        return _viz_chain.invoke({
            "user_query": user_query,
            "data":       json.dumps(data_sample, default=str),
        })
    except Exception as exc:
        logger.error("[VisualizationAgent] Failed: %s", exc)
        return {"visualizable": False, "error": "Failed to generate visualization config."}