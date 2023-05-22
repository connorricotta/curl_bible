#!/bin/bash
cd /usr/src
gunicorn --bind 0.0.0.0:10000 -k uvicorn.workers.UvicornWorker wsgi:app 
# --log-level warning --error-logfile error.log --capture-output --log-config logging.conf