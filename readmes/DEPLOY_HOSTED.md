```markdown
Deploying the Flask backend to a hosted service

This document describes simple deployment options for hosting the existing Flask app.

Recommended DB: MongoDB Atlas (managed) — configure via MONGODB_URI env var or in .env.

Options:

1) Render / Railway / Heroku (quickest)
   - Push your repo to GitHub and connect the service.
   - Set environment variables in the service dashboard:
     - MONGODB_URI (your Atlas connection string)
     - FLASK_SECRET_KEY
     - STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN (if needed)
     - PORT (optional)
   - If using the included Dockerfile, the service will build and run the container.

2) Docker-based VPS or Cloud Run
   - Build and push Docker image to registry (Docker Hub, GHCR).
   - Deploy image to your host (Cloud Run, VPS with Docker).

3) IONOS shared hosting (NOT recommended for backend)
   - Use only for static frontend. For backend you need external host or their Tomcat/Java support.

Local Docker build & run (example):
  docker build -t move2earn-backend:latest .
  docker run -e MONGODB_URI="your-mongo-uri" -e FLASK_SECRET_KEY="your-secret" -p 5000:5000 move2earn-backend:latest

Run locally without Docker (example PowerShell commands):
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  $env:FLASK_SECRET_KEY='replace-me'
  $env:MONGODB_URI='mongodb://localhost:27017/move2earn'
  python wsgi.py

Notes:
- The app reads PORT and FLASK_DEBUG from environment for production.
- Ensure CORS is configured if serving frontend from a different origin (we can add flask-cors).

```
