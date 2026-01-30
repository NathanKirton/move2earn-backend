FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Use gunicorn with proper timeout settings
# --timeout 60: Give requests up to 60 seconds to complete
# --workers 4: Use 4 worker processes
# --worker-class sync: Use synchronous worker
# --max-requests 1000: Restart worker after 1000 requests to prevent memory leaks
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "60", "--workers", "4", "--max-requests", "1000", "--error-logfile", "-", "--access-logfile", "-", "wsgi:app"]
