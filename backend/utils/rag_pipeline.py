"""
utils/rag_pipeline.py
---------------------
Core RAG (Retrieval-Augmented Generation) pipeline.

Combines:
    1. Semantic retrieval from a FAISS vector store
    2. A prompt template grounded in retrieved document context
    3. A configurable LLM provider

Supported providers:
    - Groq
    - Ollama
    - OpenAI
"""

from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from config import Config


RAG_PROMPT_TEMPLATE = """
You are a professional AI document assistant.

Answer the user's question using only the information available in the
provided document context.

Instructions:
- Use only the provided document context.
- Do not use outside knowledge.
- Do not invent or assume information.
- Answer naturally, as if you carefully read the document.
- Do not mention phrases such as "document chunk", "chunk 1",
  "retrieved context", or "source chunk" in the answer.
- Do not explain how the information was retrieved.
- For questions asking for skills, qualifications, experience, projects,
  responsibilities, achievements, or similar lists, use clear bullet points.
- For simple questions, give a direct and concise answer.
- Correct minor grammar mistakes in the user's question silently.
- Do not include page numbers or source names in the main answer because
  the application already displays source chunks separately.
- If the answer is not available in the context, say:
  "I couldn't find this information in the uploaded document."

Document context:
{context}

User question:
{question}

Answer:
"""


class RAGPipeline:
    """Handles retrieval and answer generation for uploaded documents."""

    def __init__(self, vector_store: FAISS):
        """
        Initialize the RAG pipeline.

        Args:
            vector_store: FAISS vector store containing document chunks.
        """
        if vector_store is None:
            raise ValueError("A valid FAISS vector store is required.")

        self.vector_store = vector_store

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.RETRIEVAL_TOP_K},
        )

        self.llm = self._load_llm()
        self.prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

        self.chain = (
            {
                "context": self._format_docs_wrapper,
                "question": RunnablePassthrough(),
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _load_llm(self):
        """
        Load the LLM selected in Config.LLM_PROVIDER.

        Supported values:
            groq
            ollama
            openai
        """
        provider = Config.LLM_PROVIDER.strip().lower()

        if provider == "groq":
            if not Config.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is missing. Add it to backend/.env."
                )

            return ChatGroq(
                api_key=Config.GROQ_API_KEY,
                model=Config.GROQ_MODEL_NAME,
                temperature=Config.LLM_TEMPERATURE,
            )

        if provider == "ollama":
            return ChatOllama(
                model=Config.OLLAMA_MODEL_NAME,
                temperature=Config.LLM_TEMPERATURE,
            )

        if provider == "openai":
            if not Config.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is missing. Add it to backend/.env."
                )

            return ChatOpenAI(
                api_key=Config.OPENAI_API_KEY,
                model=Config.OPENAI_MODEL_NAME,
                temperature=Config.LLM_TEMPERATURE,
            )

        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            "Expected 'groq', 'ollama', or 'openai'."
        )

    def _format_docs_wrapper(self, question: str) -> str:
        """
        Retrieve relevant documents for the question and format them.
        """
        documents = self.retriever.invoke(question)
        return self._format_docs(documents)

    @staticmethod
    def _format_docs(documents: List[Document]) -> str:
        """
        Format retrieved document chunks into one context string.

        Chunk labels are included only to separate context internally.
        The prompt instructs the model not to mention them in its answer.
        """
        if not documents:
            return "No relevant document context was found."

        formatted_documents = []

        for document in documents:
            content = document.page_content.strip()

            if content:
                formatted_documents.append(content)

        return "\n\n---\n\n".join(formatted_documents)

    def answer_question(
        self,
        question: str,
    ) -> Tuple[str, List[Document]]:
        """
        Answer a question using retrieved PDF content.

        Returns:
            Tuple containing:
            - generated answer
            - retrieved source documents
        """
        cleaned_question = question.strip() if question else ""

        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        try:
            source_documents = self.retriever.invoke(cleaned_question)

            if not source_documents:
                return (
                    "I couldn't find this information "
                    "in the uploaded document.",
                    [],
                )

            answer = self.chain.invoke(cleaned_question)

            if not answer or not answer.strip():
                answer = (
                    "I couldn't generate an answer from "
                    "the uploaded document."
                )

            return answer.strip(), source_documents

        except Exception as error:
            raise RuntimeError(
                f"Failed to generate an answer: {error}"
            ) from error