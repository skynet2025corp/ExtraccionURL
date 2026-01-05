# URL Extractor — API for Render

This repository originally contained a CLI and a Tkinter GUI. I added a minimal Flask API to allow deployment on Render.

Quick start (locally):

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
gunicorn app:app
# URL Extractor — API for Render

This repository originally contained a CLI and a Tkinter GUI. I added a minimal Flask API to allow deployment on Render.

Quick start (locally):

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
gunicorn app:app
```

API:
- POST /extract
  - JSON body: `{ "url": "example.com", "depth": 2 }`
  - Response: JSON with `status`, `domain`, `found`, and `file` (filename saved on server)

Deploy to Render:
1. Create a new Web Service on Render from this repo.
2. Render will detect the `Procfile` and install `requirements.txt`.
3. Set `PORT` (Render sets this automatically). Start command uses the `Procfile`.

Notes:
- The API reuses the existing `main.py` functions. Long crawls may take time; consider running as a background worker or adding timeouts/limits.
- The GUI (`gui.py`) remains desktop-only and is not used on the server.
