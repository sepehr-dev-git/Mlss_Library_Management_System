from flask import Flask

from application.database import db
from application.models import *

app:Flask = Flask(__name__, template_folder='../Templates', static_folder='../static')
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'

db.init_app(app)

with app.app_context():
    db.create_all()

