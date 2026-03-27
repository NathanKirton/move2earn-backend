# Move2Earn

Move2Earn is a Flask app for parent-managed screen time. Children earn extra minutes through activity uploads and optional Strava imports, while parents manage accounts, limits, bonus time, messaging, challenges, and friends.

## What the app does

- Parent and child accounts with session-based auth
- Child dashboard with activity upload, timer, streaks, AI recommendations, friends, challenges, and leaderboard
- Parent dashboard for child management, limit updates, bonus time, and messaging
- Optional Strava integration for importing activities
- MongoDB-backed storage for users, activities, challenges, and related app state

## Architecture

Move2Earn is a monolithic Flask application with MongoDB persistence. The app serves both HTML pages and JSON API endpoints. Parent and child users share the same backend, with role checks enforced in the route layer.

Core modules:
- `app.py`: route handlers, session handling, template rendering, and API responses
- `core/database.py`: `UserDB` helpers and core state transitions for users, time balances, streaks, timers, Strava tokens, and parent messages
- `core/ai_engine.py`, `core/ai_helpers.py`, `core/recommendations.py`, `core/rag.py`, `core/analytics.py`, `core/embeddings.py`: AI and recommendation helpers
- `core/profile_ingest.py`: profile ingestion support

UI structure:
- `templates/landing.html`, `templates/login.html`, `templates/register.html`: entry pages
- `templates/dashboard.html`: child dashboard
- `templates/parent_dashboard.html`: parent dashboard
- `templates/upload_activity.html`, `templates/friends.html`, `templates/challenges.html`, `templates/leaderboard.html`: supporting screens
- `static/`: CSS, JavaScript, and assets

Data model notes:
- Parents can own multiple child accounts.
- `daily_screen_time_limit` is the fixed base allowance.
- `daily_earned_minutes_today` stores extra minutes earned for the current day.
- Available time is `base + earned today - used today`.
- Streaks are computed from `activity_dates` via backend logic.

## Current project layout

- `app.py`: Flask routes and application setup
- `wsgi.py`: WSGI entrypoint for production
- `core/`: database, AI, recommendation, analytics, and profile helpers
- `templates/`: Jinja templates
- `static/`: CSS, client-side JavaScript, images
- `ml/` and `models/`: model code and serialized model files
- `scripts/maintenance/`: destructive admin scripts
- `scripts/debug/`: local diagnostic helpers
- `scripts/training/`: model generation and training scripts
- `tests/`: unittest-based regression suite
- `Dockerfile`: container image definition
- `render.yaml`: Render deployment configuration

## Local setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file. The app expects at least:

   ```env
   FLASK_SECRET_KEY=replace-me
   MONGODB_URI=mongodb://...
   MONGODB_DB_NAME=move2earn
   STRAVA_CLIENT_ID=...
   STRAVA_CLIENT_SECRET=...
   STRAVA_REFRESH_TOKEN=...
   ```

4. Run the app:

   ```bash
   python app.py
   ```

5. Open `http://localhost:5000`.

## Operations

Maintenance scripts:
- `python scripts/maintenance/db_management.py` (destructive local admin utility)

Debug scripts:
- `python scripts/debug/debug_ai_call.py` (test-client check for `/api/recommendations`)

Training scripts:
- `python scripts/training/generate_pickle_models.py` (create dummy pickle models)
- `python scripts/training/train_models.py` (train models from MongoDB activity data)

Testing:

```bash
python -m unittest discover -s tests -p "test*.py"
```

## Deployment

- Local entrypoint: `python app.py`
- Production entrypoint: `wsgi.py`
- Container runtime: `Dockerfile` with gunicorn
- Hosted config: `render.yaml`

## ML evaluation snapshot

- Athlete classifier dataset rows: 3864
- Features shape: `(3864, 7)`
- Previous evaluation file reported perfect metrics; re-run evaluation before relying on this in production.
