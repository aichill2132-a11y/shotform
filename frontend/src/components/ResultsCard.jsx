import { useState } from "react";
import MetricRow from "./MetricRow";
import PoseAnimation from "./PoseAnimation";

const SCORE_COLOR = (s) =>
  s >= 85 ? "var(--good)" : s >= 60 ? "var(--warn)" : "var(--poor)";

const CONFIDENCE_KEY = {
  "Knee Bend":   "knee_bend",
  "Elbow Angle": "elbow_angle",
  "Body Lean":   "body_lean",
};

function overallConfidence(confidence) {
  if (!confidence || typeof confidence !== "object") return confidence ?? "low";
  const levels = Object.values(confidence);
  if (levels.includes("low"))    return "low";
  if (levels.includes("medium")) return "medium";
  return "high";
}

const styles = {
  card: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    overflow: "hidden",
  },
  header: () => ({
    padding: "1.5rem",
    borderBottom: "1px solid var(--border)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "1rem",
  }),
  titleGroup: { flex: 1 },
  title: {
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 800,
    fontSize: "1.35rem",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    marginBottom: "0.35rem",
  },
  summary: { color: "var(--muted)", fontSize: "0.9rem", lineHeight: 1.5 },
  score: (score) => ({
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 800,
    fontSize: "3rem",
    lineHeight: 1,
    color: SCORE_COLOR(score),
    flexShrink: 0,
  }),
  scoreLabel: {
    fontSize: "0.65rem",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    color: "var(--muted)",
    textAlign: "right",
    marginTop: "0.2rem",
    fontFamily: "'Barlow Condensed', sans-serif",
  },
  metrics: {
    padding: "1.25rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  poseSection: {
    padding: "1.25rem",
    borderTop: "1px solid var(--border)",
    // Prevent children from overflowing the card
    minWidth: 0,
    overflow: "hidden",
  },
  poseSectionLabel: {
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 700,
    fontSize: "0.75rem",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    color: "var(--muted)",
    marginBottom: "0.75rem",
  },
  footer: {
    padding: "0.75rem 1.25rem",
    borderTop: "1px solid var(--border)",
    fontSize: "0.75rem",
    color: "var(--muted)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "0.5rem",
  },
  confidenceBadge: (level) => ({
    padding: "0.15rem 0.55rem",
    borderRadius: "99px",
    fontSize: "0.7rem",
    fontWeight: 700,
    letterSpacing: "0.06em",
    fontFamily: "'Barlow Condensed', sans-serif",
    flexShrink: 0,
    color:      level === "high" ? "var(--good)" : level === "medium" ? "var(--warn)" : "var(--poor)",
    background: level === "high" ? "var(--good-lo)" : level === "medium" ? "var(--warn-lo)" : "var(--poor-lo)",
  }),
  lowConfidenceWarning: {
    margin: "0.75rem 1.25rem",
    padding: "0.6rem 0.85rem",
    background: "rgba(239,68,68,0.08)",
    border: "1px solid rgba(239,68,68,0.25)",
    borderRadius: "var(--radius)",
    fontSize: "0.8rem",
    color: "#fca5a5",
    lineHeight: 1.5,
  },
  resetBtn: {
    marginTop: "1.25rem",
    padding: "0.65rem 0",
    width: "100%",
    background: "transparent",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    color: "var(--muted)",
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 600,
    fontSize: "0.95rem",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    cursor: "pointer",
    transition: "border-color 0.15s, color 0.15s",
  },
  debugWrap: {
    marginTop: "1rem",
    border: "1px solid #2a2f3d",
    borderRadius: "var(--radius)",
    overflow: "hidden",
    fontFamily: "monospace",
    fontSize: "0.78rem",
  },
  debugToggle: {
    width: "100%",
    background: "#161922",
    border: "none",
    color: "#4b5563",
    padding: "0.5rem 0.85rem",
    textAlign: "left",
    cursor: "pointer",
    fontSize: "0.75rem",
    letterSpacing: "0.08em",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  debugBody: {
    background: "#0d0f14",
    padding: "0.75rem 0.85rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.3rem",
  },
  debugRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: "1rem",
    borderBottom: "1px solid #1e2330",
    paddingBottom: "0.25rem",
  },
  debugKey:   { color: "#6b7280" },
  debugValue: { color: "#e2e8f0", fontWeight: 600 },
};

function DebugPanel({ debug }) {
  const [open, setOpen] = useState(false);
  if (!debug) return null;

  const rows = [
    ["shooting_side_chosen",        debug.shooting_side_chosen],
    ["left_elbow_at_release",       `${debug.left_elbow_at_release}°`],
    ["right_elbow_at_release",      `${debug.right_elbow_at_release}°`],
    ["final_displayed_elbow_angle", `${debug.final_displayed_elbow_angle}°`],
    ["left_visibility_score",       debug.left_visibility_score],
    ["right_visibility_score",      debug.right_visibility_score],
    ["release_frame_index",         debug.release_frame_index],
    ["knee_bend_frame_index",       debug.knee_bend_frame_index],
  ];

  return (
    <div style={styles.debugWrap}>
      <button style={styles.debugToggle} onClick={() => setOpen(o => !o)}>
        <span>🔬 DEBUG</span>
        <span>{open ? "▲ hide" : "▼ show"}</span>
      </button>
      {open && (
        <div style={styles.debugBody}>
          {rows.map(([k, v]) => (
            <div key={k} style={styles.debugRow}>
              <span style={styles.debugKey}>{k}</span>
              <span style={styles.debugValue}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ResultsCard({ result, onReset }) {
  const {
    overall_score, overall_feedback, metrics, frames_analyzed,
    confidence, shooting_side, debug, pose_frames, corrected_pose_frames,
  } = result;

  const overallLevel = overallConfidence(confidence);

  const sideLabel = shooting_side && shooting_side !== "unknown"
    ? ` · ${shooting_side}-side view`
    : "";

  const confidenceLabel = {
    high:   "HIGH CONFIDENCE",
    medium: "MEDIUM CONFIDENCE",
    low:    "LOW CONFIDENCE",
  };

  return (
    <div>
      {/*
        Responsive grid CSS injected inline so we don't need an external
        stylesheet. Switches from 2-col to 1-col at 480px container width.
      */}
      <style>{`
        .pose-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          min-width: 0;
        }
        @media (max-width: 480px) {
          .pose-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div style={styles.card}>
        <div style={styles.header(overall_score)}>
          <div style={styles.titleGroup}>
            <p style={styles.title}>Shot Analysis</p>
            <p style={styles.summary}>{overall_feedback}</p>
          </div>
          <div>
            <p style={styles.score(overall_score)}>{overall_score}</p>
            <p style={styles.scoreLabel}>/ 100</p>
          </div>
        </div>

        <div style={styles.metrics}>
          {metrics.map((m) => (
            <MetricRow
              key={m.name}
              metric={m}
              confidence={confidence?.[CONFIDENCE_KEY[m.name]]}
            />
          ))}
        </div>

        {pose_frames?.length > 0 && (
          <div style={styles.poseSection}>
            <p style={styles.poseSectionLabel}>Shot Playback</p>
            <div className="pose-grid">
              <PoseAnimation
                poseFrames={pose_frames}
                label="Original"
              />
              <PoseAnimation
                poseFrames={corrected_pose_frames ?? []}
                label="Corrected"
              />
            </div>
          </div>
        )}

        {overallLevel === "low" && (
          <p style={styles.lowConfidenceWarning}>
            ⚠ Analysis may be less accurate. Try filming 5–7 seconds from the side with your full body visible.
          </p>
        )}

        <div style={styles.footer}>
          <span>
            Analyzed {frames_analyzed} frame{frames_analyzed !== 1 ? "s" : ""}{sideLabel}
          </span>
          <span style={styles.confidenceBadge(overallLevel)}>
            {confidenceLabel[overallLevel] ?? overallLevel.toUpperCase()}
          </span>
        </div>
      </div>

      <button style={styles.resetBtn} onClick={onReset}>
        ↩ Analyze Another Clip
      </button>

      <DebugPanel debug={debug} />
    </div>
  );
}