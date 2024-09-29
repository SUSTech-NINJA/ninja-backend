import os
import dotenv
from flask import Flask, Blueprint, g
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import Config
from app.models import db, User

from app.routes.auth import auth
from app.routes.admin import admin
from app.routes.chat import chat
from app.routes.robots import robots
from app.routes.shopping import shopping
from app.routes.user import user

migrate = Migrate()
dotenv.load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    db_path = os.path.join(app.instance_path, 'database.sqlite')
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///' + db_path
    )
    app.config.from_object(Config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize the database
    with app.app_context():
        db.init_app(app)
        migrate.init_app(app, db)
        db.create_all()

    # register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(chat)
    app.register_blueprint(robots)
    app.register_blueprint(shopping)
    app.register_blueprint(user)

    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    # public folders
    @app.route('/', methods=['GET'])
    def index():
        return "Success"

    return app
