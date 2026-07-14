"""
utils/vector_store.py
------------------------
Manages creation, saving, and loading of the FAISS vector store.

FAISS (Facebook AI Similarity Search) is a library for efficient
similarity search over dense vectors. Here it stores the embeddings
of our document chunks and lets us retrieve the most relevant chunks
for a given user question.
"""

from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config import Config
from utils.embeddings import EmbeddingModel


class VectorStoreManager:
    """
    Responsible for building, saving, and loading the FAISS vector store.
    """

    def __init__(self):
        # Load (or retrieve cached) embedding model once, reused for all
        # embedding operations in this manager.
        self.embedding_model = EmbeddingModel.get_embedding_model()
        self.index_path = Config.VECTORSTORE_DIR / Config.FAISS_INDEX_NAME

    def build_vector_store(self, chunks: List[Document]) -> FAISS:
        """
        Builds a new FAISS vector store from a list of text chunks.

        Args:
            chunks: List of Document chunks (from TextChunker) to embed
                    and index.

        Returns:
            A FAISS vector store instance ready for similarity search.

        Raises:
            ValueError: If no chunks are provided.
            RuntimeError: If embedding/index creation fails.
        """
        if not chunks:
            raise ValueError("No text chunks provided to build the vector store.")

        try:
            # FAISS.from_documents handles embedding generation for every
            # chunk AND building the similarity search index in one step.
            vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=self.embedding_model,
            )
            return vector_store

        except Exception as e:
            raise RuntimeError(f"Failed to build FAISS vector store: {e}") from e

    def save_local(self, vector_store: FAISS) -> None:
        """
        Persists the FAISS index to disk so it can be reloaded later
        without re-embedding all documents.

        Args:
            vector_store: The FAISS vector store instance to save.
        """
        try:
            vector_store.save_local(str(self.index_path))
        except Exception as e:
            raise RuntimeError(f"Failed to save FAISS index to disk: {e}") from e

    def load_local(self) -> FAISS:
        """
        Loads a previously saved FAISS index from disk.

        Returns:
            The loaded FAISS vector store instance.

        Raises:
            FileNotFoundError: If no saved index exists at the expected path.
            RuntimeError: If loading the index fails for another reason.
        """
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"No saved FAISS index found at '{self.index_path}'. "
                "Please process documents first."
            )

        try:
            # allow_dangerous_deserialization=True is required by LangChain
            # because loading a FAISS index involves unpickling metadata.
            # This is safe here since we only ever load indexes WE created
            # and saved ourselves (not from an untrusted external source).
            vector_store = FAISS.load_local(
                str(self.index_path),
                embeddings=self.embedding_model,
                allow_dangerous_deserialization=True,
            )
            return vector_store
        except Exception as e:
            raise RuntimeError(f"Failed to load FAISS index from disk: {e}") from e