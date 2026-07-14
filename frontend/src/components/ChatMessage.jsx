import { useEffect, useState } from "react";

export default function ChatMessage({
  role,
  content,
  enableTyping = false,
}) {
  const [displayedContent, setDisplayedContent] = useState(
    enableTyping && role === "assistant" ? "" : content
  );

  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!enableTyping || role !== "assistant") {
      setDisplayedContent(content);
      return;
    }

    let currentIndex = 0;

    const intervalId = window.setInterval(() => {
      currentIndex += 1;
      setDisplayedContent(content.slice(0, currentIndex));

      if (currentIndex >= content.length) {
        window.clearInterval(intervalId);
      }
    }, 10);

    return () => window.clearInterval(intervalId);
  }, [content, enableTyping, role]);

  const copyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch {
      setCopied(false);
    }
  };

  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      {!isUser && <div className="message-avatar">🤖</div>}

      <div className={`message-bubble ${isUser ? "user-bubble" : "ai-bubble"}`}>
        <div className="message-content">
          {displayedContent}
        </div>

        {!isUser && content && (
          <button
            type="button"
            className="copy-answer-button"
            onClick={copyAnswer}
          >
            {copied ? "✓ Copied" : "📋 Copy"}
          </button>
        )}
      </div>

      {isUser && <div className="message-avatar">🧑</div>}
    </div>
  );
}