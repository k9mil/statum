from flask import Flask
from flask_apscheduler import APScheduler
from statum.config import Config
import pymongo

client = pymongo.MongoClient("localhost", 27017)
database = client.statum_db
scheduler = APScheduler()
scheduler.start()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    from statum.main.routes import main
    from statum.errors.routes import errors

    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app