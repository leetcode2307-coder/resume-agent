# Resume AI Agent – Flutter Frontend

A premium Flutter UI that connects to the FastAPI Resume Agent backend,
streaming live results from four AI agents: **Analyzer**, **Rewriter**,
**Critique**, and **Interview Prep**.

---

## Project Structure

```
frontend/
├── lib/
│   ├── main.dart                   # App entry point
│   ├── theme/
│   │   └── app_theme.dart          # Dark theme, colors & typography
│   ├── models/
│   │   └── workflow_models.dart    # Data classes (mirrors FastAPI state)
│   ├── services/
│   │   └── api_service.dart        # SSE streaming client
│   ├── screens/
│   │   └── home_screen.dart        # Main screen (form + results)
│   └── widgets/
│       ├── shared_widgets.dart     # Reusable UI primitives
│       ├── analyzer_widget.dart    # Analyzer agent output card
│       ├── rewriter_widget.dart    # Rewriter agent output card
│       ├── critique_widget.dart    # Critique agent output card
│       └── interview_widget.dart   # Interview prep agent output card
├── pubspec.yaml
└── README.md
```

---

## Prerequisites

| Tool    | Version   |
|---------|-----------|
| Flutter | >= 3.10   |
| Dart    | >= 3.0    |

Verify with:
```bash
flutter --version
```

---

## Running the Application

### 1. Start the FastAPI backend (from the project root)

```bash
cd /path/to/resume-agent

# Using uv
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# OR using pip venv
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Confirm it is healthy:
```bash
curl http://127.0.0.1:8000/health
# -> {"status":"healthy"}
```

### 2. Install Flutter dependencies

```bash
cd frontend
flutter pub get
```

### 3. Run on desktop (Linux / macOS / Windows)

```bash
flutter run -d linux          # Linux
flutter run -d macos          # macOS
flutter run -d windows        # Windows
```

### 4. Run in browser (Chrome)

```bash
flutter run -d chrome
```

Note: Chrome runs as http://localhost:PORT. The backend already sets
allow_origins=["*"] so CORS is not an issue.

### 5. Run on Android / iOS

```bash
flutter devices               # list connected devices
flutter run -d <device-id>
```

---

## How It Works

1. **Input Form** - Paste resume text and job description. Optional contact
   fields (name, email, phone, LinkedIn, GitHub) are forwarded to the PDF
   generator.

2. **SSE Streaming** - The app opens a persistent HTTP POST to
   http://127.0.0.1:8000/workflow-result and reads text/event-stream
   events line-by-line without any third-party SSE library.

3. **Live Pipeline** - A step indicator at the top animates as each agent
   completes: Analyzer -> Rewriter -> Critique -> Interview Prep.

4. **Agent Cards** - Each agent's card appears as soon as its event arrives:

   | Agent          | Widget             | Key UI elements                                      |
   |----------------|--------------------|------------------------------------------------------|
   | Analyzer       | AnalyzerWidget     | Circular score gauges, skill chips, S/W columns      |
   | Rewriter       | RewriterWidget     | 3-tab view: bullet points, full resume, cover letter |
   | Critique       | CritiqueWidget     | Score banner, iteration timeline, error list          |
   | Interview Prep | InterviewWidget    | Stats strip, 4-tab question lists + prep guide       |

5. **PDF Banner** - When the workflow completes, a success banner shows the
   generated PDF filename (saved to ~/Downloads/).

---

## Changing the Backend URL

Edit lib/services/api_service.dart:

```dart
static const String _baseUrl = 'http://127.0.0.1:8000';
```
