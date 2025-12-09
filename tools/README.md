# Tools Directory

This directory contains maintenance and diagnostic scripts.

Common scripts

- `debug_db.py` — quick debug helper to create/verify test parent accounts.
- `clear_database.py` — clears users and activities from the configured database (use with caution).

Usage

Run from the project root, for example:

```powershell
python tools/debug_db.py
python tools/clear_database.py
```

Notes

- These scripts perform destructive operations (deleting users/activities). Only run against test/staging DBs.
- Environment variables are loaded via `.env` for local development.
# Tools

This folder contains maintenance and utility scripts used during development and deployment.

Available tools

- `reset_times.py` - Reset daily usage counters for all child accounts. Usage:
  ```powershell
  python tools/reset_times.py
  ```

- `setup_test_accounts.py` - Create demo parent/child accounts for local testing. Usage:
  ```powershell
  python tools/setup_test_accounts.py
  ```

- `diagnose_users.py` - Inspect user documents and verify password hashing logic. Usage:
  ```powershell
  python tools/diagnose_users.py
  ```

- `clear_users.py` - Interactive utility to delete users (use with caution). Usage:
  ```powershell
  python tools/clear_users.py
  ```

Notes

- These scripts require `MONGODB_URI` and `MONGODB_DB_NAME` to be set in the environment or a `.env` file.
- Prefer running these tools against a staging/test database to avoid accidental data loss.
- Consider adding a more robust CLI or argparse-based entrypoints if these tools will be used frequently.
