import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    AUTH_KEY = os.environ.get('AUTH_KEY')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    SCHEDULER_API_ENABLED = True
    LOGIN_URL = f"https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=http://localhost:5000/dashboard&response_type=code&scope=openid+user:read:email&claims={'id_token'}"