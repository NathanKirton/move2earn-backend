from datetime import datetime, timedelta
from database import get_db


def compute_weekly_km(db, user_id):
    activities = db['activities']
    week_ago = datetime.utcnow() - timedelta(days=7)
    total = 0.0
    for a in activities.find({'user_id': user_id, 'created_at': {'$gte': week_ago}}):
        dist = a.get('distance') or a.get('distance_km') or a.get('distance_m')
        try:
            if dist is None:
                continue
            d = float(dist)
            if d > 1000:
                d = d / 1000.0
            total += d
        except Exception:
            continue
    return total


def compute_user_profiles():
    """Compute lightweight user profiles and write to `user_profiles` collection.

    Fields: user_id, weekly_km, last_activity, avg_session_minutes (best-effort),
            max_minutes_per_session (default 120)
    """
    db = get_db()
    if db is None:
        return False

    users = db['users']
    profiles = db['user_profiles']

    for u in users.find({}):
        uid = str(u.get('_id'))
        weekly_km = compute_weekly_km(db, uid)

        # best-effort last activity
        last_act = db['activities'].find_one({'user_id': uid}, sort=[('created_at', -1)])
        last_date = last_act.get('created_at') if last_act else None

        profile_doc = {
            'user_id': uid,
            'weekly_km': weekly_km,
            'last_activity': last_date,
            'max_minutes_per_session': u.get('preferred_max_minutes', 120)
        }

        profiles.update_one({'user_id': uid}, {'$set': profile_doc}, upsert=True)

    return True


if __name__ == '__main__':
    ok = compute_user_profiles()
    print('profiles computed' if ok else 'failed')
