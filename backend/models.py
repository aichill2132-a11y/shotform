from pydantic import BaseModel
from typing import Any, Optional


class MetricResult(BaseModel):
    name: str
    value: float
    unit: str
    status: str
    score: float
    feedback: str


class PoseLandmark(BaseModel):
    x: float
    y: float
    z: float
    vis: float


class PoseFrame(BaseModel):
    frame_index: int
    phase: str
    landmarks: dict[str, PoseLandmark]


class AnalysisResponse(BaseModel):
    overall_score: int
    overall_feedback: str
    metrics: list[MetricResult]
    frames_analyzed: int
    confidence: dict[str, str]
    pose_frames: list[PoseFrame] = []
    corrected_pose_frames: list[PoseFrame] = []
    shooting_side: str = "unknown"
    debug: Optional[dict[str, Any]] = None
    error: Optional[str] = None