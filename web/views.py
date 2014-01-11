
from flask import (
    render_template,
    request,
    g,
    url_for,
    session,
    flash,
    redirect
)

from tables.models import Table, Camera, CameraManager
from tables.reporter import ChaosReporter
import redis
import json
import requests
from main import app
from utils import login_required, table_statuses, store_image


@app.route("/status/", methods=['POST'])
def post_status():
    status_data = request.form['json_response']
    return 'ok'


@app.route("/", methods=['GET', 'POST'])
def index():
    cameras = CameraManager().get_all_cameras()
    cameras_info = []
    for camera in cameras:
        images = camera.get_images()
        path = store_image(images[0], camera.camera_id)
        cameras_info.append((camera.camera_id, path))

    context = {
        'cameras': cameras_info,
        'tables_per_cam': table_statuses(),
    }
    return render_template('index.html', **context)

@login_required
@app.route('/claim', methods=['POST'])
def claim():
    table_id = request.form['table_id']
    table = Table(table_id)
    table.claim(session['username'])

    flash('Table: %s in now on you. Take care of it!' % table.name)
    return "200"

@login_required
@app.route('/free', methods=['POST'])
def free():
    table_id = request.form['table_id']
    table = Table(table_id)
    table.free(session['username'])
    flash('Table: %s is now free. Thanks!' % table.name)
    return "200"

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


