import os
from flask import Flask, Blueprint


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, 'database.sqlite'),
    )
    app.config.from_pyfile('config.py', silent=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize the database
    with app.app_context():
        from . import db
        db.init_app(app)

    # public folders
    @app.route('/', methods=['GET'])
    def index():
        pass
        
    # @app.route('/assets/<path:filename>', methods=['GET'])
    # def static_files(filename):
    #     return send_from_directory(app.config['ASSETS_DIR'], filename)

    return app
