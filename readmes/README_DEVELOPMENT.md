README — Development History, Decisions and Deployment

Overview

This repository contains the Flask backend and supporting scripts for the Move2Earn family app (parent-child game-time management with Strava integration). This document captures the full development process performed, the major decisions and trade-offs, the technologies used, and the rationale behind them.

1) Project goals and scope

- Host the Flask backend microservice on Render (https://move2earn-backend.onrender.com)
- Primary domain (https://move2earn.uk/) redirects to Render backend
- Integrate Strava OAuth and ingestion of activities to award game time.
- Implement and harden a streaks feature that awards escalating daily rewards for consecutive active days.
- Provide parent controls for configuring streak rewards (but not manual per-child manipulation).
- Ensure authoritative server-side logic for awarding game time and avoiding race/duplication issues.
- Improve child dashboard UX (accurate timer counting, eliminate drift) and parent dashboard UX (simplification and configuration placement).

2) Technologies and tooling used

- Python 3.x with Flask: chosen for speed of development, simplicity for small web backends, and compatibility with Render.
- Jinja2 templates: server-rendered child and parent dashboards for straightforward UI updates and integration with Flask session-based authentication.
- MongoDB via PyMongo: flexible document model to store user data, messages, and streak metadata; simple to evolve schema without migrations.
- Strava API (OAuth v3): used for activity ingestion. Implemented authorization and refresh token handling.
- Render: used as the target hosting for the Flask backend (supports Python apps and deploy webhooks).
- PowerShell helper scripts (temporary): used locally to create/poll deploys and run quick tasks — later removed from repo.
- dotenv: to manage local environment variables during development.
- Logging: Python's logging module to replace ad-hoc prints and preserve stack traces.

3) High-level workflow and steps performed

- Repo inspection and baseline: explored existing endpoints, templates, and Strava flows.
- Implemented server-side streak logic inside `database.py` in `UserDB.record_daily_activity()`:
  - Robust date parsing for activity inputs and previously stored `last_activity_date`.
  - Streak increment only when activity date == (last activity date + 1 day), else reset to 1.
  - Prevent duplicate awarding for same day.
  - Reward formula: reward = base + (streak - 1) * increment, capped by a parent-configurable cap.
  - On awarding, increment both `earned_game_time` and `daily_screen_time_limit`.
- Child dashboard fixes:
  - Compute displayed used time as `server_used + elapsed_since_timer_started` (server is authoritative) to avoid drift when the browser is backgrounded.
  - Update `renderStreakDays()` to calculate each day's reward using `streak_settings` (base, increment, cap) — so day boxes show per-day amounts.
- Parent dashboard changes:
  - Removed per-child manual streak controls and per-child bonus-per-day inputs to reduce abuse and mistakes.
  - Moved global streak settings to a dedicated bottom-of-page card where parents can set base/increment/cap.
  - Implemented `/api/set-streak-settings` and `/api/get-streak-settings`.
- Testing & diagnostics:
  - Added many small test scripts (moved to `tests/`) for manual and integration checks.
  - Added tools in `tools/` for DB resets, test account bootstrap, and diagnostics. These require conservative use (prefer staging DB).
- Deployment:
  - Created and iterated Render deployment config (Dockerfile/Procfile/render.yaml-like artifacts) and used Render API to trigger deploys.
  - Polled deploys until live and validated the live site.
- Clean up:
  - Replaced `print()` debugging with `logger.debug/info/exception` across `app.py` and `database.py`.
  - Consolidated tests into `tests/` and tools into `tools/`.
  - Removed temporary deploy helper scripts from the repo.

4) Key files created or changed

- `app.py`: main Flask application. Added endpoints for gametime balance, streak settings, message APIs, and Strava token handling.
- `database.py`: central `UserDB` class and `record_daily_activity` logic. Also contains DB helpers used by the app.
- `templates/parent_dashboard.html`: simplified parent UI and moved streak-setting controls.
- `templates/dashboard.html`: child dashboard; updated timer display and streak day rendering.
- `tests/`: directory with test scripts for messaging, e2e flows, progress bar calculations, streak harness, and DB connection checks.
- `tools/`: maintenance utilities: `reset_times.py`, `diagnose_users.py`, `setup_test_accounts.py`, `clear_users.py`.
- Documentation files updated: `IMPLEMENTATION_SUMMARY.md`, `QUICK_START.md`, `MESSAGING_GUIDE.md`, `FEATURE_DEMO.md`.

5) Important implementation details and rationale

- Server-side authority: All awarding of `earned_game_time` and changes to `daily_screen_time_limit` are performed server-side and only via well-audited functions (`record_daily_activity`, message/broadcast endpoints). This prevents client-side tampering.

- Date handling and streak correctness:
  - Streaks should reflect consecutive-day activity, not calendar days relative to 'now'. To handle out-of-order uploads and timezone nuances we normalize dates using ISO date strings YYYY-MM-DD and compare the activity date to the stored `last_activity_date` as date objects.
  - Award only once per day (guard against duplicate ingestion) — the function returns applied=False if an activity for that date was already recorded.

- Reward formula:
  - reward = base + (streak - 1) * increment, with optional cap. We made the values configurable by parents because families may prefer different progression rates.

- Timer drift fix:
  - The problem: JavaScript count-up timers drift when tabs are backgrounded or system sleeps. Fix: compute elapsed using server `timer_started_at` UTC timestamp on each tick and add to server `used_game_time` rather than trusting continuous JS increments.

- No parent manual per-child streak edits:
  - To preserve fairness and prevent accidental changes, parents can only set global streak rules (base/increment/cap). Actual streak increments occur only via `record_daily_activity` when an activity is ingested.

- Logging & error handling:
  - Replace prints with structured `logging` so stack traces are captured (`logger.exception`) and logs are consistent across environments.

6) Challenges encountered & how they were solved

- Duplicate awards & out-of-order uploads:
  - Symptom: duplicate earned minutes when the same activity or same-day activity ingested twice.
  - Fix: detect same-day award in `record_daily_activity` and skip awarding. Use `last_activity_date` stored on child user doc.

- Streak resetting inappropriately:
  - Symptom: streak reset when a later-uploaded activity was processed because logic compared to 'today' rather than to the uploaded activity's date.
  - Fix: compute streak continuation by comparing activity date to `last_activity_date + 1 day`.

- Timer drift when tab backgrounded or system sleeps:
  - Symptom: client-side timers were out-of-sync with server after returning to tab.
  - Fix: server provides `timer_started_at` and `used_game_time`, client computes elapsed using server-supplied timestamp so refresh and tab re-activation show correct elapsed.

- Debugging/deploy complexity with Render API transient behavior:
  - Symptom: occasional 404s when polling newly created deploys.
  - Fix: resilient polling and retry logic; created temporary PS helpers for convenience and then removed them after deploying successfully.

7) Security & operational notes

- Environment variables required (set in Render and locally for dev):
  - `MONGODB_URI`, `MONGODB_DB_NAME`, `FLASK_SECRET_KEY`, `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`.

- Access controls:
  - Endpoints check `account_type` (parent/child) in the session; parent-only endpoints enforce parent identity.

- Considerations for production:
  - Use indices on `users.parent_id` and `users.email` for performance.
  - Add tests and CI (e.g., GitHub Actions) to run the test suite against a test DB.
  - Add rate-limiting and more robust auditing for admin-level operations.

8) Next recommended steps

- Add automated `pytest` tests and a small CI pipeline to prevent regressions.
- Add versioned DB migrations or a lightweight schema version key in user documents for safe schema evolution.
- Consider extracting streak logic into a dedicated service/module and add unit tests around that logic.
- Add backups and monitoring for the MongoDB instance.

9) Where things live now (file layout highlights)

- `app.py` — Flask entrypoint
- `database.py` — DB helpers and streak logic
- `templates/` — front-end views (`parent_dashboard.html`, `dashboard.html`)
- `tests/` — moved test scripts
- `tools/` — moved utility scripts
- `README_DEVELOPMENT.md` — this file (comprehensive development narrative)

10) Contact / support

If you want, I can now:
- Remove the original root stubs/files entirely (clean up the repo root), or
- Run the tests locally against a staging DB (if you provide credentials or allow me to use your environment), or
- Create a `pytest` suite and minimal GitHub Actions CI job to automate the tests.

— End of development README
