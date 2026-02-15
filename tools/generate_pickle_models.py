import os, pickle
ROOT = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# Simple dummy models with a predict method
class StreakModel:
    def predict(self, X):
        # If avg_duration>0 return 0 else 1 (risk)
        out = []
        for v in X:
            try:
                avg_duration = float(v[1])
            except Exception:
                avg_duration = 0
            out.append(0 if avg_duration>0 else 1)
        return out

class ChallengeModel:
    def predict(self, X):
        out = []
        for v in X:
            try:
                avg_distance = float(v[0])
            except Exception:
                avg_distance = 0
            if avg_distance >= 2.0:
                out.append('hard')
            elif avg_distance >= 1.0:
                out.append('medium')
            else:
                out.append('easy')
        return out

class MinutesModel:
    def predict(self, X):
        out = []
        for v in X:
            try:
                total_earned = float(v[6])
            except Exception:
                total_earned = 0
            # predict an int minutes
            pred = max(1, int(total_earned or 10))
            out.append(pred)
        return out

# Save models
with open(os.path.join(MODEL_DIR, 'streak_model.pkl'), 'wb') as f:
    pickle.dump(StreakModel(), f)
with open(os.path.join(MODEL_DIR, 'challenge_model.pkl'), 'wb') as f:
    pickle.dump(ChallengeModel(), f)
with open(os.path.join(MODEL_DIR, 'minutes_model.pkl'), 'wb') as f:
    pickle.dump(MinutesModel(), f)

print('Dummy pickle models written to', MODEL_DIR)
