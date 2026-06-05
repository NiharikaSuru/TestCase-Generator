"""
Input and Output Validation Utilities
--------------------------------------
Provides comprehensive validation for:
- User input (code, language, framework)
- LLM responses (JSON, code, test cases)
- State transitions between agents
"""

import json
import re
from typing import Any, Dict, List, Tuple
from fastapi import HTTPException


# Constants
MAX_CODE_LENGTH = 50000  # ~50KB max code input
MIN_CODE_LENGTH = 10
ALLOWED_LANGUAGES = {"python", "javascript", "typescript"}
ALLOWED_FRAMEWORKS = {"pytest", "jest", "unittest", "mocha"}


def validate_code_input(code: str, language: str) -> Tuple[bool, str]:
    """
    Validate user code input.
    
    Returns:
        (is_valid, error_message)
    """
    # Check empty
    if not code or not code.strip():
        return False, "Code cannot be empty or only whitespace."
    
    # Check length
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code is too long. Maximum {MAX_CODE_LENGTH} characters allowed."
    
    if len(code.strip()) < MIN_CODE_LENGTH:
        return False, f"Code is too short. Minimum {MIN_CODE_LENGTH} characters required."
    
    # Check for excessive special characters (potential injection)
    special_char_ratio = sum(1 for c in code if not c.isalnum() and c not in ' \n\t_-()[]{},.;:"\'/\\') / len(code)
    if special_char_ratio > 0.5:
        return False, "Code contains too many unusual characters. Please provide valid source code."
    
    # Language-specific basic validation
    if language == "python":
        # Should have at least one def or class
        if not re.search(r'\b(def|class)\b', code):
            return False, "Python code should contain at least one function (def) or class definition."
    
    elif language in ["javascript", "typescript"]:
        # Should have at least one function declaration
        if not re.search(r'\b(function|const|let|var|class|export)\b', code):
            return False, f"{language.title()} code should contain at least one function or class definition."
    
    return True, ""


def validate_json_structure(json_str: str, required_keys: List[str] = None) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validate JSON string and optionally check for required keys.
    
    Returns:
        (is_valid, parsed_json, error_message)
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, {}, f"Invalid JSON: {str(e)}"
    
    if not isinstance(data, dict):
        return False, {}, "JSON must be an object/dictionary."
    
    if required_keys:
        missing = [key for key in required_keys if key not in data]
        if missing:
            return False, data, f"Missing required keys: {', '.join(missing)}"
    
    return True, data, ""


def validate_analysis_response(raw_response: str) -> Tuple[bool, str, str]:
    """
    Validate code analysis LLM response.
    
    Returns:
        (is_valid, cleaned_json, error_message)
    """
    # Strip markdown fences
    cleaned = strip_markdown_fences(raw_response)
    
    # Validate JSON structure
    required_keys = ["summary", "signatures", "dependencies"]
    is_valid, data, error = validate_json_structure(cleaned, required_keys)
    
    if not is_valid:
        # Create fallback
        fallback = {
            "summary": raw_response[:500] if raw_response else "Analysis failed",
            "signatures": [],
            "dependencies": [],
            "complexity": "unknown",
            "parameters": [],
            "return_value": "",
            "side_effects": ""
        }
        return True, json.dumps(fallback), "Fallback analysis created"
    
    # Validate field types
    if not isinstance(data.get("signatures", []), list):
        data["signatures"] = []
    if not isinstance(data.get("dependencies", []), list):
        data["dependencies"] = []
    if not isinstance(data.get("summary", ""), str):
        data["summary"] = str(data.get("summary", ""))
    
    return True, json.dumps(data), ""


def validate_test_cases_response(raw_response: str, code: str = None) -> Tuple[bool, List[Dict], str]:
    """
    Validate test cases LLM response.
    
    Args:
        raw_response: Raw LLM response containing test cases JSON
        code: Optional source code to check for operation-specific requirements
    
    Returns:
        (is_valid, test_cases_list, error_message)
    """
    # Strip markdown fences
    cleaned = strip_markdown_fences(raw_response)
    
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return False, [], f"Invalid test cases JSON: {str(e)}"
    
    if not isinstance(data, list):
        return False, [], "Test cases must be a JSON array."
    
    if len(data) == 0:
        return False, [], "No test cases generated. Please try again."
    
    # Validate each test case
    valid_cases = []
    categorization_warnings = []
    
    for i, tc in enumerate(data):
        if not isinstance(tc, dict):
            continue
        
        # Ensure required fields
        name = tc.get("name", f"test_case_{i}")
        description = tc.get("description", "No description")
        category = tc.get("category", "happy_path")
        inputs = tc.get("inputs", "")
        expected = tc.get("expected_output", "")
        
        # Validate category
        if category not in ["happy_path", "edge_case", "error_case"]:
            category = "happy_path"
        
        # Check for common categorization mistakes
        inputs_lower = str(inputs).lower()
        expected_lower = str(expected).lower()
        
        # Negative numbers should NOT be error_case
        if category == "error_case" and ("negative" in inputs_lower or "-" in inputs):
            # Check if it's actually expecting an exception
            if not any(exc in expected_lower for exc in ["error", "exception", "raise", "typeerror", "valueerror"]):
                categorization_warnings.append(
                    f"Test '{name}': Negative numbers categorized as error_case but no exception expected. Should be edge_case."
                )
        
        # Large numbers should NOT be error_case unless validating range
        if category == "error_case" and any(word in inputs_lower for word in ["large", "1000000", "big"]):
            if not any(exc in expected_lower for exc in ["error", "exception", "raise", "overflow"]):
                categorization_warnings.append(
                    f"Test '{name}': Large numbers categorized as error_case but no exception expected. Should be edge_case."
                )
        
        # Zero should NOT be error_case
        if category == "error_case" and ("zero" in inputs_lower or "=0" in inputs or inputs.strip() == "0"):
            if not any(exc in expected_lower for exc in ["error", "exception", "raise", "zerodivision"]):
                categorization_warnings.append(
                    f"Test '{name}': Zero categorized as error_case but no exception expected. Should be edge_case."
                )
        
        valid_cases.append({
            "name": name,
            "description": description,
            "category": category,
            "inputs": inputs,
            "expected_output": expected
        })
    
    if len(valid_cases) == 0:
        return False, [], "No valid test cases found in response."
    
    # Log categorization warnings
    for warning in categorization_warnings:
        print(f"[VALIDATOR WARNING] {warning}")
    
    # CRITICAL: Check for excessive duplicate exception tests
    exception_counts = {}
    for tc in valid_cases:
        if tc.get('category') == 'error_case':
            expected_str = str(tc.get('expected_output', '')).lower()
            # Extract exception type from expected output
            for exc_type in ['zerodivisionerror', 'typeerror', 'valueerror', 'keyerror', 
                           'indexerror', 'attributeerror', 'nameerror', 'runtimeerror']:
                if exc_type in expected_str:
                    exception_counts[exc_type] = exception_counts.get(exc_type, 0) + 1
                    break
    
    # Warn about excessive duplicate exception tests (more than 2 per type)
    for exc_type, count in exception_counts.items():
        if count > 2:
            print(f"[VALIDATOR WARNING] Excessive tests for {exc_type.title()}: {count} tests found. "
                  f"Maximum 2 recommended. Consider testing only distinct scenarios, not minor input variations.")
    
    # CRITICAL: Validate division operations have both required test scenarios
    if code:
        is_division_func = _is_division_function(code)
        if is_division_func:
            has_divisor_zero = False
            has_dividend_zero = False
            
            for tc in valid_cases:
                inputs_str = str(tc.get('inputs', '')).lower()
                expected_str = str(tc.get('expected_output', '')).lower()
                
                # Check for divisor = 0 (should be error_case with ZeroDivisionError)
                if tc.get('category') == 'error_case':
                    # Look for patterns like "b=0", "divisor=0", "denominator=0", second param = 0
                    if re.search(r'(b\s*=\s*0|divisor\s*=\s*0|denominator\s*=\s*0|,\s*0\s*[,)])', inputs_str):
                        if 'zerodivision' in expected_str or 'error' in expected_str:
                            has_divisor_zero = True
                
                # Check for dividend = 0 (should be edge_case with result = 0)
                if tc.get('category') == 'edge_case':
                    # Look for patterns like "a=0", "dividend=0", "numerator=0", first param = 0, "0,", "0 /"
                    if re.search(r'(a\s*=\s*0|dividend\s*=\s*0|numerator\s*=\s*0|^\s*0\s*[,/]|\(\s*0\s*,)', inputs_str):
                        # Expected output should NOT be an error - should be 0 or 0.0
                        if 'error' not in expected_str and 'exception' not in expected_str:
                            has_dividend_zero = True
            
            # If either scenario is missing, fail validation
            if not has_divisor_zero or not has_dividend_zero:
                missing = []
                if not has_divisor_zero:
                    missing.append("divisor=0 (error_case with ZeroDivisionError)")
                if not has_dividend_zero:
                    missing.append("dividend=0 (edge_case returning 0)")
                
                error_msg = (
                    f"CRITICAL: Division function detected but missing required test scenarios: {', '.join(missing)}. "
                    f"Division functions MUST test BOTH: (1) divisor=0 raising ZeroDivisionError, "
                    f"and (2) dividend=0 returning 0 (not an error). Please regenerate with both tests."
                )
                print(f"[VALIDATOR ERROR] {error_msg}")
                return False, valid_cases, error_msg
    
    return True, valid_cases, ""


def validate_code_response(raw_response: str, language: str) -> Tuple[bool, str, str]:
    """
    Validate generated code response (test code or final tests).
    
    Returns:
        (is_valid, cleaned_code, error_message)
    """
    # Strip markdown fences
    cleaned = strip_markdown_fences(raw_response)
    
    if not cleaned or len(cleaned.strip()) < 10:
        return False, "", "Generated code is empty or too short."
    
    # Basic language-specific validation
    if language == "python":
        if not re.search(r'\bdef\s+test_', cleaned):
            return False, cleaned, "Warning: Python test code should contain test functions (def test_...)"
        
        # Check for invalid test function signatures with default parameters
        invalid_pattern = r'def\s+test_\w+\s*\([^)]*='
        if re.search(invalid_pattern, cleaned):
            return False, cleaned, "ERROR: Test functions cannot have default parameter values. Use fixtures or direct values instead."
        
        # Check for duplicate test function names
        test_names = re.findall(r'def\s+(test_\w+)\s*\(', cleaned)
        unique_names = set(test_names)
        if len(test_names) != len(unique_names):
            # Find only the actual duplicates
            duplicates = [name for name in unique_names if test_names.count(name) > 1]
            return False, cleaned, f"ERROR: Duplicate test function names: {', '.join(sorted(duplicates))}"
        
        # Check for duplicate parameter names within function signatures
        # Find all test function signatures with their parameters
        func_signatures = re.findall(r'def\s+(test_\w+)\s*\(([^)]*)\)', cleaned)
        for func_name, params_str in func_signatures:
            if params_str.strip():  # Only check if function has parameters
                # Split parameters and clean them
                params = [p.split(':')[0].strip() for p in params_str.split(',') if p.strip()]
                unique_params = set(params)
                if len(params) != len(unique_params):
                    # Find duplicate parameters
                    dup_params = [p for p in unique_params if params.count(p) > 1]
                    return False, cleaned, f"ERROR: Function '{func_name}' has duplicate parameter names: {', '.join(sorted(dup_params))}. Each parameter must have a unique name."
        
        # Check for brittle error message assertions (warning, not error)
        # Pattern: pytest.raises(...) as exc_info: ... assert str(exc_info.value) == "exact message"
        brittle_pattern = r'assert\s+str\s*\(\s*exc_info\.value\s*\)\s*==\s*["\']'
        if re.search(brittle_pattern, cleaned):
            # This is a warning - we'll still return the code but log it
            print("[VALIDATOR WARNING] Detected brittle error message assertions. Consider checking exception type only.")
        
        # Check for fixture comparison in assertions (likely incorrect)
        # More direct approach: look for assert result == <identifier> where <identifier> is a parameter
        for func_name, params_str in func_signatures:
            if params_str.strip():
                # Get fixture names from parameters
                fixture_names = [p.split(':')[0].strip() for p in params_str.split(',') if p.strip()]
                
                # Look for the pattern more broadly in the cleaned code
                for fixture_name in fixture_names:
                    # Check for: assert <var> == fixture_name (where var might be result, res, output, etc)
                    pattern = rf'\bassert\s+\w+\s*==\s*{re.escape(fixture_name)}\s*$'
                    if re.search(pattern, cleaned, re.MULTILINE):
                        print(f"[VALIDATOR WARNING] Detected assertion comparing to fixture '{fixture_name}'. Use actual expected value instead (e.g., assert result == 5).")
                        break  # Only warn once per function
        
        # Check for unrealistic exception expectations
        unrealistic_exceptions = [
            (r'pytest\.raises\(OverflowError\)', 
             "OverflowError is unlikely for basic arithmetic in Python 3 (integers have arbitrary precision, floats don't overflow to error)"),
            (r'pytest\.raises\(MemoryError\)', 
             "MemoryError is unrealistic for simple operations"),
            (r'pytest\.raises\(SystemError\)', 
             "SystemError is rarely raised by user code and unlikely for basic operations"),
        ]
        
        for pattern, message in unrealistic_exceptions:
            if re.search(pattern, cleaned, re.IGNORECASE):
                print(f"[VALIDATOR WARNING] Unrealistic exception test detected: {message}. This test will likely fail.")
        
        # Check for non-Pythonic boolean assertions
        non_pythonic_patterns = [
            r'assert\s+\w+\s*==\s*True\b',
            r'assert\s+\w+\s*==\s*False\b'
        ]
        
        found_non_pythonic = []
        for pattern in non_pythonic_patterns:
            if re.search(pattern, cleaned):
                found_non_pythonic.append(pattern)
        
        if found_non_pythonic:
            print("[VALIDATOR WARNING] Non-Pythonic boolean assertions detected:")
            print("  ❌ WRONG: assert result == True")
            print("  ✅ CORRECT: assert result")
            print("  ❌ WRONG: assert result == False")
            print("  ✅ CORRECT: assert not result")
        
        # CRITICAL: Check for excessive exception tests of the same type
        exception_test_counts = {}
        exception_types = ['TypeError', 'ValueError', 'ZeroDivisionError', 'KeyError', 
                          'IndexError', 'AttributeError', 'NameError', 'RuntimeError',
                          'OverflowError', 'MemoryError']
        
        for exc_type in exception_types:
            # Count pytest.raises(ExceptionType) occurrences
            pattern = rf'pytest\.raises\(\s*{exc_type}\s*\)'
            matches = re.findall(pattern, cleaned)
            if len(matches) > 2:
                exception_test_counts[exc_type] = len(matches)
        
        if exception_test_counts:
            for exc_type, count in exception_test_counts.items():
                print(f"[VALIDATOR WARNING] Excessive {exc_type} tests: {count} tests found. "
                      f"Maximum 2 recommended per exception type. "
                      f"Test distinct scenarios only, not minor input variations (e.g., 3.5 vs 5.5, [5] vs [10]).")
        
        # CRITICAL: Check for missing pytest import when pytest.raises() is used
        uses_pytest_raises = re.search(r'pytest\.raises\s*\(', cleaned)
        has_pytest_import = re.search(r'^\s*import\s+pytest\s*$', cleaned, re.MULTILINE)
        
        if uses_pytest_raises and not has_pytest_import:
            return False, cleaned, "ERROR: Code uses pytest.raises() but 'import pytest' is missing. Add 'import pytest' at the top of the file."
    
    elif language in ["javascript", "typescript"]:
        if not re.search(r'\b(test|it|describe)\s*\(', cleaned):
            return False, cleaned, "Warning: JS/TS test code should contain test() or it() blocks"
    
    return True, cleaned, ""


def _is_division_function(code: str) -> bool:
    """
    Detect if the code is a division function that requires special test coverage.
    
    Returns:
        True if this is a division operation function
    """
    code_lower = code.lower()
    
    # Check function name
    if re.search(r'\bdef\s+(divide|division|div|quotient)\s*\(', code_lower):
        return True
    
    # Check for division operations in the code
    if re.search(r'\breturn\s+.*\s*/\s+', code_lower):  # return a / b
        return True
    
    # Check docstring/comments
    if re.search(r'(divid|quotient|division|divisor|denominator)', code_lower):
        return True
    
    return False


def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences from LLM responses.
    """
    text = text.strip()
    
    # Remove opening fence
    if text.startswith("```"):
        lines = text.split("\n")
        # Skip first line (```language)
        text = "\n".join(lines[1:])
    
    # Remove closing fence
    if text.endswith("```"):
        text = text[:-3]
    
    # Remove language identifier on first line
    lines = text.split("\n", 1)
    if lines and lines[0].strip().lower() in ["python", "javascript", "typescript", "js", "ts", "json"]:
        text = lines[1] if len(lines) > 1 else ""
    
    return text.strip()


def validate_state_keys(state: dict, required_keys: List[str], agent_name: str) -> None:
    """
    Validate that state contains all required keys before an agent processes it.
    
    Raises HTTPException if validation fails.
    """
    missing = [key for key in required_keys if key not in state or state[key] is None]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"{agent_name} error: Missing required state keys: {', '.join(missing)}"
        )


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to avoid exposing sensitive information.
    """
    error_str = str(error)
    
    # Remove file paths
    error_str = re.sub(r'[A-Za-z]:\\[^\s]+', '[PATH]', error_str)
    error_str = re.sub(r'/[^\s]+\.py', '[FILE]', error_str)
    
    # Remove API keys or tokens
    error_str = re.sub(r'(api[_-]?key|token|secret)[=:]\s*[^\s]+', r'\1=[REDACTED]', error_str, flags=re.IGNORECASE)
    
    # Limit length
    if len(error_str) > 500:
        error_str = error_str[:500] + "... [truncated]"
    
    return error_str
