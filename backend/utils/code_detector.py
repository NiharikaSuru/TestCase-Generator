from typing import Literal


def detect_language(code: str) -> Literal["python", "javascript", "typescript"]:
    """
    Heuristically detects the programming language from source code.
    Used as a fallback when the user does not specify a language.
    """
    code_lower = code.lower()

    typescript_signals = [": string", ": number", ": boolean", "interface ", "type ", ": void", "<T>", "readonly "]
    if any(sig in code for sig in typescript_signals):
        return "typescript"

    python_signals = ["def ", "import ", "from ", "self.", "print(", "elif ", "__init__"]
    js_signals = ["function ", "const ", "let ", "var ", "=>", "require(", "module.exports"]

    py_score = sum(1 for s in python_signals if s in code)
    js_score = sum(1 for s in js_signals if s in code)

    if py_score >= js_score:
        return "python"
    return "javascript"


def resolve_framework(language: str, framework_override: str | None) -> str:
    """Returns the test framework to use, applying defaults if no override is given."""
    if framework_override:
        return framework_override
    defaults = {"python": "pytest", "javascript": "jest", "typescript": "jest"}
    return defaults.get(language, "pytest")
