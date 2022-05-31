#!/bin/bash
cd /usr/src/app
gunicorn --bind 0.0.0.0:10000 wsgi:app --log-level warning --error-logfile error.log --capture-output --log-config logging.conf