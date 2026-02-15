"""
Train AI models from historical activities and save to `models/`.

This script expects the project to have `pymongo` configured and access to the app's
MongoDB. It will extract features from activities, train three models, and save
using `joblib` into `models/`:
- streak_model.pkl (classification)
- challenge_model.pkl (classification)
- minutes_model.pkl (regression)

Usage:
  python tools/train_models.py

Note: This script requires `scikit-learn` and `joblib`. If not installed, it will
print instructions to run inside a proper environment (local or Docker).
"""
import os
import sys
import logging
from pprint import pprint

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from ai_helpers import fetch_all_activities

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MODEL_DIR = os.path.join(ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    import joblib
    import numpy as np
except Exception as e:
    print('Required packages missing for training:', e)
    print('Run this script in an environment with scikit-learn and joblib installed.')
    print('Example (local):')
    print('  python -m pip install scikit-learn joblib numpy')
    print('Then run:')
    print('  python tools/train_models.py')
    sys.exit(1)


def build_feature_vector(act):
    # Use numeric features: distance, duration, pace, intensity_num, earned_minutes, day_of_week
    # Extend with heart rate, cadence and elevation
    return [
        act.get('distance', 0.0),
        act.get('duration', 0.0),
        act.get('pace') or 999.0,
        act.get('intensity_num', 1),
        act.get('earned_minutes', 0),
        act.get('day_of_week') if act.get('day_of_week') is not None else -1,
        act.get('avg_heartrate') or 0.0,
        act.get('max_heartrate') or 0.0,
        act.get('avg_cadence') or 0.0,
        act.get('avg_elevation_gain') or 0.0,
    ]


def prepare_dataset(activities):
    # We'll derive labels heuristically from the data so models can be trained
    X = []
    y_minutes = []
    y_challenge = []
    y_streak = []

    # Sort activities by date ascending so we can inspect next-day behavior
    activities_sorted = sorted(activities, key=lambda x: x.get('date') or '')

    # Build simple arrays first
    for i, a in enumerate(activities_sorted):
        X.append(build_feature_vector(a))
        y_minutes.append(a.get('earned_minutes', 0))

    # Challenge labeling: use distribution of earned_minutes to define easy/medium/hard
    import numpy as np
    earned = np.array([a.get('earned_minutes', 0) for a in activities_sorted])
    if len(earned) > 0:
        p33 = np.percentile(earned, 33)
        p66 = np.percentile(earned, 66)
    else:
        p33 = p66 = 0

    for a in activities_sorted:
        val = a.get('earned_minutes', 0)
        if val >= p66 and val > 0:
            y_challenge.append('hard')
        elif val >= p33 and val > 0:
            y_challenge.append('medium')
        else:
            y_challenge.append('easy')

    # Streak labeling: 1 if there is activity the next calendar day
    from datetime import datetime, timedelta
    dates = [a.get('date') for a in activities_sorted]
    for i, d in enumerate(dates):
        try:
            cur = datetime.fromisoformat(d)
            found_next = False
            # check if any activity exists with date == cur + 1 day
            for j in range(i+1, min(i+8, len(dates))):
                try:
                    other = datetime.fromisoformat(dates[j])
                    if other.date() == (cur + timedelta(days=1)).date():
                        found_next = True
                        break
                except Exception:
                    continue
            y_streak.append(1 if found_next else 0)
        except Exception:
            y_streak.append(0)

    return np.array(X), np.array(y_minutes), np.array(y_challenge), np.array(y_streak)


def train_and_save(models_out=('streak_model.pkl','challenge_model.pkl','minutes_model.pkl')):
    activities = fetch_all_activities()
    if not activities:
        print('No activities found in DB. Please populate activities before training.')
        return

    X, y_minutes, y_challenge, y_streak = prepare_dataset(activities)
    print('Dataset shapes:', X.shape, y_minutes.shape, y_challenge.shape, y_streak.shape)

    # Train minutes regression
    X_train, X_test, y_train, y_test = train_test_split(X, y_minutes, test_size=0.2, random_state=42)
    reg = RandomForestRegressor(n_estimators=50, random_state=42)
    reg.fit(X_train, y_train)
    print('Minutes model R2 on test:', reg.score(X_test, y_test))
    joblib.dump(reg, os.path.join(MODEL_DIR, models_out[2]))

    # Train challenge classifier
    X_train, X_test, y_train, y_test = train_test_split(X, y_challenge, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_train, y_train)
    print('Challenge model acc on test:', clf.score(X_test, y_test))
    joblib.dump(clf, os.path.join(MODEL_DIR, models_out[1]))

    # Train streak classifier
    X_train, X_test, y_train, y_test = train_test_split(X, y_streak, test_size=0.2, random_state=42)
    clf2 = RandomForestClassifier(n_estimators=50, random_state=42)
    clf2.fit(X_train, y_train)
    print('Streak model acc on test:', clf2.score(X_test, y_test))
    joblib.dump(clf2, os.path.join(MODEL_DIR, models_out[0]))

    print('Models trained and saved to', MODEL_DIR)


if __name__ == '__main__':
    train_and_save()
