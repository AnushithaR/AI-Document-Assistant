
/**
 * Sidebar.jsx
 * -----------
 * Handles PDF upload, document processing, and session controls.
 *
 * Features:
 * - Drag-and-drop PDF upload
 * - Multiple file support
 * - Processing status
 * - Processed document list
 * - Clear chat
 * - Reset session
 */

import { useState } from "react";

import PDFDropzone from "./PDFDropzone";
import { resetSession, uploadDocuments } from "../api";


export default function Sidebar({
  docsProcessed,
  processedPdfNames = [],
  llmProvider,
  questionsAskedCount,
  onDocumentsProcessed,
  onClearChat,
  onSessionReset,
}) {
  const [selectedFiles, setSelectedFiles] = useState([]);

  const [isProcessing, setIsProcessing] = useState(false);

  const [isResetting, setIsResetting] = useState(false);

  const [statusMessage, setStatusMessage] = useState(null);


  // ------------------------------------------------------------------
  // HANDLE FILE SELECTION
  // ------------------------------------------------------------------
  const handleFilesChange = (files) => {
    setSelectedFiles(Array.isArray(files) ? files : []);

    setStatusMessage(null);
  };


  // ------------------------------------------------------------------
  // PROCESS DOCUMENTS
  // ------------------------------------------------------------------
  const handleProcessDocuments = async () => {
    if (selectedFiles.length === 0) {
      setStatusMessage({
        type: "error",
        text: "⚠️ Please select at least one PDF before processing.",
      });

      return;
    }

    setIsProcessing(true);
    setStatusMessage({
      type: "info",
      text: "📄 Reading documents and creating embeddings...",
    });

    try {
      const result = await uploadDocuments(selectedFiles);

      const processedNames = Array.isArray(
        result.processed_pdf_names
      )
        ? result.processed_pdf_names
        : selectedFiles.map((file) => file.name);

      onDocumentsProcessed(processedNames);

      setStatusMessage({
        type: "success",
        text:
          `✅ Processed ${result.num_files ?? selectedFiles.length} ` +
          `document(s) into ${result.num_chunks ?? 0} chunks.`,
      });

      setSelectedFiles([]);
    } catch (error) {
      setStatusMessage({
        type: "error",
        text:
          `❌ ${
            error?.message ||
            "Failed to process the selected documents."
          }`,
      });
    } finally {
      setIsProcessing(false);
    }
  };


  // ------------------------------------------------------------------
  // RESET SESSION
  // ------------------------------------------------------------------
  const handleResetAll = async () => {
    setIsResetting(true);

    setStatusMessage({
      type: "info",
      text: "🔄 Resetting documents and conversation...",
    });

    try {
      await resetSession();

      onSessionReset();

      setSelectedFiles([]);

      setStatusMessage(null);
    } catch (error) {
      setStatusMessage({
        type: "error",
        text:
          `❌ ${
            error?.message ||
            "Failed to reset the current session."
          }`,
      });
    } finally {
      setIsResetting(false);
    }
  };


  // ------------------------------------------------------------------
  // RENDER
  // ------------------------------------------------------------------
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand-icon">
          📄
        </div>

        <div>
          <h2>Upload Documents</h2>

          <p className="sidebar-hint">
            Add one or more PDF files and process them
            before asking questions.
          </p>
        </div>
      </div>


      <PDFDropzone
        files={selectedFiles}
        onFilesChange={handleFilesChange}
        disabled={isProcessing || isResetting}
      />


      <button
        type="button"
        className="btn btn-primary process-documents-button"
        onClick={handleProcessDocuments}
        disabled={
          isProcessing ||
          isResetting ||
          selectedFiles.length === 0
        }
      >
        {isProcessing
          ? "🤖 Processing Documents..."
          : "🚀 Process Documents"}
      </button>


      {isProcessing && (
        <div className="document-processing-animation">
          <div className="processing-spinner" />

          <div>
            <strong>
              AI is reading your documents
            </strong>

            <p>
              Extracting text, creating chunks, and building
              the vector index.
            </p>
          </div>
        </div>
      )}


      {statusMessage && (
        <div
          className={
            `status-message status-${statusMessage.type}`
          }
        >
          {statusMessage.text}
        </div>
      )}


      <hr />


      {docsProcessed ? (
        <div className="status-box status-success">
          <div className="status-box-header">
            <span className="ready-indicator" />

            <div>
              <strong>
                Documents are ready
              </strong>

              <p>
                You can now ask questions about the uploaded PDFs.
              </p>
            </div>
          </div>


          {processedPdfNames.length > 0 && (
            <div className="processed-document-list">
              {processedPdfNames.map((name, index) => (
                <div
                  className="processed-document-card"
                  key={`${name}-${index}`}
                >
                  <div className="processed-document-icon">
                    📄
                  </div>

                  <div className="processed-document-info">
                    <p title={name}>
                      {name}
                    </p>

                    <span>
                      ✓ Ready for questions
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="status-box status-info">
          <div className="status-box-header">
            <span className="waiting-indicator" />

            <div>
              <strong>
                No documents processed
              </strong>

              <p>
                Upload and process PDFs to begin.
              </p>
            </div>
          </div>
        </div>
      )}


      <hr />


      <div className="button-row">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onClearChat}
          disabled={!docsProcessed}
        >
          🗑️ Clear Chat
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleResetAll}
          disabled={isProcessing || isResetting}
        >
          {isResetting
            ? "⏳ Resetting..."
            : "🔄 Reset All"}
        </button>
      </div>


      <hr />


      <div className="sidebar-stats">
        <div className="sidebar-stat-item">
          <span>
            🧠 LLM Provider
          </span>

          <strong>
            {(llmProvider || "groq").toUpperCase()}
          </strong>
        </div>

        <div className="sidebar-stat-item">
          <span>
            💬 Questions asked
          </span>

          <strong>
            {questionsAskedCount ?? 0}
          </strong>
        </div>
      </div>
    </aside>
  );
}

