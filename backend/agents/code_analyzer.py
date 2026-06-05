"""
Code Analysis Agent
-------------------
Analyses the submitted source code and extracts:
  - Function/class signatures
  - Logic summary
  - External dependencies
  - Complexity notes

Returns a structured JSON string stored in AgentState['analysis'].
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from llm.factory import get_llm
from utils.validators import validate_analysis_response, validate_state_keys
from utils.retry_helper import invoke_llm_with_retry


SYSTEM_PROMPT = """You are an expert code analysis agent.
Your job is to deeply understand a piece of source code and return a structured JSON analysis.

IMPORTANT - Analyze Type Checking & Validation:
- If code uses isinstance() checks, note EXACTLY what types are accepted/rejected
- If code validates ranges (if x < 0, if x > 100), note the constraints
- If code performs modulo operations (%), note what this means (even/odd, etc.)
- If code has division, note potential ZeroDivisionError cases

Return ONLY valid JSON with the following keys:
{
  "signatures": ["list of function/class/method signatures"],
  "summary": "clear plain-English description including type checking and validation behavior",
  "dependencies": ["list of external libraries, imports or modules used"],
  "complexity": "brief note on time/space complexity or overall complexity",
  "parameters": [{"name": "...", "type": "...", "description": "...", "accepted_values": "e.g., 'any integer including negative and zero' or 'positive integers only'"}],
  "return_value": "description of what is returned",
  "side_effects": "any I/O, mutations, or side effects",
  "type_validation": "describe isinstance or type checks if present",
  "edge_cases": "list potential edge cases like zero, negative numbers, empty inputs"
}

Examples of good analysis:
- "Uses isinstance(n, int) so accepts positive, negative, and zero integers but rejects floats, strings, None"
- "Returns n % 2 == 0, which means True for even numbers (including 0, -2, -4) and False for odd"
- "No range validation, so negative numbers are valid inputs"

Do not include markdown fences or extra text — return raw JSON only."""


def run_code_analyzer(state: dict) -> dict:
    """
    LangGraph node: analyses the source code in state and writes
    analysis (JSON string) back into state.
    """
    # Validate state has required keys
    validate_state_keys(state, ["code", "language"], "Code Analyzer")
    
    llm = get_llm(temperature=0)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Language: {state['language']}\n\n"
                f"Code:\n```{state['language']}\n{state['code']}\n```\n\n"
                f"Similar prior examples (optional context):\n{state.get('memory_context', '') or 'None'}"
            )
        ),
    ]

    response = invoke_llm_with_retry(llm, messages, max_retries=3)
    raw = response.content.strip()

    # Validate and clean the response
    is_valid, analysis, validation_msg = validate_analysis_response(raw)
    
    if not is_valid:
        # This shouldn't happen as validate_analysis_response creates fallback
        analysis = json.dumps({"summary": "Analysis failed", "signatures": [], 
                               "dependencies": [], "complexity": "unknown",
                               "parameters": [], "return_value": "", "side_effects": ""})

    step = {"agent": "Code Analyzer", "status": "completed",
            "output_summary": "Extracted signatures, logic summary, dependencies and complexity."}

    return {
        **state,
        "analysis": analysis,
        "agent_steps": state.get("agent_steps", []) + [step],
    }
