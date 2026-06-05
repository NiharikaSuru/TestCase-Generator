"""
Automated Output Validator
--------------------------
Validates the quality and correctness of generated test responses.
"""

import json
import re
from typing import Dict, List, Tuple


def validate_response(response: Dict) -> Dict[str, any]:
    """
    Validate a test generation response and return detailed report.
    
    Args:
        response: The API response dictionary
    
    Returns:
        Dict with validation results and identified issues
    """
    issues = []
    warnings = []
    metrics = {}
    
    # 1. Validate structure
    required_fields = ['analysis', 'test_cases', 'test_code', 'final_tests', 'agent_steps']
    missing_fields = [f for f in required_fields if f not in response]
    if missing_fields:
        issues.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    # 2. Validate agent pipeline
    if 'agent_steps' in response:
        agents = [step['agent'] for step in response['agent_steps']]
        expected_agents = ['Code Analyzer', 'Test Case Generator', 'Test Code Writer', 'Assertion Agent']
        
        for expected in expected_agents:
            if expected not in agents:
                issues.append(f"Missing agent in pipeline: {expected}")
        
        failed_agents = [step['agent'] for step in response['agent_steps'] if step.get('status') != 'completed']
        if failed_agents:
            issues.append(f"Failed agents: {', '.join(failed_agents)}")
    
    # 3. Validate test cases
    if 'test_cases' in response:
        test_cases = response['test_cases']
        metrics['test_case_count'] = len(test_cases)
        
        if len(test_cases) == 0:
            issues.append("No test cases generated")
        elif len(test_cases) < 3:
            warnings.append(f"Only {len(test_cases)} test cases generated (recommend at least 5)")
        
        # Check category distribution
        categories = {}
        for tc in test_cases:
            cat = tc.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        metrics['category_distribution'] = categories
        
        if categories.get('happy_path', 0) == 0:
            warnings.append("No happy path tests generated")
        if categories.get('edge_case', 0) == 0:
            warnings.append("No edge case tests generated")
        if categories.get('error_case', 0) == 0:
            warnings.append("No error case tests generated")
        
        # Validate test case structure
        for i, tc in enumerate(test_cases):
            if not tc.get('name'):
                issues.append(f"Test case {i} missing name")
            if not tc.get('description'):
                warnings.append(f"Test case {i} missing description")
    
    # 4. Validate final tests code
    if 'final_tests' in response:
        final_tests = response['final_tests']
        metrics['code_length'] = len(final_tests)
        
        if len(final_tests) < 50:
            issues.append("Final test code is too short (likely generation failed)")
        
        # Check for required patterns
        test_func_count = len(re.findall(r'def test_', final_tests))
        assertion_count = len(re.findall(r'\bassert\b', final_tests))
        pytest_raises_count = len(re.findall(r'pytest\.raises', final_tests))
        
        metrics['test_function_count'] = test_func_count
        metrics['assertion_count'] = assertion_count
        metrics['pytest_raises_count'] = pytest_raises_count
        
        if test_func_count == 0:
            issues.append("No test functions found in final tests")
        elif test_func_count < len(response.get('test_cases', [])):
            warnings.append(f"Test function count ({test_func_count}) less than test cases ({len(response.get('test_cases', []))})")
        
        if assertion_count == 0 and pytest_raises_count == 0:
            issues.append("No assertions or pytest.raises found in tests")
        
        # Check for common issues
        if re.search(r'def test_.*:\s+pass\s*$', final_tests, re.MULTILINE):
            issues.append("Empty test functions with only 'pass' statement found")
        
        if 'import pytest' not in final_tests and 'pytest.raises' in final_tests:
            issues.append("Uses pytest.raises but missing 'import pytest'")
        
        # Check for proper imports
        if not re.search(r'(from|import)\s+\w+\s+(import|as)', final_tests):
            warnings.append("No import statements found - tests may not be executable")
    
    # 5. Calculate overall score
    score = 100
    score -= len(issues) * 10  # Each issue: -10 points
    score -= len(warnings) * 5  # Each warning: -5 points
    score = max(0, score)
    
    # Determine grade
    if score >= 90:
        grade = "A (Excellent)"
    elif score >= 80:
        grade = "B (Good)"
    elif score >= 70:
        grade = "C (Acceptable)"
    elif score >= 60:
        grade = "D (Needs Improvement)"
    else:
        grade = "F (Poor)"
    
    return {
        'score': score,
        'grade': grade,
        'issues': issues,
        'warnings': warnings,
        'metrics': metrics,
        'is_valid': len(issues) == 0,
        'quality_level': 'PASS' if score >= 70 else 'FAIL'
    }


def print_validation_report(validation: Dict):
    """Print a formatted validation report."""
    print("=" * 70)
    print("OUTPUT VALIDATION REPORT")
    print("=" * 70)
    print()
    
    print(f"Overall Score: {validation['score']}/100")
    print(f"Grade: {validation['grade']}")
    print(f"Quality Level: {validation['quality_level']}")
    print(f"Valid: {'✓ YES' if validation['is_valid'] else '✗ NO'}")
    print()
    
    if validation['metrics']:
        print("METRICS:")
        print("-" * 70)
        for key, value in validation['metrics'].items():
            print(f"  {key}: {value}")
        print()
    
    if validation['issues']:
        print("CRITICAL ISSUES:")
        print("-" * 70)
        for i, issue in enumerate(validation['issues'], 1):
            print(f"  {i}. ❌ {issue}")
        print()
    
    if validation['warnings']:
        print("WARNINGS:")
        print("-" * 70)
        for i, warning in enumerate(validation['warnings'], 1):
            print(f"  {i}. ⚠️  {warning}")
        print()
    
    if not validation['issues'] and not validation['warnings']:
        print("✓ No issues or warnings found!")
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <response_json_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8-sig') as f:
        response = json.load(f)
    
    validation = validate_response(response)
    print_validation_report(validation)
    
    # Exit with error code if quality is poor
    sys.exit(0 if validation['quality_level'] == 'PASS' else 1)
