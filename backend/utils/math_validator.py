"""
Post-Generation Math Validator
-------------------------------
Validates mathematical assertions in generated test code to catch calculation errors.
"""

import re
import ast
from typing import List, Dict, Tuple


def extract_assertions_from_test_code(test_code: str, language: str) -> List[Dict]:
    """
    Extract assertion statements from generated test code.
    
    Returns:
        List of dictionaries with assertion details
    """
    assertions = []
    
    if language == "python":
        # Extract assert statements with numeric comparisons
        pattern = r'assert\s+(.+?)\s*==\s*([0-9]+\.?[0-9]*)'
        matches = re.finditer(pattern, test_code)
        
        for match in matches:
            assertions.append({
                'left': match.group(1).strip(),
                'expected': float(match.group(2)),
                'line': test_code[:match.start()].count('\n') + 1
            })
    
    return assertions


def validate_financial_calculations(test_code: str, source_code: str, language: str) -> List[Dict]:
    """
    Validate financial/mathematical calculations in test assertions.
    
    Returns:
        List of potential issues found
    """
    issues = []
    
    if language != "python":
        return issues  # Only Python validation for now
    
    # Look for common financial calculation patterns
    # Pattern: subtotal * tax_rate calculations
    tax_pattern = r'(\d+\.?\d*)\s*\*\s*0\.0*(\d+)'
    tax_matches = re.finditer(tax_pattern, test_code)
    
    for match in re.finditer(r'assert\s+result\["tax"\]\s*==\s*([0-9]+\.?[0-9]*)', test_code):
        expected_tax = float(match.group(1))
        line_num = test_code[:match.start()].count('\n') + 1
        
        # Check if the tax value looks incorrectly rounded
        # Common error: 0.8792 -> 0.87 instead of 0.88
        decimal_part = expected_tax - int(expected_tax)
        
        # Flag suspicious values that end in .X7 or .X9 (often truncation errors)
        last_digit = int(str(decimal_part * 100) % 10)
        second_last = int(str(decimal_part * 100) // 10 % 10)
        
        if second_last == 0 and last_digit in [7, 9]:
            issues.append({
                'type': 'suspicious_rounding',
                'line': line_num,
                'field': 'tax',
                'value': expected_tax,
                'message': f'Tax value {expected_tax} may be incorrectly rounded. '
                          f'Verify: should it be {expected_tax + 0.01:.2f}?'
            })
    
    # Check for inconsistent values in similar tests
    test_pattern = r'def\s+(test_\w+)\([^)]*\):.*?(?=def\s+test_|$)'
    tests = re.finditer(test_pattern, test_code, re.DOTALL)
    
    price_tax_map = {}
    for test_match in tests:
        test_body = test_match.group(0)
        test_name = test_match.group(1)
        
        # Extract price/quantity if present
        qty_match = re.search(r'quantity["\']?\s*[:=]\s*(\d+)', test_body)
        price_match = re.search(r'price["\']?\s*[:=]\s*(\d+\.?\d*)', test_body)
        tax_match = re.search(r'assert\s+result\["tax"\]\s*==\s*([0-9]+\.?[0-9]*)', test_body)
        
        if qty_match and price_match and tax_match:
            qty = int(qty_match.group(1))
            price = float(price_match.group(1))
            expected_tax = float(tax_match.group(1))
            
            key = f"{qty}x{price}"
            if key in price_tax_map:
                if price_tax_map[key] != expected_tax:
                    issues.append({
                        'type': 'inconsistent_values',
                        'line': test_code[:test_match.start()].count('\n') + 1,
                        'message': f'Test {test_name} expects tax={expected_tax} for {key}, '
                                  f'but another test expects {price_tax_map[key]} for same inputs!'
                    })
            else:
                price_tax_map[key] = expected_tax
    
    return issues


def suggest_fixes(issues: List[Dict], test_code: str) -> str:
    """
    Generate suggested fixes for identified issues.
    """
    if not issues:
        return "No issues found. Tests appear mathematically correct."
    
    suggestions = ["MATHEMATICAL VALIDATION ISSUES FOUND:\n"]
    
    for i, issue in enumerate(issues, 1):
        suggestions.append(f"\n{i}. {issue['type'].upper()} (Line {issue['line']})")
        suggestions.append(f"   {issue['message']}")
        
        if issue['type'] == 'suspicious_rounding' and 'value' in issue:
            val = issue['value']
            suggestions.append(f"   Suggested fix: Change {val} to {val + 0.01:.2f}")
    
    return "\n".join(suggestions)


def validate_math_in_response(response_data: Dict) -> Tuple[bool, List[Dict]]:
    """
    Main validation function for API response.
    
    Returns:
        (is_valid, issues_list)
    """
    test_code = response_data.get('final_tests', '')
    source_code = response_data.get('code', '')  # From request
    language = response_data.get('language', 'python')
    
    issues = validate_financial_calculations(test_code, source_code, language)
    
    return len(issues) == 0, issues


if __name__ == "__main__":
    # Example usage
    sample_test = '''
def test_example():
    result = add_item_to_cart(item_name="Test", quantity=1, price=10.99, category="general")
    assert result["tax"] == 0.87
    assert result["total"] == 11.86
    
def test_example_2():
    result = add_item_to_cart(item_name="Test", quantity=1, price=10.99, category="electronics")
    assert result["tax"] == 0.88
    assert result["total"] == 11.87
'''
    
    issues = validate_financial_calculations(sample_test, "", "python")
    print(suggest_fixes(issues, sample_test))
