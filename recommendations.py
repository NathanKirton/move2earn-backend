from datetime import datetime, timedelta, date
from database import get_db
from embeddings import build_user_embeddings, query_similar_users


def get_today_activity(user_id):
    """Get activity summary for today using the 'date' field, not created_at."""
    db = get_db()
    if db is None:
        return None
    
    today_str = date.today().isoformat()  # Format: YYYY-MM-DD
    
    activities = db['activities']
    # Filter by 'date' field (the activity's actual date) not 'created_at' (insert time)
    today_acts = list(activities.find({
        'user_id': user_id,
        'date': today_str
    }))
    
    if not today_acts:
        return None
    
    total_dist = 0
    total_mins = 0
    act_types = []
    for a in today_acts:
        dist = a.get('distance') or a.get('distance_km') or a.get('distance_m') or 0
        try:
            d = float(dist)
            if d > 1000:
                d = d / 1000.0
            total_dist += d
        except:
            pass
        
        duration = a.get('moving_time') or a.get('duration') or 0
        try:
            total_mins += float(duration) // 60
        except:
            pass
        
        act_type = a.get('type') or a.get('sport_type') or 'Activity'
        if act_type not in act_types:
            act_types.append(act_type)
    
    return {
        'count': len(today_acts),
        'distance': round(total_dist, 2),
        'minutes': int(total_mins),
        'types': act_types
    }


def generate_intro_message(user_id, weekly_km, session_type):
    """Generate a contextual intro message for the recommendation that matches the session type."""
    today_act = get_today_activity(user_id)
    
    # Base messages depending on activity today and session type
    if today_act is None or today_act['count'] == 0:
        # No activity today
        if session_type == 'intervals':
            return "Build intensity today with a challenging interval session!"
        elif session_type == 'tempo':
            return "You're ready for a controlled tempo effort today."
        elif session_type == 'easy_run':
            return "Start your day with a relaxed, easy-paced session."
        elif session_type == 'recovery_walk':
            return "Your body has earned a recovery day - light movement only."
        else:
            return "Build the habit with some gentle movement today."
    else:
        # Has activity today
        types_str = ' and '.join(today_act['types'])
        activity_count = today_act['count']
        total_distance = today_act['distance']
        
        # Clarify distance info
        if activity_count == 1:
            distance_str = f"{total_distance}km"
        else:
            distance_str = f"{total_distance}km ({activity_count} activities)"
        
        # Match intro message to the actual session type being recommended
        if session_type == 'intervals':
            return f"Great work—you've covered {distance_str}! You're ready for a challenging interval workout."
        elif session_type == 'tempo':
            return f"Solid effort with {distance_str}! Let's maintain energy with a tempo session."
        elif session_type == 'easy_run':
            if total_distance > 15:
                return f"Impressive {distance_str} today! Time to recover with a relaxed easy session."
            else:
                return f"Nice session with {distance_str}! Add an easy session to round out your day."
        elif session_type == 'recovery_walk':
            return f"Fantastic work—you've covered {distance_str}! Your body needs recovery. A light walk is perfect."
        else:  # walk_or_easy
            return f"Getting started with {distance_str}? Perfect—let's build on this with a gentle activity."


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
    """Return a recommended session based on recent weekly load.
    
    Logic: Higher activity volume -> easier/recovery sessions. Lower volume -> more intense workouts.
    This ensures balanced training and prevents overtraining.

    Output format:
    {
      'type': 'easy_run',
      'duration_min': 30,
      'intro': 'Based on your recent activity...',
      'notes': 'Keep effort conversational.'
    }
    """
    weekly_km = get_weekly_distance(user_id)

    # Smart thresholds: high volume = recovery, low volume = build intensity
    if weekly_km >= 50:
        # Very high volume -> active recovery / rest day
        session = {
            'type': 'recovery_walk',
            'duration_min': 20,
            'structure': [
                {'type': 'easy walk or very light activity'}
            ],
            'notes': 'Take it easy today. Your body needs recovery to get stronger. Light activity only.'
        }
    elif weekly_km >= 35:
        # High volume -> easy session
        session = {
            'type': 'easy_run',
            'duration_min': 30,
            'structure': [
                {'type': 'easy, conversational pace'}
            ],
            'notes': 'You\'ve been very active! Easy session today to allow recovery.'
        }
    elif weekly_km >= 20:
        # Moderate volume -> balanced effort (tempo)
        session = {
            'type': 'tempo',
            'duration_min': 40,
            'structure': [{'tempo_min': 20}],
            'notes': '20 minutes at comfortably hard effort. Good middle ground.'
        }
    elif weekly_km >= 10:
        # Lower volume -> build intensity (intervals)
        session = {
            'type': 'intervals',
            'duration_min': 45,
            'structure': [
                {'repeat': 6, 'work_sec': 60, 'rest_sec': 90}
            ],
            'notes': '6 x 1min hard with 90s recovery. Warm up 15min, cool down 10min. Time to push!'
        }
    else:
        # Very low volume -> consistent easy building
        session = {
            'type': 'walk_or_easy',
            'duration_min': 20,
            'notes': 'Start building consistency: walk/run or steady walk. Focus on frequency over intensity.'
        }

    # Generate contextual intro message that matches the recommendation
    session['intro'] = generate_intro_message(user_id, weekly_km, session['type'])

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
