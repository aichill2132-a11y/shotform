import { useEffect, useRef, useState } from "react";

const PHASE_COLOR = {
  setup:          "#6366f1",
  knee_bend:      "#f59e0b",
  release:        "#ef4444",
  follow_through: "#10b981",
};

const BONES = [
  ["left_shoulder",  "right_shoulder"],
  ["left_shoulder",  "left_elbow"],
  ["left_elbow",     "left_wrist"],
  ["right_shoulder", "right_elbow"],
  ["right_elbow",    "right_wrist"],
  ["left_shoulder",  "left_hip"],
  ["right_shoulder", "right_hip"],
  ["left_hip",       "right_hip"],
  ["left_hip",       "left_knee"],
  ["left_knee",      "left_ankle"],
  ["right_hip",      "right_knee"],
  ["right_knee",     "right_ankle"],
  ["left_ankle",     "left_heel"],
  ["right_ankle",    "right_heel"],
];

const VIS_THRESHOLD = 0.4;
// Intrinsic canvas resolution — drawing coords.
// CSS scales it to 100% of whatever column it sits in,
// so these numbers only affect internal drawing precision.
const CANVAS_W = 240;
const CANVAS_H = 360;
const BASE_FPS = 20;
const SPEEDS   = [0.5, 1, 1.5, 2];

function drawFrame(ctx, frame) {
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

  const lm        = frame.landmarks;
  const isRelease = frame.phase === "release";
  const color     = PHASE_COLOR[frame.phase] ?? "#888";

  const pt = (name) => {
    const j = lm[name];
    if (!j || j.vis < VIS_THRESHOLD) return null;
    return { x: j.x * CANVAS_W, y: j.y * CANVAS_H };
  };

  if (isRelease) {
    const glow = ctx.createRadialGradient(
      CANVAS_W / 2, CANVAS_H / 2, CANVAS_H * 0.1,
      CANVAS_W / 2, CANVAS_H / 2, CANVAS_H * 0.65,
    );
    glow.addColorStop(0, "rgba(239,68,68,0.13)");
    glow.addColorStop(1, "rgba(239,68,68,0)");
    ctx.fillStyle   = glow;
    ctx.globalAlpha = 1;
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
  }

  ctx.strokeStyle = color;
  ctx.lineWidth   = isRelease ? 3.5 : 2.5;
  ctx.lineCap     = "round";
  ctx.globalAlpha = isRelease ? 1.0 : 0.8;

  for (const [a, b] of BONES) {
    const pa = pt(a);
    const pb = pt(b);
    if (!pa || !pb) continue;
    ctx.beginPath();
    ctx.moveTo(pa.x, pa.y);
    ctx.lineTo(pb.x, pb.y);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;
  for (const name of Object.keys(lm)) {
    const p = pt(name);
    if (!p) continue;
    ctx.beginPath();
    ctx.arc(p.x, p.y, isRelease ? 5.5 : 4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }

  if (isRelease) {
    ctx.globalAlpha = 1;
    ctx.font        = "bold 13px sans-serif";
    ctx.fillStyle   = color;
    ctx.fillText("● RELEASE", 8, 18);
  } else {
    ctx.globalAlpha = 0.75;
    ctx.font        = "bold 11px sans-serif";
    ctx.fillStyle   = color;
    ctx.fillText(frame.phase.replace("_", " "), 8, 16);
  }
  ctx.globalAlpha = 1;
}

export default function PoseAnimation({ poseFrames, label }) {
  const canvasRef = useRef(null);
  const rafRef    = useRef(null);
  const idxRef    = useRef(0);
  const lastRef   = useRef(null);

  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [started, setStarted] = useState(false);
  const [speed,   setSpeed]   = useState(1);

  const frames     = poseFrames ?? [];
  const total      = frames.length;
  const frameMs    = 1000 / (BASE_FPS * speed);
  const releaseIdx = frames.findIndex((f) => f.phase === "release");

  const renderIdx = (i) => {
    const canvas = canvasRef.current;
    if (!canvas || !frames[i]) return;
    drawFrame(canvas.getContext("2d"), frames[i]);
    setCurrent(i);
  };

  useEffect(() => {
    if (!playing) return;
    const loop = (timestamp) => {
      if (!lastRef.current || timestamp - lastRef.current >= frameMs) {
        lastRef.current = timestamp;
        renderIdx(idxRef.current);
        idxRef.current += 1;
        if (idxRef.current >= total) {
          idxRef.current = 0;
          setPlaying(false);
          return;
        }
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing, frameMs, total]);

  useEffect(() => {
    if (total > 0) renderIdx(0);
  }, [total]);

  const handlePlay = () => {
    idxRef.current  = 0;
    lastRef.current = null;
    setStarted(true);
    setPlaying(true);
  };

  const handlePauseAtRelease = () => {
    if (releaseIdx === -1) return;
    cancelAnimationFrame(rafRef.current);
    idxRef.current = releaseIdx;
    setPlaying(false);
    setStarted(true);
    renderIdx(releaseIdx);
  };

  if (total === 0) return null;

  const currentPhase = frames[current]?.phase;
  const isRelease    = currentPhase === "release";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", minWidth: 0 }}>

      {label && (
        <p style={{
          fontFamily: "'Barlow Condensed', sans-serif",
          fontWeight: 700,
          fontSize: "0.72rem",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--muted)",
          margin: 0,
        }}>
          {label}
        </p>
      )}

      {/* Canvas — width:100% fills the column, height auto-scales via aspect-ratio */}
      <canvas
        ref={canvasRef}
        width={CANVAS_W}
        height={CANVAS_H}
        style={{
          width: "100%",
          height: "auto",
          aspectRatio: `${CANVAS_W} / ${CANVAS_H}`,
          background: "#0d0f14",
          borderRadius: "var(--radius)",
          display: "block",
          border: isRelease
            ? "1px solid rgba(239,68,68,0.5)"
            : "1px solid transparent",
          transition: "border-color 0.1s",
        }}
      />

      {/* Phase legend — wraps freely */}
      <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
        {Object.entries(PHASE_COLOR).map(([phase, color]) => {
          const active = currentPhase === phase;
          return (
            <span key={phase} style={{
              fontSize: "0.65rem",
              fontWeight: 600,
              padding: "2px 6px",
              borderRadius: 999,
              fontFamily: "'Barlow Condensed', sans-serif",
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              background: active ? color + "28" : "transparent",
              color:      active ? color        : "var(--muted)",
              border:     `1px solid ${active ? color : "var(--border)"}`,
              transition: "all 0.1s",
              whiteSpace: "nowrap",
            }}>
              {phase.replace("_", " ")}
            </span>
          );
        })}
      </div>

      {/* Scrubber */}
      <input
        type="range"
        min={0}
        max={total - 1}
        value={current}
        onChange={(e) => {
          const i = Number(e.target.value);
          idxRef.current = i;
          renderIdx(i);
          setPlaying(false);
        }}
        style={{ width: "100%", accentColor: PHASE_COLOR[currentPhase] ?? "#6366f1" }}
      />

      {/* Controls row */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
        <button
          onClick={handlePlay}
          disabled={playing}
          style={{
            padding: "0.35rem 0.8rem",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
            background: "transparent",
            color: playing ? "var(--muted)" : "var(--text)",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 700,
            fontSize: "0.82rem",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            cursor: playing ? "default" : "pointer",
            flexShrink: 0,
          }}
        >
          {!started ? "▶ Play" : playing ? "Playing…" : "↩ Replay"}
        </button>

        <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
          {SPEEDS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              style={{
                padding: "0.25rem 0.45rem",
                borderRadius: "var(--radius)",
                border: `1px solid ${speed === s ? "var(--text)" : "var(--border)"}`,
                background: speed === s ? "var(--text)" : "transparent",
                color: speed === s ? "var(--surface)" : "var(--muted)",
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 700,
                fontSize: "0.72rem",
                cursor: "pointer",
                transition: "all 0.12s",
              }}
            >
              {s}x
            </button>
          ))}
        </div>

        <span style={{ fontSize: "0.68rem", color: "var(--muted)", fontFamily: "monospace", marginLeft: "auto" }}>
          {current + 1}/{total}
        </span>
      </div>

      {/* Pause at Release */}
      {releaseIdx !== -1 && (
        <button
          onClick={handlePauseAtRelease}
          style={{
            padding: "0.35rem 0",
            width: "100%",
            borderRadius: "var(--radius)",
            border: "1px solid rgba(239,68,68,0.4)",
            background: isRelease ? "rgba(239,68,68,0.12)" : "transparent",
            color: "#ef4444",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 700,
            fontSize: "0.82rem",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            cursor: "pointer",
            transition: "background 0.1s",
          }}
        >
          ● Pause at Release
        </button>
      )}

    </div>
  );
}