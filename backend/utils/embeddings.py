"""
utils/embeddings.py
---------------------
Provides the embedding model used to convert text chunks into vectors.

Uses a local Sentence-Transformers model via langchain-huggingface, so
embedding generation is free and works fully offline (no API key needed).
"""

from langchain_huggingface import HuggingFaceEmbeddings

from config import Config


class EmbeddingModel:
    """
    Wraps the HuggingFace/Sentence-Transformers embedding model.

    Uses a class-level cache so the (relatively large) model weights are
    only loaded into memory once, even if this class is instantiated
    multiple times during a Streamlit session (Streamlit reruns scripts
    on every interaction, so avoiding redundant model loads matters for
    performance).
    """

    _cached_instance = None  # class-level cache for the loaded embedding model

    @classmethod
    def get_embedding_model(cls) -> HuggingFaceEmbeddings:
        """
        Returns a cached HuggingFaceEmbeddings instance, creating it on
        first call.

        Returns:
            An instance of HuggingFaceEmbeddings ready to embed text.

        Raises:
            RuntimeError: If the embedding model fails to load (e.g. no
                          internet connection on first-time download, or
                          an invalid model name).
        """
        if cls._cached_instance is not None:
            return cls._cached_instance

        try:
            embedding_model = HuggingFaceEmbeddings(
                model_name=Config.EMBEDDING_MODEL_NAME,
                # Running on CPU by default keeps this portable across
                # laptops without requiring CUDA/GPU setup.
                model_kwargs={"device": "cpu"},
                # Normalizing embeddings improves similarity search accuracy
                # when using cosine-similarity-based FAISS indexes.
                encode_kwargs={"normalize_embeddings": True},
            )
            cls._cached_instance = embedding_model
            return embedding_model

        except Exception as e:
            raise RuntimeError(
                f"Failed to load embedding model '{Config.EMBEDDING_MODEL_NAME}': {e}"
            ) from e