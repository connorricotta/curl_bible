import time
from flask import stream_with_context, Flask, request, Response
from time import sleep
from datetime import datetime
import json
import random

app = Flask(__name__)

SLEEP_TIME = .2


@app.route('/colors')
# Taken from ron.sh
def chart_data():
    def generate_random_data():
        count = 1
        while True:
            json_data = json.dumps(
                {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100})
            code = random.randint(0, 255)
            yield('\033[2J \033[H')
            # yield f"data:{json_data}\n"
            # yield f"\033[38;5;{code}mHello\033[38;5;${code}\033[0m\n"
            count = (count + 1) % 4
            if count == 1:
                yield f"\033[38;5;{code}m ― \033[0m\n"
                time.sleep(SLEEP_TIME)
            elif count == 2:
                yield f"\033[38;5;{code}m \\ \033[0m\n"
                time.sleep(SLEEP_TIME)
            elif count == 3:
                yield f"\033[38;5;{code}m | \033[0m\n"
                time.sleep(SLEEP_TIME)
            elif count == 4:
                yield f"\033[38;5;{code}m / \033[0m\n"
                time.sleep(SLEEP_TIME)

    if 'curl' in request.user_agent.string:
        response = Response(
            stream_with_context(
                generate_random_data()),
            mimetype="text/event-stream")
    else:
        response = Response(stream_with_context(generate_random_data()))
    # response.headers["Cache-Control"] = "no-cache"
    # response.headers["X-Accel-Buffering"] = "no"
    return response


# from flask import Flask, Response


# app = Flask(__name__)


# @app.route('/')
# def index():
#     def gen():
#         for c in 'Hello world!':
#             yield c
#             time.sleep(0.5)
#     return stream_with_context(gen())

if __name__ == '__main__':
    app.run()

# if __name__ == "__main__":
#     app.run()
