"""
AI integration module.

Loads 3 sklearn models (joblib):
- models/streak_model.pkl (classification -> 0/1)
- models/challenge_model.pkl (classification -> easy/medium/hard)
- models/minutes_model.pkl (regression -> minutes)

Exposes `generate_ai_insights(child_id)` which returns:
{
  "streak_risk": 0/1,
  "challenge_recommendation": "easy|medium|hard",
  "predicted_minutes": int,
  "recommended_workout": str,
  "message": str
}

Models are optional (may be trained later). When missing, sensible heuristics are used.
"""
import os
import logging
from math import floor
from ai_helpers import fetch_last_7_days, has_activity_today
from database import UserDB

logger = logging.getLogger(__name__)

# Attempt to load models from models/ directory using joblib
try:
    import joblib
except Exception:
    joblib = None

ROOT = os.path.dirname(__file__)
MODEL_DIR = os.path.join(ROOT, 'models')

def _load_model(filename):
    path = os.path.join(MODEL_DIR, filename)
    if joblib is None:
        logger.warning('joblib not available; models will not be loaded')
        return None
    try:
        if os.path.exists(path):
            return joblib.load(path)
    except Exception:
        logger.exception('Failed to load model %s', path)
    return None

streak_model = _load_model('streak_model.pkl')
challenge_model = _load_model('challenge_model.pkl')
minutes_model = _load_model('minutes_model.pkl')


def recommend_workout(minutes, difficulty):
    """Return human-friendly workout suggestion based on minutes and difficulty."""
    if difficulty == 'easy':
        return 'Try a 1 km walk or 10 minutes light activity.'
    if difficulty == 'medium':
        return 'Try a 1.5 km walk or a 15-minute jog.'
    if difficulty == 'hard':
        return 'Try a 2 km run or 20 minutes intense activity.'
    # Fallback
    if minutes <= 10:
        return 'Try a 10 minute walk.'
    return f'Try about {minutes} minutes of activity.'


def _aggregate_features(activities, child_id):
    """Compute a simple feature vector from recent activities and user info.

    Returns a dict of features used by models; models are expected to accept a
    list/array-like with ordering matching this helper.
    """
    # Default values
    avg_distance = 0.0
    avg_duration = 0.0
    avg_pace = 999.0
    avg_intensity = 1.0
    total_earned = 0
    days = 0

    for a in activities:
        try:
            avg_distance += float(a.get('distance') or 0.0)
            avg_duration += float(a.get('duration') or 0.0)
            p = a.get('pace')
            if p:
                avg_pace += float(p)
            avg_intensity += float(a.get('intensity_num') or 1)
            total_earned += int(a.get('earned_minutes') or 0)
            days += 1
        except Exception:
            continue

    if days > 0:
        avg_distance = avg_distance / days
        avg_duration = avg_duration / days
        avg_pace = avg_pace / days
        avg_intensity = avg_intensity / days
    else:
        avg_pace = 999.0

    child = UserDB.get_user_by_id(child_id)
    streak_length = int(child.get('streak_count', 0)) if child else 0

    # day_of_week (0-6) for today
    from datetime import datetime
    day_of_week = datetime.utcnow().weekday()

    features = {
        'avg_distance': avg_distance,
        'avg_duration': avg_duration,
        'avg_pace': avg_pace,
        'avg_intensity': avg_intensity,
        'streak_length': streak_length,
        'total_earned': total_earned,
        'day_of_week': day_of_week
    }
    return features


def generate_ai_insights(child_id):
    """Main entry point. Returns the insight dictionary described in module docstring."""
    activities = fetch_last_7_days(child_id)
    activity_today = has_activity_today(child_id)
    features = _aggregate_features(activities, child_id)

    # Default outputs
    streak_risk = 0
    challenge_recommendation = 'easy'
    predicted_minutes = 5

    # Prepare a simple numeric vector for models (order: avg_distance, avg_duration, avg_pace, avg_intensity, streak_length, total_earned, day_of_week)
    vector = [
        features['avg_distance'],
        features['avg_duration'],
        features['avg_pace'],
        features['avg_intensity'],
        features['streak_length'],
        features['total_earned'],
        features['day_of_week']
    ]

    try:
        if streak_model is not None:
            pred = streak_model.predict([vector])
            streak_risk = int(pred[0]) if len(pred) else 0
        else:
            # Heuristic: if streak_length > 0 and no activity today, small risk; if streak_length is small, higher risk
            if activity_today:
                streak_risk = 0
            else:
                streak_risk = 1 if features['streak_length'] < 3 else 0
    except Exception:
        logger.exception('streak_model prediction failed')

    try:
        if challenge_model is not None:
            cpred = challenge_model.predict([vector])
            # Some models may return one-hot or label-strings; try to coerce
            rec = cpred[0]
            if isinstance(rec, (bytes, bytearray)):
                rec = rec.decode('utf-8')
            challenge_recommendation = str(rec)
        else:
            # Simple heuristic: base on avg_pace and avg_distance
            if features['avg_distance'] >= 2.0 or features['avg_pace'] < 6.0:
                challenge_recommendation = 'hard'
            elif features['avg_distance'] >= 1.0:
                challenge_recommendation = 'medium'
            else:
                challenge_recommendation = 'easy'
    except Exception:
        logger.exception('challenge_model prediction failed')

    try:
        if minutes_model is not None:
            m = minutes_model.predict([vector])
            predicted_minutes = int(floor(float(m[0])))
        else:
            # Heuristic: predicted minutes equals average earned or small default
            if features['total_earned'] > 0:
                predicted_minutes = int(min(120, max(1, features['total_earned'] // max(1, len(activities) or 1))))
            else:
                predicted_minutes = 10 if activity_today else 5
    except Exception:
        logger.exception('minutes_model prediction failed')

    # Make sure predicted_minutes is reasonable
    try:
        predicted_minutes = int(max(0, min(240, int(predicted_minutes))))
    except Exception:
        predicted_minutes = 5

    # Recommended workout text
    recommended_text = recommend_workout(predicted_minutes, challenge_recommendation)

    # Message content depending on activity today
    if activity_today:
        message = f"Nice work today! Based on recent activity, try this: {recommended_text}"
    else:
        # Motivational message when no activity
        message = f"No activity yet today — a short activity would keep your streak alive. {recommended_text}"

    # Compose result dict
    result = {
        'streak_risk': int(streak_risk),
        'challenge_recommendation': challenge_recommendation,
        'predicted_minutes': int(predicted_minutes),
        'recommended_workout': recommended_text,
        'message': message
    }

    return result
