from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager()
login.init_app(app)
login.login_view = 'login'

# Load all routes
from app.routes import admin_routes
from app.routes import auth_routes
from app.routes import achievement_routes
from app.routes import cube_routes
from app.routes import custom_routes
from app.routes import draft_routes
from app.routes import game_routes
from app.routes import other_routes
from app.routes import user_routes

# Load custom filters
from app.filters import *

# Load all models for flask migrate
from app.models.cube_models import *
from app.models.draft_models import *
from app.models.game_models import *
from app.models.user_models import *

# Ensure initial objects are created
# These need to be commented out if the db isn't set up for them yet.
# from app.util import setup
# setup.ensure_starter_user()
# setup.ensure_basic_lands()
# setup.ensure_art_crop()
