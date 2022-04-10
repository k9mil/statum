from flask import Flask
from flask_apscheduler import APScheduler
from statum.config import Config
import pymongo, certifi

ca = certifi.where()
client = pymongo.MongoClient(f"mongodb+srv://statum:{Config.MONGO_PASSWORD}@statum.c5zu0.mongodb.net/statum_db?retryWrites=true&w=majority", tlsCAFile=ca)
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