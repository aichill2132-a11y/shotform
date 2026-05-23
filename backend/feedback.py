"""
Pure logic: takes computed metric values, returns coaching feedback.
No external dependencies — easy to unit test in isolation.

Scoring model
─────────────
Each metric produces a continuous 0–100 sub-score that reflects how close
the measured angle is to the centre of its ideal range, not just which bucket
it fell into.  The three sub-scores are combined with weights, a confidence
factor (frames_analyzed) is applied, and the result is capped so that 100 is
only reachable by a near-perfect shot with high-confidence data.

  all-good metrics, many frames  →  ~88–95
  all-good metrics, few frames   →  ~80–88  (confidence cap)
  one warning metric             →  ~65–78
  one poor metric                →  ~45–60
  multiple poor metrics          →  <45
"""

from models import MetricResult


# ── Thresholds ──────────────────────────────────────────────────────────────

KNEE_BEND = {
    # Knee angle at deepest bend (hip→knee→ankle).
    # Smaller angle = more bend. 180° = fully straight leg.
    "too_straight": (150, 180),   # barely dipping — needs more bend
    "slightly_low":  (135, 149),  # workable but could go deeper
    "good":          (90,  134),  # strong athletic load, ideal range
    "too_deep":      (0,    89),  # excessive — may affect balance/timing
}

ELBOW_ANGLE = {
    "good":    (80, 105),    # degrees at release
    "warning": (106, 120),
}

BODY_LEAN = {
    "good":    (0, 12),      # degrees forward tilt
    "warning": (13, 22),
}


# ── Continuous sub-score helpers ─────────────────────────────────────────────

def _score_in_range(value: float, lo: float, hi: float, peak_score: float = 95) -> float:
    """
    Score a value that sits inside [lo, hi].
    The centre of the range earns peak_score; edges earn peak_score * 0.85.
    This means even a "textbook" reading isn't automatically a 95 — only
    values right in the sweet spot earn near-peak.
    """
    mid = (lo + hi) / 2
    half = (hi - lo) / 2
    if half == 0:
        return peak_score
    dist = abs(value - mid) / half          # 0 at centre, 1 at edge
    return peak_score * (1 - 0.15 * dist)   # drops to 85 % of peak at edge


def _score_outside_range(
    value: float,
    good_lo: float,
    good_hi: float,
    warn_lo: float,
    warn_hi: float,
    warn_base: float = 62,
    poor_base: float = 28,
) -> float:
    """
    Score a value that lies in the warning or poor zone.
    Within the warning band: interpolates from warn_base down to poor_base.
    Outside the warning band: poor_base minus a distance penalty.
    """
    # Determine which side of the good range we're on
    if value < good_lo:
        warn_edge = warn_lo      # lower warning boundary
        dist_into_warn = (good_lo - value) / max(good_lo - warn_lo, 1)
    else:
        warn_edge = warn_hi      # upper warning boundary
        dist_into_warn = (value - good_hi) / max(warn_hi - good_hi, 1)

    dist_into_warn = max(0.0, min(1.0, dist_into_warn))  # clamp 0–1

    in_warning = (warn_lo <= value <= warn_hi) if value < good_lo else (value <= warn_hi)

    if in_warning:
        return warn_base - (warn_base - poor_base) * dist_into_warn
    else:
        overshoot = abs(value - (warn_lo if value < good_lo else warn_hi))
        return max(5.0, poor_base - overshoot * 0.4)


def _classify(value: float, thresholds: dict) -> str:
    lo_g, hi_g = thresholds["good"]
    lo_w, hi_w = thresholds["warning"]
    if lo_g <= value <= hi_g:
        return "good"
    if lo_w <= value <= hi_w:
        return "warning"
    return "poor"


# ── Per-metric scoring ────────────────────────────────────────────────────────

def _score_knee_bend(angle: float) -> float:
    kb = KNEE_BEND
    g_lo, g_hi = kb["good"]
    if g_lo <= angle <= g_hi:
        return _score_in_range(angle, g_lo, g_hi, peak_score=95)
    elif kb["slightly_low"][0] <= angle <= kb["slightly_low"][1]:
        # warning: slightly shallow
        return _score_outside_range(angle, g_lo, g_hi, kb["slightly_low"][0], kb["good"][1]+15,
                                    warn_base=65, poor_base=35)
    elif angle > kb["slightly_low"][1]:
        # poor: barely bending — distance penalty from 149
        return max(5.0, 30 - (angle - 149) * 0.5)
    else:
        # warning: too deep (<90°)
        return max(20.0, 60 - (g_lo - angle) * 0.8)


def _score_elbow(angle: float) -> float:
    g_lo, g_hi = ELBOW_ANGLE["good"]
    w_lo, w_hi = ELBOW_ANGLE["warning"]
    if g_lo <= angle <= g_hi:
        return _score_in_range(angle, g_lo, g_hi, peak_score=95)
    return _score_outside_range(angle, g_lo, g_hi, g_lo - 15, w_hi,
                                warn_base=62, poor_base=25)


def _score_body_lean(angle: float) -> float:
    g_lo, g_hi = BODY_LEAN["good"]
    w_lo, w_hi = BODY_LEAN["warning"]
    if g_lo <= angle <= g_hi:
        return _score_in_range(angle, g_lo, g_hi, peak_score=95)
    return _score_outside_range(angle, g_lo, g_hi, g_lo, w_hi,
                                warn_base=60, poor_base=22)


# ── Public API ───────────────────────────────────────────────────────────────

def evaluate_knee_bend(angle: float) -> MetricResult:
    kb = KNEE_BEND
    if kb["good"][0] <= angle <= kb["good"][1]:
        status = "good"
        msg = "Solid knee bend — good leg load for your shot."
    elif kb["slightly_low"][0] <= angle <= kb["slightly_low"][1]:
        status = "warning"
        msg = (
            "Knee bend is a little shallow. Dropping a bit lower will give "
            "you more leg drive on the way up."
        )
    elif angle > kb["slightly_low"][1]:
        status = "poor"
        msg = (
            "Your knees are barely bending. Aim to dip into an athletic squat "
            "before you rise into your shot."
        )
    else:
        status = "warning"
        msg = (
            "Knee bend looks very deep. That much flexion can slow your "
            "release — try staying slightly higher in your dip."
        )

    return MetricResult(
        name="Knee Bend",
        value=round(angle, 1),
        unit="°",
        status=status,
        score=round(_score_knee_bend(angle), 1),
        feedback=msg,
    )


def evaluate_elbow_angle(angle: float) -> MetricResult:
    status = _classify(angle, ELBOW_ANGLE)

    if status == "good":
        msg = "Elbow is in a good position at release — tucked under the ball."
    elif angle < ELBOW_ANGLE["good"][0]:
        msg = (
            "Elbow is too tucked in. Relax it slightly so your forearm "
            "drives upward at release."
        )
    else:
        msg = (
            "'Chicken wing' elbow detected. Bring your elbow under the ball "
            "to improve arc and consistency."
        )

    return MetricResult(
        name="Elbow Angle at Release",
        value=round(angle, 1),
        unit="°",
        status=status,
        score=round(_score_elbow(angle), 1),
        feedback=msg,
    )


def evaluate_body_lean(angle: float) -> MetricResult:
    status = _classify(angle, BODY_LEAN)

    if status == "good":
        msg = "Body lean looks balanced — upright and in control through the shot."
    elif angle > BODY_LEAN["warning"][1]:
        msg = (
            "You're leaning too far forward. Stay tall through the shot "
            "to keep the ball on line."
        )
    else:
        msg = "Slight forward lean — try to stay a touch more upright."

    return MetricResult(
        name="Body Lean",
        value=round(angle, 1),
        unit="°",
        status=status,
        score=round(_score_body_lean(angle), 1),
        feedback=msg,
    )


# ── Overall score ─────────────────────────────────────────────────────────────

# Metric weights — must sum to 1.0.
# Elbow angle at release is the strongest predictor of shot accuracy,
# so it gets the most weight.
_WEIGHTS = {
    "Knee Bend":              0.30,
    "Elbow Angle at Release": 0.40,
    "Body Lean":              0.30,
}

# How many accepted frames we consider "high confidence".
# Below this the score is softly penalised.
_HIGH_CONFIDENCE_FRAMES = 12


def compute_overall(
    metrics: list[MetricResult],
    frames_analyzed: int = 99,
) -> tuple[int, str]:
    """
    Return (score 0–100, plain-English summary).

    Score anatomy:
      weighted_raw   weighted average of per-metric continuous scores (0–95 max)
      ceiling        hard cap: all-good = 96, one warning = 87, one poor = 68
      confidence     soft penalty when frames_analyzed is low
      final          min(weighted_raw, ceiling) * confidence_factor, clamped 0–100
    """
    # ── weighted raw score ───────────────────────────────────────────────────
    total_weight = sum(_WEIGHTS.get(m.name, 1 / len(metrics)) for m in metrics)
    weighted_raw = sum(
        m.score * _WEIGHTS.get(m.name, 1 / len(metrics))
        for m in metrics
    ) / total_weight

    # ── ceiling based on worst status present ────────────────────────────────
    statuses = [m.status for m in metrics]
    poor_count    = statuses.count("poor")
    warning_count = statuses.count("warning")

    if poor_count >= 2:
        ceiling = 55
    elif poor_count == 1:
        ceiling = 68
    elif warning_count >= 2:
        ceiling = 78
    elif warning_count == 1:
        ceiling = 87
    else:
        ceiling = 96   # all-good: still not 100 — perfect is genuinely rare

    # ── confidence factor (0.88–1.0) ─────────────────────────────────────────
    # More accepted frames = more reliable phase detection = higher confidence.
    # Scales smoothly: 12+ frames → 1.0, 4 frames → ~0.88
    confidence = min(1.0, 0.88 + 0.12 * (frames_analyzed / _HIGH_CONFIDENCE_FRAMES))

    # ── final score ───────────────────────────────────────────────────────────
    raw = min(weighted_raw, ceiling) * confidence
    score = max(0, min(100, int(round(raw))))

    # ── summary text ──────────────────────────────────────────────────────────
    if score >= 90:
        summary = "Pro-level mechanics on this one. Very clean form."
    elif score >= 80:
        summary = "Solid form overall — this is where most good shooters live."
    elif score >= 65:
        summary = "Decent foundation. A couple of targeted fixes will add real consistency."
    elif score >= 45:
        summary = "Several form issues detected. Work through the feedback below one at a time."
    else:
        summary = "Significant form issues — focus on the basics before worrying about results."

    return score, summary