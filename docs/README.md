# Move2Earn Docs

This folder holds the project documentation that is useful after setup.

## Documents

- `README.md`: this index
- `ARCHITECTURE.md`: high-level application structure and behavior
- `OPERATIONS.md`: local admin, debug, and training scripts

## Key runtime facts

- The app is a single Flask service centered on `app.py` and `database.py`.
- MongoDB is the source of truth for accounts, activities, messages, challenges, and timers.
- Jinja templates in `templates/` render the main user-facing pages.
- Strava import, AI recommendations, and analytics all run inside the same application process.

## Where to start

- For local setup and common commands, go back to the root `README.md`.
- For the code structure and core behavior, read `ARCHITECTURE.md`.
- For destructive scripts and utilities, read `OPERATIONS.md`.
