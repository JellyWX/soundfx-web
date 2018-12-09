from flask import Flask
from config import Config
from flask_dance.contrib.discord import make_discord_blueprint, discord
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config.from_object(Config)
discord_blueprint = make_discord_blueprint(scope=['identify'], redirect_url='dashboard')
app.register_blueprint(discord_blueprint, url_prefix='/login')
db = SQLAlchemy(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
)

from app import routes, models

db.create_all()
