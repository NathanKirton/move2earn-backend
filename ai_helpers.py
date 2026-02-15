"""
Helper functions to fetch and normalise activity data from MongoDB for AI features.

These helpers are lightweight and robust to missing fields. They expose:
- fetch_last_7_days(child_id)
- has_activity_today(child_id)
- calc_pace(distance_km, duration_minutes)
- normalize_activity(activity)

They use the existing `get_db` and `UserDB` helpers in `database.py`.
"""
from datetime import datetime, timedelta
from database import get_db, UserDB
import logging

logger = logging.getLogger(__name__)


def calc_pace(distance_km, duration_minutes):
    """Calculate pace (minutes per km). Returns None when not computable."""
    try:
        d = float(distance_km)
        t = float(duration_minutes)
        if d > 0 and t >= 0:
            return t / d
    except Exception:
        pass
    return None


def normalize_activity(activity):
    """Return a normalized activity dict with expected keys and defaults."""
    a = {}
    a['distance'] = float(activity.get('distance') or 0.0)
    a['duration'] = float(activity.get('time_minutes') or activity.get('duration') or 0.0)
    a['pace'] = activity.get('pace')
    if a['pace'] is None:
        a['pace'] = calc_pace(a['distance'], a['duration'])
    a['intensity'] = activity.get('intensity') or activity.get('intensity_label') or 'Medium'
    # Map intensity to numeric for simple features
    intensity_map = {'Easy': 0, 'easy': 0, 'Medium': 1, 'medium': 1, 'Hard': 2, 'hard': 2}
    a['intensity_num'] = intensity_map.get(a['intensity'], 1)
    a['earned_minutes'] = int(activity.get('earned_minutes') or activity.get('time_minutes') or 0)
    # Normalize date -> ISO YYYY-MM-DD when possible
    date = activity.get('date') or activity.get('start_date')
    try:
        if isinstance(date, str) and 'T' in date:
            a['date'] = date.split('T')[0]
        elif isinstance(date, datetime):
            a['date'] = date.date().isoformat()
        else:
            a['date'] = str(date) if date else None
    except Exception:
        a['date'] = None

    # Day of week (0=Monday .. 6=Sunday) when date available
    try:
        if a['date']:
            a['day_of_week'] = datetime.fromisoformat(a['date']).weekday()
        else:
            a['day_of_week'] = None
    except Exception:
        a['day_of_week'] = None

    a['challenge_completed'] = bool(activity.get('challenge_completed', False))

    return a


def fetch_last_7_days(child_id):
    """Fetch last 7 activities for child_id from activities collection.

    Returns a list of normalized activity dicts (newest first). If DB unavailable,
    returns an empty list.
    """
    db = get_db()
    if db is None:
        logger.warning('fetch_last_7_days: DB not available')
        return []

    activities_collection = db['activities']
    try:
        docs = list(activities_collection.find({'user_id': child_id}).sort('created_at', -1).limit(7))
        normalized = [normalize_activity(d) for d in docs]
        return normalized
    except Exception:
        logger.exception('Error fetching last 7 days for %s', child_id)
        return []


def has_activity_today(child_id):
    """Return True if the child has an activity recorded today.

    This checks both the `activities` collection and the child's `last_activity_date`.
    """
    db = get_db()
    today = datetime.utcnow().date().isoformat()

    # Check user document first (fast)
    try:
        child = UserDB.get_user_by_id(child_id)
        if child:
            last = child.get('last_activity_date')
            if last:
                # Normalize stored last_activity_date
                if isinstance(last, str) and 'T' in last:
                    last = last.split('T')[0]
                if last == today:
                    return True
    except Exception:
        logger.debug('has_activity_today: user lookup failed for %s', child_id)

    if db is None:
        return False

    activities_collection = db['activities']
    try:
        # Some records store date or start_date as ISO string
        found = activities_collection.find_one({'user_id': child_id, '$or': [{'date': today}, {'start_date': {'$regex': '^' + today}}]})
        return bool(found)
    except Exception:
        logger.exception('has_activity_today DB query failed for %s', child_id)
        return False
