# GitDeep 🔍

GitDeep is an advanced "Software Archaeology" and repository analysis tool. It dives deep into public GitHub projects to determine their health, contributor risk (Bus Factor), and semantic intent of the development team using NLP.

## Features ✨

* **Activity & Decay Tracking:** Mathematically calculates commit stagnation and developer drop-off rates.
* **Bus Factor Risk:** Analyzes if a project relies too heavily on a single central developer.
* **Semantic Intent (NLP):** Uses natural language processing (Google Gemini) to categorize commits (e.g., feature work vs. technical debt).
* **Plagiarism Detection:** Scans code patterns to detect potential copied or overly duplicated logic.
* **Multi-language PDF Reports:** Generates professional, academic-style PDF reports with embedded charts.
* **Smart Caching:** SQLite-based caching for recent analyses to improve response times and save API quotas.
* **Interactive SPA Interface:** Beautiful, responsive Vanilla JS frontend with Chart.js visualization and smooth page transitions.

## Tech Stack 🛠️

* **Backend:** Python, FastAPI, SQLite (Caching & History), SQLAlchemy, FPDF2 (for PDF Generation), PyGithub, Gemini API.
* **Frontend:** HTML5, Vanilla CSS3 (Glassmorphism UI), Vanilla JavaScript, Chart.js.

## Getting Started 🚀

### 1. Backend Setup

Navigate to the `backend/` directory:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```
GITHUB_PAT=your_github_personal_access_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Run the backend server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

The frontend is a static SPA. You can serve it using Python's built-in HTTP server:

```bash
cd frontend
python3 -m http.server 8080
```

Navigate to `http://localhost:8080` in your web browser.

## Architecture & Workflows

1. **Ingestion:** Asynchronously fetches repository metadata via GitHub API to avoid rate limits blocking the UI.
2. **Analysis:** The `MetricsEngine` processes the commit/contributor logic.
3. **Reasoning:** The `NLPEngine` and `ReasoningEngine` compile the data, format it into an AI prompt, and synthesize the final decision.
4. **Delivery:** The API returns JSON payload combining metric stats, `Chart.js` arrays, and the direct URL to the downloadable PDF report.

---
*Built with ❤️ for Software Archaeologists.*
