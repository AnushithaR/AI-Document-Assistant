
/**
 * App.jsx
 * -------
 * Top-level component for the AI Document Assistant.
 *
 * Responsibilities:
 * - Displays the landing page
 * - Manages light/dark mode
 * - Loads backend status
 * - Manages processed-document state
 * - Manages chat history
 * - Connects Sidebar and ChatWindow
 */

import { useEffect, useState } from "react";

import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import LandingPage from "./components/LandingPage";
import ThemeToggle from "./components/ThemeToggle";
import LoadingIndicator from "./components/LoadingIndicator";

import { getStatus } from "./api";

import "./App.css";


export default function App() {
  const [docsProcessed, setDocsProcessed] = useState(false);

  const [processedPdfNames, setProcessedPdfNames] = useState([]);

  const [llmProvider, setLlmProvider] = useState("groq");

  const [chatHistory, setChatHistory] = useState([]);

  const [isInitialLoading, setIsInitialLoading] = useState(true);

  const [showWorkspace, setShowWorkspace] = useState(false);

  const [isDarkMode, setIsDarkMode] = useState(() => {
    const storedTheme = localStorage.getItem("document-assistant-theme");

    if (storedTheme) {
      return storedTheme === "dark";
    }

    return window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
  });


  // ------------------------------------------------------------------
  // LOAD BACKEND STATUS
  // ------------------------------------------------------------------
  useEffect(() => {
    async function loadInitialStatus() {
      try {
        const status = await getStatus();

        setDocsProcessed(Boolean(status.docs_processed));

        setProcessedPdfNames(
          Array.isArray(status.processed_pdf_names)
            ? status.processed_pdf_names
            : []
        );

        setLlmProvider(
          status.llm_provider || "groq"
        );

        // Open the workspace automatically when documents
        // are already processed in the backend.
        if (status.docs_processed) {
          setShowWorkspace(true);
        }
      } catch (error) {
        console.error(
          "Failed to fetch backend status:",
          error.message
        );
      } finally {
        setIsInitialLoading(false);
      }
    }

    loadInitialStatus();
  }, []);


  // ------------------------------------------------------------------
  // APPLY THEME
  // ------------------------------------------------------------------
  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      isDarkMode ? "dark" : "light"
    );

    document.body.classList.toggle(
      "dark-theme",
      isDarkMode
    );

    localStorage.setItem(
      "document-assistant-theme",
      isDarkMode ? "dark" : "light"
    );
  }, [isDarkMode]);


  // ------------------------------------------------------------------
  // DOCUMENT HANDLERS
  // ------------------------------------------------------------------
  const handleDocumentsProcessed = (pdfNames) => {
    setDocsProcessed(true);

    setProcessedPdfNames(
      Array.isArray(pdfNames) ? pdfNames : []
    );

    setChatHistory([]);

    setShowWorkspace(true);
  };


  const handleSessionReset = () => {
    setDocsProcessed(false);

    setProcessedPdfNames([]);

    setChatHistory([]);

    setShowWorkspace(false);
  };


  // ------------------------------------------------------------------
  // CHAT HANDLERS
  // ------------------------------------------------------------------
  const handleClearChat = () => {
    setChatHistory([]);
  };


  const handleNewMessage = (message) => {
    setChatHistory((previousMessages) => [
      ...previousMessages,
      message,
    ]);
  };


  // ------------------------------------------------------------------
  // THEME HANDLER
  // ------------------------------------------------------------------
  const handleThemeToggle = () => {
    setIsDarkMode((previousMode) => !previousMode);
  };


  // ------------------------------------------------------------------
  // LANDING PAGE HANDLER
  // ------------------------------------------------------------------
  const handleGetStarted = () => {
    setShowWorkspace(true);
  };


  // Count only user messages.
  const questionsAskedCount = chatHistory.filter(
    (message) => message.role === "user"
  ).length;


  // ------------------------------------------------------------------
  // INITIAL LOADING SCREEN
  // ------------------------------------------------------------------
  if (isInitialLoading) {
    return (
      <div
        className={`app-loading-screen ${
          isDarkMode ? "dark" : ""
        }`}
      >
        <LoadingIndicator message="Loading AI Document Assistant..." />
      </div>
    );
  }


  // ------------------------------------------------------------------
  // LANDING PAGE
  // ------------------------------------------------------------------
  if (!showWorkspace) {
    return (
      <div
        className={`app-shell ${
          isDarkMode ? "dark" : ""
        }`}
      >
        <div className="landing-theme-control">
          <ThemeToggle
            isDarkMode={isDarkMode}
            onToggle={handleThemeToggle}
          />
        </div>

        <LandingPage
          isDarkMode={isDarkMode}
          onGetStarted={handleGetStarted}
        />
      </div>
    );
  }


  // ------------------------------------------------------------------
  // MAIN APPLICATION
  // ------------------------------------------------------------------
  return (
    <div
      className={`app-container ${
        isDarkMode ? "dark" : ""
      }`}
    >
      <Sidebar
        docsProcessed={docsProcessed}
        processedPdfNames={processedPdfNames}
        llmProvider={llmProvider}
        questionsAskedCount={questionsAskedCount}
        onDocumentsProcessed={handleDocumentsProcessed}
        onClearChat={handleClearChat}
        onSessionReset={handleSessionReset}
      />

      <main className="main-panel">
        <header className="main-header">
          <div className="main-header-content">
            <div>
              <p className="header-eyebrow">
                Powered by {llmProvider.toUpperCase()} + RAG
              </p>

              <h1>📄 AI Document Assistant</h1>

              <p className="main-subtitle">
                Upload PDF documents and ask natural-language
                questions. Receive fast, context-aware answers
                grounded in your files.
              </p>
            </div>

            <ThemeToggle
              isDarkMode={isDarkMode}
              onToggle={handleThemeToggle}
            />
          </div>

          <div className="chat-toolbar">
            <div className="document-status-summary">
              {docsProcessed ? (
                <>
                  <span className="status-dot ready" />

                  <span>
                    {processedPdfNames.length}{" "}
                    {processedPdfNames.length === 1
                      ? "document"
                      : "documents"}{" "}
                    ready
                  </span>
                </>
              ) : (
                <>
                  <span className="status-dot waiting" />

                  <span>No documents processed</span>
                </>
              )}
            </div>

            <button
              type="button"
              className="clear-chat-toolbar-button"
              onClick={handleClearChat}
              disabled={chatHistory.length === 0}
            >
              🗑️ Clear Chat
            </button>
          </div>
        </header>

        <ChatWindow
          docsProcessed={docsProcessed}
          chatHistory={chatHistory}
          onNewMessage={handleNewMessage}
        />
      </main>
    </div>
  );
}

