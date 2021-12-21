import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    AUTH_KEY = os.environ.get('AUTH_KEY')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    SCHEDULER_API_ENABLED = True