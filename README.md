# AI-Powered Unit Test Generator

An intelligent test generation system that uses a **4-agent LangGraph pipeline** powered by GPT-4o to automatically create comprehensive unit tests for Python, JavaScript, and TypeScript code.

## 🚀 Features

- **Multi-Language Support**: Python (pytest), JavaScript (Jest), TypeScript (Jest)
- **4-Agent Architecture**: Code Analyzer → Test Case Generator → Test Code Writer → Assertion Validator
- **Comprehensive Coverage**: Generates happy path, edge cases, and error cases
- **Math Validation**: Automatic detection of calculation errors in assertions
- **Vector Memory**: Optional ChromaDB integration for learning from past generations
- **Interactive UI**: React-based frontend with Monaco code editor
- **Real-time Progress**: Live agent execution tracking

---

## 🏗️ Architecture

### Backend (FastAPI + LangGraph)

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                           │
│                 /api/generate-tests                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│  1. Code Analyzer Agent                                     │
│     └─> Analyzes function signature, logic, edge cases     │
│                                                             │
│  2. Test Case Generator Agent                               │
│     └─> Designs structured test cases with inputs/outputs  │
│                                                             │
│  3. Test Code Writer Agent                                  │
│     └─> Writes executable pytest/Jest test code            │
│                                                             │
│  4. Assertion Validator Agent                               │
│     └─> Verifies assertions & validates test correctness   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                  [ChromaDB Vector Store]
                   (Optional Memory)
```

### Frontend (React + TypeScript + Vite)

- **Monaco Editor**: Syntax-highlighted code input
- **Language Selector**: Python / JavaScript / TypeScript
- **Agent Progress Stepper**: Visual pipeline execution tracking
- **Test Output Viewer**: Syntax-highlighted generated tests

---

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI 0.115.5
- **LLM**: OpenAI GPT-4o (via LangChain)
- **Orchestration**: LangGraph 0.2.60
- **Vector DB**: ChromaDB (optional)
- **Validation**: Custom math validators, pytest runners

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS 4
- **Editor**: Monaco Editor
- **Icons**: Lucide React
- **HTTP**: Axios

---

## 🛠️ Setup & Installation

### Prerequisites
- **Python**: 3.13+ (with venv)
- **Node.js**: 18+ (with npm)
- **OpenAI API Key**: Required for GPT-4o

### 1. Clone Repository
```bash
git clone <repository-url>
cd capstone-project
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv ../.venv
../.venv/Scripts/activate  # Windows
# source ../.venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
echo "ENABLE_VECTOR_DB=false" >> .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install
```

---

## 🚀 Running the Application

### Start Backend (Port 8000)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Start Frontend (Port 5173)
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

---

## 📡 API Documentation

### POST `/api/generate-tests`

Generate unit tests for provided source code.

**Request Body:**
```json
{
  "code": "def calculate_discount(price, discount_percent):\n    return price * (1 - discount_percent / 100)",
  "language": "python",
  "framework": "pytest"
}
```

**Response:**
```json
{
  "analysis": "Function calculates discount...",
  "test_cases": [
    {
      "name": "test_happy_path_valid_discount",
      "description": "Verify correct discount calculation",
      "category": "happy_path",
      "inputs": "price=100, discount_percent=20",
      "expected_output": "80.0"
    }
  ],
  "test_code": "# Structured test case metadata",
  "final_tests": "import pytest\nfrom solution import calculate_discount\n\ndef test_happy_path_valid_discount():\n    assert calculate_discount(100, 20) == 80.0",
  "agent_steps": [
    {
      "agent": "Code Analyzer",
      "status": "completed",
      "output_summary": "Analyzed function signature..."
    }
  ]
}
```

**Supported Languages:**
- `python` (framework: `pytest`)
- `javascript` (framework: `jest`)
- `typescript` (framework: `jest`)

---

## 📁 Project Structure

```
capstone-project/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── requirements.txt        # Python dependencies
│   ├── agents/                 # 4 LangGraph agents
│   │   ├── code_analyzer.py
│   │   ├── test_case_generator.py
│   │   ├── test_code_writer.py
│   │   └── assertion_agent.py
│   ├── graph/
│   │   └── orchestrator.py     # LangGraph pipeline
│   ├── llm/
│   │   └── factory.py          # LLM provider factory
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── utils/                  # Validators & helpers
│   └── vector_store/
│       └── chroma_store.py     # Optional ChromaDB
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main application
│   │   ├── components/
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── AgentProgressStepper.tsx
│   │   │   └── TestOutput.tsx
│   │   └── api/
│   │       └── client.ts       # Axios API client
│   ├── package.json
│   └── vite.config.ts
└── .venv/                      # Python virtual environment
```

---

## 🔧 Configuration

### Environment Variables (Backend)

Create a `.env` file in the `backend/` directory:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
ENABLE_VECTOR_DB=false           # Enable ChromaDB memory
CHROMA_PERSIST_DIR=./chroma_db   # ChromaDB storage path
CHROMA_COLLECTION=unit_test_creator_memory
```

### ChromaDB Setup (Optional)

To enable vector memory for learning from past test generations:

1. Install ChromaDB:
```bash
pip install chromadb
```

2. Update `.env`:
```env
ENABLE_VECTOR_DB=true
```

---

## 🧪 Example Usage

### Python Example
```python
def calculate_discount(price, discount_percent, customer_type="regular"):
    if price < 0:
        raise ValueError("Price cannot be negative")
    
    base_discount = price * (discount_percent / 100)
    
    if customer_type == "premium":
        base_discount += price * 0.05
    elif customer_type == "vip":
        base_discount += price * 0.10
    
    return round(price - base_discount, 2)
```

**Generated Tests:** ✓ Happy path, ✓ Edge cases, ✓ Error cases, ✓ Boundary values

---

## 🛡️ Error Handling

The system handles:
- ✅ Invalid OpenAI API keys (401)
- ✅ Rate limits & quota errors (429/402)
- ✅ Network connection issues (503)
- ✅ Invalid code input (422)
- ✅ Malformed requests (400)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **LangChain & LangGraph**: Agent orchestration framework
- **OpenAI**: GPT-4o language model
- **FastAPI**: High-performance Python web framework
- **React & Vite**: Modern frontend tooling

---

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check API documentation at `/docs` endpoint
- Review agent logs in terminal output

---

**Built with ❤️ as a Capstone Project**
