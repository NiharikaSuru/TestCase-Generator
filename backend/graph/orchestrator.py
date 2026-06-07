"""
LangGraph Orchestrator
----------------------
Defines the AgentState and the StateGraph that wires the four agents
into a linear pipeline:

  analyze_code → generate_test_cases → write_test_code → add_assertions → END

The compiled graph is invoked by the FastAPI endpoint.
"""

import os
import time
from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END

from agents.code_analyzer import run_code_analyzer
from agents.test_case_generator import run_test_case_generator
from agents.test_code_writer import run_test_code_writer
from agents.assertion_agent import run_assertion_agent


# Rate limit delay between agents (seconds) - helps avoid hitting API limits
INTER_AGENT_DELAY = float(os.getenv("INTER_AGENT_DELAY", "2.0"))


class AgentState(TypedDict):
    """Shared state passed between every node in the pipeline."""
    code: str                   # Raw source code submitted by the user
    language: str               # python | javascript | typescript
    framework: str              # pytest | jest
    analysis: str               # JSON string — output of Code Analyzer
    test_cases: List[Any]       # List of dicts — output of Test Case Generator
    test_code: str              # Skeleton test file — output of Test Code Writer
    final_tests: str            # Complete test file — output of Assertion Agent
    memory_context: str         # Similar historical runs from vector memory
    agent_steps: List[Any]      # Audit log of completed agent steps


def rate_limited_agent_wrapper(agent_func):
    """Wrapper to add delay after agent execution to prevent rate limits."""
    def wrapper(state: AgentState) -> AgentState:
        result = agent_func(state)
        # Add delay after agent completes (except for the last agent)
        if INTER_AGENT_DELAY > 0:
            time.sleep(INTER_AGENT_DELAY)
        return result
    return wrapper


def build_graph() -> StateGraph:
    """Constructs and compiles the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # Register the four agent nodes with rate limiting wrappers
    graph.add_node("analyze_code", rate_limited_agent_wrapper(run_code_analyzer))
    graph.add_node("generate_test_cases", rate_limited_agent_wrapper(run_test_case_generator))
    graph.add_node("write_test_code", rate_limited_agent_wrapper(run_test_code_writer))
    graph.add_node("add_assertions", run_assertion_agent)  # Last agent doesn't need delay

    # Linear pipeline edges
    graph.set_entry_point("analyze_code")
    graph.add_edge("analyze_code", "generate_test_cases")
    graph.add_edge("generate_test_cases", "write_test_code")
    graph.add_edge("write_test_code", "add_assertions")
    graph.add_edge("add_assertions", END)

    return graph.compile()


# Compile once at import time so FastAPI reuses the same compiled graph
compiled_graph = build_graph()


def run_pipeline(code: str, language: str, framework: str, memory_context: str = "") -> AgentState:
    """
    Runs the full 4-agent pipeline and returns the final state.

    Args:
        code:      Source code to generate tests for.
        language:  'python', 'javascript', or 'typescript'.
        framework: 'pytest' or 'jest'.

    Returns:
        Final AgentState with all fields populated.
    """
    initial_state: AgentState = {
        "code": code,
        "language": language,
        "framework": framework,
        "analysis": "",
        "test_cases": [],
        "test_code": "",
        "final_tests": "",
        "memory_context": memory_context,
        "agent_steps": [],
    }
    return compiled_graph.invoke(initial_state)
