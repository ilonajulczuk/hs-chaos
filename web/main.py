from flask import Flask
from flask import render_template
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
import redis
import json

app = Flask(__name__)
TABLE_TIMEOUT = 60 * 100

redis_client = redis.Redis()

registered_tables = range(1, 5)

@app.route("/")
def index():
    context = {
        'tables': [
            table_status(table_id) for table_id in registered_tables
        ]
    }
    return render_template('index.html', tables=context['tables'])

def handle_websocket(ws):
    while True:
        message = ws.receive()
        if message is None:
            break
        else:
            message = json.loads(message)
            id = message['table_id']
            username = message['username']
            print id, username
            claim_table(id, username)

            ws.send(json.dumps({'output': "cool, table %s claimed by: %s" % (id, username)}))


def fetch_chaos_percentage(table_id):
    import random

    return ('%s' % random.randint(1, 100)) + '%'


def table_status(table_id):
    occupied, occupant = check_if_occupied(table_id)
    chaos_percentage = fetch_chaos_percentage(table_id)
    return {
        'id': table_id,
        'occupied': occupied,
        'chaos_percentage': chaos_percentage,
        'occupant': occupant
    }

def check_if_occupied(table_id):
    username = redis_client.get('table-%s' % table_id)
    if not username:
        return False, None
    else:
        return True, username

def claim_table(id, username):
    redis_client.set('table-%s' % id, username, TABLE_TIMEOUT)
    redis_client.set('last-table-%s' % id, username)

app.debug = True

def my_app(environ, start_response):
    path = environ["PATH_INFO"]
    if path == "/":
        return app(environ, start_response)
    elif path == "/websocket":
        handle_websocket(environ["wsgi.websocket"])
    else:
        return app(environ, start_response)


if __name__ == "__main__":
    http_server = WSGIServer(('0.0.0.0',8000), my_app,
                             handler_class=WebSocketHandler)
    http_server.serve_forever()

