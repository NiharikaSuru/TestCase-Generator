"""
FastAPI Application Entry Point
--------------------------------
Exposes a single POST endpoint /api/generate-tests that:
  1. Accepts source code + language
  2. Runs the 4-agent LangGraph pipeline
  3. Returns the full structured response including the final test file
"""

import json
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import RateLimitError, AuthenticationError, APIConnectionError

from models.schemas import GenerateTestRequest, GenerateTestResponse, TestCase, AgentStep
from graph.orchestrator import run_pipeline
from utils.code_detector import resolve_framework
from utils.validators import validate_code_input, sanitize_error_message
from utils.math_validator import validate_math_in_response

load_dotenv()

# Optional vector store - only load if enabled
ENABLE_VECTOR_DB = os.getenv("ENABLE_VECTOR_DB", "true").lower() == "true"
memory_store = None

if ENABLE_VECTOR_DB:
    try:
        from vector_store.chroma_store import ChromaMemoryStore, format_memory_context
        memory_store = ChromaMemoryStore()
    except Exception as e:
        print(f"Warning: Vector store disabled due to error: {e}")
        ENABLE_VECTOR_DB = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: graph is already compiled at import time
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="Unit Test Creator API",
    description="AI-powered unit test generation using a 4-agent LangGraph pipeline (GPT-4o).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "https://testcase-generators.netlify.app",  # Your Netlify frontend
        "https://*.netlify.app",  # Allow all Netlify deployments
        "https://*.vercel.app",  # Allow all Vercel deployments
    ],
    allow_origin_regex=r"https://.*\.(vercel|netlify)\.app",  # Regex for Vercel and Netlify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Quick health-check endpoint."""
    return {"status": "ok", "service": "unit-test-creator"}


@app.post("/api/generate-tests", response_model=GenerateTestResponse)
async def generate_tests(request: GenerateTestRequest):
    """
    Runs the 4-agent pipeline and returns the generated test file.

    - **code**: The source code (function or class) to generate tests for
    - **language**: 'python', 'javascript', or 'typescript'
    - **framework**: Optional override; defaults to 'pytest' (Python) or 'jest' (JS/TS)
    """
    # Comprehensive input validation
    is_valid, error_msg = validate_code_input(request.code, request.language)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)

    framework = resolve_framework(request.language, request.framework)
    memory_context = ""

    # Optional retrieval from vector memory (non-blocking).
    if ENABLE_VECTOR_DB and memory_store:
        try:
            matches = memory_store.search_similar(request.code, request.language, top_k=3)
            memory_context = format_memory_context(matches)
        except Exception:
            memory_context = ""

    try:
        state = run_pipeline(
            code=request.code,
            language=request.language,
            framework=framework,
            memory_context=memory_context,
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Check your OPENAI_API_KEY or GROQ_API_KEY in backend/.env",
        )
    except RateLimitError as exc:
        msg = str(exc)
        
        # Check for Groq-specific rate limit errors
        if "groq" in msg.lower() or "rate_limit_exceeded" in msg.lower():
            # Extract useful info from Groq error
            detail_msg = "Rate limit reached. "
            if "tokens per minute" in msg.lower():
                detail_msg += "Groq free tier has token limits per minute. "
            if "try again in" in msg.lower():
                import re
                match = re.search(r'try again in ([\d.]+)s', msg)
                if match:
                    wait_time = match.group(1)
                    detail_msg += f"Please wait {wait_time} seconds and try again. "
            detail_msg += "Tips: 1) Use simpler/shorter code, 2) Wait a minute between requests, 3) Upgrade at https://console.groq.com/settings/billing"
            raise HTTPException(status_code=429, detail=detail_msg)
        
        # OpenAI rate limits
        if "insufficient_quota" in msg:
            raise HTTPException(
                status_code=402,
                detail=(
                    "Your OpenAI account has no remaining quota. "
                    "Add credits at https://platform.openai.com/account/billing"
                ),
            )
        
        # Generic rate limit
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached. Please wait a moment and try again with simpler code if the issue persists.",
        )
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to LLM API. Check your internet connection.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=sanitize_error_message(exc))
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Request timeout: The LLM took too long to respond. Please try again with simpler code."
        )
    except Exception as exc:
        sanitized_error = sanitize_error_message(exc)
        # Check if error message contains rate limit info
        error_lower = sanitized_error.lower()
        if "rate" in error_lower and "limit" in error_lower:
            detail_msg = f"Rate limit error: {sanitized_error}. Please wait a moment and try again."
            raise HTTPException(status_code=429, detail=detail_msg)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {sanitized_error}")

    # Optional write-back to vector memory (non-blocking).
    if ENABLE_VECTOR_DB and memory_store:
        try:
            memory_store.store_run(
                code=request.code,
                language=request.language,
                analysis=state.get("analysis", ""),
                final_tests=state.get("final_tests", ""),
            )
        except Exception:
            pass

    # Deserialise test_cases from the state (already a list of dicts)
    raw_cases = state.get("test_cases", [])
    test_cases = []
    for tc in raw_cases:
        try:
            test_cases.append(
                TestCase(
                    name=tc.get("name", "unnamed_test"),
                    description=tc.get("description", ""),
                    category=tc.get("category", "happy_path"),
                    inputs=tc.get("inputs"),
                    expected_output=tc.get("expected_output"),
                )
            )
        except Exception:
            continue  # Skip malformed entries gracefully

    # Build agent steps list
    agent_steps = [
        AgentStep(
            agent=s.get("agent", "Unknown"),
            status=s.get("status", "completed"),
            output_summary=s.get("output_summary", ""),
        )
        for s in state.get("agent_steps", [])
    ]

    # Parse analysis JSON for a human-readable summary
    try:
        analysis_obj = json.loads(state.get("analysis", "{}"))
        analysis_summary = analysis_obj.get("summary", state.get("analysis", ""))
    except (json.JSONDecodeError, TypeError):
        analysis_summary = state.get("analysis", "")

    # Optional: Validate mathematical assertions in tests
    validation_data = {
        'final_tests': state.get("final_tests", ""),
        'code': request.code,
        'language': request.language
    }
    is_math_valid, math_issues = validate_math_in_response(validation_data)
    
    if not is_math_valid and math_issues:
        # Add validation warnings to agent steps
        warning_summary = f"⚠️ Found {len(math_issues)} potential calculation issue(s). " + \
                         "Review assertions for rounding errors."
        agent_steps.append(
            AgentStep(
                agent="Math Validator",
                status="completed",
                output_summary=warning_summary
            )
        )
        # Log details server-side
        print(f"[MATH VALIDATION] Found issues in generated tests:")
        for issue in math_issues:
            print(f"  - Line {issue.get('line', '?')}: {issue.get('message', 'Unknown issue')}")

    return GenerateTestResponse(
        analysis=analysis_summary,
        test_cases=test_cases,
        test_code=state.get("test_code", ""),
        final_tests=state.get("final_tests", ""),
        agent_steps=agent_steps,
        language=request.language,
        framework=framework,
    )
