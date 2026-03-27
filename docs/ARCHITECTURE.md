# Architecture

## Overview

Move2Earn is a monolithic Flask application with MongoDB persistence. The app serves both HTML pages and JSON API endpoints. Parent and child users share the same backend, with role checks enforced in the route layer.

## Main modules

- `app.py`: route handlers, session handling, template rendering, and API responses
- `database.py`: `UserDB` helpers and most state transitions for users, time balances, streaks, timers, and parent messages
- `ai_engine.py`, `ai_helpers.py`, `recommendations.py`, `rag.py`, `analytics.py`, `embeddings.py`: AI, recommendation, and analytics helpers
- `profile_ingest.py`: profile ingestion support
- `ml/` and `models/`: model code and serialized artifacts

## UI structure

- `templates/landing.html`, `login.html`, `register.html`: entry pages
- `templates/dashboard.html`: child dashboard
- `templates/parent_dashboard.html`: parent dashboard
- `templates/upload_activity.html`, `friends.html`, `challenges.html`, `leaderboard.html`: supporting screens
- `static/`: CSS, JavaScript, and assets used by the templates

## Data model notes

### Accounts

- Parents can own multiple child accounts.
- Children store the parent link plus game-time, timer, message, and streak-related fields.

### Game time

- `daily_screen_time_limit` is the fixed base daily allowance.
- `daily_earned_minutes_today` stores extra minutes earned for the current day.
- `earned_game_time` still tracks credited minutes in the database, but day-only earned time is reversed on daily reset.

### Streaks

- Streaks are computed from `activity_dates` instead of persisted counters.
- `calculate_current_streak()` derives the streak dynamically from normalized ISO dates.
- `record_activity_date()` adds a day once, computes the streak reward, and credits minutes.

## External integrations

- MongoDB via `pymongo`
- Strava OAuth and activity APIs via `requests`
- Optional ML helpers using `scikit-learn`, `joblib`, and `sentence-transformers`

## Deployment shape

- Local entrypoint: `python app.py`
- Production entrypoint: `wsgi.py`
- Container: `Dockerfile`
- Hosted configuration: `render.yaml`
