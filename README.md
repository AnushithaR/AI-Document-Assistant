# 📄 AI Document Assistant — RAG-based Q&A over PDFs

An AI-powered document assistant that lets you upload PDF files and ask natural language questions about their content. Built using **Retrieval-Augmented Generation (RAG)** with **LangChain**, **FAISS**, **Sentence-Transformers**, and **OpenAI/Ollama**, wrapped in a clean **Streamlit** UI, with **SQLite** logging of every interaction.

Instead of relying purely on an LLM's training data (which can be outdated or hallucinate facts), this app retrieves the *actual relevant text* from your documents and grounds the LLM's answer in that context — with full citations back to the source page.

---

## ✨ Features

- 📤 Upload one or multiple PDF documents
- 📖 Automatic text extraction and chunking
- 🧠 Local, free embedding generation (Sentence-Transformers)
- 🔍 Semantic similarity search via FAISS vector database
- 💬 Chat-style Q&A interface with conversation history
- 📚 Expandable source citations (see exactly which page/chunk the answer came from)
- 🗑️ Separate "Clear Chat" (keeps documents) and "Reset All" (clears everything) controls
- 🗄️ SQLite logging of every question, answer, PDF name, and timestamp
- ⚙️ Swappable LLM backend (OpenAI or free local Ollama)
- 🛡️ Robust error handling throughout the pipeline

---

## 🏗️ Architecture

```
PDF Upload
    │
    ▼
PDF Text Extraction (pypdf / PyPDFLoader)
    │
    ▼
Text Chunking (RecursiveCharacterTextSplitter)
    │
    ▼
Embedding Generation (Sentence-Transformers, local)
    │
    ▼
FAISS Vector Store (semantic search index)
    │
    ▼
User Question ──► Similarity Search ──► Top-K Relevant Chunks
                                              │
                                              ▼
                                   Prompt + Context ──► LLM (OpenAI / Ollama)
                                              │
                                              ▼
                                   Answer + Source Citations
                                              │
                                              ▼
                                   Logged to SQLite (database.py)
```

---

## 🛠️ Tech Stack

| Component          | Technology                                      |
|---------------------|--------------------------------------------------|
| UI                  | Streamlit                                        |
| Orchestration       | LangChain (LCEL)                                |
| Vector Database     | FAISS                                            |
| Embeddings          | Sentence-Transformers (`all-MiniLM-L6-v2`)       |
| LLM                 | OpenAI (`gpt-4o-mini`) or local Ollama (`llama3.2`) |
| PDF Parsing         | pypdf                                            |
| History Logging     | SQLite (Python standard library)                 |
| Config Management   | python-dotenv                                    |

---

## 📁 Project Structure

```
AI-Document-Assistant/
│
├── app.py                     # Streamlit UI + main orchestration
├── config.py                  # Centralized configuration
├── database.py                # SQLite logging (NEW)
├── requirements.txt           # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore
├── README.md
│
├── data/                       # Uploaded PDFs (temporary storage)
├── vectorstore/                 # Persisted FAISS index
├── app_data.db                  # SQLite database (auto-created, gitignored)
│
├── utils/
│   ├── pdf_loader.py           # PDF text extraction
│   ├── text_splitter.py        # Chunking logic
│   ├── embeddings.py           # Embedding model loader
│   ├── vector_store.py         # FAISS build/save/load
│   ├── rag_pipeline.py         # Retrieval + LLM generation (LCEL)
│   └── helpers.py              # File I/O + formatting utilities
│
└── assets/                     # Screenshots, diagrams, etc.
```

---

## 🚀 Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/AI-Document-Assistant.git
cd AI-Document-Assistant
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Open `.env` and set your real `OPENAI_API_KEY` (or set `LLM_PROVIDER=ollama` for a free local model — see below).

### 5. Run the app
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`.

---

## 🔄 Using a Free Local LLM (Ollama) Instead of OpenAI

1. Install Ollama from https://ollama.com/download
2. Pull a model:
```bash
   ollama pull llama3.2
```
3. In `.env`, set:
```env
   LLM_PROVIDER=ollama
```
No other code changes needed — `utils/rag_pipeline.py` already supports both providers via `Config.LLM_PROVIDER`.

---

## ☁️ Deployment

### Option A: Streamlit Community Cloud (easiest, free)

1. Push your code to a **public or private GitHub repo** (make sure `.env` is NOT committed — check `.gitignore`).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, select your repo, branch, and set the main file path to `app.py`.
4. Under **Advanced settings → Secrets**, add your environment variables in TOML format:
```toml
   OPENAI_API_KEY = "sk-your-real-key-here"
   LLM_PROVIDER = "openai"
```
5. Click **Deploy**.

**Important limitation to know and mention if asked:** Streamlit Community Cloud's filesystem is **ephemeral** — it resets on every redeploy/restart. This means:
- The SQLite database (`app_data.db`) will reset on redeploy — fine for a demo, but not for long-term history.
- The FAISS index isn't meant to persist between users/sessions either — each user should upload and process their own PDFs per session, which is exactly how the app already works.
- If you need permanent history storage in production, the next step would be an external database (e.g., Supabase Postgres, or a mounted persistent volume on a VPS) — worth mentioning as a "future improvement" rather than something the free tier supports out of the box.

### Option B: Render / Railway / a VPS (more control, supports persistent storage)

1. Create a `Procfile` (if using Render/Railway with buildpacks):
```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```
2. Set environment variables (`OPENAI_API_KEY`, `LLM_PROVIDER`, etc.) in your host's dashboard — never in code.
3. Attach a **persistent disk/volume** mounted at your project root if you want `app_data.db`, `data/`, and `vectorstore/` to survive restarts.
4. Note: Ollama requires the Ollama binary running on the same host — most simple PaaS free tiers don't support this well. For hosted deployment, `LLM_PROVIDER=ollama` is the practical choice; keep Ollama for local development/demos.

### Environment Variables Checklist for Any Host
```
OPENAI_API_KEY=sk-...
LLM_PROVIDER=ollama
OLLAMA_MODEL_NAME=llama3.2
LLM_TEMPERATURE=0.2
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
RETRIEVAL_TOP_K=4
```
None of these should ever be hardcoded in source files — they're all read via `Config` from environment variables, so the same codebase works locally and in production just by changing the host's secret values.

---

## 🧪 How to Test Locally

1. Launch with `streamlit run app.py`.
2. Upload one or more PDFs in the sidebar and click **🚀 Process Documents**.
3. Ask a question grounded in the PDF content.
4. Expand **📚 View Source Chunks Used** to verify the citation is accurate.
5. Ask an out-of-scope question → confirm it says it couldn't find the info instead of hallucinating.
6. Click **🗑️ Clear Chat** → confirm chat clears but documents remain processed (no reprocessing needed).
7. Click **🔄 Reset All** → confirm everything resets, including uploaded files.
8. Check that `app_data.db` was created in your project root, and inspect it with any SQLite viewer (e.g., [DB Browser for SQLite](https://sqlitebrowser.org/)) to confirm your Q&A history is being logged correctly.

---

## 🗄️ Database Schema

```sql
CREATE TABLE qa_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_names TEXT NOT NULL,     -- comma-separated list of processed PDF filenames
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    timestamp TEXT NOT NULL      -- format: YYYY-MM-DD HH:MM:SS
);
```

---

## 🌱 Possible Future Improvements

- 🖼️ **OCR support** for scanned/image-based PDFs (via `pytesseract` or `unstructured`)
- 🧵 **Conversation memory** — follow-up questions referencing earlier chat context (`RunnableWithMessageHistory`)
- 📊 **Admin dashboard** — a simple page reading from `database.py`'s `get_history()` to visualize usage trends
- ☁️ **External persistent database** — swap SQLite for Supabase/Postgres for true production persistence across redeploys
- 🔌 **Full local LLM deployment** — self-host with Ollama on a VPS with a GPU for a zero-API-cost production version
- 🗣️ **Multi-format support** — .docx, .txt, .pptx uploads

---

## 📜 License

This project is open-source and available for personal/portfolio use.