export default function LoadingIndicator({
  message = "🤖 AI is reading your documents...",
}) {
  return (
    <div className="loading-indicator">
      <div className="loading-dots">
        <span />
        <span />
        <span />
      </div>

      <p>{message}</p>
    </div>
  );
}