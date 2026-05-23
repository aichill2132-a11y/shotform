"""
analyzer.py — pose extraction + metric computation

Workflow:
  1. Sample frames from the uploaded video at ~6 fps (was 1 fps)
  2. Run MediaPipe Pose on each accepted frame
  3. Detect four shot phases from the landmark sequence:
       setup          → first good frame
       knee_bend      → frame with smallest knee angle (deepest squat)
       release        → wrist highest AND elbow most extended after knee_bend
       follow_through → last good frame after release
  4. Smooth angle readings by averaging a ±1-frame window around each phase frame
  5. Return raw metric values (per-phase) to main.py
"""

import copy
import math
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
PL = mp_pose.PoseLandmark


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _angle(a, b, c) -> float:
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.hypot(*ba)
    mag_bc = math.hypot(*bc)
    if mag_ba == 0 or mag_bc == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def _lm(landmarks, idx):
    lm = landmarks[idx]
    return (lm.x, lm.y)


# ── Frame sampling ────────────────────────────────────────────────────────────

def sample_frames(video_path: str, target_fps: float = 6.0) -> list[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(native_fps / target_fps))
    frames = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            frames.append(frame)
        idx += 1

    cap.release()
    return frames


# ── Pose extraction ───────────────────────────────────────────────────────────

_KEY_LANDMARK_INDICES = [
    PL.LEFT_SHOULDER,  PL.RIGHT_SHOULDER,
    PL.LEFT_ELBOW,     PL.RIGHT_ELBOW,
    PL.LEFT_WRIST,     PL.RIGHT_WRIST,
    PL.LEFT_HIP,       PL.RIGHT_HIP,
    PL.LEFT_KNEE,      PL.RIGHT_KNEE,
    PL.LEFT_ANKLE,     PL.RIGHT_ANKLE,
]
_VISIBILITY_THRESHOLD = 0.6
_MIN_KEY_LANDMARKS    = 8

# ── Confidence + pose frame export ───────────────────────────────────────────

_CONFIDENCE_JOINT_GROUPS = {
    "knee_bend":   [PL.LEFT_KNEE,     PL.RIGHT_KNEE,
                    PL.LEFT_HIP,      PL.RIGHT_HIP,
                    PL.LEFT_ANKLE,    PL.RIGHT_ANKLE],
    "elbow_angle": [PL.LEFT_ELBOW,    PL.RIGHT_ELBOW,
                    PL.LEFT_SHOULDER, PL.RIGHT_SHOULDER,
                    PL.LEFT_WRIST,    PL.RIGHT_WRIST],
    "body_lean":   [PL.LEFT_SHOULDER, PL.RIGHT_SHOULDER,
                    PL.LEFT_HIP,      PL.RIGHT_HIP],
}

_POSE_EXPORT_JOINTS = {
    "nose":             PL.NOSE,
    "left_shoulder":    PL.LEFT_SHOULDER,  "right_shoulder":   PL.RIGHT_SHOULDER,
    "left_elbow":       PL.LEFT_ELBOW,     "right_elbow":      PL.RIGHT_ELBOW,
    "left_wrist":       PL.LEFT_WRIST,     "right_wrist":      PL.RIGHT_WRIST,
    "left_hip":         PL.LEFT_HIP,       "right_hip":        PL.RIGHT_HIP,
    "left_knee":        PL.LEFT_KNEE,      "right_knee":       PL.RIGHT_KNEE,
    "left_ankle":       PL.LEFT_ANKLE,     "right_ankle":      PL.RIGHT_ANKLE,
    "left_heel":        PL.LEFT_HEEL,      "right_heel":       PL.RIGHT_HEEL,
    "left_foot_index":  PL.LEFT_FOOT_INDEX,"right_foot_index": PL.RIGHT_FOOT_INDEX,
}


def _count_visible(landmarks) -> int:
    return sum(
        1 for idx in _KEY_LANDMARK_INDICES
        if landmarks[idx].visibility >= _VISIBILITY_THRESHOLD
    )


def extract_landmarks(frames: list[np.ndarray]):
    results = []
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.5,
    ) as pose:
        for i, frame in enumerate(frames):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            if not res.pose_landmarks:
                continue

            lms = res.pose_landmarks.landmark
            visible_count = _count_visible(lms)

            if visible_count < _MIN_KEY_LANDMARKS:
                continue

            results.append((i, lms))

    return results


def pick_shooting_side(landmark_sets: list) -> str:
    _SIDE_JOINTS = {
        "RIGHT": [PL.RIGHT_SHOULDER, PL.RIGHT_ELBOW, PL.RIGHT_WRIST,
                  PL.RIGHT_KNEE,     PL.RIGHT_ANKLE],
        "LEFT":  [PL.LEFT_SHOULDER,  PL.LEFT_ELBOW,  PL.LEFT_WRIST,
                  PL.LEFT_KNEE,      PL.LEFT_ANKLE],
    }

    vis_scores = {}
    for side, joints in _SIDE_JOINTS.items():
        total = sum(
            lms[j].visibility
            for _, lms in landmark_sets
            for j in joints
        )
        vis_scores[side] = total / (len(landmark_sets) * len(joints))

    _PLAUSIBLE_LO, _PLAUSIBLE_HI = 60.0, 150.0

    def _plausibility(side: str) -> float:
        wrist_lm = getattr(PL, f"{side}_WRIST")
        best_lms = min(landmark_sets, key=lambda item: item[1][wrist_lm].y)[1]
        angle = compute_elbow_angle(best_lms, side)
        if _PLAUSIBLE_LO <= angle <= _PLAUSIBLE_HI:
            mid  = (_PLAUSIBLE_LO + _PLAUSIBLE_HI) / 2
            half = (_PLAUSIBLE_HI - _PLAUSIBLE_LO) / 2
            return 1.0 - abs(angle - mid) / half * 0.3
        if angle < _PLAUSIBLE_LO:
            return max(0.0, angle / _PLAUSIBLE_LO)
        return max(0.0, (180.0 - angle) / (180.0 - _PLAUSIBLE_HI))

    plaus_scores = {side: _plausibility(side) for side in ("RIGHT", "LEFT")}

    combined = {
        side: 0.6 * vis_scores[side] + 0.4 * plaus_scores[side]
        for side in ("RIGHT", "LEFT")
    }

    return "RIGHT" if combined["RIGHT"] >= combined["LEFT"] else "LEFT"


def assert_pose_quality(landmark_sets: list, shooting_side: str) -> None:
    if not landmark_sets:
        raise ValueError(
            "No person detected in the video. "
            "Please upload a clear clip of a basketball shot with your full "
            "body visible and decent lighting."
        )

    S = shooting_side

    wrist_lm = getattr(PL, f"{S}_WRIST")
    best_landmarks = min(
        landmark_sets,
        key=lambda item: item[1][wrist_lm].y,
    )[1]

    critical = [
        getattr(PL, f"{S}_SHOULDER"),
        getattr(PL, f"{S}_ELBOW"),
        getattr(PL, f"{S}_WRIST"),
        getattr(PL, f"{S}_HIP"),
        getattr(PL, f"{S}_KNEE"),
        getattr(PL, f"{S}_ANKLE"),
    ]
    low_confidence = [
        PL(idx).name
        for idx in critical
        if best_landmarks[idx].visibility < _VISIBILITY_THRESHOLD
    ]

    if len(low_confidence) >= 3:
        joints = ", ".join(low_confidence)
        raise ValueError(
            f"Pose detected but key joints on the {S.lower()} side are not "
            f"clearly visible ({joints}). Film from the side with your full "
            f"body in frame and the camera perpendicular to your shot direction."
        )


def smooth_angle(
    landmark_sets: list,
    center_idx: int,
    compute_fn,
    window: int = 1,
) -> float:
    lo = max(0, center_idx - window)
    hi = min(len(landmark_sets) - 1, center_idx + window)
    values = [compute_fn(landmark_sets[i][1]) for i in range(lo, hi + 1)]
    return sum(values) / len(values)


def _compute_confidence(landmark_sets: list, phase_idx: int) -> dict[str, str]:
    result = {}
    for metric, joints in _CONFIDENCE_JOINT_GROUPS.items():
        vis = [
            lms[j].visibility
            for _, lms in landmark_sets
            for j in joints
        ]
        avg = sum(vis) / len(vis) if vis else 0.0
        if avg >= 0.85:
            result[metric] = "high"
        elif avg >= 0.60:
            result[metric] = "medium"
        else:
            result[metric] = "low"
    return result


def _extract_pose_frames(
    landmark_sets: list,
    phases: dict[str, int],
    max_frames: int = 60,
) -> list[dict]:
    phase_for_idx = {}
    boundaries = [
        (phases["setup"],          phases["knee_bend"],      "setup"),
        (phases["knee_bend"],      phases["release"],        "knee_bend"),
        (phases["release"],        phases["follow_through"], "release"),
        (phases["follow_through"], len(landmark_sets),       "follow_through"),
    ]
    for start, end, label in boundaries:
        for i in range(start, max(start + 1, end + 1)):
            if i < len(landmark_sets):
                phase_for_idx[i] = label

    total = len(landmark_sets)
    step = max(1, total // max_frames)
    sampled = list(range(0, total, step))[:max_frames]

    pose_frames = []
    for idx in sampled:
        frame_no, lms = landmark_sets[idx]
        joints = {}
        for name, pl_idx in _POSE_EXPORT_JOINTS.items():
            j = lms[pl_idx]
            joints[name] = {
                "x":   round(j.x,          4),
                "y":   round(j.y,          4),
                "z":   round(j.z,          4),
                "vis": round(j.visibility, 3),
            }
        pose_frames.append({
            "frame_index": frame_no,
            "phase":       phase_for_idx.get(idx, "setup"),
            "landmarks":   joints,
        })

    return pose_frames


def _build_corrected_pose_frames(
    pose_frames: list[dict],
    elbow_angle: float,
    knee_angle: float,
    shooting_side: str,
) -> list[dict]:
    """
    Produce a corrected copy of pose_frames with subtle visual adjustments.

    Rules (deltas are in normalised 0-1 canvas coords):
      Elbow too tucked  (< 80°)  → nudge shooting wrist/elbow outward during release frames
      Elbow too flared  (> 140°) → nudge shooting wrist/elbow inward  during release frames
      Knee too straight (> 150°) → lower hip/knee slightly during knee_bend frames
    """
    IDEAL_ELBOW_LO = 80.0
    IDEAL_ELBOW_HI = 140.0
    IDEAL_KNEE_HI  = 150.0

    side_sign = 1.0 if shooting_side.upper() == "RIGHT" else -1.0

    elbow_delta = 0.0
    if elbow_angle < IDEAL_ELBOW_LO:
        deficit     = IDEAL_ELBOW_LO - elbow_angle
        elbow_delta = side_sign * min(deficit / 400.0, 0.04)
    elif elbow_angle > IDEAL_ELBOW_HI:
        excess      = elbow_angle - IDEAL_ELBOW_HI
        elbow_delta = -side_sign * min(excess / 400.0, 0.04)

    knee_delta = 0.0
    if knee_angle > IDEAL_KNEE_HI:
        excess     = knee_angle - IDEAL_KNEE_HI
        knee_delta = min(excess / 1000.0, 0.03)

    s = shooting_side.lower()
    corrected = []

    for frame in pose_frames:
        f  = copy.deepcopy(frame)
        lm = f["landmarks"]

        if f["phase"] == "release" and elbow_delta != 0.0:
            for joint in (f"{s}_wrist", f"{s}_elbow"):
                if joint in lm:
                    lm[joint]["x"] = round(lm[joint]["x"] + elbow_delta, 4)

        if f["phase"] == "knee_bend" and knee_delta != 0.0:
            for joint in ("left_hip", "right_hip", "left_knee", "right_knee"):
                if joint in lm:
                    lm[joint]["y"] = round(lm[joint]["y"] + knee_delta, 4)

        corrected.append(f)

    return corrected


def detect_shot_phases(landmark_sets: list, shooting_side: str) -> dict[str, int]:
    n = len(landmark_sets)

    setup_idx = 0

    knee_angles   = [compute_knee_bend(lms) for _, lms in landmark_sets]
    knee_bend_idx = int(np.argmin(knee_angles))

    candidates = list(range(knee_bend_idx, n))
    wrist_lm   = getattr(PL, f"{shooting_side}_WRIST")
    wrist_y    = [landmark_sets[i][1][wrist_lm].y for i in candidates]
    min_y      = min(wrist_y)
    near_peak  = [candidates[j] for j, y in enumerate(wrist_y) if y <= min_y + 0.02]

    release_idx = max(
        near_peak,
        key=lambda i: compute_elbow_angle(landmark_sets[i][1], shooting_side),
    )

    follow_through_idx = n - 1 if release_idx < n - 1 else release_idx

    return {
        "setup":          setup_idx,
        "knee_bend":      knee_bend_idx,
        "release":        release_idx,
        "follow_through": follow_through_idx,
    }


# ── Metric computation ────────────────────────────────────────────────────────

def compute_knee_bend(landmarks) -> float:
    r_vis = landmarks[PL.RIGHT_KNEE].visibility
    l_vis = landmarks[PL.LEFT_KNEE].visibility
    side  = "RIGHT" if r_vis >= l_vis else "LEFT"

    hip   = _lm(landmarks, getattr(PL, f"{side}_HIP"))
    knee  = _lm(landmarks, getattr(PL, f"{side}_KNEE"))
    ankle = _lm(landmarks, getattr(PL, f"{side}_ANKLE"))
    return _angle(hip, knee, ankle)


def compute_elbow_angle(landmarks, side: str = "RIGHT") -> float:
    shoulder = _lm(landmarks, getattr(PL, f"{side}_SHOULDER"))
    elbow    = _lm(landmarks, getattr(PL, f"{side}_ELBOW"))
    wrist    = _lm(landmarks, getattr(PL, f"{side}_WRIST"))
    return _angle(shoulder, elbow, wrist)


def compute_body_lean(landmarks) -> float:
    lsh = _lm(landmarks, PL.LEFT_SHOULDER)
    rsh = _lm(landmarks, PL.RIGHT_SHOULDER)
    lhp = _lm(landmarks, PL.LEFT_HIP)
    rhp = _lm(landmarks, PL.RIGHT_HIP)

    shoulder_mid = ((lsh[0] + rsh[0]) / 2, (lsh[1] + rsh[1]) / 2)
    hip_mid      = ((lhp[0] + rhp[0]) / 2, (lhp[1] + rhp[1]) / 2)

    dx = shoulder_mid[0] - hip_mid[0]
    dy = hip_mid[1] - shoulder_mid[1]

    if dy == 0:
        return 0.0
    return math.degrees(math.atan(abs(dx) / dy))


# ── Public entry point ────────────────────────────────────────────────────────

def analyze_video(video_path: str) -> dict:
    frames = sample_frames(video_path, target_fps=6.0)
    if not frames:
        raise ValueError("Could not read any frames from the video.")

    landmark_sets = extract_landmarks(frames)

    shooting_side = pick_shooting_side(landmark_sets) if landmark_sets else "RIGHT"

    assert_pose_quality(landmark_sets, shooting_side)

    phases = detect_shot_phases(landmark_sets, shooting_side)

    confidence  = _compute_confidence(landmark_sets, phases["release"])
    pose_frames = _extract_pose_frames(landmark_sets, phases)

    # ── debug: both-side elbow angles and visibility at release ──────────────
    release_lms            = landmark_sets[phases["release"]][1]
    left_elbow_at_release  = round(compute_elbow_angle(release_lms, "LEFT"),  1)
    right_elbow_at_release = round(compute_elbow_angle(release_lms, "RIGHT"), 1)

    _SIDE_JOINTS_DBG = {
        "RIGHT": [PL.RIGHT_SHOULDER, PL.RIGHT_ELBOW, PL.RIGHT_WRIST,
                  PL.RIGHT_KNEE,     PL.RIGHT_ANKLE],
        "LEFT":  [PL.LEFT_SHOULDER,  PL.LEFT_ELBOW,  PL.LEFT_WRIST,
                  PL.LEFT_KNEE,      PL.LEFT_ANKLE],
    }
    vis_debug = {}
    for side, joints in _SIDE_JOINTS_DBG.items():
        total = sum(lms[j].visibility for _, lms in landmark_sets for j in joints)
        vis_debug[side] = round(total / (len(landmark_sets) * len(joints)), 3)

    debug = {
        "shooting_side_chosen":   shooting_side.lower(),
        "left_elbow_at_release":  left_elbow_at_release,
        "right_elbow_at_release": right_elbow_at_release,
        "left_visibility_score":  vis_debug["LEFT"],
        "right_visibility_score": vis_debug["RIGHT"],
        "release_frame_index":    phases["release"],
        "knee_bend_frame_index":  phases["knee_bend"],
    }

    # ── metric computation ────────────────────────────────────────────────────
    knee_angle  = smooth_angle(landmark_sets, phases["knee_bend"], compute_knee_bend, window=1)
    elbow_angle = compute_elbow_angle(release_lms, shooting_side)
    body_lean   = smooth_angle(landmark_sets, phases["release"], compute_body_lean, window=1)

    debug["final_displayed_elbow_angle"] = round(elbow_angle, 1)

    corrected_pose_frames = _build_corrected_pose_frames(
        pose_frames,
        elbow_angle=elbow_angle,
        knee_angle=knee_angle,
        shooting_side=shooting_side,
    )

    return {
        "knee_bend":             knee_angle,
        "elbow_angle":           elbow_angle,
        "body_lean":             body_lean,
        "shooting_side":         shooting_side.lower(),
        "frames_analyzed":       len(landmark_sets),
        "phases": {
            name: landmark_sets[idx][0]
            for name, idx in phases.items()
        },
        "confidence":            confidence,
        "pose_frames":           pose_frames,
        "corrected_pose_frames": corrected_pose_frames,
        "debug":                 debug,
    }


# ── Quick local test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test.mp4"
    result = analyze_video(path)
    print(result)