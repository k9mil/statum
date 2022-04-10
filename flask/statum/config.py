import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    AUTH_KEY = os.environ.get('AUTH_KEY')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')
    LOGIN_URL = f"https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https://statum-demo.tk/dashboard&response_type=code&scope=openid+user:read:email&claims={'id_token'}"
    SCHEDULER_API_ENABLED = True