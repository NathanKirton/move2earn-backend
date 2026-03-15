"""
AI integration module.

Provides `generate_ai_insights(child_id)` which returns a structured
insight dict used by the frontend. The implementation prefers lightweight
sklearn models when available (joblib or pickle), but falls back to
robust heuristics that use recent activity data when models are absent.

Fields returned include:
- total_activities, avg_pace, avg_heartrate, avg_distance, streak_length
- pace_trend, streak_risk, challenge_recommendation, predicted_minutes
- recommended_workout, tips, message

This file is intentionally self-contained and tolerant to missing DB or
model artifacts so it can run in development and on deployed instances
that lack heavy build tooling.
"""
import os
import logging
from math import floor
from typing import List

from core.ai_helpers import fetch_last_7_days, has_activity_today
from core.database import UserDB

logger = logging.getLogger(__name__)

# Attempt to load joblib / pickle models from models/ directory.
MODEL_STATUS = {'streak': False, 'challenge': False, 'minutes': False}
MODEL_SOURCE = None


def _safe_load_model(path):
    """Try to load a model using joblib, then pickle. Return None on failure."""
    if not os.path.exists(path):
        return None
    try:
        import joblib

        return joblib.load(path)
    except Exception:
        try:
            import pickle

            with open(path, 'rb') as fh:
                return pickle.load(fh)
        except Exception:
            logger.exception('Failed to load model %s', path)
            return None


# Load models if present. Keep references global for reuse.
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
streak_model = None
challenge_model = None
minutes_model = None
try:
    streak_model = _safe_load_model(os.path.join(MODELS_DIR, 'streak_model.pkl'))
    challenge_model = _safe_load_model(os.path.join(MODELS_DIR, 'challenge_model.pkl'))
    minutes_model = _safe_load_model(os.path.join(MODELS_DIR, 'minutes_model.pkl'))
    if streak_model or challenge_model or minutes_model:
        MODEL_SOURCE = 'models'
        MODEL_STATUS['streak'] = bool(streak_model)
        MODEL_STATUS['challenge'] = bool(challenge_model)
        MODEL_STATUS['minutes'] = bool(minutes_model)
except Exception:
    logger.debug('Model load attempt failed; continuing with heuristics')


def recommend_workout(minutes: int, difficulty: str) -> str:
    """Return a friendly workout description given minutes and difficulty."""
    minutes = max(1, int(minutes or 5))
    difficulty = (difficulty or 'easy').lower()
    if difficulty == 'hard':
        return f'{minutes} minutes — 5 min warmup, {max(1, minutes-10)} min intervals, cool down'
    if difficulty == 'medium':
        return f'{minutes} minutes — sustained effort; include 2 x 5 min tempo blocks'
    return f'{minutes} minutes — easy aerobic session or brisk walk'


def _aggregate_features(activities: List[dict], child_id: str) -> dict:
    """Aggregate commonly used features from normalized activities list.

    activities should be newest-first (as returned by fetch_last_7_days).
    """
    avg_distance = 0.0
    avg_duration = 0.0
    avg_pace = 0.0
    avg_intensity = 1.0
    total_earned = 0
    days = 0
    avg_hr = None
    hr_days = 0
    max_hr = None
    avg_cadence = None
    cadence_days = 0
    avg_elev = 0.0

    for a in activities:
        try:
            d = float(a.get('distance') or 0.0)
            avg_distance += d
            avg_duration += float(a.get('duration') or 0.0)
            p = a.get('pace')
            if p:
                avg_pace += float(p)
            intensity_num = a.get('intensity_num') or 1
            avg_intensity += float(intensity_num)
            total_earned += int(a.get('earned_minutes') or 0)
            # HR
            if a.get('avg_heartrate'):
                avg_hr = (avg_hr or 0.0) + float(a.get('avg_heartrate'))
                hr_days += 1
            if a.get('max_heartrate'):
                try:
                    max_hr = max(max_hr, float(a.get('max_heartrate'))) if max_hr else float(a.get('max_heartrate'))
                except Exception:
                    pass
            # cadence/elevation
            if a.get('cadence'):
                avg_cadence = (avg_cadence or 0.0) + float(a.get('cadence'))
                cadence_days += 1
            avg_elev += float(a.get('elevation_gain') or 0.0)
            days += 1
        except Exception:
            continue

    if days > 0:
        avg_distance = avg_distance / days
        avg_duration = avg_duration / days
        avg_pace = avg_pace / days if avg_pace else None
        avg_intensity = avg_intensity / max(1, days)
        if hr_days > 0:
            avg_hr = avg_hr / hr_days
        else:
            avg_hr = None
        if cadence_days > 0:
            avg_cadence = avg_cadence / cadence_days
        else:
            avg_cadence = None
        avg_elev = avg_elev / days
    else:
        avg_pace = None

    child = UserDB.get_user_by_id(child_id)
    # Calculate streak from activity_dates
    streak_length = UserDB.calculate_current_streak(child_id) if child else 0

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
    features['avg_heartrate'] = avg_hr
    features['max_heartrate'] = max_hr
    features['avg_cadence'] = avg_cadence
    features['avg_elevation_gain'] = avg_elev
    return features


def generate_ai_insights(child_id: str) -> dict:
    """Generate a friendly, structured insights dict for the given child.

    This function is robust: it will operate when DB is unavailable or models
    are missing by using sensible heuristics.
    """
    activities = fetch_last_7_days(child_id)
    activity_today = has_activity_today(child_id)
    features = _aggregate_features(activities, child_id)
    logger.debug('generate_ai_insights: child=%s activity_today=%s activities_count=%d features=%s', child_id, activity_today, len(activities), features)

    total_activities = len(activities)
    avg_pace = features.get('avg_pace')
    avg_hr = features.get('avg_heartrate')
    avg_distance = features.get('avg_distance')
    streak_length = features.get('streak_length')

    # Trend detection (recent vs prior pace)
    pace_trend = None
    try:
        paces = [a.get('pace') for a in activities if a.get('pace')]
        if len(paces) >= 4:
            recent = sum(paces[:3]) / min(3, len(paces[:3]))
            prior = sum(paces[3:6]) / max(1, len(paces[3:6]))
            pace_trend = 'improving' if recent < prior else ('slowing' if recent > prior else 'stable')
        elif len(paces) > 0:
            pace_trend = 'insufficient_data'
    except Exception:
        pace_trend = None

    # Heart rate note
    hr_note = None
    try:
        if avg_hr and avg_hr > 160:
            hr_note = 'High average heart rate — consider easier sessions or check effort.'
        elif avg_hr and avg_hr < 120:
            hr_note = 'Lower heart rate — mainly easy aerobic work.'
    except Exception:
        pass

    # Build numeric vector for models (order matches training script)
    vector = [
        features.get('avg_distance', 0.0),
        features.get('avg_duration', 0.0),
        features.get('avg_pace', 999.0) or 999.0,
        features.get('avg_intensity', 1.0),
        features.get('total_earned', 0),
        features.get('day_of_week', 0),
        features.get('avg_heartrate') or 0.0,
        features.get('max_heartrate') or 0.0,
        features.get('avg_cadence') or 0.0,
        features.get('avg_elevation_gain') or 0.0,
    ]

    # Defaults
    streak_risk = 0
    challenge_recommendation = 'easy'
    predicted_minutes = 5

    # Model predictions with safe fallbacks
    try:
        if streak_model is not None:
            pred = streak_model.predict([vector])
            streak_risk = int(pred[0]) if len(pred) else 0
        else:
            streak_risk = 0 if activity_today else (1 if streak_length < 3 else 0)
    except Exception:
        logger.exception('streak_model prediction failed')

    try:
        if challenge_model is not None:
            cpred = challenge_model.predict([vector])
            rec = cpred[0]
            if isinstance(rec, (bytes, bytearray)):
                rec = rec.decode('utf-8')
            challenge_recommendation = str(rec)
        else:
            if avg_distance and avg_distance >= 2.0 or (avg_pace and avg_pace < 6.0):
                challenge_recommendation = 'hard'
            elif avg_distance and avg_distance >= 1.0:
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
            predicted_minutes = int(min(120, max(1, features.get('total_earned', 0) // max(1, total_activities or 1))))
    except Exception:
        logger.exception('minutes_model prediction failed')

    predicted_minutes = max(0, min(240, int(predicted_minutes)))

    # Build tips and user-facing message
    tips = []
    if activity_today:
        tips.append('Nice work today — keep the momentum!')
    else:
        tips.append('No activity yet today — a short 10 minute walk helps keep streaks alive.')

    if pace_trend == 'improving':
        tips.append('Pace is improving — try short intervals to build speed.')
    elif pace_trend == 'slowing':
        tips.append('Pace slowed — consider an easy recovery session.')

    if hr_note:
        tips.append(hr_note)

    workout_text = recommend_workout(predicted_minutes, challenge_recommendation)
    tips.append(f'Suggested: {workout_text} ({predicted_minutes} min, {challenge_recommendation})')

    result = {
        'total_activities': total_activities,
        'avg_pace': avg_pace,
        'avg_heartrate': avg_hr,
        'avg_distance': avg_distance,
        'streak_length': streak_length,
        'pace_trend': pace_trend,
        'streak_risk': int(streak_risk),
        'challenge_recommendation': challenge_recommendation,
        'predicted_minutes': int(predicted_minutes),
        'recommended_workout': workout_text,
        'tips': tips,
        'message': ' '.join(tips)
    }

    # Attach diagnostics
    result['_model_status'] = MODEL_STATUS
    result['_model_source'] = MODEL_SOURCE

    return result
