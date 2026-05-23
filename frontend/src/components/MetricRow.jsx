const CONFIDENCE_CONFIG = {
  high:   { label: "High confidence",   color: "#16a34a", bg: "#dcfce7" },
  medium: { label: "Medium confidence", color: "#b45309", bg: "#fef3c7" },
  low:    { label: "Low confidence",    color: "#b91c1c", bg: "#fee2e2" },
};

function ConfidenceBadge({ level }) {
  const c = CONFIDENCE_CONFIG[level];
  if (!c) return null;
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: "2px 8px",
      borderRadius: 999,
      fontSize: "0.7rem",
      fontWeight: 600,
      background: c.bg,
      color: c.color,
    }}>
      <span style={{
        width: 5, height: 5, borderRadius: "50%",
        background: c.color, flexShrink: 0,
      }} />
      {c.label}
    </span>
  );
}

const STATUS_COLOR = {
  good:    "var(--good)",
  warning: "var(--warn)",
  poor:    "var(--poor)",
};

const STATUS_BG = {
  good:    "var(--good-lo)",
  warning: "var(--warn-lo)",
  poor:    "var(--poor-lo)",
};

const STATUS_LABEL = {
  good:    "✓ Good",
  warning: "⚠ Fair",
  poor:    "✗ Fix This",
};

const styles = {
  row: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    padding: "1rem 1.25rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.4rem",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  name: {
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 700,
    fontSize: "1rem",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: "var(--text)",
  },
  badge: (status) => ({
    padding: "0.2rem 0.65rem",
    borderRadius: "99px",
    fontSize: "0.75rem",
    fontWeight: 700,
    letterSpacing: "0.05em",
    color: STATUS_COLOR[status],
    background: STATUS_BG[status],
    fontFamily: "'Barlow Condensed', sans-serif",
  }),
  value: {
    fontSize: "1.5rem",
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 800,
    color: "var(--text)",
    lineHeight: 1,
  },
  feedback: {
    fontSize: "0.875rem",
    color: "var(--muted)",
    lineHeight: 1.5,
  },
};

export default function MetricRow({ metric, confidence }) {
  const { name, value, unit, status, feedback } = metric;
  return (
    <div style={styles.row}>
      <div style={styles.header}>
        <span style={styles.name}>{name}</span>
        <span style={styles.badge(status)}>{STATUS_LABEL[status]}</span>
      </div>
      <span style={styles.value}>{value}{unit}</span>
      <p style={styles.feedback}>{feedback}</p>
    </div>
  );
}
