import os

import redis
from flask import Flask, g, jsonify

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

COUNTER_KEY = "visits"


@app.before_request
def count_visit():
    try:
        g.visit_count = redis_client.incr(COUNTER_KEY)
    except redis.exceptions.RedisError:
        app.logger.exception("Could not increment the visit counter in Redis")
        return jsonify(error="Visit counter is temporarily unavailable."), 503


@app.get("/")
@app.get("/increment")
@app.get("/showCurrentCount")
def show_count():
    return jsonify(visits=g.visit_count)
