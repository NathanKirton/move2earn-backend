"""Simple test harness to exercise streak recording for a child.

Usage:
    python scripts/test_streaks.py <child_id> [date]

If date is omitted, today's UTC date is used. Date may be YYYY-MM-DD or ISO datetime.

This will call UserDB.record_daily_activity and print the result.

WARNING: This will modify the database (increment earned_game_time and daily limit).
"""
import sys
from database import UserDB

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_streaks.py <child_id> [date]")
        return
    child_id = sys.argv[1]
    date = None
    if len(sys.argv) >= 3:
        date = sys.argv[2]
    res = UserDB.record_daily_activity(child_id, activity_date=date, source='test')
    print('Result:', res)

if __name__ == '__main__':
    main()
