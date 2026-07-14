"""
utils/helpers.py
------------------
Small, reusable utility functions used across the backend.
"""

import shutil
from pathlib import Path
from typing import List

from fastapi import UploadFile
from langchain_core.documents import Document


async def save_uploaded_files(uploaded_files: List[UploadFile], destination_dir: Path) -> List[Path]:
    """
    Saves FastAPI UploadFile objects to disk so they can be read by
    file-path-based loaders like PyPDFLoader.

    NOTE: This is now an async function because FastAPI's UploadFile.read()
    is an async method (it streams the file rather than loading it all
    into memory synchronously, which is more efficient for larger PDFs).

    Args:
        uploaded_files: List of FastAPI UploadFile objects from a
                        multipart/form-data request.
        destination_dir: Directory (Path) to save the files into.

    Returns:
        List of Paths pointing to the newly saved files on disk.

    Raises:
        RuntimeError: If a file fails to save.
    """
    saved_paths = []

    for uploaded_file in uploaded_files:
        try:
            file_path = destination_dir / uploaded_file.filename

            # Read the uploaded file's bytes asynchronously, then write to disk
            contents = await uploaded_file.read()
            with open(file_path, "wb") as f:
                f.write(contents)

            saved_paths.append(file_path)

        except Exception as e:
            raise RuntimeError(
                f"Failed to save uploaded file '{uploaded_file.filename}': {e}"
            ) from e

    return saved_paths


def clear_data_folder(data_dir: Path = None) -> None:
    """
    Deletes all files inside the data/ directory.
    """
    from config import Config

    target_dir = data_dir or Config.DATA_DIR

    try:
        if target_dir.exists():
            for item in target_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
    except Exception as e:
        print(f"[helpers] Warning: Failed to clear data folder: {e}")


def format_source_label(document: Document, index: int) -> str:
    """
    Builds a clean, human-readable label for a source chunk.
    """
    source = document.metadata.get("source", "Unknown document")
    page = document.metadata.get("page", None)

    if page is not None:
        return f"Source {index}: {source} — Page {page + 1}"
    else:
        return f"Source {index}: {source}"