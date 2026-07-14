/**
 * ChatWindow.jsx
 * --------------
 * Renders the conversation and handles question submission.
 *
 * Features:
 * - Modern user/assistant chat bubbles
 * - Typing animation for new assistant answers
 * - Copy-answer button
 * - Loading animation
 * - Auto-scroll
 * - Multiline question input
 */

import { useEffect, useRef, useState } from "react";

import { askQuestion } from "../api";


function ChatMessage({
  message,
  shouldAnimate = false,
}) {
  const isUser = message.role === "user";

  const [displayedContent, setDisplayedContent] = useState(
    shouldAnimate && !isUser ? "" : message.content
  );

  const [copied, setCopied] = useState(false);


  useEffect(() => {
    if (!shouldAnimate || isUser) {
      setDisplayedContent(message.content);
      return;
    }

    let currentIndex = 0;

    const intervalId = window.setInterval(() => {
      currentIndex += 1;

      setDisplayedContent(
        message.content.slice(0, currentIndex)
      );

      if (currentIndex >= message.content.length) {
        window.clearInterval(intervalId);
      }
    }, 8);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [message.content, shouldAnimate, isUser]);


  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);

      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch (error) {
      console.error(
        "Failed to copy answer:",
        error
      );
    }
  };


  return (
    <div
      className={`chat-message-row ${
        isUser
          ? "chat-message-row-user"
          : "chat-message-row-assistant"
      }`}
    >
      {!isUser && (
        <div className="chat-message-avatar assistant-avatar">
          🤖
        </div>
      )}

      <div
        className={`chat-message-bubble ${
          isUser
            ? "chat-message-bubble-user"
            : "chat-message-bubble-assistant"
        }`}
      >
        <div className="chat-message-text">
          {displayedContent}
        </div>

        {!isUser && message.content && (
          <div className="chat-message-actions">
            <button
              type="button"
              className="copy-answer-button"
              onClick={handleCopy}
              title="Copy answer"
            >
              {copied ? "✓ Copied" : "📋 Copy"}
            </button>
          </div>
        )}
      </div>

      {isUser && (
        <div className="chat-message-avatar user-avatar">
          🧑
        </div>
      )}
    </div>
  );
}


function ThinkingMessage() {
  return (
    <div className="chat-message-row chat-message-row-assistant">
      <div className="chat-message-avatar assistant-avatar">
        🤖
      </div>

      <div className="chat-message-bubble chat-message-bubble-assistant">
        <div className="thinking-indicator">
          <div className="thinking-dots">
            <span />
            <span />
            <span />
          </div>

          <div>
            <strong>
              AI is generating an answer
            </strong>

            <p>
              Searching the document and preparing a response...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


export default function ChatWindow({
  docsProcessed,
  chatHistory,
  onNewMessage,
}) {
  const [questionInput, setQuestionInput] = useState("");

  const [isThinking, setIsThinking] = useState(false);

  const [latestAssistantIndex, setLatestAssistantIndex] =
    useState(null);

  const chatEndRef = useRef(null);

  const textAreaRef = useRef(null);


  // ------------------------------------------------------------------
  // AUTO-SCROLL
  // ------------------------------------------------------------------
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [chatHistory, isThinking]);


  // ------------------------------------------------------------------
  // AUTO-RESIZE INPUT
  // ------------------------------------------------------------------
  useEffect(() => {
    const textArea = textAreaRef.current;

    if (!textArea) {
      return;
    }

    textArea.style.height = "auto";

    textArea.style.height = `${Math.min(
      textArea.scrollHeight,
      140
    )}px`;
  }, [questionInput]);


  // ------------------------------------------------------------------
  // SUBMIT QUESTION
  // ------------------------------------------------------------------
  const handleSubmit = async (event) => {
    event?.preventDefault();

    const question = questionInput.trim();

    if (
      !question ||
      isThinking ||
      !docsProcessed
    ) {
      return;
    }

    onNewMessage({
      role: "user",
      content: question,
    });

    setQuestionInput("");

    setIsThinking(true);

    setLatestAssistantIndex(null);

    try {
      const result = await askQuestion(question);

      const assistantMessage = {
        role: "assistant",
        content:
          result?.answer ||
          "I couldn't generate an answer.",
      };

      const nextAssistantIndex =
        chatHistory.length + 1;

      onNewMessage(assistantMessage);

      setLatestAssistantIndex(
        nextAssistantIndex
      );
    } catch (error) {
      const errorMessage = {
        role: "assistant",
        content:
          `❌ Sorry, I couldn't generate an answer: ${
            error?.message ||
            "Please try again."
          }`,
      };

      const nextAssistantIndex =
        chatHistory.length + 1;

      onNewMessage(errorMessage);

      setLatestAssistantIndex(
        nextAssistantIndex
      );
    } finally {
      setIsThinking(false);
    }
  };


  // ------------------------------------------------------------------
  // KEYBOARD HANDLING
  // ------------------------------------------------------------------
  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      handleSubmit(event);
    }
  };


  // ------------------------------------------------------------------
  // RENDER
  // ------------------------------------------------------------------
  return (
    <section className="chat-window">
      <div className="chat-messages">
        {chatHistory.length === 0 && (
          <div className="chat-empty-state">
            <div className="chat-empty-icon">
              {docsProcessed ? "💬" : "📤"}
            </div>

            <h2>
              {docsProcessed
                ? "Your documents are ready"
                : "Upload a PDF to begin"}
            </h2>

            <p>
              {docsProcessed
                ? "Ask a question about the uploaded document below."
                : "Upload and process one or more PDFs from the sidebar."}
            </p>

            {docsProcessed && (
              <div className="suggested-questions">
                <span>
                  Try asking:
                </span>

                <button
                  type="button"
                  onClick={() =>
                    setQuestionInput(
                      "What is this document about?"
                    )
                  }
                >
                  What is this document about?
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestionInput(
                      "Summarize the key points."
                    )
                  }
                >
                  Summarize the key points
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestionInput(
                      "What are the most important details?"
                    )
                  }
                >
                  Show important details
                </button>
              </div>
            )}
          </div>
        )}


        {chatHistory.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}`}
            message={message}
            shouldAnimate={
              message.role === "assistant" &&
              index === latestAssistantIndex
            }
          />
        ))}


        {isThinking && (
          <ThinkingMessage />
        )}


        <div ref={chatEndRef} />
      </div>


      <form
        className="chat-input-form"
        onSubmit={handleSubmit}
      >
        <div className="chat-input-wrapper">
          <textarea
            ref={textAreaRef}
            value={questionInput}
            onChange={(event) =>
              setQuestionInput(event.target.value)
            }
            onKeyDown={handleKeyDown}
            placeholder={
              docsProcessed
                ? "Ask a question about your documents..."
                : "Upload and process documents first..."
            }
            disabled={
              !docsProcessed ||
              isThinking
            }
            className="chat-input"
            rows={1}
          />

          <button
            type="submit"
            disabled={
              !docsProcessed ||
              isThinking ||
              !questionInput.trim()
            }
            className="chat-send-button"
            title="Send question"
            aria-label="Send question"
          >
            ➤
          </button>
        </div>

        <p className="chat-input-hint">
          Press Enter to send · Shift + Enter for a new line
        </p>
      </form>
    </section>
  );
}