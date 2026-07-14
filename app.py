
"""
app.py
------
Main Streamlit entry point for the AI Document Assistant.

Run with:
    streamlit run app.py
"""

import streamlit as st

from config import Config
from database import Database
from utils.pdf_loader import PDFLoader
from utils.text_splitter import TextChunker
from utils.vector_store import VectorStoreManager
from utils.rag_pipeline import RAGPipeline
from utils.helpers import save_uploaded_files, clear_data_folder


# ----------------------------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------------
# CONFIGURATION VALIDATION
# ----------------------------------------------------------------------
try:
    Config.validate()
except ValueError as error:
    st.error(f"⚠️ Configuration error: {error}")
    st.stop()


# ----------------------------------------------------------------------
# DATABASE INITIALIZATION
# ----------------------------------------------------------------------
@st.cache_resource
def get_database() -> Database:
    """Create and cache a single Database instance."""
    return Database()


db = get_database()


# ----------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------------------------
def init_session_state() -> None:
    """Initialize required Streamlit session-state values."""

    defaults = {
        "chat_history": [],
        "docs_processed": False,
        "rag_pipeline": None,
        "processed_pdf_names": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ----------------------------------------------------------------------
# CUSTOM STYLING
# ----------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main-subtitle {
            color: #6b7280;
            font-size: 1rem;
            margin-top: -0.5rem;
            margin-bottom: 1.5rem;
        }

        .stat-badge {
            background-color: #f3f4f6;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("📁 Upload Documents")

    st.write(
        "Upload one or more PDF files, then click "
        "**Process Documents**."
    )

    uploaded_files = st.file_uploader(
        label="Choose PDF file(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help=(
            "You can upload multiple PDFs at once. "
            "They will all be searchable together."
        ),
    )

    process_clicked = st.button(
        "🚀 Process Documents",
        use_container_width=True,
        type="primary",
    )

    st.divider()

    if st.session_state.docs_processed:
        st.success(
            "✅ Documents processed and ready for questions."
        )

        with st.expander("📄 Processed files"):
            for name in st.session_state.processed_pdf_names:
                st.write(f"• {name}")
    else:
        st.info("⏳ No documents processed yet.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        clear_chat_clicked = st.button(
            "🗑️ Clear Chat",
            use_container_width=True,
            help=(
                "Clears the conversation but keeps "
                "processed documents."
            ),
        )

        if clear_chat_clicked:
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        reset_all_clicked = st.button(
            "🔄 Reset All",
            use_container_width=True,
            help=(
                "Clears documents, chat, and the vector store."
            ),
        )

        if reset_all_clicked:
            clear_data_folder()

            st.session_state.chat_history = []
            st.session_state.docs_processed = False
            st.session_state.rag_pipeline = None
            st.session_state.processed_pdf_names = []

            st.rerun()

    st.divider()

    st.caption(
        f"🧠 LLM Provider: **{Config.LLM_PROVIDER}**"
    )

    question_count = sum(
        1
        for message in st.session_state.chat_history
        if message.get("role") == "user"
    )

    st.caption(
        f"💬 Questions asked this session: **{question_count}**"
    )


# ----------------------------------------------------------------------
# DOCUMENT PROCESSING
# ----------------------------------------------------------------------
if process_clicked:
    if not uploaded_files:
        st.sidebar.error(
            "⚠️ Please upload at least one PDF before processing."
        )

    else:
        try:
            with st.spinner("📥 Saving uploaded files..."):
                saved_paths = save_uploaded_files(
                    uploaded_files,
                    Config.DATA_DIR,
                )

            with st.spinner("📖 Extracting text from PDFs..."):
                loader = PDFLoader()
                documents = loader.load_documents(saved_paths)

            if not documents:
                st.sidebar.error(
                    "⚠️ No extractable text was found in the "
                    "uploaded PDF files. They may contain scanned "
                    "images, and OCR support is not currently enabled."
                )

            else:
                with st.spinner("✂️ Splitting text into chunks..."):
                    chunker = TextChunker(
                        chunk_size=Config.CHUNK_SIZE,
                        chunk_overlap=Config.CHUNK_OVERLAP,
                    )

                    chunks = chunker.split_documents(documents)

                if not chunks:
                    raise ValueError(
                        "No text chunks could be created "
                        "from the uploaded documents."
                    )

                with st.spinner(
                    "🧠 Generating embeddings and building "
                    "the FAISS index..."
                ):
                    vector_store_manager = VectorStoreManager()

                    vector_store = (
                        vector_store_manager.build_vector_store(
                            chunks
                        )
                    )

                    vector_store_manager.save_local(vector_store)

                with st.spinner(
                    "🔗 Initializing the RAG pipeline..."
                ):
                    rag_pipeline = RAGPipeline(
                        vector_store=vector_store
                    )

                    st.session_state.rag_pipeline = rag_pipeline

                st.session_state.docs_processed = True
                st.session_state.chat_history = []
                st.session_state.processed_pdf_names = [
                    uploaded_file.name
                    for uploaded_file in uploaded_files
                ]

                st.sidebar.success(
                    f"✅ Processed {len(uploaded_files)} "
                    f"document(s) into {len(chunks)} chunks."
                )

                st.rerun()

        except Exception as error:
            st.sidebar.error(
                "❌ An error occurred while processing "
                f"the documents: {error}"
            )


# ----------------------------------------------------------------------
# MAIN PANEL
# ----------------------------------------------------------------------
st.title("📄 AI Document Assistant")

st.markdown(
    """
    <p class="main-subtitle">
        Ask natural-language questions about your uploaded PDF
        documents — powered by Retrieval-Augmented Generation.
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ----------------------------------------------------------------------
# DISPLAY CHAT HISTORY
# ----------------------------------------------------------------------
for message in st.session_state.chat_history:
    role = message.get("role", "assistant")
    content = message.get("content", "")

    with st.chat_message(role):
        st.markdown(content)


# ----------------------------------------------------------------------
# CHAT INPUT
# ----------------------------------------------------------------------
user_question = st.chat_input(
    placeholder=(
        "Ask a question about your documents..."
        if st.session_state.docs_processed
        else "Upload and process documents first..."
    ),
    disabled=not st.session_state.docs_processed,
)


# ----------------------------------------------------------------------
# QUESTION-ANSWERING FLOW
# ----------------------------------------------------------------------
if user_question:
    cleaned_question = user_question.strip()

    if cleaned_question:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": cleaned_question,
            }
        )

        with st.chat_message("user"):
            st.markdown(cleaned_question)

        with st.chat_message("assistant"):
            try:
                rag_pipeline = st.session_state.rag_pipeline

                if rag_pipeline is None:
                    raise RuntimeError(
                        "The RAG pipeline is not initialized. "
                        "Please process the documents again."
                    )

                with st.spinner("🤔 Thinking..."):
                    answer, _sources = (
                        rag_pipeline.answer_question(
                            cleaned_question
                        )
                    )

                st.markdown(answer)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

                db.log_interaction(
                    pdf_names=(
                        st.session_state.processed_pdf_names
                    ),
                    question=cleaned_question,
                    answer=answer,
                )

            except Exception as error:
                error_message = (
                    "❌ Sorry, I couldn't generate an answer: "
                    f"{error}"
                )

                st.error(error_message)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )
```
