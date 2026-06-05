from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class GenerateTestRequest(BaseModel):
    code: str = Field(..., description="The source code (function or class) to generate tests for")
    language: Literal["python", "javascript", "typescript"] = Field(
        ..., description="The programming language of the provided code"
    )
    framework: Optional[str] = Field(
        None,
        description="Test framework override. Defaults to 'pytest' for Python, 'jest' for JS/TS",
    )


class TestCase(BaseModel):
    name: str
    description: str
    category: Literal["happy_path", "edge_case", "error_case"]
    inputs: Optional[str] = None
    expected_output: Optional[str] = None


class AgentStep(BaseModel):
    agent: str
    status: Literal["completed", "failed"]
    output_summary: str


class GenerateTestResponse(BaseModel):
    analysis: str
    test_cases: List[TestCase]
    test_code: str
    final_tests: str
    agent_steps: List[AgentStep]
    language: str
    framework: str
