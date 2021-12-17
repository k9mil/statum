from flask import Blueprint, render_template, request, session, url_for, redirect
from statum.config import Config
from dateutil import parser
from furl import furl
<<<<<<< HEAD
from statum.users.models import User
=======
from statum.users.models import User, System
from statum import database
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
import httpx, datetime, json, time

main = Blueprint('main', __name__)

<<<<<<< HEAD
login_url = "https://api.twitch.tv/kraken/oauth2/authorize?response_type=code&client_id=xhrzck2b40wioai0i2uye7319cdxuk&redirect_uri=http://localhost:5000/dashboard&scope=openid+user:read:email&claims={'id_token'}"
=======
login_url = "https://id.twitch.tv/oauth2/authorize?client_id=xhrzck2b40wioai0i2uye7319cdxuk&redirect_uri=http://localhost:5000/dashboard&response_type=code&scope=openid+user:read:email&claims={'id_token'}"
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)

@main.route("/")
def index():
    if session:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html", login_url=login_url)

@main.route("/dashboard")
async def dashboard():
    f = furl(request.full_path) 
    streamer_data = {}
<<<<<<< HEAD
    
    if f.args:
        await send_requests(streamer_data, twitch_login())
        return redirect(url_for("main.dashboard"))
    
    if session:
        streamer_list = session["user"]["follower_list"]
        await send_requests(streamer_data, streamer_list)
    else:
        streamer_list = load_default_data()
        await send_requests(streamer_data, streamer_list)

=======

    if session:
        streamer_list = session["user"]["follower_list"]
    else:
        streamer_list = load_default_data()

    if f.args:
        header = generateToken()
        twitch_login(header)
    
    await send_requests(streamer_data, streamer_list)
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
    return render_template("dashboard.html", live_data=streamer_data, login_url=login_url)

@main.route("/streamer/<streamer_name>")
def streamer(streamer_name):
    vod_data = temp_get_vods(streamer_name)
    if len(vod_data) > 1:
        return render_template("streamer.html", vod_data=vod_data, streamer=streamer_name)
    else:
        return render_template("streamer.html", streamer=streamer_name)

@main.route("/about")
def about():
    return render_template("about.html", login_url=login_url)

@main.route("/privacy")
def privacy():
    return render_template("privacy.html", login_url=login_url)
    
@main.route("/tos")
def terms_of_service():
    return render_template("tos.html", login_url=login_url)

def load_default_data():
    with open("statum\static\streamers.json", "r") as json_data:
        streamer_list = json.load(json_data)
        json_data.close()
        return streamer_list

<<<<<<< HEAD
def twitch_login():
=======
def generateToken():
    f = furl(request.full_path)
    user_auth_url = f"https://id.twitch.tv/oauth2/token?client_id=xhrzck2b40wioai0i2uye7319cdxuk&client_secret={Config.AUTH_KEY}&grant_type=authorization_code&redirect_uri=http://localhost:5000&code={f.args['code']}"
    post_auth = httpx.post(user_auth_url).json()
    header = {'Authorization': 'Bearer ' + post_auth["access_token"], 'Client-ID': 'xhrzck2b40wioai0i2uye7319cdxuk'}
    return header

def generateBearer():
    bearerGenerator = f"https://id.twitch.tv/oauth2/token?client_id=xhrzck2b40wioai0i2uye7319cdxuk&client_secret={Config.AUTH_KEY}&grant_type=client_credentials"
    postBearer = httpx.post(bearerGenerator).json()
    header = {'Authorization': 'Bearer ' + postBearer["access_token"], 'Client-ID': 'xhrzck2b40wioai0i2uye7319cdxuk'}
    return header

def twitch_login(header):
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
    streamer_list = {}
    users_url = "https://api.twitch.tv/helix/users"

    if session:
        user_data_id = session["user"]["_id"]
    else:
<<<<<<< HEAD
        f = furl(request.full_path)
        user_auth_url = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=authorization_code&redirect_uri=http://localhost:5000&code={f.args['code']}"
        post_auth = httpx.post(user_auth_url).json()
        header = {'Authorization': 'Bearer ' + post_auth["access_token"], 'Client-ID': Config.CLIENT_ID}
=======
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
        response_result = httpx.get(users_url, headers=header).json()
        user_data_id = response_result["data"][0]["id"]

    users_follow = f"https://api.twitch.tv/helix/users/follows?from_id={user_data_id}"
<<<<<<< HEAD
    users_follow_request = httpx.get(users_follow, headers={'Authorization': 'Bearer ' + "d9crvpuiz3x0jos525d272swtfn0ev", 'Client-ID': Config.CLIENT_ID}).json() #temp
=======
    users_follow_request = httpx.get(users_follow, headers=header).json()
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
    follow_count = len(users_follow_request["data"])

    for value in range(follow_count):
        streamer_name = users_follow_request["data"][value]["to_name"]
        streamer_list[streamer_name] = f"https://twitch.tv/{streamer_name}"
    
<<<<<<< HEAD
    User().twitch_signup(user_data_id ,streamer_list)
    return streamer_list 

async def send_requests(streamer_data, streamer_list):
    header = {'Authorization': 'Bearer ' + "d9crvpuiz3x0jos525d272swtfn0ev", 'Client-ID': Config.CLIENT_ID} #temp
    async with httpx.AsyncClient() as client:
        for streamer in streamer_list:
            stream_url = "https://api.twitch.tv/helix/search/channels?query=" + streamer
            pre_presponse = await client.get(stream_url, headers=header)
            presponse = pre_presponse.json()
            results = len(presponse["data"])
            populate_data(results, streamer_data, presponse, streamer)

def populate_data(results, streamer_data, presponse, streamer):
    for numb in range(results):
        if presponse["data"][numb]["broadcaster_login"] == streamer.lower():
            try:
                if presponse["data"][numb]["is_live"] == True:
                    streamer_data[streamer] = ["LIVE", presponse["data"][numb]["game_name"], epoch_conversion(presponse, numb)]
                else:
                    streamer_data[streamer] = ["NOT LIVE", "none", "none"]
            except parser.ParserError as e:
=======
    User().twitchSignup(user_data_id, streamer_list)
    return streamer_list 

async def send_requests(streamer_data, streamer_list):
    header = generateBearer()

    async with httpx.AsyncClient() as client:
        for streamer in streamer_list:
            streamerExists = database.twitch_streamer_data.find_one({'broadcaster_name': streamer.lower()})

            if streamerExists:
                pass
            else:
                stream_url = "https://api.twitch.tv/helix/search/channels?query=" + streamer
                getDetails = await client.get(stream_url, headers=header)
                getDetailsJSON = getDetails.json()
                results = len(getDetailsJSON["data"])
                indexStreamer(results, streamer_data, getDetailsJSON, streamer)

    stream_url = "https://api.twitch.tv/helix/streams?"

    for streamer in streamer_list:
        stream_url += "user_login=" + streamer + "&"

    getDetails = httpx.get(stream_url, headers=header)
    getDetailsJSON = getDetails.json()

    tempFunc(streamer_data, getDetailsJSON['data'], streamer_list)

def tempFunc(streamer_data, getDetailsJSON, streamer_list):
    for n in getDetailsJSON:
        # if n['user_name'] in streamer_list:
        streamer_data[n['user_name']] = ["LIVE", n["game_name"], tmpEpoch(n)]
        # else:
            #  streamer_data[n['user_name']] = ["NOT LIVE", "none", "none"]
    return streamer_data


def indexStreamer(results, streamer_data, getDetailsJSON, streamer):
    for numb in range(results):
        if getDetailsJSON["data"][numb]["broadcaster_login"] == streamer.lower():
            try:
                System().indexStreamer(getDetailsJSON["data"][numb]["id"], getDetailsJSON["data"][numb]["broadcaster_login"])
                if getDetailsJSON["data"][numb]["is_live"] == True:
                    streamer_data[streamer] = ["LIVE", getDetailsJSON["data"][numb]["game_name"], epoch_conversion(getDetailsJSON, numb)]
                # else:
                #     streamer_data[streamer] = ["NOT LIVE", "none", "none"]
            except parser.ParserError:
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
                pass
            break
        else:
            pass
    return streamer_data

def temp_get_vods(streamer):
    vod_data = {}
<<<<<<< HEAD

    header = {'Authorization': 'Bearer ' + "d9crvpuiz3x0jos525d272swtfn0ev", 'Client-ID': Config.CLIENT_ID} #temp
=======
    header = generateBearer()
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)

    userIDURL = f"https://api.twitch.tv/helix/users?login={streamer}"
    responseB = httpx.get(userIDURL, headers=header)
    userID = responseB.json()["data"][0]["id"]

    findVideoURL = f"https://api.twitch.tv/helix/videos?user_id={userID}&type=archive"
    responseC = httpx.get(findVideoURL, headers=header)

    try:
        for n in range(20):
            thumbnail_url = responseC.json()["data"][n]["thumbnail_url"]
            vod_url = responseC.json()["data"][n]["url"]
            title = responseC.json()["data"][n]["title"]
            duration = responseC.json()["data"][n]["duration"]
            if thumbnail_url == "":
                vod_data[n] = ["https://ffwallpaper.com/card/tv-static/tv-static--12.jpg", vod_url, title, duration]
            else:
                thumbnail_url = thumbnail_url.replace("%{width}x%{height}.jpg", "1920x1080.jpg")
                vod_data[n] = [thumbnail_url, vod_url, title, duration]
<<<<<<< HEAD
    except IndexError as i:
=======
    except IndexError:
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
        pass
    
    return vod_data

<<<<<<< HEAD
=======
def tmpEpoch(data):
    time_now = datetime.datetime.utcnow()
    epoch_current = int(time.mktime(time_now.timetuple()))
    twitch_api_date_parsed = parser.parse(data["started_at"]).strftime("%d.%m.%Y %H:%M:%S")
    epoch_twitch = int(time.mktime(time.strptime(twitch_api_date_parsed, "%d.%m.%Y %H:%M:%S")))
    epoch_diff = epoch_current - epoch_twitch
    epoch_final = str(datetime.timedelta(seconds=epoch_diff))
    return epoch_final

>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
def epoch_conversion(presponse, numb):
    time_now = datetime.datetime.utcnow()
    epoch_current = int(time.mktime(time_now.timetuple()))
    twitch_api_date_parsed = parser.parse(presponse["data"][numb]["started_at"]).strftime("%d.%m.%Y %H:%M:%S")
    epoch_twitch = int(time.mktime(time.strptime(twitch_api_date_parsed, "%d.%m.%Y %H:%M:%S")))
    epoch_diff = epoch_current - epoch_twitch
    epoch_final = str(datetime.timedelta(seconds=epoch_diff))
    return epoch_final