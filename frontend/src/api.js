/**
 * api.js
 * -------
 * Centralized API client for communicating with the FastAPI backend.
 * All HTTP requests to the backend go through this file, so components
 * never need to know about URLs, headers, or axios directly.
 */

import axios from "axios";

// Base URL of the FastAPI backend. In development this is localhost:8000.
// In production, this should be set via an environment variable (Vite
// exposes env vars prefixed with VITE_ at build time) rather than hardcoded.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// A pre-configured axios instance — every request automatically uses
// the base URL above, so calls elsewhere just need the path (e.g. "/ask").
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds — LLM responses (especially local Ollama) can be slow
});

/**
 * Uploads one or more PDF files to the backend for processing.
 *
 * @param {File[]} files - Array of File objects from an <input type="file">
 * @returns {Promise<Object>} Response data: { message, num_files, num_chunks, processed_pdf_names }
 */
export async function uploadDocuments(files) {
  const formData = new FormData();
  files.forEach((file) => {
    // Field name "files" must match the FastAPI route's parameter name
    formData.append("files", file);
  });

  try {
    const response = await apiClient.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    // Normalize error handling: FastAPI returns error details in
    // error.response.data.detail — surface that clearly to the caller.
    throw new Error(
      error.response?.data?.detail || "Failed to upload documents. Please try again."
    );
  }
}

/**
 * Asks a question about the currently processed documents.
 *
 * @param {string} question - The user's natural language question
 * @returns {Promise<Object>} Response data: { answer, sources: [{content, source, page, label}] }
 */
export async function askQuestion(question) {
  try {
    const response = await apiClient.post("/ask", { question });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || "Failed to get an answer. Please try again."
    );
  }
}

/**
 * Retrieves past Q&A history from the backend's SQLite database.
 *
 * @param {number} limit - Max number of history entries to fetch
 * @returns {Promise<Array>} List of history items: { id, pdf_names, question, answer, timestamp }
 */
export async function getHistory(limit = 50) {
  try {
    const response = await apiClient.get("/history", { params: { limit } });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || "Failed to fetch history."
    );
  }
}

/**
 * Resets the current session — clears processed documents and the
 * in-memory RAG pipeline state on the backend (does not clear history).
 *
 * @returns {Promise<Object>} Response data: { message }
 */
export async function resetSession() {
  try {
    const response = await apiClient.post("/reset");
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || "Failed to reset session."
    );
  }
}

/**
 * Checks whether documents are currently processed and ready for questions.
 *
 * @returns {Promise<Object>} { docs_processed, processed_pdf_names, llm_provider }
 */
export async function getStatus() {
  try {
    const response = await apiClient.get("/status");
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || "Failed to fetch status."
    );
  }
}