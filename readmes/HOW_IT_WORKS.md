# How Move2Earn Works — Complete Technical Overview

## 🎯 What is Move2Earn?

Move2Earn is a **parent-child game time management system** that rewards children with earned gaming minutes based on physical activities tracked via the Strava API. Parents set rules and screen time limits; children earn minutes by running, cycling, swimming, or other activities; and the system automatically calculates rewards, maintains streaks, and manages screen time balances.

---

## 📊 Architecture Overview

### Microservice Architecture

Move2Earn Backend is designed as a **self-contained microservice** that operates independently while integrating with external services. This microservice-oriented approach provides several benefits:

- **Single Responsibility:** Focuses solely on parent-child game-time management logic
- **Independent Deployment:** Can be deployed, scaled, and updated without affecting other services
- **API-First Design:** Exposes REST endpoints consumed by various clients (web, mobile, etc.)
- **Decoupled from Frontend:** Frontend is static (IONOS) and communicates only via REST APIs
- **Composable:** Can be combined with other microservices (e.g., payment processing, notifications) in the future

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend Layer (Static Site - IONOS)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Landing Page (HTML/CSS/JS)                          │   │
│  │  • Marketing & onboarding content                    │   │
│  │  • Login/Register redirects                          │   │
│  └──────────────────────────────────────────────────────┘   │
│               ↓↑ HTTP REST API Calls                         │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌──────────────────────────────────────────────────────────────┐
│                 MOVE2EARN MICROSERVICE                       │
│            (Backend API - Render Hosted)                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  API Gateway / Entry Point                            │  │
│  │  • All requests routed through REST endpoints         │  │
│  │  • CORS enabled for cross-origin requests             │  │
│  │  • Request validation & authentication                │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Web Browser (Client)                                 │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  HTML Templates (Jinja2)                         │ │  │
│  │  │  • register.html / login.html (auth)             │ │  │
│  │  │  • dashboard.html (child view)                   │ │  │
│  │  │  • parent_dashboard.html (control center)        │ │  │
│  │  │  • upload_activity.html (manual entry)           │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Application Logic (Flask + Python)                   │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  app.py — Route Handlers                         │ │  │
│  │  │  • /login, /register (authentication)            │ │  │
│  │  │  • /dashboard, /parent-dashboard (views)         │ │  │
│  │  │  • /api/* (REST endpoints for all operations)    │ │  │
│  │  │  • /callback (OAuth Strava integration)          │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  database.py — Business Logic & Data Access      │ │  │
│  │  │  • UserDB class (encapsulates all DB ops)        │ │  │
│  │  │  • Game time calculation engine                  │ │  │
│  │  │  • Streak computation & validation               │ │  │
│  │  │  • Authentication & authorization                │ │  │
│  │  │  • Message management                            │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  Session Management (Flask-Session)              │ │  │
│  │  │  • Server-side session storage                   │ │  │
│  │  │  • HTTP cookie-based session tracking            │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│               ↓↑ PyMongo Driver                               │
└──────────────────────────────────────────────────────────────┘
                            ↓↑
┌──────────────────────────────────────────────────────────────┐
│  Data Layer (Shared Resource)                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  MongoDB Atlas (Cloud Database)                        │  │
│  │  • users: parent & child account data                  │  │
│  │  • activities: activity records & streak history       │  │
│  │  • Authoritative source of truth                       │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
            ↓↑ (Writes)    ↓↑ (Reads via API)
┌──────────────────────────────────────────────────────────────┐
│  External Microservices & APIs                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Strava API (OAuth v3)                                │  │
│  │  • Activity data ingestion                            │  │
│  │  • OAuth 2.0 flow for user authorization              │  │
│  │  • Activity sync & enrichment                         │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Deployment Environment (Render)                             │
│  • Containerized with Docker (Python 3.11-slim)             │
│  • Gunicorn WSGI server (multi-worker HTTP handling)        │
│  • Auto-deployment on git push (CI/CD via webhook)          │
│  • Environment isolation (separate secrets management)       │
│  • Horizontal scaling ready (stateless design)              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Microservice Design Principles

The Move2Earn Backend is built as a **true microservice** following these principles:

### 1. **Single Responsibility**
- **One Job:** Manages parent-child game-time relationships and activity rewards
- **Not Responsible For:** Email notifications, payment processing, analytics dashboards, etc.
- **Clean Boundaries:** If new requirements emerge (e.g., notifications), they can be added as separate microservices

### 2. **Independent Deployment**
- **No Coupled Releases:** Backend updates don't require frontend redeployment
- **Render Auto-Deploy:** Changes to `master` branch trigger automated deployment
- **Zero-Downtime:** Gunicorn allows rolling updates with multiple worker processes
- **Rollback Ready:** Git history enables quick reverts if issues arise

### 3. **API-First Design**
- **REST Endpoints:** All functionality exposed as HTTP APIs (not server-side pages only)
- **Content Negotiation:** APIs return JSON for programmatic consumption, HTML for browsers
- **Stateless Routes:** Each request is independent; no cross-request coupling
- **Extensible:** New clients (mobile app, admin portal, third-party integrations) can use the same APIs

**API Endpoint Categories:**
```
Authentication:
  POST /register          # Create new user (parent or child)
  POST /login             # Authenticate and create session
  POST /logout            # End session

Child Dashboard:
  GET  /dashboard         # Render child dashboard (Jinja2)
  GET  /api/get-parent-messages  # Fetch messages (JSON)
  POST /api/record-activity      # Log activity and earn time

Parent Dashboard:
  GET  /parent-dashboard  # Render parent dashboard (Jinja2)
  POST /api/add-child     # Create new child account
  POST /api/add-earned-time/<child_id>  # Grant bonus time
  POST /api/update-child-limits/<child_id>  # Set daily/weekly limits
  GET  /api/child-summary/<child_id>   # Get child stats

Strava Integration:
  GET  /strava-auth       # Initiate OAuth flow
  GET  /callback          # OAuth callback handler
  GET  /api/activities    # Fetch Strava activities

System:
  GET  /health            # Health check (for load balancers)
  GET  /api/athlete       # Current authenticated user info
```

### 4. **Loose Coupling, High Cohesion**
- **Loose Coupling:** Depends only on Strava API and MongoDB; can be replaced independently
- **High Cohesion:** All game-time logic lives in one codebase (`database.py` UserDB class)
- **Clear Interfaces:** Public functions in `database.py` define the contract; internal implementation can change

### 5. **Horizontal Scalability**
- **Stateless Design:** Flask app holds no session memory; sessions stored server-side in filesystem (or can use Redis)
- **Multi-Worker:** Gunicorn runs multiple worker processes to handle concurrent requests
- **Database-Backed:** All persistent data in MongoDB, not in-memory
- **Ready for Load Balancing:** Multiple instances of the microservice can run behind a load balancer

### 6. **Technology Agnostic**
- **Clear Contracts:** Other services interact via HTTP/REST, not tight coupling
- **Implementation Hidden:** Frontend doesn't care if backend uses Flask/Python or Node.js/TypeScript
- **Replaceable:** Backend could be rewritten in Go, Rust, or Java without breaking clients

### 7. **Separation of Concerns**

**Frontend (IONOS - Static)**
- Serves landing page, login/register UI
- Makes HTTP calls to backend
- No backend logic or database access

**Backend Microservice (Render)**
- Handles all business logic (game time, streaks, messages)
- Manages sessions and authentication
- Integrates with Strava for activity data
- Provides REST APIs for all operations

**Database (MongoDB Atlas)**
- Single source of truth
- Accessed only via microservice (not directly by frontend)
- Ensures data consistency

**External APIs (Strava)**
- Provides activity data
- Microservice acts as client, not exposed to frontend

---

## 🔐 Account System & Parent-Child Linking

### User Types

Move2Earn supports two account types:

#### **Parent/Guardian Account**
- Created during registration with `is_parent=True`
- Has email, password, full name
- Can create and manage multiple child accounts
- Access to parent dashboard with controls and analytics

#### **Child Account**
- Created by parent through parent dashboard or API
- Inherits parent's email domain but has unique email
- Has email, password, full name
- Cannot create other child accounts
- Access to child dashboard with activity tracking

### How Linking Works

```
Parent Account (parent@example.com)
    │
    ├─→ Child 1 (child1@example.com)
    │   └─ parent_id = parent@example.com
    │   └ game_time tracking
    │
    └─→ Child 2 (child2@example.com)
        └─ parent_id = parent@example.com
        └ game_time tracking
```

**Database Schema (Simplified):**
```javascript
// Parent user document
{
  "_id": ObjectId("..."),
  "email": "parent@example.com",
  "password": "bcrypt_hash_...",
  "name": "John Parent",
  "account_type": "parent",
  "children": ["child1@example.com", "child2@example.com"],
  "created_at": ISODate("2025-12-09...")
}

// Child user document
{
  "_id": ObjectId("..."),
  "email": "child1@example.com",
  "password": "bcrypt_hash_...",
  "name": "Emma",
  "account_type": "child",
  "parent_id": "parent@example.com",
  "earned_game_time": 120,          // Total minutes earned
  "used_game_time": 45,             // Minutes already spent
  "daily_screen_time_limit": 60,    // Parent-set daily limit
  "weekly_screen_time_limit": 300,  // Parent-set weekly limit
  "strava_connected": true,
  "strava_access_token": "...",
  "strava_refresh_token": "...",
  "activity_streak": 5,             // Consecutive days active
  "last_activity_date": "2025-12-08",
  "parent_messages": [
    {
      "from_parent": "John Parent",
      "message": "Great job!",
      "bonus_minutes": 30,
      "timestamp": ISODate("2025-12-09T10:30:00Z"),
      "read": false
    }
  ],
  "created_at": ISODate("2025-12-09...")
}
```

---

## 🔄 User Flow & Authentication

### Registration Flow

```
User visits /register
    ↓
Fills form:
  • Email
  • Password (bcrypt hashed)
  • Full Name
  • [Optional] Check "I am a Parent" checkbox
    ↓
System validates:
  • Email doesn't exist
  • Password strength
    ↓
Creates user document in MongoDB
    ↓
Redirects to /login
```

**Code Reference:** `app.py` route `/register`

### Login Flow

```
User visits /login
    ↓
Submits email + password
    ↓
System:
  1. Fetches user by email (MongoDB)
  2. Compares password with bcrypt hash
  3. Checks account_type (parent or child)
    ↓
Sets Flask session cookie (session['user_id'])
    ↓
Redirects to appropriate dashboard:
  • Parent → /parent-dashboard
  • Child → /dashboard
```

**Code Reference:** `app.py` route `/login`, `database.py` `UserDB.find_user()`

### Session Management

- **Flask-Session:** Server-side session storage (filesystem)
- **Session ID:** Stored in HTTP cookies
- **Timeout:** Configurable (default: session lifetime)
- **Protected Routes:** Require valid session before accessing dashboard/API

---

## 💪 Activity Tracking & Game Time Calculation

### How Activities Generate Game Time

#### **Method 1: Manual Upload**
Child can manually log an activity via `/upload-activity`:
- Activity title
- Distance (km)
- Activity type (Running, Cycling, Swimming, etc.)
- Intensity level (Easy, Medium, Hard)

**Formula:**
```
Earned Game Time = Distance (km) × Intensity Multiplier

Where:
  Easy    = 1.0x multiplier
  Medium  = 1.5x multiplier
  Hard    = 2.0x multiplier

Example: 10 km Medium intensity activity
  = 10 × 1.5 = 15 minutes earned
```

#### **Method 2: Strava Integration**
Child connects their Strava account via OAuth:
1. Child clicks "Connect to Strava"
2. Redirected to Strava OAuth consent screen
3. Strava returns access/refresh tokens
4. System pulls recent activities from Strava API
5. Calculates game time based on distance

**Code Reference:** `app.py` routes `/strava-auth`, `/callback`, `/api/activities`

### Server-Side Game Time Logic

All game time calculations happen in `database.py` method `UserDB.record_daily_activity()`:

```python
def record_daily_activity(child_id, distance_km, intensity='medium', 
                         activity_type='Running', activity_date=None):
    """
    Calculate game time and update streak.
    
    1. Parse activity date (use today if not provided)
    2. Check if this is a new day vs. duplicate
    3. Calculate game time = distance × intensity multiplier
    4. Check streak continuation (is today consecutive after yesterday?)
    5. If streak continues: apply streak bonus multiplier
    6. Update user document: earned_game_time, activity_streak, last_activity_date
    """
```

**Why server-side?**
- Prevents cheating (client can't modify multipliers)
- Ensures consistency (no race conditions)
- Authoritative source of truth (single calculation logic)

---

## 🔥 Streak System (Consecutive Day Rewards)

### How Streaks Work

A **streak** is the number of consecutive days a child has been active:

```
Dec 5: Run 5km     → streak = 1
Dec 6: Cycle 10km  → streak = 2
Dec 7: No activity → streak = 0 (broken)
Dec 8: Swim 2km    → streak = 1 (resets)
Dec 9: Run 8km     → streak = 2
```

### Streak Bonus Calculation

As streaks get longer, rewards increase:

```javascript
Streak Bonus Multiplier:
  Days 1-2: 1.0x (no bonus)
  Days 3-5: 1.2x (20% bonus)
  Days 6+:  1.5x (50% bonus)

Example: 10 km Medium intensity, Day 5 of streak
  Base: 10 × 1.5 = 15 minutes
  With Streak Bonus: 15 × 1.2 = 18 minutes earned
```

**Code Reference:** `database.py` `record_daily_activity()` method, streak multiplier logic

### Why Streaks Matter

- **Motivation:** Encourages consistent daily activity
- **Health:** Promotes regular exercise habits
- **Escalating Rewards:** Greater rewards for dedication (compound effect)

---

## 👨‍👩‍👧 Parent Dashboard Features

Parents have a control center (`parent_dashboard.html`) where they can:

### 1. **Add Child Accounts**
```
Form:
  - Child's Name
  - Child's Email
  - Child's Password

Action: Creates child user document + links to parent
```

### 2. **View Child Game Time**
For each child, display:
- **Earned (min):** Total minutes earned from activities
- **Used (min):** Total minutes spent on gaming
- **Balance:** Remaining minutes available (earned - used)

### 3. **Set Screen Time Limits**
```javascript
Daily Limit: 60 minutes/day
Weekly Limit: 300 minutes/week
```
Parents can set and modify these; system enforces them.

### 4. **Grant Bonus Time**
```
Form:
  - Minutes to award (e.g., 30)
  - Optional message (e.g., "Great job on your soccer game!")

Action:
  - Adds minutes to child's earned_game_time
  - Stores message in child's parent_messages array
  - Appears on child dashboard in real-time
```

**Code Reference:** `app.py` `/api/add-earned-time/<child_id>`, `parent_dashboard.html` JavaScript

---

## 👧 Child Dashboard Features

Children view their personal dashboard (`dashboard.html`) with:

### 1. **Game Time Card**
- Displays earned, used, and balance
- Real-time updates
- Visual progress bar

### 2. **Recent Activities**
- List of manually uploaded activities OR Strava-synced activities
- Activity type, distance, date, earned minutes

### 3. **Activity Streak**
- Current consecutive day count
- Visual indicator (badge)
- Next streak milestone bonus

### 4. **Messages from Parent**
- Section showing all messages with timestamps
- Green badge showing bonus minutes awarded with each message
- "No messages yet" placeholder if empty

### 5. **Strava Connection (Optional)**
- Button to connect/disconnect Strava
- Auto-sync toggle

**Code Reference:** `dashboard.html`, `/api/activities`, `/api/get-parent-messages`

---

## 🛠️ Technologies & Frameworks

### **Backend: Flask (Python Web Framework)**

**What it does:**
- Handles HTTP routing (map URLs to Python functions)
- Manages sessions (Flask-Session)
- Renders HTML templates (Jinja2)
- Handles form submissions and API requests

**Why Flask?**
- Lightweight (not over-engineered)
- Quick development cycles
- Excellent template engine (Jinja2)
- Easy to deploy (Render supports Python)

**Key Flask Extensions:**
- `Flask-CORS`: Cross-Origin Resource Sharing (APIs accessible from frontend)
- `Flask-Session`: Server-side session management
- `Werkzeug`: Secure file uploads, utility functions

**Code:** `app.py` (main Flask app definition and route handlers)

---

### **Database: MongoDB (NoSQL Document Database)**

**What it does:**
- Stores user documents (parent/child accounts)
- Stores activity records
- Stores streak data, messages, settings

**Why MongoDB?**
- **Flexible schema:** Can add new fields without migrations
- **Scalability:** Horizontal scaling for growth
- **Cloud hosting:** MongoDB Atlas (managed service)
- **JSON-like documents:** Maps naturally to Python dicts

**How PyMongo works:**
```python
from pymongo import MongoClient

client = MongoClient(MONGODB_URI)  # Connect to Atlas
db = client[MONGODB_DB_NAME]       # Select database
users = db['users']                # Get collection

# Insert a document
users.insert_one({'email': 'test@example.com', 'name': 'Test'})

# Find a document
user = users.find_one({'email': 'test@example.com'})

# Update a document
users.update_one(
    {'email': 'test@example.com'},
    {'$set': {'earned_game_time': 150}}
)
```

**Code:** `database.py` (all MongoDB operations via PyMongo)

---

### **Authentication & Security: bcrypt**

**What it does:**
- Hashes passwords irreversibly (one-way encryption)
- Salts hashes to prevent rainbow table attacks
- Compares plaintext password with hash during login

**Why bcrypt?**
- Industry standard (OWASP recommended)
- Slow by design (resistant to brute force)
- Built-in salt handling

**Flow:**
```python
# Registration
password = "MySecurePassword123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
# Store hashed in database

# Login
provided_password = "MySecurePassword123"
is_valid = bcrypt.checkpw(provided_password.encode(), stored_hash)
# Returns True/False
```

**Code:** `database.py` functions `hash_password()`, `verify_password()`

---

### **OAuth: Strava API Integration**

**What it does:**
- Allows children to authorize Move2Earn to access their Strava activities
- Strava returns access tokens
- System uses tokens to fetch activities on demand

**OAuth 2.0 Flow:**
```
1. Child clicks "Connect to Strava"
   ↓
2. Redirected to Strava login (strava.com)
   ↓
3. Child authorizes Move2Earn to read activities
   ↓
4. Strava redirects back to our /callback endpoint
   with authorization code
   ↓
5. Backend exchanges code for access token + refresh token
   ↓
6. Tokens stored in database (encrypted credentials)
   ↓
7. System can now fetch child's activities from Strava
```

**Token Refresh:**
- Access tokens expire (typically 6 hours)
- System uses refresh token to get new access token
- Automatic refresh before API calls

**Code:** `app.py` routes `/strava-auth`, `/callback`, functions `get_strava_access_token()`, `get_user_strava_headers()`

---

### **Templating: Jinja2**

**What it does:**
- Renders HTML with dynamic data from Python
- Variables, loops, conditionals, filters

**Example:**
```html
<!-- templates/dashboard.html -->
<div class="game-time-card">
  <h2>Game Time Balance</h2>
  <p>Earned: {{ earned_time }} minutes</p>
  <p>Used: {{ used_time }} minutes</p>
  <p>Balance: {{ balance }} minutes</p>
  
  {% for message in parent_messages %}
    <div class="message">
      <p>{{ message.from_parent }}: {{ message.message }}</p>
    </div>
  {% endfor %}
  
  {% if not parent_messages %}
    <p>No messages yet.</p>
  {% endif %}
</div>
```

**Code:** All HTML files in `templates/` directory

---

### **Hosting: Render (Cloud Platform)**

**What it does:**
- Runs your Flask app 24/7 on the internet
- Auto-deploys on git push
- Manages environment variables
- Provides HTTPS certificates (security)

**Microservice Deployment Benefits:**
- **Isolated Environment:** Backend runs independently from frontend; frontend outages don't affect backend
- **Automatic Scaling:** Render can spawn multiple instances of this microservice based on traffic
- **Environment Management:** Different configs for dev/staging/prod without code changes
- **API-Ready:** Microservice is built to be consumed by multiple clients

**Render Setup:**
```yaml
Service: move2earn-backend
Runtime: Docker (Python 3.11-slim)
Build Command: pip install -r requirements.txt
Start Command: gunicorn wsgi:app
Environment Variables:
  - MONGODB_URI
  - MONGODB_DB_NAME
  - FLASK_SECRET_KEY
  - STRAVA_CLIENT_ID
  - STRAVA_CLIENT_SECRET
  - RENDER_EXTERNAL_URL (auto-set)
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:10000"]
```

**Why Render for Microservices?**
- Simple to use
- Automatic HTTPS
- Git-based deployment (CI/CD)
- Free tier available
- Supports containers (Docker) for advanced deployments
- Environment variable management (secrets)
- Can scale to multiple instances

**Code:** `Dockerfile`, `.render.yaml` (if present)

---

### **HTTP Server: Gunicorn (WSGI)**

**What it does:**
- Runs Flask app in production (not Flask's dev server)
- Handles multiple concurrent requests via worker processes
- Listens on port 10000 (Render standard)

**Why Gunicorn?**
- Production-grade HTTP server
- Thread/process pool for concurrency
- Supports keepalive and pipelining

**Command:**
```bash
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:10000
```

---

### **Frontend: Vanilla JavaScript (No Framework)**

**What it does:**
- Handles client-side interactions
- API calls to Flask backend
- Real-time UI updates (game time counters, streak displays)

**Example:**
```javascript
// dashboard.html
async function loadParentMessages() {
  const response = await fetch('/api/get-parent-messages');
  const data = await response.json();
  
  if (data.messages && data.messages.length > 0) {
    data.messages.forEach(msg => {
      const div = document.createElement('div');
      div.className = 'message-item';
      div.innerHTML = `
        <p><strong>${msg.from_parent}:</strong> ${msg.message}</p>
        <span class="bonus">+${msg.bonus_minutes} min</span>
      `;
      messagesContainer.appendChild(div);
    });
  }
}

// Parent dashboard
document.getElementById('add-time-btn').addEventListener('click', async () => {
  const minutes = document.getElementById('minutes').value;
  const message = document.getElementById('message').value;
  
  const response = await fetch(`/api/add-earned-time/${childId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ minutes, message })
  });
  
  if (response.ok) {
    alert('Time added!');
  }
});
```

---

## 🚀 Complete Request-Response Lifecycle

### **Example: Child Logs Manual Activity**

```
User Action: Child fills form and clicks "Upload Activity"
  ↓
FRONTEND (browser):
  • Validates form (distance, type, intensity)
  • Sends POST request to /api/record-activity
  • Payload: { distance: 10, type: "Running", intensity: "medium" }
  ↓
FLASK BACKEND (app.py):
  • Route: @app.route('/api/record-activity', methods=['POST'])
  • Extract user from session['user_id']
  • Validate request (user is child, not parent)
  • Call: UserDB.record_daily_activity(child_id, distance, intensity)
  ↓
DATABASE LAYER (database.py):
  • Parse activity date
  • Calculate game time = 10 × 1.5 = 15 minutes
  • Check streak (consecutive days?)
  • Apply streak bonus if applicable
  • MongoDB update: earned_game_time += 15, last_activity_date = today
  ↓
RESPONSE:
  • Return JSON: { success: true, earned: 15, new_balance: 125 }
  ↓
FRONTEND (browser):
  • Display success message: "You earned 15 minutes!"
  • Reload game time card with new balance (125)
  • Show updated streak count
```

---

## 📊 Data Flow Summary

### **Write Path (Activity Recording)**
```
Child Dashboard Form
  → POST /api/record-activity
    → Flask validates session
      → database.py: record_daily_activity()
        → MongoDB: update earned_game_time
          → Return success response
            → JavaScript updates UI
```

### **Read Path (Display Game Time)**
```
Child Dashboard Load
  → GET /dashboard (Jinja2 renders template)
    → Flask queries current user from session
      → database.py: get_user()
        → MongoDB: fetch user document
          → Jinja2 inserts data into HTML
            → Browser displays game time card
```

### **Parent-Child Communication**
```
Parent Dashboard
  → POST /api/add-earned-time/<child_id>
    → Flask validates parent is owner
      → database.py: add_earned_game_time() + add_parent_message()
        → MongoDB: update child's earned_game_time + parent_messages array
          ↓
Child Dashboard
  → GET /api/get-parent-messages
    → Flask queries current user from session
      → database.py: get_parent_messages()
        → MongoDB: fetch parent_messages array
          → Return JSON to frontend
            → JavaScript displays messages with timestamps
```

---

## 🔒 Security Measures

1. **Password Hashing:** bcrypt (irreversible, salted)
2. **Session Management:** Server-side Flask sessions (not JWT)
3. **CORS:** Limited to necessary endpoints
4. **Input Validation:** Server-side checks on all API endpoints
5. **Authorization:** Verify user owns child account before allowing modifications
6. **OAuth Tokens:** Stored securely in database, refreshed automatically
7. **HTTPS:** Render provides SSL/TLS certificates
8. **Environment Variables:** Sensitive data (API keys, DB URI) never in code

---

## 🎓 Summary Table

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python Flask | HTTP routing, session management, business logic |
| **Database** | MongoDB Atlas | Document storage (users, activities, messages) |
| **Authentication** | bcrypt | Password hashing & verification |
| **External API** | Strava OAuth v3 | Activity ingestion & user authorization |
| **Hosting** | Render | Cloud deployment, auto-scaling, HTTPS |
| **HTTP Server** | Gunicorn WSGI | Production-grade request handling |
| **Templates** | Jinja2 | Server-rendered HTML with dynamic data |
| **Frontend** | Vanilla JavaScript | Client-side interactions & API calls |
| **Session** | Flask-Session | Server-side session storage |
| **Password Security** | bcrypt + salt | One-way hashing, brute-force resistant |

---

## 🔗 File Structure Reference

```
move2earn-backend/
├── app.py                        # Flask routes & handlers
├── database.py                   # MongoDB operations (UserDB class)
├── wsgi.py                       # Gunicorn entry point
├── Dockerfile                    # Container configuration
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (local dev)
├── templates/                    # HTML Jinja2 templates
│   ├── landing.html              # Public landing page
│   ├── login.html                # Login form
│   ├── register.html             # Registration form
│   ├── dashboard.html            # Child dashboard
│   ├── parent_dashboard.html     # Parent control center
│   └── upload_activity.html      # Manual activity form
├── static/                       # CSS, JS, images
│   ├── styles.css                # Global styles
│   └── logo.svg                  # Brand logo
├── tests/                        # Test scripts
│   ├── test_messaging.py         # Parent-child messaging tests
│   ├── test_parent_auth.py       # Parent account tests
│   └── ... (other test scripts)
├── tools/                        # Maintenance & diagnostic scripts
│   ├── setup_test_accounts.py    # Create test accounts
│   ├── reset_times.py            # Reset game times
│   └── diagnose_users.py         # Debug user accounts
└── readmes/                      # Documentation
    ├── README.md                 # Project overview
    ├── README_DEVELOPMENT.md     # Development decisions
    ├── PARENT_GUIDE.md           # Parent user guide
    ├── MESSAGING_GUIDE.md        # Messaging system docs
    └── HOW_IT_WORKS.md          # This file!
```

---

## 🚀 Microservice Scaling & Evolution

### Current Architecture (Today)
```
Single Monolithic Microservice (move2earn-backend)
├─ All business logic
├─ User management
├─ Game time calculations
├─ Session handling
└─ Strava integration

Supporting Services:
├─ MongoDB (shared data layer)
├─ Render (hosting/deployment)
├─ Strava API (external)
└─ IONOS Static (frontend)
```

### Future Evolution Path

As the platform grows, the microservice can be decomposed further:

#### **Phase 2: Notifications Microservice**
```
Notifications Service (separate microservice)
├─ Email notifications (achievement milestones)
├─ Push notifications (mobile)
└─ SMS alerts (parent-requested)

Move2Earn Backend (core service)
├─ Publishes events to message queue
│  └─ "activity_recorded", "streak_achieved", etc.
└─ Notifications Service subscribes to events
```

#### **Phase 3: Analytics Microservice**
```
Analytics Service
├─ Activity aggregation
├─ Trend analysis
├─ Usage metrics
└─ Dashboards for parents/children

Communication: Event bus or direct API calls
```

#### **Phase 4: Payment Processing Microservice**
```
Payments Service
├─ In-app purchases
├─ Subscription management
├─ Premium features
└─ Refund handling

Move2Earn Backend calls Payments API for billing
```

### Why Microservices Architecture?

| Benefit | Impact |
|---------|--------|
| **Independent Scaling** | Notifications service can scale separately when users spike; core service unaffected |
| **Technology Freedom** | Notifications could be Node.js, Analytics could be Python, Payments could be Go |
| **Fault Isolation** | If notifications fail, core game-time logic still works |
| **Team Autonomy** | Different teams can own different microservices independently |
| **Rapid Iteration** | New features (e.g., leaderboards) added as new services without touching core |
| **Cost Optimization** | Scale expensive services (notifications) separately from cheap ones (core logic) |

### Deployment at Scale

**Current Single Microservice:**
```
┌────────────────────────┐
│  GitHub (master push)  │
└────────┬───────────────┘
         │
         ↓ (Webhook)
┌────────────────────────┐
│  Render Build & Deploy │
├────────────────────────┤
│  Instance 1 (gunicorn) │
│  Instance 2 (gunicorn) │  ← Load balanced
│  Instance 3 (gunicorn) │
└──────────┬─────────────┘
           │
           ↓
┌────────────────────────┐
│  MongoDB Atlas         │
└────────────────────────┘
```

**Future Multi-Microservice:**
```
┌────────────────────────┐
│  GitHub (multiple)     │
├────────────────────────┤
│  move2earn-core        │
│  notifications-service │
│  analytics-service     │
│  payments-service      │
└────────┬───────────────┘
         │
         ↓ (Webhooks per repo)
┌─────────────────────────────────────────┐
│  Render Deployments                     │
├─────────────────────────────────────────┤
│  Core Service                           │
│  ├─ Instance 1  ├─ Instance 2           │
│  └─ Instance 3                          │
│                                         │
│  Notifications Service                  │
│  ├─ Instance 1  ├─ Instance 2           │
│  └─ Instance 3  ├─ Instance 4           │
│                                         │
│  Analytics Service                      │
│  └─ Instance 1                          │
│                                         │
│  Payments Service                       │
│  ├─ Instance 1  ├─ Instance 2           │
│  └─ Instance 3                          │
└──────────┬────────────────────────────┬─┘
           │                            │
           ↓                            ↓
┌─────────────────────┐  ┌──────────────────────┐
│  MongoDB Atlas      │  │  Message Queue       │
│  (Shared Data)      │  │  (Event Bus)         │
└─────────────────────┘  └──────────────────────┘
```

### Communication Between Microservices

**Synchronous (HTTP REST):**
```
Payments Service needs user info
  → Makes GET /api/user/<id> call to Core Service
  → Core Service returns user JSON
  → Payments Service processes

Pros: Simple, direct, immediate response
Cons: Tight coupling, slow if called service is slow
```

**Asynchronous (Event Bus):**
```
User achieves milestone
  → Core Service publishes "milestone_achieved" event to message queue
  → Notifications Service listens and sends notification
  → Analytics Service listens and records metric

Pros: Loose coupling, fast (fire-and-forget)
Cons: Eventual consistency, complex debugging
```

---

## 🚀 Quick Start for Developers

### Local Development Setup
```bash
# 1. Clone and navigate to repo
git clone https://github.com/NathanKirton/move2earn-backend
cd move2earn-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
# Create .env file with:
# MONGODB_URI=mongodb+srv://...
# MONGODB_DB_NAME=move2earn
# FLASK_SECRET_KEY=dev-secret-key-change-in-prod
# STRAVA_CLIENT_ID=your_client_id
# STRAVA_CLIENT_SECRET=your_client_secret

# 5. Run locally
python app.py
# Visit: http://localhost:5000
```

### Live Site

The production site is hosted at:
```
Primary Domain:  https://move2earn.uk/
   ↓ (redirects to)
Backend API:     https://move2earn-backend.onrender.com/
```

### Deploy to Render
```bash
# 1. Push to GitHub master branch
git add -A
git commit -m "Your changes"
git push origin master

# 2. Render auto-deploys (configured via webhook)
# 3. Monitor deployment at: https://dashboard.render.com

# 4. Check live site
# https://move2earn-backend.onrender.com (backend API)
# https://move2earn.uk (primary domain, redirects to Render)
```

---

## 📞 Support & Questions

For technical questions, refer to:
- **README_DEVELOPMENT.md** — Decisions & rationale
- **PARENT_GUIDE.md** — User guide for parents
- **MESSAGING_GUIDE.md** — How parent-child messaging works
- **Code comments** — Inline documentation in `app.py` & `database.py`

Happy coding! 🚀
