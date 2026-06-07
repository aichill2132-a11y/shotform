# ShotForm — AI Basketball Shot Analysis

ShotForm is an AI-powered basketball training application that analyzes jump-shot mechanics from user-uploaded videos and provides plain-English coaching feedback.

Using computer vision and pose estimation, ShotForm evaluates key shooting metrics such as knee bend, elbow angle at release, and body lean to help players identify mechanical issues and improve shooting consistency.

---

## Key Features

- Upload short basketball shooting videos
- Detect body landmarks using MediaPipe pose estimation
- Analyze shooting mechanics from video frames
- Measure knee bend, elbow angle at release, and body lean
- Generate automated coaching feedback in plain English
- Full-stack web application with FastAPI backend and React frontend
- Built and improved through AI-assisted development workflows using Claude

---

## Motivation

As someone interested in basketball, AI, and human performance, I wanted to explore whether computer vision could be used to give athletes accessible feedback without requiring expensive coaching tools or specialized hardware.

ShotForm combines sports analytics, computer vision, and AI-assisted software development to create a tool that helps players better understand their shooting mechanics through objective video analysis.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python · FastAPI · MediaPipe |
| Frontend | React · Vite |
| Development | GitHub · Claude-assisted debugging and iteration |

---

## Project Structure

```text
shotform/
├── backend/
│   ├── main.py        # FastAPI app — POST /analyze route
│   ├── analyzer.py    # Video → pose landmarks → raw metric values
│   ├── feedback.py    # Metric values → coaching feedback strings
│   ├── models.py      # Pydantic response schemas
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── UploadZone.jsx
    │       ├── ResultsCard.jsx
    │       └── MetricRow.jsx
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## Local Setup

### Prerequisites

- Python 3.10+
- Node.js 18+

---

### 1 — Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

API is now running at `http://localhost:8000`

Verify: `curl http://localhost:8000/health` → `{"status":"ok"}`

---

### 2 — Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

App is now running at `http://localhost:5173`

The Vite dev server proxies `/analyze` and `/health` to `localhost:8000`,
so no CORS issues during development.

---

## API Reference

### `POST /analyze`

**Request:** `multipart/form-data` with a single field `file` (MP4 or MOV, ≤ 50 MB)

**Response:**
```json
{
  "overall_score": 74,
  "overall_feedback": "Decent foundation — a couple of fixes will add real consistency.",
  "frames_analyzed": 8,
  "metrics": [
    {
      "name": "Knee Bend",
      "value": 138.4,
      "unit": "°",
      "status": "good",
      "feedback": "Great knee bend! You're loading your legs well for power."
    },
    {
      "name": "Elbow Angle at Release",
      "value": 112.1,
      "unit": "°",
      "status": "warning",
      "feedback": "'Chicken wing' elbow detected. Bring your elbow under the ball to improve arc and consistency."
    },
    {
      "name": "Body Lean",
      "value": 8.3,
      "unit": "°",
      "status": "good",
      "feedback": "Body lean is balanced — upright and controlled on your shot."
    }
  ]
}
```

---

## Quick Test (no frontend)

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@/path/to/your/shot.mp4"
```

---

## Tips for Best Results

- Film from the **side** (perpendicular to the basket) so joints are visible
- Ensure the **full body is in frame** — head to toe
- **Good lighting** helps MediaPipe detect landmarks accurately
- Keep clips **under 30 seconds** for faster analysis

---

## Next Steps (post-MVP)

- [ ] Detect shooting hand automatically (left vs right)
- [ ] Overlay landmark skeleton on the release frame image
- [ ] Add wrist snap / follow-through metric
- [ ] Video history with progress tracking
- [ ] Real-time webcam mode

## What I Learned
Building ShotForm helped me gain experience with:

Full-stack application development
Computer vision and pose estimation
Backend API design with FastAPI
Frontend development with React
Debugging video-analysis workflows
Translating raw model outputs into user-friendly feedback
Using AI tools such as Claude to accelerate development, troubleshoot errors, and iterate on product features
