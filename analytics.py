import hashlib
from datetime import datetime
from database import get_db


def log_event(user_id, event_type, metadata=None):
    """Log an analytics event to `analytics.events` collection."""
    db = get_db()
    if db is None:
        return False
    if metadata is None:
        metadata = {}
    doc = {
        'user_id': user_id,
        'event_type': event_type,
        'metadata': metadata,
        'ts': datetime.utcnow()
    }
    db['analytics.events'].insert_one(doc)
    return True


def assign_variant(user_id, experiment_name, variants):
    """Deterministically assign a user to one of `variants` for experiment.

    - `variants` is list like ['control','treatment']
    - Returns selected variant
    """
    if not variants:
        raise ValueError('variants required')
    # stable hash of user+experiment
    key = f"{experiment_name}:{user_id}".encode('utf-8')
    h = hashlib.md5(key).hexdigest()
    n = int(h[:8], 16)
    idx = n % len(variants)
    return variants[idx]


def record_ab_outcome(user_id, experiment_name, outcome_name, variant=None):
    """Record an outcome (conversion) for a user in an experiment.

    If variant not provided, we attempt to infer assignment by hashing.
    """
    db = get_db()
    if db is None:
        return False
    if variant is None:
        # naive: assume two variants control/treatment if experiment exists
        # caller should provide variant when available
        variant = assign_variant(user_id, experiment_name, ['control', 'treatment'])

    doc = {
        'user_id': user_id,
        'experiment': experiment_name,
        'variant': variant,
        'outcome': outcome_name,
        'ts': datetime.utcnow()
    }
    db['analytics.outcomes'].insert_one(doc)
    return True


def compute_experiment_report(experiment_name):
    """Return a simple conversion report for an experiment grouped by variant.

    Output: { variant: {count: N, conversions: M, rate: M/N} }
    """
    db = get_db()
    if db is None:
        return {}
    # count exposures (events of type 'exposure') in analytics.events
    events = db['analytics.events']
    outcomes = db['analytics.outcomes']

    # find distinct user assignments by hashing when needed
    # We'll scan outcomes and events and aggregate by variant
    pipeline = [
        {'$match': {'event_type': 'ab_exposure', 'metadata.experiment': experiment_name}},
        {'$group': {'_id': '$metadata.variant', 'users': {'$addToSet': '$user_id'}, 'count': {'$sum': 1}}}
    ]
    agg = list(events.aggregate(pipeline))
    report = {}
    for r in agg:
        var = r['_id'] or 'unknown'
        users = r.get('users', [])
        cnt = len(users)
        conv = outcomes.count_documents({'experiment': experiment_name, 'variant': var})
        rate = conv / cnt if cnt else 0.0
        report[var] = {'count': cnt, 'conversions': conv, 'rate': rate}
    return report
