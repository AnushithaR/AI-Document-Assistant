"""
backend/main.py
-----------------
FastAPI backend for the AI Document Assistant.

Exposes REST endpoints consumed by the React frontend:
    POST /upload   -> process uploaded PDFs into a FAISS index
    POST /ask      -> ask a question, get an answer + source citations
    GET  /history  -> retrieve past Q&A history from SQLite
    POST /reset    -> clear the current session's documents/index
    GET  /health   -> basic health check

Run with:
    uvicorn main:app --reload --port 8000
"""

from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import Config
from database import Database
from utils.pdf_loader import PDFLoader
from utils.text_splitter import TextChunker
from utils.vector_store import VectorStoreManager
from utils.rag_pipeline import RAGPipeline
from utils.helpers import save_uploaded_files, clear_data_folder, format_source_label


# ----------------------------------------------------------------------
# APP INITIALIZATION
# ----------------------------------------------------------------------
app = FastAPI(
    title="AI Document Assistant API",
    description="RAG-based Q&A backend over uploaded PDF documents.",
    version="1.0.0",
)

# CORS: allows the React frontend (different origin/port) to call this API.
# Without this, browsers block the requests with a CORS policy error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database is initialized once at startup and reused across requests.
db = Database()


# ----------------------------------------------------------------------
# IN-MEMORY APPLICATION STATE
# ----------------------------------------------------------------------
# IMPORTANT ARCHITECTURAL NOTE:
# Streamlit gave each browser tab its own st.session_state automatically.
# FastAPI has no equivalent built in — it's just a stateless request/response
# server. For this portfolio-scale project, we use a simple in-memory
# dictionary to hold the "current" RAG pipeline and processed PDF names.
#
# LIMITATION: This means all users share ONE active document set at a time
# (single-session behavior) — fine for a solo portfolio demo, but NOT
# suitable for multiple concurrent users in production. A production
# version would key this state by a session ID (e.g., a cookie or JWT)
# or per-user database records. This is called out as a "Future Improvement"
# in the README.
class AppState:
    rag_pipeline: Optional[RAGPipeline] = None
    processed_pdf_names: List[str] = []
    docs_processed: bool = False


state = AppState()


# ----------------------------------------------------------------------
# PYDANTIC MODELS (request/response schemas)
# ----------------------------------------------------------------------
class AskRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    label: str


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]


class UploadResponse(BaseModel):
    message: str
    num_files: int
    num_chunks: int
    processed_pdf_names: List[str]


class HistoryItem(BaseModel):
    id: int
    pdf_names: str
    question: str
    answer: str
    timestamp: str


class StatusResponse(BaseModel):
    docs_processed: bool
    processed_pdf_names: List[str]
    llm_provider: str


# ----------------------------------------------------------------------
# STARTUP VALIDATION
# ----------------------------------------------------------------------
@app.on_event("startup")
async def startup_validation():
    """
    Fails fast at server startup if required config (like the OpenAI key)
    is missing — same principle as Config.validate() in the Streamlit app,
    just triggered by the server boot instead of a page load.
    """
    try:
        Config.validate()
    except ValueError as e:
        # Log loudly but don't crash the whole server — lets you still
        # hit /health while fixing the .env file.
        print(f"⚠️  Configuration warning at startup: {e}")


# ----------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------
@app.get("/health", response_model=dict)
async def health_check():
    """Simple health check endpoint — useful for uptime monitoring and deployment checks."""
    return {"status": "ok"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Returns whether documents are currently processed and ready for questions."""
    return StatusResponse(
        docs_processed=state.docs_processed,
        processed_pdf_names=state.processed_pdf_names,
        llm_provider=Config.LLM_PROVIDER,
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Accepts one or more PDF files, extracts text, chunks it, builds a
    FAISS index, and initializes the RAG pipeline for subsequent /ask calls.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"'{f.filename}' is not a PDF. Only PDF files are supported.",
            )

    try:
        # Save uploaded files to disk (PyPDFLoader needs a real file path)
        saved_paths = await save_uploaded_files(files, Config.DATA_DIR)

        # Extract text
        loader = PDFLoader()
        documents = loader.load_documents(saved_paths)

        if not documents:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No extractable text found in the uploaded PDF(s). "
                    "They may be scanned images — OCR support is not enabled."
                ),
            )

        # Chunk text
        chunker = TextChunker(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
        )
        chunks = chunker.split_documents(documents)

        # Build FAISS index
        vector_store_manager = VectorStoreManager()
        vector_store = vector_store_manager.build_vector_store(chunks)
        vector_store_manager.save_local(vector_store)

        # Initialize RAG pipeline and store it in app state
        state.rag_pipeline = RAGPipeline(vector_store=vector_store)
        state.processed_pdf_names = [f.filename for f in files]
        state.docs_processed = True

        return UploadResponse(
            message=f"Successfully processed {len(files)} document(s).",
            num_files=len(files),
            num_chunks=len(chunks),
            processed_pdf_names=state.processed_pdf_names,
        )

    except HTTPException:
        raise  # re-raise our own intentional HTTP errors as-is
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process documents: {e}")


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Answers a natural language question using the currently processed
    documents. Requires /upload to have been called first.
    """
    if not state.docs_processed or state.rag_pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="No documents have been processed yet. Please upload PDFs first.",
        )

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer, source_documents = state.rag_pipeline.answer_question(request.question)

        # Build structured source chunk responses for the frontend
        sources = [
            SourceChunk(
                content=doc.page_content[:500] + ("..." if len(doc.page_content) > 500 else ""),
                source=doc.metadata.get("source", "unknown"),
                page=doc.metadata.get("page"),
                label=format_source_label(doc, i + 1),
            )
            for i, doc in enumerate(source_documents)
        ]

        # Log this interaction to SQLite (never blocks the response if it fails)
        db.log_interaction(
            pdf_names=state.processed_pdf_names,
            question=request.question,
            answer=answer,
        )

        return AskResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate an answer: {e}")


@app.get("/history", response_model=List[HistoryItem])
async def get_history(limit: int = 50):
    """Returns the most recent Q&A history entries, newest first."""
    history = db.get_history(limit=limit)
    return [HistoryItem(**item) for item in history]


@app.post("/reset")
async def reset_session():
    """
    Clears the current in-memory session (processed documents, RAG pipeline)
    and deletes uploaded files from disk. Does NOT clear SQLite history —
    use a separate endpoint/action for that if needed.
    """
    clear_data_folder()
    state.rag_pipeline = None
    state.processed_pdf_names = []
    state.docs_processed = False
    return {"message": "Session reset successfully."}