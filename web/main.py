from flask import Flask

from flask import (
    render_template,
    request,
    url_for,
    session,
    flash,
    redirect
)

from tables.manager import TableManager
from tables.reporter import ChaosReporter
import redis
import json
import requests


SECRET_KEY = 'development key'
app = Flask(__name__)
app.config.from_object(__name__)
TABLE_TIMEOUT = 60 * 100

redis_client = redis.Redis()


@app.route("/status/", methods=['POST'])
def post_status():
    status_data = request.form['json_response']
    return 'ok'


@app.route("/")
def index():
    reporter = ChaosReporter()
    images = reporter.get_last_images('camera')
    path = reporter.store_image('camera', images[0])
    context = {
        'path': path,
        'tables': table_statuses(),
    }
    return render_template('index.html', **context)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        login_credentials = {"login": username,
                             "password": password}
        auth_website = 'https://auth.hackerspace.pl'
        r = requests.post(auth_website, login_credentials)
        if r.status_code == 200:
            session['logged_in'] = True
            session['username'] = username
            flash('You were logged in')
            return redirect(url_for('index'))
        else:
            flash('Authorization error,'
                  ' login or password incorrect!')
            error = True
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))



def fetch_chaos_percentage(table_id):
    import random

    return ('%s' % random.randint(1, 100)) + '%'


def table_statuses():
    manager = TableManager()
    reporter = ChaosReporter()
    tables_ids = reporter.get_all_tables()
    tables = []
    for table_id in tables_ids:
        try:
            chaos_level = reporter.get_chaos_levels(table_id)[0]
            occupancy_data = manager.check_table(table_id)
            occupied = manager.is_table_used_now(table_id)
            table_status = {
                'id': table_id,
                'chaos_percentage': chaos_level,
                'actions': occupancy_data,
                'occupied': occupied
            }

            if int(chaos_level) > 50 and not occupied:
                table_status['message'] = 'Oh snap! There\'s a mess and there is nobody near!'
            tables.append(table_status)
        except:
            # TODO - create some logging system
            pass

    return tables


def check_if_occupied(table_id):
    username = redis_client.get('table-%s' % table_id)
    if not username:
        return False, None
    else:
        return True, username


def claim_table(id, username):
    manager = TableManager()
    return manager.claim_table(id, username)


app.debug = True

def my_app(environ, start_response):
    path = environ["PATH_INFO"]
    return app(environ, start_response)


if __name__ == "__main__":
    app.run()
