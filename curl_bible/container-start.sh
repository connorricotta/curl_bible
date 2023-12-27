#!/bin/bash
gunicorn --bind 0.0.0.0:10000 -k uvicorn.workers.UvicornWorker server:app --timeout 90
#--log-level info --error-logfile error.log --capture-output --log-config logging.conf
