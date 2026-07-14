"""
utils/text_splitter.py
------------------------
Splits full-page Document objects into smaller overlapping text chunks.

Uses RecursiveCharacterTextSplitter, which tries to split on natural
boundaries first (paragraphs -> sentences -> words -> characters),
producing more coherent chunks than a naive fixed-size split.
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class TextChunker:
    """
    Responsible for splitting Document objects into smaller chunks
    suitable for embedding and retrieval.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        """
        Args:
            chunk_size: Max number of characters per chunk.
            chunk_overlap: Number of overlapping characters between
                           consecutive chunks (preserves context continuity).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # RecursiveCharacterTextSplitter tries these separators in order,
        # falling back to the next one if a chunk is still too large.
        # This produces more "natural" chunks than splitting every N characters.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of full-page Documents into smaller chunk Documents.
        Metadata (source, page) is automatically carried over to each chunk
        by LangChain's splitter.

        Args:
            documents: List of Document objects (typically one per PDF page).

        Returns:
            List of smaller Document chunks ready for embedding.

        Raises:
            ValueError: If the input document list is empty.
        """
        if not documents:
            raise ValueError("No documents provided to split. Did PDF extraction fail?")

        try:
            chunks = self.splitter.split_documents(documents)
            return chunks
        except Exception as e:
            # Wrap unexpected splitter errors with more context for easier debugging
            raise RuntimeError(f"Failed to split documents into chunks: {e}") from e