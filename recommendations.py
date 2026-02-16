from datetime import datetime, timedelta
from database import get_db
from embeddings import build_user_embeddings, query_similar_users


def get_weekly_distance(user_id):
    db = get_db()
    if db is None:
        return 0

    activities = db['activities']
    week_ago = datetime.utcnow() - timedelta(days=7)
    total = 0
    for a in activities.find({'user_id': user_id, 'created_at': {'$gte': week_ago}}):
        # activities may store distance in metres or km; try common keys
        dist = a.get('distance') or a.get('distance_km') or a.get('distance_m')
        try:
            if dist is None:
                continue
            # normalize: if >1000 assume metres -> km
            d = float(dist)
            if d > 1000:
                d = d / 1000.0
            total += d
        except Exception:
            continue
    return total


def rule_based_session(user_id, user_profile=None):
    """Return a simple recommended session based on recent weekly load.

    Output format:
    {
      'type': 'easy_run',
      'duration_min': 30,
      'notes': 'Keep effort conversational.'
    }
    """
    weekly_km = get_weekly_distance(user_id)

    # basic thresholds
    if weekly_km >= 50:
        # high-volume athlete -> maintain or do intervals
        session = {
            'type': 'intervals',
            'duration_min': 45,
            'structure': [
                {'repeat': 6, 'work_sec': 60, 'rest_sec': 90}
            ],
            'notes': '6 x 1min hard with 90s recovery. Warm up 15min, cool down 10min.'
        }
    elif weekly_km >= 20:
        session = {
            'type': 'tempo',
            'duration_min': 40,
            'structure': [{'tempo_min': 20}],
            'notes': '20 minutes at comfortably hard effort.'
        }
    elif weekly_km >= 5:
        session = {
            'type': 'easy_run',
            'duration_min': 30,
            'notes': 'Easy conversational pace to build consistency.'
        }
    else:
        session = {
            'type': 'walk_or_easy',
            'duration_min': 20,
            'notes': 'Start gently: walk/run or steady walk to build habit.'
        }

    # add a safety cap
    if user_profile:
        max_minutes = user_profile.get('max_minutes_per_session')
        if max_minutes:
            session['duration_min'] = min(session['duration_min'], max_minutes)

    return session


def recommend(user_id, constraints=None):
    # constraints could include preferred_session (run/walk), max_duration, goal
    # load lightweight profile
    db = get_db()
    profile = None
    if db is not None:
        profile = db['user_profiles'].find_one({'user_id': user_id})
    # If we have enough users, try personalization via embeddings
    try:
        emb_index = build_user_embeddings()
        if emb_index:
            similar = query_similar_users(user_id, emb_index, topk=3)
            # If similar users exist and this user has low weekly km, prefer sessions similar users accept
            if similar:
                # simple heuristic: if similar users have higher weekly_km, suggest slightly harder session
                sim_kms = []
                for s in similar:
                    p = db['user_profiles'].find_one({'user_id': s})
                    if p:
                        sim_kms.append(p.get('weekly_km', 0))
                if sim_kms:
                    avg_sim = sum(sim_kms)/len(sim_kms)
                    # bump thresholds by 50% of difference
                    # create an adjusted profile copy
                    if profile is None:
                        profile = {'max_minutes_per_session': 120}
                    profile_adjusted = dict(profile)
                    # if similar users run more, increase recommended duration
                    if avg_sim > (profile.get('weekly_km', 0)):
                        profile_adjusted['max_minutes_per_session'] = min(180, profile_adjusted.get('max_minutes_per_session',120) + 15)
                    return rule_based_session(user_id, profile_adjusted)
    except Exception:
        pass

    return rule_based_session(user_id, profile)
