# Move2Earn

Move2Earn is a Flask app for parent-managed screen time. Children earn extra minutes through activity uploads and optional Strava imports, while parents manage accounts, limits, bonus time, messaging, challenges, and friends.

## What the app does

- Parent and child accounts with session-based auth
- Child dashboard with activity upload, timer, streaks, AI recommendations, friends, challenges, and leaderboard
- Parent dashboard for child management, limit updates, bonus time, and messaging
- Optional Strava integration for importing activities
- MongoDB-backed storage for users, activities, challenges, and related app state

## Current project layout

- `app.py`: Flask routes and application setup
- `database.py`: MongoDB access and core user/game-time logic
- `ai_engine.py`, `ai_helpers.py`, `rag.py`, `recommendations.py`, `analytics.py`, `embeddings.py`: recommendation and analytics helpers
- `templates/`: Jinja templates
- `static/`: CSS, client-side JavaScript, images
- `ml/` and `models/`: model code and serialized model files
- `scripts/maintenance/`: destructive admin scripts
- `scripts/debug/`: local diagnostic helpers
- `scripts/training/`: model generation and training scripts
- `tests/`: unittest-based regression suite
- `docs/`: supporting documentation

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

## Daily time model

- `daily_screen_time_limit` is the base limit for the day.
- `daily_earned_minutes_today` tracks extra minutes earned today.
- Available time is `base limit + earned today - used today`.
- Daily reset keeps the base limit and clears only the day-specific earned bonus.

## Streak model

- Streaks are derived from `activity_dates` on the child record.
- The server is authoritative for streak count; the frontend does not recalculate it.
- Recording an activity date can award streak minutes based on the parent-configured base, increment, and cap values.

## Useful commands

Run the test suite:
```bash
python -m unittest discover -s tests -p "test*.py"
```

Run the maintenance utility:
```bash
python scripts/maintenance/db_management.py
```

Run the AI recommendation diagnostic:
```bash
python scripts/debug/debug_ai_call.py
```

Train local models:
```bash
python scripts/training/train_models.py
```

## Deployment

- `wsgi.py` provides the WSGI entrypoint.
- `Dockerfile` defines the container image.
- `render.yaml` contains the Render deployment configuration.

See `docs/README.md` for a more detailed system overview and `docs/OPERATIONS.md` for maintenance notes.
