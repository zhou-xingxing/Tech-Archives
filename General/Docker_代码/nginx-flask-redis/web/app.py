import os
from flask import Flask
import redis
from typing import Optional

app = Flask(__name__)
try:
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        socket_connect_timeout=5
    )
except Exception:
    print("无法创建Redis客户端")
    raise

@app.route('/')
def home() -> str:
    try:
        num_visits = redis_client.incr('numVisits')
    except redis.RedisError:
        return "Redis服务器错误"
    
    return f"{os.uname().nodename}: Number of visits is: {num_visits}"

if __name__ == '__main__':
    print('start run')
    app.run(host='0.0.0.0', port=5000)
