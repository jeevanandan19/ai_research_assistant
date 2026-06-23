# AI Research Assistant Agent

A production-ready AI-powered web application for deep analysis of research papers using **Retrieval-Augmented Generation (RAG)**, **LangChain**, **FAISS**, and **Large Language Models**.

---

## Features

| Feature | Description |
|---|---|
| **PDF Upload** | Upload research papers up to 50 MB with drag-and-drop |
| **Structured Summary** | Abstract, Detailed Summary, Key Contributions, Limitations, Future Work |
| **Keyword Extraction** | Categorized: Primary Keywords, Methods, Datasets/Metrics, Domain Concepts |
| **Intelligent Q&A** | RAG-based Q&A — answers grounded strictly in the document |
| **Key Insights** | Core insights, technical innovation, empirical findings, broader impact |
| **Novelty Assessment** | AI-assessed novelty score and differentiators |
| **Chat History** | Persistent Q&A history with timestamps and source counts |
| **Export** | Download summary as PDF, export keywords as JSON |
| **FAISS Vector DB** | Per-session semantic vector index for fast retrieval |

---

## Technology Stack

- **Backend**: Python 3.10+, Flask 3.0
- **AI/ML**: LangChain, HuggingFace (`all-MiniLM-L6-v2`), OpenAI / Google Gemini
- **Vector DB**: FAISS (Facebook AI Similarity Search)
- **PDF Processing**: PyPDFLoader, RecursiveCharacterTextSplitter
- **Frontend**: HTML5, Bootstrap 5, Vanilla JavaScript
- **PDF Export**: ReportLab

---

## Project Structure

```
ai_research_assistant/
├── app.py                    # Flask application & API routes
├── config.py                 # Configuration & environment settings
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── uploads/                  # Uploaded PDF files (git-ignored)
├── database/                 # FAISS indices (git-ignored)
├── static/
│   ├── css/style.css         # Complete UI stylesheet
│   └── js/
│       ├── upload.js         # Upload page logic
│       └── dashboard.js      # Dashboard logic (summary, Q&A, keywords)
├── templates/
│   ├── index.html            # Landing page
│   ├── upload.html           # PDF upload page
│   └── dashboard.html        # Analysis dashboard
└── modules/
    ├── pdf_loader.py         # PDF text extraction (PyPDFLoader)
    ├── text_splitter.py      # RecursiveCharacterTextSplitter
    ├── embeddings.py         # HuggingFace embeddings
    ├── vector_store.py       # FAISS vector store management
    ├── summarizer.py         # LLM-based summarization
    ├── keyword_extractor.py  # Keyword & concept extraction
    ├── rag_chain.py          # LangChain RetrievalQA pipeline
    ├── prompt_templates.py   # Custom prompt templates
    └── llm_provider.py       # OpenAI / Gemini LLM factory
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd ai_research_assistant
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** First run downloads the `all-MiniLM-L6-v2` model (~90 MB). This is cached locally.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

**Using Google Gemini (recommended — has a free tier):**
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
```
Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

**Using OpenAI:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## RAG Pipeline

```
PDF Upload
    │
    ▼
PyPDFLoader → extract text (page-by-page)
    │
    ▼
RecursiveCharacterTextSplitter → chunks (1000 chars, 200 overlap)
    │
    ▼
HuggingFace all-MiniLM-L6-v2 → embedding vectors
    │
    ▼
FAISS Vector Store → indexed per session
    │
    ▼
User Question → semantic search → top-K chunks retrieved
    │
    ▼
LLM (Gemini / GPT) + custom prompt → grounded answer
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload and process a PDF |
| `POST` | `/api/summarize` | Generate structured summary |
| `POST` | `/api/keywords` | Extract keywords |
| `POST` | `/api/insights` | Extract insights & novelty |
| `POST` | `/api/ask` | Ask a question (RAG) |
| `GET` | `/api/chat-history` | Get Q&A chat history |
| `POST` | `/api/chat-history/clear` | Clear chat history |
| `GET` | `/api/session-info` | Get session metadata |
| `POST` | `/api/download-summary` | Download summary as PDF |
| `POST` | `/api/export-keywords` | Export keywords as JSON |

---

## Prompt Engineering

All prompts are defined in `modules/prompt_templates.py` and are designed to:

- **Minimize hallucinations** by strictly restricting answers to retrieved context
- **Maintain academic language** appropriate for research paper analysis
- **Return structured output** (markdown sections, JSON for keywords)
- **Provide a fallback** response: *"Information not found in the uploaded document."*

---

## Skills Demonstrated

This project demonstrates:

- **AI Agent Development** — End-to-end autonomous document analysis pipeline
- **LangChain** — RetrievalQA chains, PromptTemplate, document loaders
- **RAG (Retrieval-Augmented Generation)** — FAISS retrieval + LLM generation
- **Prompt Engineering** — Custom prompts for summarization, QA, keywords, novelty
- **Vector Databases** — FAISS indexing, similarity search, per-session indices
- **LLM Integration** — OpenAI and Google Gemini provider abstraction
- **Semantic Search** — HuggingFace sentence transformers + cosine similarity
- **Flask Development** — REST APIs, session management, file handling
- **Full-Stack Development** — Responsive UI with Bootstrap 5 + vanilla JS

---

## License

MIT License
