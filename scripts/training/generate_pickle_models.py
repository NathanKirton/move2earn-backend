import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODEL_DIR = ROOT / 'models'
MODEL_DIR.mkdir(exist_ok=True)

from models.dummy_models import StreakModel, ChallengeModel, MinutesModel

# Save models (instances from importable module so pickle can load them later)
with open(MODEL_DIR / 'streak_model.pkl', 'wb') as f:
    pickle.dump(StreakModel(), f)
with open(MODEL_DIR / 'challenge_model.pkl', 'wb') as f:
    pickle.dump(ChallengeModel(), f)
with open(MODEL_DIR / 'minutes_model.pkl', 'wb') as f:
    pickle.dump(MinutesModel(), f)

print('Dummy pickle models written to', MODEL_DIR)
