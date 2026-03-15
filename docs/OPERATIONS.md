# Operations

## Maintenance scripts

### `python scripts/maintenance/db_management.py`

Interactive utility for local database administration. It includes actions such as listing users, deleting users, clearing activities, resetting game time, and dropping the configured database. Treat it as destructive.

## Debug scripts

### `python scripts/debug/debug_ai_call.py`

Runs a quick Flask test-client request against `/api/recommendations` with a simulated child session. Useful for verifying that the AI recommendation endpoint is wired correctly.

## Training scripts

### `python scripts/training/generate_pickle_models.py`

Writes dummy pickle models into `models/` from the importable dummy model classes.

### `python scripts/training/train_models.py`

Reads activities from MongoDB, derives labels, trains three scikit-learn models, and writes them into `models/`.

## Testing

Run the full unittest suite:

```bash
python -m unittest discover -s tests -p "test*.py"
```

## Cleanup choices made in this repository

The following items were intentionally removed during cleanup because they were not part of the Flask runtime and had no code references:

- old standalone HTML mockups in the repo root
- old standalone CSS files in the repo root
- duplicate quick-clear database scripts
- `templates/dashboard_old.html`
- generated cache/session folders that should not live in source control

If you need another one-off maintenance helper later, place it under `scripts/` rather than the repo root.
