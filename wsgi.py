from app import app

# WSGI entrypoint for production servers (gunicorn, uWSGI, etc.)
# Example: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

if __name__ == '__main__':
    app.run()
