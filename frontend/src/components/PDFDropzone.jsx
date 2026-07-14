/**
 * PDFDropzone.jsx
 * ----------------
 * Drag-and-drop PDF uploader.
 *
 * Props:
 * - files: currently selected PDF files
 * - onFilesChange: function called when files are selected
 * - disabled: prevents file selection while processing
 */

import { useRef, useState } from "react";

export default function PDFDropzone({
  files = [],
  onFilesChange,
  disabled = false,
}) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState("");

  const validateFiles = (selectedFiles) => {
    const fileArray = Array.from(selectedFiles || []);

    const invalidFiles = fileArray.filter(
      (file) =>
        file.type !== "application/pdf" &&
        !file.name.toLowerCase().endsWith(".pdf")
    );

    if (invalidFiles.length > 0) {
      setError("Only PDF files are allowed.");
      return [];
    }

    const maximumSize = 20 * 1024 * 1024;

    const oversizedFiles = fileArray.filter(
      (file) => file.size > maximumSize
    );

    if (oversizedFiles.length > 0) {
      setError("Each PDF must be smaller than 20 MB.");
      return [];
    }

    setError("");
    return fileArray;
  };

  const addFiles = (selectedFiles) => {
    const validFiles = validateFiles(selectedFiles);

    if (validFiles.length === 0) {
      return;
    }

    const combinedFiles = [...files];

    validFiles.forEach((newFile) => {
      const alreadyExists = combinedFiles.some(
        (existingFile) =>
          existingFile.name === newFile.name &&
          existingFile.size === newFile.size
      );

      if (!alreadyExists) {
        combinedFiles.push(newFile);
      }
    });

    onFilesChange(combinedFiles);
  };

  const handleInputChange = (event) => {
    addFiles(event.target.files);

    // Allows selecting the same file again after removal.
    event.target.value = "";
  };

  const handleDragEnter = (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (event.currentTarget === event.target) {
      setIsDragging(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();

    setIsDragging(false);

    if (disabled) {
      return;
    }

    addFiles(event.dataTransfer.files);
  };

  const openFilePicker = () => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  const removeFile = (indexToRemove) => {
    const updatedFiles = files.filter(
      (_, index) => index !== indexToRemove
    );

    onFilesChange(updatedFiles);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="pdf-dropzone-wrapper">
      <div
        className={[
          "pdf-dropzone",
          isDragging ? "pdf-dropzone-dragging" : "",
          disabled ? "pdf-dropzone-disabled" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onClick={openFilePicker}
        onKeyDown={(event) => {
          if (
            !disabled &&
            (event.key === "Enter" || event.key === " ")
          ) {
            event.preventDefault();
            openFilePicker();
          }
        }}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          disabled={disabled}
          className="pdf-dropzone-input"
          onChange={handleInputChange}
        />

        <div className="pdf-dropzone-icon">📄</div>

        <h3>
          {isDragging
            ? "Drop your PDFs here"
            : "Drag and drop PDF files"}
        </h3>

        <p>
          Drop files here or{" "}
          <span className="pdf-dropzone-browse">
            click to browse
          </span>
        </p>

        <small>
          Multiple PDF files supported · Maximum 20 MB each
        </small>
      </div>

      {error && (
        <p className="pdf-dropzone-error">
          ⚠️ {error}
        </p>
      )}

      {files.length > 0 && (
        <div className="selected-pdf-list">
          <div className="selected-pdf-list-header">
            <span>Selected documents</span>

            <span>
              {files.length}{" "}
              {files.length === 1 ? "file" : "files"}
            </span>
          </div>

          {files.map((file, index) => (
            <div
              className="selected-pdf-item"
              key={`${file.name}-${file.size}-${index}`}
            >
              <div className="selected-pdf-icon">
                📄
              </div>

              <div className="selected-pdf-details">
                <p title={file.name}>
                  {file.name}
                </p>

                <span>
                  {formatFileSize(file.size)}
                </span>
              </div>

              <button
                type="button"
                className="selected-pdf-remove"
                onClick={(event) => {
                  event.stopPropagation();
                  removeFile(index);
                }}
                disabled={disabled}
                aria-label={`Remove ${file.name}`}
                title="Remove file"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}