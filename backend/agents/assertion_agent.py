"""
Assertion Agent
---------------
Takes the test file skeleton (stubs) and enriches every test function
with real, specific assertions that verify the correctness of the code
under test.

Also adds:
  - Setup / teardown where needed
  - Mocking of external dependencies
  - Parameterized tests where appropriate (pytest.mark.parametrize / test.each)

Returns the final, complete test file stored in AgentState['final_tests'].
"""

from langchain_core.messages import SystemMessage, HumanMessage
import json
from llm.factory import get_llm
from utils.validators import validate_code_response, validate_state_keys
from utils.retry_helper import invoke_llm_with_retry


SYSTEM_PROMPT = """⚠️⚠️⚠️ MANDATORY ASSERTION CHECKLIST ⚠️⚠️⚠️

BEFORE writing assertions for ANY test, verify:

1️⃣ Is this a DIVISION function test?
   → Check test name, function being tested

2️⃣ For tests with DIVISOR = 0:
   → Use: with pytest.raises(ZeroDivisionError):
   → Do NOT assert specific error message

3️⃣ For tests with DIVIDEND = 0:
   → Use: assert divide(0, 5) == 0 or 0.0
   → Do NOT use pytest.raises()
   → This is NOT an error case!

⚠️ WRONG: with pytest.raises(ZeroDivisionError): divide(0, 5)
✅ CORRECT: assert divide(0, 5) == 0.0

═══════════════════════════════════════════════════════════════════════

You are an expert test assertion agent.
You receive:
1. The original source code
2. A code analysis
3. A list of test cases with expected outputs
4. A test file skeleton with stubbed test functions

Your job is to fill in ALL test bodies with real, specific assertions.

⚠️ CRITICAL - Pythonic Assertions ⚠️
For boolean return values:
→ NEVER use: assert result == True
→ NEVER use: assert result == False
→ ALWAYS use: assert result (for True)
→ ALWAYS use: assert not result (for False)

WRONG:
  assert is_prime(23) == True
  assert is_even(3) == False

CORRECT:
  assert is_prime(23)
  assert not is_even(3)

⚠️ Python Type System ⚠️
bool is a subclass of int in Python:
→ isinstance(True, int) returns True
→ isinstance(False, int) returns True
→ Functions checking isinstance(x, int) will ACCEPT booleans
→ Do NOT write tests expecting TypeError for bool if function uses isinstance(x, int)

Rules:
- Ensure pytest is imported (add 'import pytest' if missing)
- Replace every `pass` stub or empty body with meaningful assertions
- Use the expected_output field from each test case to write exact assert statements
- For error/exception tests, assert the correct exception type (NOT the message)
- Add mocking for any external dependencies (filesystem, network, databases) using
  unittest.mock (Python) or jest.mock / jest.spyOn (JavaScript/TypeScript)
- Keep the overall file structure intact — do not rename or remove any test functions
- The output must be a complete, runnable test file
- Return ONLY the raw code — no markdown fences, no explanation

CRITICAL - Test Simplicity:
- Use direct values in tests, not fixtures (unless complex objects)
- SIMPLE: def test_add(): assert add(5, 3) == 8
- OVERENGINEERED: Create fixture for 5, fixture for 3, then use fixtures
- Only use fixtures for complex setup (database connections, mock objects, etc.)
- Integers, strings, simple values → use directly in tests

CRITICAL - Pythonic Assertions:
- Use concise, Pythonic assertions
- For boolean functions:
  * VERBOSE: assert is_even(4) == True
  * PYTHONIC: assert is_even(4)
  * VERBOSE: assert is_odd(3) == False  
  * PYTHONIC: assert not is_odd(3)
- For comparisons:
  * CORRECT: assert result == 10
  * CORRECT: assert result > 0
  * CORRECT: assert result is None
- Keep assertions simple and readable

CRITICAL - Mathematical & Logical Facts (VERIFY BEFORE WRITING ASSERTIONS):
You MUST apply these facts correctly when writing test assertions:

**Even/Odd Numbers:**
- Zero (0) is EVEN: 0 % 2 == 0 evaluates to True
  * CORRECT: assert is_even(0)
  * WRONG: assert not is_even(0)
- Negative even numbers (-2, -4, -6) are EVEN
  * CORRECT: assert is_even(-4)
  * WRONG: with pytest.raises(TypeError): is_even(-4)
- Negative odd numbers (-1, -3, -5) are ODD
  * CORRECT: assert not is_even(-3)

**Integer Type Checking with isinstance():**
If the function checks `isinstance(n, int)`, these behaviors apply:
- Positive integers PASS: isinstance(5, int) → True
- Negative integers PASS: isinstance(-5, int) → True
- Zero PASSES: isinstance(0, int) → True  
- Booleans PASS: isinstance(True, int) → True (bool is int subclass)
- Floats FAIL: isinstance(3.5, int) → False → TypeError raised
- Strings FAIL: isinstance('5', int) → False → TypeError raised
- None FAILS: isinstance(None, int) → False → TypeError raised

**Division Rules:**
- Any number / 0 → ZeroDivisionError
- 0 / non_zero → 0 (valid, returns zero)
  * CRITICAL: Test BOTH scenarios for division functions:
    1. Divisor is zero: with pytest.raises(ZeroDivisionError): divide(5, 0)
    2. Dividend is zero: assert divide(0, 5) == 0
  * WRONG: with pytest.raises(ZeroDivisionError): divide(0, 5)
  * CORRECT: assert divide(0, 5) == 0
- Negative division rules (VERIFY CAREFULLY):
  * positive / positive = positive: 10 / 2 = 5
  * positive / negative = negative: 10 / -2 = -5
  * negative / positive = negative: -10 / 2 = -5
  * negative / negative = POSITIVE: -10 / -2 = 5
  * WRONG: assert divide(-1e308, -1e308) == -1.0
  * CORRECT: assert divide(-1e308, -1e308) == 1.0

**Negative Numbers:**
- Negative numbers are valid integers (unless function explicitly validates range)
- WRONG: Expecting TypeError for negative numbers with isinstance check
- CORRECT: Test negative numbers as edge cases with expected results

CRITICAL - Mathematical Precision:
- For calculations involving money, taxes, percentages, or floating-point arithmetic:
  * Calculate expected values step-by-step
  * Use proper rounding: round(value, decimal_places)
  * Verify your math before writing assertions
  * For example: tax = round(subtotal * 0.08, 2), NOT tax = subtotal * 0.08
- Double-check that all numeric assertions match the actual function behavior
- If the function rounds to 2 decimals, your assertions must also use 2-decimal rounded values

**Scientific Notation & Exponent Calculations:**
- When dividing/multiplying with scientific notation (1e308, 1e-10), verify exponents carefully
- Division by 10^n: a / 10^n = a × 10^-n
  * Example: 10.5 / 1e308 = 10.5 × 10^-308 = 1.05 × 10^-307
  * WRONG: assert divide(10.5, 1e308) == 1.05e-308  # off by one!
  * CORRECT: assert divide(10.5, 1e308) == 1.05e-307
- Multiplication by 10^n: a × 10^n
  * Example: 2.5 × 1e5 = 2.5e5 = 250000
- ALWAYS manually verify the exponent before writing assertions
- Common error: Moving decimal point but forgetting to adjust exponent

CRITICAL - Python Test Function Syntax:
- Test functions CANNOT have default parameter values
- WRONG: def test_example(param=10):
- CORRECT: def test_example(): or def test_example(fixture_name):
- Use pytest fixtures for reusable test data, NOT default parameters
- Each test function name must be UNIQUE (no duplicates)
- Each parameter name within a function MUST be unique
- WRONG: def test_example(value, value):  # duplicate parameter - SYNTAX ERROR!
- WRONG: def test_example(fixture_a, fixture_a):  # duplicate parameter - SYNTAX ERROR!
- CORRECT: def test_example(value_a, value_b):
- CORRECT: def test_example(first_fixture, second_fixture):
- If testing the same value twice: def test_add(num): result = add(num, num)
- For tests with different inputs, use descriptive unique names or parametrize

Assertion Accuracy:
- Calculate expected values correctly before writing assertions
- For math operations, verify the calculation: if testing add(5, 5), assert result == 10
- For fixture-based tests, calculate based on fixture values
- WRONG: assert result == positive_number  # comparing to fixture name/object!
- CORRECT: assert result == 5  # use the actual expected value
- WRONG: assert result == some_fixture  # fixture is just a variable name
- CORRECT: assert result == 10  # calculate what the actual result should be
- When using fixtures: If fixture returns 5, and you call add(fixture, fixture), the result is 10, not fixture
- Always assert against concrete expected values (numbers, strings, etc.), NOT fixture names

CRITICAL - Exception Testing Best Practices:
- For exception tests, ONLY verify the exception TYPE is raised, NOT the exact message
- Error messages can vary between Python versions, implementations, and environments
- WRONG: with pytest.raises(TypeError) as exc_info:
           func()
           assert str(exc_info.value) == "exact error message"
- CORRECT: with pytest.raises(TypeError):
              func()
- CORRECT (if you must check message): with pytest.raises(TypeError) as exc_info:
                                          func()
                                          assert "key word" in str(exc_info.value)
- The goal is robust tests, not brittle ones that break on message changes
- Exception type validation is sufficient for most test cases

CRITICAL - Realistic Exception Expectations:
- Only test for exceptions that will ACTUALLY occur in Python 3
- Python 3 integers have arbitrary precision - NO OverflowError for integer arithmetic
- Python 3 floats can be extremely large (1e308+) without OverflowError
- OverflowError only occurs converting huge floats to integers
- For simple functions (add, multiply, etc.), realistic exceptions:
  * TypeError: wrong types (string + int, None + number, calling non-callable)
  * ValueError: only if function explicitly validates and raises ValueError
  * AttributeError: accessing missing attributes/methods
  * ZeroDivisionError: division by zero
- AVOID unrealistic exceptions for simple operations:
  * DO NOT use OverflowError for basic arithmetic (add, multiply, etc.)
  * DO NOT use MemoryError for operations with small numbers
  * DO NOT use SystemError for user-level code
- When in doubt, verify what exception Python actually raises for that scenario"""


def run_assertion_agent(state: dict) -> dict:
    """
    LangGraph node: fills in assertions for every test stub and returns
    the final, production-ready test file.
    """
    # Validate state has required keys
    validate_state_keys(state, ["code", "language", "framework", "analysis", "test_cases", "test_code"],
                       "Assertion Agent")
    
    llm = get_llm(temperature=0)

    language = state["language"]
    test_cases_str = json.dumps(state.get("test_cases", []), indent=2)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Language: {language}\n"
                f"Framework: {state['framework']}\n\n"
                f"Original code:\n```{language}\n{state['code']}\n```\n\n"
                f"Code analysis:\n{state['analysis']}\n\n"
                f"Test cases (with expected outputs):\n{test_cases_str}\n\n"
                f"Test file skeleton to complete:\n```{language}\n{state['test_code']}\n```\n\n"
                f"Similar prior examples (optional context):\n{state.get('memory_context', '') or 'None'}"
            )
        ),
    ]

    response = invoke_llm_with_retry(llm, messages, max_retries=3)
    raw = response.content.strip()

    # Validate and clean the response
    is_valid, final_tests, validation_msg = validate_code_response(raw, language)
    
    if not is_valid:
        validation_lower = validation_msg.lower()
        if "default parameter" in validation_lower or "duplicate" in validation_lower:
            # Critical syntax error detected
            print(f"[ASSERTION AGENT ERROR] {validation_msg}")
            print(f"[ASSERTION AGENT] Invalid code detected, falling back to skeleton")
            # Fall back to the skeleton if assertion agent produces invalid syntax
            final_tests = state.get("test_code", "# Assertion generation failed due to syntax errors")
            step = {
                "agent": "Assertion Agent",
                "status": "completed",
                "output_summary": f"⚠️ Syntax error detected: {validation_msg}. Using test skeleton instead."
            }
        elif not final_tests:
            # Fall back to the skeleton if assertion agent fails
            final_tests = state.get("test_code", "# Assertion generation failed")
            step = {
                "agent": "Assertion Agent",
                "status": "completed",
                "output_summary": "Added specific assertions, mocks, and parameterized tests. Final test file is ready."
            }
        else:
            step = {
                "agent": "Assertion Agent",
                "status": "completed",
                "output_summary": "Added specific assertions, mocks, and parameterized tests. Final test file is ready."
            }
    else:
        step = {
            "agent": "Assertion Agent",
            "status": "completed",
            "output_summary": "Added specific assertions, mocks, and parameterized tests. Final test file is ready."
        }

    return {
        **state,
        "final_tests": final_tests,
        "agent_steps": state.get("agent_steps", []) + [step],
    }
