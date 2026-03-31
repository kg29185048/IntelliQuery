from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END

from agents.query_generator import generate_query
from agents.validator import validate_query
from agents.executor import execute_query


class State(TypedDict):
    user_query: str
    schema: Dict[str, Any]

    llm_output: Optional[Dict]
    validated: Optional[Dict]
    result: Optional[Dict]


# 🔹 Nodes

def query_gen_node(state: State):
    output = generate_query(state["user_query"], state["schema"])
    return {"llm_output": output}


def route_after_query(state: State):
    status = state["llm_output"].get("status")

    if status == "ambiguous":
        return "clarify"
    elif status == "error":
        return "error"
    return "validate"


def clarify_node(state: State):
    return {
        "result": {
            "type": "clarification",
            "message": state["llm_output"].get("clarification_question", "")
        }
    }


def error_node(state: State):
    return {
        "result": {
            "type": "error",
            "message": state["llm_output"].get("error", "Unknown error")
        }
    }


def validate_node(state: State):
    result = validate_query(state["llm_output"])

    if result["status"] == "fail":
        return {
            "result": {
                "type": "error",
                "message": result["error"]
            }
        }

    return {"validated": result["query"]}


def execute_node(state: State):
    result = execute_query(state["validated"])

    if result["status"] == "error":
        return {
            "result": {
                "type": "error",
                "message": result["error"]
            }
        }

    return {
        "result": {
            "type": "success",
            "data": result["data"],
            "explanation": result["explanation"]
        }
    }


# 🔹 Build Graph

graph = StateGraph(State)

graph.add_node("query_gen", query_gen_node)
graph.add_node("clarify", clarify_node)
graph.add_node("error", error_node)
graph.add_node("validate", validate_node)
graph.add_node("execute", execute_node)

graph.add_edge(START, "query_gen")

graph.add_conditional_edges(
    "query_gen",
    route_after_query,
    {
        "clarify": "clarify",
        "error": "error",
        "validate": "validate"
    }
)

graph.add_edge("validate", "execute")

graph.add_edge("clarify", END)
graph.add_edge("error", END)
graph.add_edge("execute", END)

app = graph.compile()