#!/usr/bin/env python
"""Stub placeholder — test moved to `tests/` directory.

Run the moved test with:

    python -m tests.test_streaks <child_id> [date]

This file remains to avoid breaking scripts that referenced it at the old path.
"""

print("This test has moved to ./tests/test_streaks.py")
print("Run it from the project root with: python -m tests.test_streaks <child_id> [date]")
"""Simple test harness to exercise streak recording for a child.

Usage:
    python -m tests.test_streaks <child_id> [date]

If date is omitted, today's UTC date is used. Date may be YYYY-MM-DD or ISO datetime.

This will call UserDB.record_daily_activity and print the result.

WARNING: This will modify the database (increment earned_game_time and daily limit).
"""
import sys
from database import UserDB

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_streaks <child_id> [date]")
        return
    child_id = sys.argv[1]
    date = None
    if len(sys.argv) >= 3:
        date = sys.argv[2]
    res = UserDB.record_daily_activity(child_id, activity_date=date, source='test')
    print('Result:', res)

if __name__ == '__main__':
    main()
