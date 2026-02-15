class StreakModel:
    def predict(self, X):
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
            pred = max(1, int(total_earned or 10))
            out.append(pred)
        return out
