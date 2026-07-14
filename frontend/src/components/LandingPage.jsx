export default function LandingPage({ onGetStarted, isDarkMode }) {
  return (
    <main className={`landing-page ${isDarkMode ? "dark" : ""}`}>
      <section className="landing-hero">
        <div className="landing-badge">Powered by Groq + RAG</div>

        <div className="landing-icon">📄</div>

        <h1>AI Document Assistant</h1>

        <p className="landing-description">
          Upload PDF documents and ask questions using natural language.
          Get fast, accurate answers grounded in your documents.
        </p>

        <div className="landing-features">
          <div className="feature-card">
            <span>📄</span>
            <h3>Upload PDFs</h3>
            <p>Upload one or multiple PDF documents.</p>
          </div>

          <div className="feature-card">
            <span>🤖</span>
            <h3>Ask Questions</h3>
            <p>Ask natural-language questions about your documents.</p>
          </div>

          <div className="feature-card">
            <span>⚡</span>
            <h3>Instant Answers</h3>
            <p>Receive context-aware answers powered by Groq and RAG.</p>
          </div>
        </div>

        <button
          type="button"
          className="get-started-button"
          onClick={onGetStarted}
        >
          Upload Documents
        </button>
      </section>
    </main>
  );
}