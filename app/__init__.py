from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

login = LoginManager()
login.init_app(app)
login.login_view = 'login'

from app import routes
