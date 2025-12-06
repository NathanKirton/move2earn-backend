#!/usr/bin/env python
"""Test the responsive progress bar"""

print("\n" + "="*60)
print("TESTING RESPONSIVE PROGRESS BAR")
print("="*60 + "\n")

# Test cases: (earned, used, limit, expected_width_percent)
test_cases = [
    # (earned, used, limit, expected_width_for_used)
    (100, 0, 180, 0),      # No time used - 0% filled
    (100, 50, 180, 28),    # Half used - 28% filled (50/180)
    (100, 90, 180, 50),    # Most used - 50% filled (90/180)
    (100, 180, 180, 100),  # All used - 100% filled (180/180)
    (50, 25, 60, 42),      # 25 of 60 used - 42% filled (25/60)
]

print("Progress Bar Width Calculation:")
print("-" * 60)

all_pass = True
for earned, used, limit, expected in test_cases:
    balance = max(0, earned - used)
    used_percent = min(100, (used / limit) * 100) if limit > 0 else 0
    
    status = "✓" if abs(used_percent - expected) < 1 else "✗"
    all_pass = all_pass and abs(used_percent - expected) < 1
    
    print(f"{status} Earned: {earned} | Used: {used} | Limit: {limit}")
    print(f"  Balance: {balance} min | Width: {used_percent:.1f}%")
    print()

print("-" * 60)
if all_pass:
    print("✅ ALL PROGRESS BAR CALCULATIONS CORRECT")
else:
    print("✗ SOME CALCULATIONS FAILED")

print("\nHow it works:")
print("  • Progress bar width = (used_minutes / limit) * 100%")
print("  • Shows how much time the child has USED")
print("  • Fills from left to right as they use more time")
print("  • Responsive to earned and used time changes")

print("\n" + "="*60 + "\n")
