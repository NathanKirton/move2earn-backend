import os, pickle, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
MODEL_DIR = os.path.join(ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

from models.dummy_models import StreakModel, ChallengeModel, MinutesModel

# Save models (instances from importable module so pickle can load them later)
with open(os.path.join(MODEL_DIR, 'streak_model.pkl'), 'wb') as f:
    pickle.dump(StreakModel(), f)
with open(os.path.join(MODEL_DIR, 'challenge_model.pkl'), 'wb') as f:
    pickle.dump(ChallengeModel(), f)
with open(os.path.join(MODEL_DIR, 'minutes_model.pkl'), 'wb') as f:
    pickle.dump(MinutesModel(), f)

print('Dummy pickle models written to', MODEL_DIR)
