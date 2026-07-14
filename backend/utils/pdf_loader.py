"""
utils/pdf_loader.py
--------------------
Handles loading PDF files and extracting text + metadata (source filename, page number).

Uses LangChain's PyPDFLoader (backed by pypdf) under the hood.
Each extracted page becomes a LangChain `Document` object with:
    - page_content: the extracted text
    - metadata: {"source": filename, "page": page_number}
"""

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


class PDFLoader:
    """
    Responsible for loading one or more PDF files and converting them
    into a list of LangChain Document objects (one per page).
    """

    def load_single_pdf(self, file_path: Path) -> List[Document]:
        """
        Loads a single PDF file and returns its pages as Document objects.

        Args:
            file_path: Path to the PDF file on disk.

        Returns:
            List of Document objects (one per page). Empty list if the
            file could not be read or contains no extractable text.
        """
        try:
            loader = PyPDFLoader(str(file_path))
            pages = loader.load()  # returns List[Document], one per page

            # Ensure the "source" metadata is just the filename (not full path)
            # This keeps citations clean in the UI, e.g. "report.pdf - Page 3"
            for page in pages:
                page.metadata["source"] = file_path.name

            return pages

        except Exception as e:
            # A single corrupt/unreadable PDF should not crash the whole batch.
            # We log a friendly message and return an empty list for this file.
            print(f"[PDFLoader] Failed to load '{file_path.name}': {e}")
            return []

    def load_documents(self, file_paths: List[Path]) -> List[Document]:
        """
        Loads multiple PDF files and combines all their pages into a single list.

        Args:
            file_paths: List of Paths to PDF files.

        Returns:
            Combined list of Document objects from all successfully loaded PDFs.
        """
        all_documents: List[Document] = []

        for file_path in file_paths:
            documents = self.load_single_pdf(file_path)
            if documents:
                all_documents.extend(documents)
            else:
                print(f"[PDFLoader] Warning: No text extracted from '{file_path.name}'.")

        return all_documents