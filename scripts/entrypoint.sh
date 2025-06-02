#!/bin/bash

set -e

case "${APP_MODE:=start}" in
  start)
    echo "Starting application in CLI mode..."
    start
    ;;
  web)
    echo "Starting application in web development mode..."
    web
    ;;
  gunicorn)
    echo "Starting application with Gunicorn..."
    gunicorn -w 4 -b 0.0.0.0:8000 docker_volume_analyzer.wsgi:application
    ;;
  *)
    echo "Invalid APP_MODE: $APP_MODE"
    echo "Valid options are: start, web, gunicorn"
    exit 1
    ;;
esac