````markdown
# 🎁 Parent-Child Messaging System - Quick Reference

## ⚡ Quick Start

### Test the System in 3 Steps

1. **Create test accounts**
   ```bash
   python tools/setup_test_accounts.py
   ```

2. **Start the app**
   ```bash
   python app.py
   ```

3. **Login and test**
   - Parent: http://localhost:5000/login
     - Email: `parent@test.com`
     - Password: `parent123`
   - Child: http://localhost:5000/login
     - Email: `child@test.com`
     - Password: `child123`

---

## 📝 Parent Workflow

1. Login to Parent Dashboard
2. Find child in "Manage Your Children"
3. Enter bonus minutes (e.g., `30`)
4. Enter optional message (e.g., `"Great job at soccer!"`)
5. Click "Add Time"
6. See "✓ Sent!" confirmation

---

... (file continues — copied from root QUICK_START.md)

````
