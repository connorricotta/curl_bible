#!/bin/bash
gunicorn --bind 0.0.0.0:10000 -k uvicorn.workers.UvicornWorker curl_bible.server:app --timeout 90
#--log-level info --error-logfile error.log --capture-output --log-config logging.conf
