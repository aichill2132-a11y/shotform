import { useState } from "react";
import UploadZone from "./components/UploadZone";
import ResultsCard from "./components/ResultsCard";

const styles = {
  wrap: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "3rem 1rem",
  },
  inner: {
    width: "100%",
    maxWidth: "520px",
  },
  header: {
    marginBottom: "2.5rem",
    textAlign: "center",
  },
  eyebrow: {
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 600,
    fontSize: "0.8rem",
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    color: "var(--accent)",
    marginBottom: "0.5rem",
  },
  title: {
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 800,
    fontSize: "clamp(2rem, 6vw, 2.8rem)",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    lineHeight: 1.05,
    marginBottom: "0.6rem",
  },
  sub: {
    color: "var(--muted)",
    fontSize: "0.9rem",
    lineHeight: 1.6,
  },
  errorBox: {
    marginTop: "1rem",
    padding: "0.75rem 1rem",
    background: "rgba(239,68,68,0.1)",
    border: "1px solid rgba(239,68,68,0.3)",
    borderRadius: "var(--radius)",
    color: "#fca5a5",
    fontSize: "0.875rem",
  },
};

export default function App() {
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);

  return (
    <div style={styles.wrap}>
      <div style={styles.inner}>

        <header style={styles.header}>
          <p style={styles.eyebrow}>AI-Powered</p>
          <h1 style={styles.title}>Jump Shot<br />Analyzer</h1>
          <p style={styles.sub}>
            Upload a short clip of your jump shot.<br />
            We'll check your knee bend, elbow angle, and body lean.
          </p>
        </header>

        {error && <div style={styles.errorBox}>⚠ {error}</div>}

        {result ? (
          <ResultsCard result={result} onReset={() => { setResult(null); setError(null); }} />
        ) : (
          <UploadZone onResult={setResult} onError={setError} />
        )}

      </div>
    </div>
  );
}
