import os
import tempfile
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from analyzer import analyze_video
from feedback import (
    compute_overall,
    evaluate_body_lean,
    evaluate_elbow_angle,
    evaluate_knee_bend,
)
from models import AnalysisResponse

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(title="ShotForm API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo"}
MAX_SIZE_MB   = 50


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Upload an MP4 or MOV.",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum is {MAX_SIZE_MB} MB.",
        )

    suffix   = ".mp4" if "mp4" in file.content_type else ".mov"
    tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{suffix}")

    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)

        raw = analyze_video(tmp_path)

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    metrics = [
        evaluate_knee_bend(raw["knee_bend"]),
        evaluate_elbow_angle(raw["elbow_angle"]),
        evaluate_body_lean(raw["body_lean"]),
    ]
    score, summary = compute_overall(metrics, frames_analyzed=raw["frames_analyzed"])

    frames     = raw["frames_analyzed"]
    confidence = raw["confidence"]

    return AnalysisResponse(
        overall_score=score,
        overall_feedback=summary,
        metrics=metrics,
        frames_analyzed=frames,
        confidence=confidence,
        pose_frames=raw.get("pose_frames", []),
        corrected_pose_frames=raw.get("corrected_pose_frames", []),
        shooting_side=raw["shooting_side"],
        debug=raw.get("debug"),
    )