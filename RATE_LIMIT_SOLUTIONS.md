# Rate Limit Solutions

## Problem
Groq free tier has strict rate limits (e.g., 6000 TPM for llama-3.1-8b-instant), which can cause 429 errors when generating tests.

## Solutions Implemented

### 1. **Switch to Higher-Limit Model** ✅
- Changed from `llama-3.1-8b-instant` (6K TPM) to `llama-3.3-70b-versatile` (30K TPM on free tier)
- Update in `.env`: `GROQ_MODEL=llama-3.3-70b-versatile`

### 2. **Enhanced Retry Logic** ✅
- Increased max retries from 3 to 5
- Increased initial delay from 2s to 3s
- Increased max delay from 30s to 60s
- Smart wait time extraction from error messages (e.g., "Please try again in 5.86s")

### 3. **Inter-Agent Delays** ✅
- Added 2-second delay between agent calls to spread token usage
- Configurable via `INTER_AGENT_DELAY` in `.env`
- Prevents rapid successive API calls that trigger rate limits

### 4. **Token Budgeting** ✅
- Reduced max output tokens from 4000 to 3000 per request
- Helps stay within rate limits while maintaining quality

## Configuration

### `.env` Settings
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
INTER_AGENT_DELAY=2.0
```

## Alternative Solutions

### Option 1: Use OpenAI (Recommended for Production)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```
- Higher rate limits
- More reliable
- Costs ~$0.005 per test generation

### Option 2: Use Ollama (Local, No Limits)
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
```
- No rate limits
- Free
- Requires local GPU/CPU resources
- Install: `ollama pull llama3.1:8b`

### Option 3: Upgrade Groq Tier
Visit https://console.groq.com/settings/billing to upgrade to Dev Tier for higher limits

## Rate Limit Comparison

| Provider | Model | Free Tier TPM | Paid Tier |
|----------|-------|---------------|-----------|
| Groq | llama-3.1-8b-instant | 6,000 | 120,000 |
| Groq | llama-3.3-70b-versatile | 30,000 | 120,000 |
| Groq | mixtral-8x7b-32768 | 18,000 | 120,000 |
| OpenAI | gpt-4o | 30,000 | 10M+ |
| Ollama | Any | Unlimited | N/A |

## Troubleshooting

### Still Getting Rate Limits?
1. **Increase delay**: Set `INTER_AGENT_DELAY=4.0` in `.env`
2. **Switch models**: Try `mixtral-8x7b-32768` for balance of speed and limits
3. **Switch providers**: Use OpenAI or Ollama
4. **Wait and retry**: The system auto-retries with exponential backoff

### Check Current Usage
- Visit https://console.groq.com/settings/limits
- Monitor your API usage and remaining tokens

## Changes Made

### Files Modified
1. `backend/.env` - Updated model and added delay config
2. `backend/llm/factory.py` - Changed default model and token limits
3. `backend/utils/retry_helper.py` - Enhanced retry logic
4. `backend/graph/orchestrator.py` - Added inter-agent delays
5. All agent files - Increased max_retries to 5

### Server Restart Required
After making changes to `.env`, restart the backend server:
```bash
# Stop the current server (Ctrl+C)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
