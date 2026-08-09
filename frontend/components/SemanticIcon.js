const STROKE_PROPS = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  strokeWidth: 1.8,
};

export default function SemanticIcon({ className = "", kind }) {
  if (["opposition", "support", "mixed"].includes(kind)) {
    const symbols = { opposition: "−", support: "+", mixed: "±" };
    return (
      <span
        aria-hidden="true"
        className={`semantic-marker semantic-marker-${kind} ${className}`}
      >
        {symbols[kind]}
      </span>
    );
  }

  if (kind === "recorded") {
    return (
      <svg aria-hidden="true" className={className} viewBox="0 0 24 24">
        <path {...STROKE_PROPS} d="M9 6h11M9 12h11M9 18h11" />
        <circle cx="4" cy="6" fill="currentColor" r="1.35" />
        <circle cx="4" cy="12" fill="currentColor" r="1.35" />
        <circle cx="4" cy="18" fill="currentColor" r="1.35" />
      </svg>
    );
  }

  if (kind === "summary") {
    return (
      <svg aria-hidden="true" className={className} viewBox="0 0 24 24">
        <circle {...STROKE_PROPS} cx="12" cy="12" r="9" />
        <path {...STROKE_PROPS} d="m8 12 2.5 2.5L16.5 8" />
      </svg>
    );
  }

  if (kind === "vote-source") {
    return (
      <svg aria-hidden="true" className={className} viewBox="0 0 24 24">
        <path {...STROKE_PROPS} d="M5 10h14v10H5zM8 10V6h8v4M9 15h6" />
        <path {...STROKE_PROPS} d="m10 6 2-2 2 2" />
      </svg>
    );
  }

  if (kind === "document-source") {
    return (
      <svg aria-hidden="true" className={className} viewBox="0 0 24 24">
        <path {...STROKE_PROPS} d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6" />
      </svg>
    );
  }

  if (["procedural", "noncounting", "limited", "unresolved"].includes(kind)) {
    const symbols = {
      procedural: "↪",
      noncounting: "○",
      limited: "?",
      unresolved: "!",
    };
    return (
      <span aria-hidden="true" className={`semantic-state ${className}`}>
        {symbols[kind]}
      </span>
    );
  }

  return null;
}
