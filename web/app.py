from flask import Flask

SECRET_KEY = 'development key'
app = Flask(__name__)
app.config.from_object(__name__)


app.debug = True
import views
