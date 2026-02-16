import traceback
from recommendations import recommend

uid = '69930cff377b3cfab105ffb5'
print('Calling recommend for', uid)
try:
    rec = recommend(uid)
    print('Recommend returned:', rec)
except Exception:
    traceback.print_exc()
