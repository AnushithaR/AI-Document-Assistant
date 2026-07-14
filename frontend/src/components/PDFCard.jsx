export default function PDFCard({
  filename,
  pages,
  chunks,
  status = "ready",
}) {
  return (
    <article className="pdf-card">
      <div className="pdf-card-icon">📄</div>

      <div className="pdf-card-content">
        <h3 title={filename}>{filename}</h3>

        <div className="pdf-card-details">
          {pages !== undefined && (
            <span>✔ {pages} {pages === 1 ? "page" : "pages"}</span>
          )}

          {chunks !== undefined && (
            <span>✔ {chunks} chunks</span>
          )}

          <span className={`pdf-status ${status}`}>
            ✔ {status === "ready" ? "Ready for questions" : status}
          </span>
        </div>
      </div>
    </article>
  );
}