# Tests Directory

This directory contains project test scripts that were moved from the repository root.

Usage

- Run a test module from the project root, for example:

```powershell
python -m tests.test_messaging
```

Notes

- These scripts are lightweight integration-style checks and expect a running Flask backend and a MongoDB configured via environment variables.
- Prefer running these against a staging database.
# Tests

This folder contains automated and manual test scripts used during development.

How to run

- From the project root run tests as modules to ensure imports resolve correctly:

  ```powershell
  python -m tests.test_messaging
  python -m tests.test_e2e_fixes
  python -m tests.test_add_time_fix
  python -m tests.test_parent_auth
  python -m tests.test_db
  python -m tests.test_progress_bar
  python -m tests.test_streaks <child_id> [YYYY-MM-DD]
  ```

Notes

- These scripts are simple integration-style drivers that call the running Flask app on `http://localhost:5000`.
- Ensure the Flask app is running and environment variables (`MONGODB_URI`, `MONGODB_DB_NAME`, `FLASK_SECRET_KEY`) are set before running tests.
- Some scripts (notably `test_streaks`) will modify the database; use a staging/test database when possible.

Conventions

- Tests are plain Python scripts (no test framework) for quick manual verification.
- To convert to an automated test suite, consider using `pytest` and fixtures for setup/teardown.
