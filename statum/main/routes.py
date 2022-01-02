from flask import Blueprint, render_template, request, session, url_for, redirect
from statum.config import Config
from furl import furl
from statum.system.models import System
from statum.users.models import User
from statum.main.utils.utils import generate_token, twitch_login, send_requests, get_vod, get_clips, get_streamer_id, get_data, get_bans, random_indexed_stream, random_stream, add_to_favourites, sort_vod, date_conversion
from statum.main.utils.scheduled import periodic_index_clearance

main = Blueprint('main', __name__)

@main.route("/")
def index():
    if session:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html", login_url=Config.LOGIN_URL)

@main.route("/dashboard")
async def dashboard():
    f: str = furl(request.full_path) 
    streamer_data: dict = {}
    top_streamer_data: dict = {}
    clips_data: dict = {}

    if session:
        streamer_list = session["user"]["follower_list"]
        user_data_id: int = session["user"]["_id"]
        favourites = User.load_favourites(user_data_id)

    if f.args:
        header: dict[str, str] = generate_token()
        twitch_login(header)
        return redirect(url_for("main.dashboard"))
    
    try:
        await send_requests(streamer_data, streamer_list, top_streamer_data, clips_data)
    except UnboundLocalError:
        return redirect(url_for("main.index"))

    return render_template("dashboard.html", live_data=streamer_data, top_data=top_streamer_data, top_clips=clips_data, favourites=favourites, login_url=Config.LOGIN_URL)

@main.route("/vod/<streamer_name>")
async def vod(streamer_name: str):
    header: dict[str, str] = generate_token("bearer")
    vod_data = await get_vod(header, streamer_name)
    vod_length: int = len(vod_data)
    if vod_length > 0:
        return render_template("vod.html", vod_data=vod_data, streamer=streamer_name, vodLength=vod_length)
    else:
        return render_template("vod.html", streamer=streamer_name)

@main.route("/streamer/<streamer_name>")
def streamer(streamer_name: str):
    header: dict[str, str] = generate_token("bearer")
    top_clips: list[list] = get_clips(header, get_streamer_id(header, streamer_name))
    faq_data: dict[str, list] = get_data(streamer_name)
    ban_data: dict = get_bans(streamer_name)
    clip_length: int = len(top_clips)

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
    add_to_favourites(streamer_name)
    return redirect(url_for("main.dashboard"))

@main.route("/settings")
def settings():
    user_data_id: int = session["user"]["_id"]
    favourites = User.load_favourites(user_data_id)
    return render_template("settings.html", favourites=favourites, login_url=Config.LOGIN_URL)

@main.route("/favourites")
async def favourites():
    user_data_id: int = session["user"]["_id"]
    header: dict[str, str] = generate_token("bearer")
    favourites = User.load_favourites(user_data_id)
    vod_length: int = 0
    vod_conglomerate: list[list] = []

    for streamer in favourites:
        vod_data = await get_vod(header, streamer, "multiple")  
        vod_length += len(vod_data)
        for n in vod_data:
            vod_conglomerate.append(n)
    
    vod_conglomerate = sort_vod(vod_conglomerate)

    for n in range(len(vod_conglomerate)):
        vod_conglomerate[n][4] = date_conversion(vod_conglomerate[n][4])

    if vod_length > 0:
        return render_template("favourites.html", vod_data=vod_conglomerate, vodLength=vod_length)
    else:
        return render_template("favourites.html")

@main.route("/random")
def randomHTML():
    random_data = System.load_random()

    try:
        if random_data['streamers']:
            user_name = random_indexed_stream(random_data['streamers'])
        else:
            user_name = random_stream()
    except TypeError:
        user_name = random_stream()

    return render_template("random.html", user_name = user_name)