import { useRef, useState } from "react";

const styles = {
  zone: {
    border: "2px dashed var(--border)",
    borderRadius: "var(--radius)",
    padding: "3rem 2rem",
    textAlign: "center",
    cursor: "pointer",
    transition: "border-color 0.2s, background 0.2s",
    background: "transparent",
  },
  zoneHover: {
    borderColor: "var(--accent)",
    background: "var(--accent-lo)",
  },
  icon: {
    fontSize: "2.5rem",
    marginBottom: "0.75rem",
    display: "block",
  },
  label: {
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 700,
    fontSize: "1.2rem",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    marginBottom: "0.4rem",
  },
  sub: { color: "var(--muted)", fontSize: "0.875rem" },
  fileName: {
    marginTop: "1rem",
    fontSize: "0.875rem",
    color: "var(--accent)",
    fontWeight: 600,
  },
  btn: {
    marginTop: "1.5rem",
    padding: "0.75rem 2.5rem",
    background: "var(--accent)",
    color: "#fff",
    border: "none",
    borderRadius: "var(--radius)",
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 700,
    fontSize: "1.1rem",
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    cursor: "pointer",
    transition: "opacity 0.15s",
    display: "block",
    width: "100%",
  },
};

export default function UploadZone({ onResult, onError }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [hover, setHover] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleFile = (f) => {
    if (!f) return;
    if (!["video/mp4", "video/quicktime", "video/x-msvideo"].includes(f.type)) {
      onError("Please upload an MP4 or MOV file.");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      onError("File is too large. Max 50 MB.");
      return;
    }
    setFile(f);
    onError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setHover(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    onError(null);

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch("/analyze", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed.");
      onResult(data);
    } catch (err) {
      onError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div
        style={{ ...styles.zone, ...(hover ? styles.zoneHover : {}) }}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setHover(true); }}
        onDragLeave={() => setHover(false)}
        onDrop={handleDrop}
      >
        <span style={styles.icon}>🏀</span>
        <p style={styles.label}>Drop your jump shot clip here</p>
        <p style={styles.sub}>MP4 or MOV · max 30 s · max 50 MB</p>
        {file && <p style={styles.fileName}>✓ {file.name}</p>}
        <input
          ref={inputRef}
          type="file"
          accept="video/mp4,video/quicktime"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {file && (
        <button
          style={{ ...styles.btn, opacity: loading ? 0.6 : 1 }}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "Analyzing…" : "Analyze My Shot"}
        </button>
      )}
    </div>
  );
}
