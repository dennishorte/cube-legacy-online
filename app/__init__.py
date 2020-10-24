from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager()
login.init_app(app)
login.login_view = 'login'

# Load all routes
from app.routes import auth_routes
from app.routes import achievement_routes
from app.routes import cube_routes
from app.routes import custom_routes
from app.routes import other_routes

# Load custom filters
from app.filters import *

# Load all models for flask migrate
from app.models.cube import *
from app.models.draft import *
from app.models.user import *
