#!/bin/bash

# Start Celery worker in the background
celery -A app.celery_app worker --concurrency=1 --max-tasks-per-child=2 --loglevel=info &

# Start a dummy web server in the foreground so Render doesn't kill the container
python3 -m http.server $PORT
