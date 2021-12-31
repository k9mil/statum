from flask import Blueprint, render_template, request, session, url_for, redirect
from statum.config import Config
from furl import furl
from statum.system.models import System
from statum.users.models import User
from statum.main.utils.utils import generateToken, twitch_login, send_requests, getVOD, getClips, getStreamerID, getData, getBans, randomIndexedStream, randomStream, addToFavourites, sortVOD
from statum.main.utils.scheduled import periodicIndexClearence

main = Blueprint('main', __name__)

@main.route("/")
def index():
    if session:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html", login_url=Config.LOGIN_URL)

@main.route("/dashboard")
async def dashboard():
    f = furl(request.full_path) 
    streamer_data = {}
    top_streamer_data = {}
    clips_data = {}

    if session:
        streamer_list = session["user"]["follower_list"]
        user_data_id: int = session["user"]["_id"]
        favourites = User.loadFavourites(user_data_id)

    if f.args:
        header = generateToken()
        twitch_login(header)
        return redirect(url_for("main.dashboard"))
    
    try:
        await send_requests(streamer_data, streamer_list, top_streamer_data, clips_data)
    except UnboundLocalError:
        return redirect(url_for("main.index"))

    return render_template("dashboard.html", live_data=streamer_data, top_data=top_streamer_data, top_clips=clips_data, favourites=favourites, login_url=Config.LOGIN_URL)

@main.route("/vod/<streamer_name>")
async def vod(streamer_name):
    header: dict[str, str] = generateToken("bearer")
    vod_data = await getVOD(header, streamer_name)
    vodLength = len(vod_data)
    if vodLength > 1:
        return render_template("vod.html", vod_data=vod_data, streamer=streamer_name, vodLength = vodLength)
    else:
        return render_template("vod.html", streamer=streamer_name)

@main.route("/streamer/<streamer_name>")
def streamer(streamer_name):
    header = generateToken("bearer")
    top_clips = getClips(header, getStreamerID(header, streamer_name))
    faq_data = getData(streamer_name)
    ban_data = getBans(streamer_name)
    clip_length = len(top_clips)

    return render_template("streamer.html", streamer=streamer_name, top_clips=top_clips, faq_data=faq_data, ban_data=ban_data, clip_length=clip_length)

@main.route("/about")
def about():
    return render_template("about.html", login_url=Config.LOGIN_URL)

@main.route("/privacy")
def privacy():
    return render_template("privacy.html", login_url=Config.LOGIN_URL)
    
@main.route("/tos")
def terms_of_service():
    return render_template("tos.html", login_url=Config.LOGIN_URL)

@main.route("/favourite/<streamer_name>")
def favourite(streamer_name):
    addToFavourites(streamer_name)
    return redirect(url_for("main.dashboard"))

@main.route("/settings")
def settings():
    user_data_id: int = session["user"]["_id"]
    favourites = User.loadFavourites(user_data_id)
    return render_template("settings.html", favourites=favourites, login_url=Config.LOGIN_URL)

@main.route("/favourites")
async def favourites():
    user_data_id: int = session["user"]["_id"]
    header: dict[str, str] = generateToken("bearer")
    favourites = User.loadFavourites(user_data_id)
    vodLength: int = 0
    vodConglomerate = []

    for streamer in favourites:
        vod_data = await getVOD(header, streamer, "multiple")  
        vodLength += len(vod_data)
        for n in vod_data:
            vodConglomerate.append(n)
    
    if vodLength > 1:
        return render_template("favourites.html", vod_data=sortVOD(vodConglomerate), vodLength = vodLength)
    else:
        return render_template("favourites.html")

@main.route("/random")
def randomHTML():
    randomData = System.loadRandom()

    try:
        if randomData['streamers']:
            user_name = randomIndexedStream(randomData['streamers'])
        else:
            user_name = randomStream()
    except TypeError:
        user_name = randomStream()

    return render_template("random.html", user_name = user_name)
