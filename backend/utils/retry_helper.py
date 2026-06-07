"""
LLM Retry Utility
-----------------
Handles rate limiting and retries with exponential backoff for LLM calls.
"""

import time
from typing import Any, Callable
from functools import wraps


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if "rate" in error_str and "limit" in error_str:
                if attempt < max_retries:
                    # Extract wait time from error message if available
                    wait_time = delay
                    if "try again in" in error_str:
                        try:
                            # Try to extract the wait time (e.g., "3.28s")
                            import re
                            match = re.search(r'try again in ([\d.]+)s', error_str)
                            if match:
                                suggested_wait = float(match.group(1))
                                wait_time = max(suggested_wait + 1, delay)  # Add 1 second buffer
                        except:
                            pass
                    
                    wait_time = min(wait_time, max_delay)
                    print(f"Rate limit hit. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    delay *= exponential_base
                    continue
            
            # For non-rate-limit errors, retry with exponential backoff
            if attempt < max_retries:
                wait_time = min(delay, max_delay)
                print(f"Error occurred. Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
                delay *= exponential_base
            else:
                # Last attempt failed, raise the exception
                raise last_exception
    
    # Should never reach here, but just in case
    raise last_exception


def invoke_llm_with_retry(llm, messages, max_retries: int = 5):
    """
    Invoke an LLM with automatic retry on rate limits.
    
    Args:
        llm: LangChain chat model instance
        messages: List of messages to send
        max_retries: Maximum number of retry attempts (default 5 for rate limit handling)
        
    Returns:
        LLM response
    """
    return retry_with_backoff(
        lambda: llm.invoke(messages),
        max_retries=max_retries,
        initial_delay=3.0,  # Increased initial delay for rate limits
        max_delay=60.0  # Increased max delay
    )
