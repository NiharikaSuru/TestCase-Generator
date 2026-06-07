"""
Test Code Writer Agent
----------------------
Takes the list of test cases and writes the actual unit test code
in the appropriate test framework (pytest for Python, Jest for JS/TS).

Returns the raw test file source string stored in AgentState['test_code'].
"""

from langchain_core.messages import SystemMessage, HumanMessage
import json
from llm.factory import get_llm
from utils.validators import validate_code_response, validate_state_keys
from utils.retry_helper import invoke_llm_with_retry


PYTHON_PROMPT = """You are an expert Python test engineer who writes pytest test code.
Given source code and a list of test cases, write a complete pytest test file.

Rules:
- ALWAYS start with required imports:
  * Import the function/class under test: from solution import <name>
  * Import pytest: import pytest
- Each test case from the list must have its own test function named test_<name>
- Use descriptive docstrings on each test function
- Handle expected exceptions with pytest.raises()
- Do NOT add assertions yet — just structure the test functions with a `pass` body or a minimal stub
- Return ONLY the raw Python code — no markdown fences, no explanation

CRITICAL - Required Imports:
```python
from solution import function_name
import pytest  # ALWAYS include this for pytest.raises()
```

CRITICAL - Avoid Over-Engineering:
- DO NOT create fixtures for simple values (integers, strings, booleans)
- WRONG: @pytest.fixture def number(): return 5
- CORRECT: Just use 5 directly in the test: def test_add(): pass  # Will use add(5, 3) later
- ONLY use fixtures for complex objects (database connections, mock objects, file handles)
- Keep tests simple and readable

CRITICAL - Test Function Syntax:
- Test functions CANNOT have default parameter values
- WRONG: def test_example(price=10.0, discount=20.0):
- CORRECT: def test_example(): or def test_example(price_fixture, discount_fixture):
- If you need different input values for different tests, either:
  * Create separate fixtures with specific names (ONLY for complex objects)
  * Or use direct values in the test body (PREFERRED for simple values)
  * Or use @pytest.mark.parametrize
- Each test function name MUST be unique (no duplicates)
- Each parameter name within a function MUST be unique
- WRONG: def test_example(value, value):  # duplicate parameter!
- WRONG: def test_example(fixture_a, fixture_a):  # duplicate parameter!
- CORRECT: def test_example(value_a, value_b):
- CORRECT: def test_example(first_fixture, second_fixture):

Fixture Usage Rules:
- If a test needs the SAME fixture value twice, use the fixture ONCE and reference it multiple times
- WRONG: def test_add(num, num):  # Python syntax error!
- CORRECT: def test_add(num): pass  # Use num twice in body: add(num, num)
- If a test needs DIFFERENT values, create different fixtures or use direct values
- CORRECT: def test_add(num_a, num_b): pass  # Use fixtures if complex objects
- PREFERRED: def test_add(): pass  # Use direct values if simple: add(5, 3)"""

JS_PROMPT = """You are an expert JavaScript/TypeScript test engineer who writes Jest test code.
Given source code and a list of test cases, write a complete Jest test file.

Rules:
- Import the function/class under test (use `const { <name> } = require('./solution')` for JS
  or `import { <name> } from './solution'` for TS)
- Group tests with describe() blocks by category (Happy Path, Edge Cases, Error Cases)
- Each test case must have its own test() or it() block named after the test case name
- Add a JSDoc comment on each test block describing what it tests
- Handle expected exceptions with expect(() => ...).toThrow()
- Do NOT add assertions yet — just stub the test bodies
- Return ONLY the raw code — no markdown fences, no explanation"""


def run_test_code_writer(state: dict) -> dict:
    """
    LangGraph node: renders the test file skeleton from the test case list.
    """
    # Validate state has required keys
    validate_state_keys(state, ["code", "language", "framework", "analysis", "test_cases"], 
                       "Test Code Writer")
    
    llm = get_llm(temperature=0)

    language = state["language"]
    system_prompt = PYTHON_PROMPT if language == "python" else JS_PROMPT

    test_cases_str = json.dumps(state.get("test_cases", []), indent=2)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=(
                f"Language: {language}\n"
                f"Framework: {state['framework']}\n\n"
                f"Original code:\n```{language}\n{state['code']}\n```\n\n"
                f"Code analysis:\n{state['analysis']}\n\n"
                f"Test cases to implement:\n{test_cases_str}\n\n"
                f"Similar prior examples (optional context):\n{state.get('memory_context', '') or 'None'}"
            )
        ),
    ]

    response = invoke_llm_with_retry(llm, messages, max_retries=5)
    raw = response.content.strip()

    # Validate and clean the response
    is_valid, test_code, validation_msg = validate_code_response(raw, language)
    
    if not is_valid:
        validation_lower = validation_msg.lower()
        if "default parameter" in validation_lower or "duplicate" in validation_lower:
            # Critical syntax error - log and use minimal fallback
            print(f"[TEST CODE WRITER ERROR] {validation_msg}")
            print(f"[TEST CODE WRITER] Falling back to minimal skeleton")
            # Don't use the invalid code
            if language == "python":
                test_code = "import pytest\n\n# Test generation failed due to syntax errors.\n# Please regenerate."
            else:
                test_code = "// Test generation failed due to syntax errors.\n// Please regenerate."
            
            # Add warning to step
            step = {
                "agent": "Test Code Writer",
                "status": "completed",
                "output_summary": f"⚠️ Syntax error: {validation_msg}. Please regenerate."
            }
        elif not test_code:
            # Create minimal fallback
            if language == "python":
                test_code = "import pytest\n\n# Tests could not be generated. Please try again."
            else:
                test_code = "// Tests could not be generated. Please try again."
            
            step = {
                "agent": "Test Code Writer",
                "status": "completed",
                "output_summary": f"Wrote {language}/{state['framework']} test file skeleton with "
                                  f"{len(state.get('test_cases', []))} test stubs.",
            }
    else:
        step = {
            "agent": "Test Code Writer",
            "status": "completed",
            "output_summary": f"Wrote {language}/{state['framework']} test file skeleton with "
                              f"{len(state.get('test_cases', []))} test stubs.",
        }

    return {
        **state,
        "test_code": test_code,
        "agent_steps": state.get("agent_steps", []) + [step],
    }
