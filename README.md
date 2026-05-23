# ShotForm — Basketball Jump Shot Analyzer

Upload a short video of your jump shot and get instant plain-English coaching
feedback on your knee bend, elbow angle, and body lean.

---

## Stack

| Layer    | Tech                          |
|----------|-------------------------------|
| Backend  | Python · FastAPI · MediaPipe  |
| Frontend | React · Vite                  |

---

## Project Structure

```
shotform/
├── backend/
│   ├── main.py        # FastAPI app — single POST /analyze route
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
