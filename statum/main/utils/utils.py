from typing import Any
from flask import request, session
from statum.users.models import User
from statum.system.models import System
from statum.config import Config
from furl import furl
from bs4 import BeautifulSoup
from dateutil import parser
from statum import database
import json, httpx, random, datetime, time

def load_default_data() -> dict[str, str]:
    """Finds and opens a .json file with streamer data.

    Reads from the file and assigns the data to streamer_list.

    Args:
        None
    
    Returns:
        A dict mapping keys (Twitch usernames) to their corresponding URLs.
        Each row is represented as a seperate streamer. For example:

        {
            "GMHikaru":"https://www.twitch.tv/GMHikaru"
        }
    """

    with open("statum\static\streamers.json", "r") as default_streamers:
        streamer_list: dict[str, str] = json.load(default_streamers)
        default_streamers.close()
        return streamer_list

def random_indexed_stream(streamers: list[str]) -> str:
    """Receives a list of streamers and returns a random individual.

    Args:
        streamers: A list of Twitch streamers.
    
    Returns:
        None
    """

    return random.choice(streamers)

def random_stream() -> str:
    """This is the main function which decides the random stream to be served by the web app.

    It sends requests to the Twitch API until a condition is met, then sents the request_status to false,
    after which is proceeds to temporarily index the streamers gathered, and picks a random streamer
    out of the list.

    Args:
        None

    Returns:
        A string with the value of the streamer. For example:

        "georgehotz"
    """

    MAX_VIEWERS: int = 100
    MIN_VIEWERS: int = 10
    request_status: bool = True
    streamer_ids: list[int] = []

    header: dict[str, str] = generate_token("bearer")
    active_streams: str = "https://api.twitch.tv/helix/streams"
    get_streams_request: dict = httpx.get(active_streams, headers=header).json()

    while request_status != False:
        active_streams: str = f"https://api.twitch.tv/helix/streams?first=100&after={get_streams_request['pagination']['cursor']}"
        get_streams_request: dict = httpx.get(active_streams, headers=header).json()
        request_instances: int = (len(get_streams_request["data"]) - 1)

        if (get_streams_request['data'][0]['viewer_count'] < MAX_VIEWERS):
            index_random(get_streams_request, streamer_ids)

        if (get_streams_request['data'][request_instances]['viewer_count'] < MIN_VIEWERS):
            request_status = False
        else: 
            pass
    
    System.index_random_db(streamer_ids)
    random_streamer: str = choose_random(streamer_ids)
    return random_streamer

def index_random(get_streams_request: dict, streamer_ids: list[int]) -> list[int]:
    """This function iterates over a sequence * times depending on the length of the GET request returned.

    It assigns the length of the GET request to a variable and loops over that amount of times, and checks whether the
    username of the streamer is compatible with Ascii, as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.

    Args:
        get_streams_request: Jsonified GET request return from the Twitch API.
        streamer_ids: A list of the streamers (to be later picked random from).
    
    Returns:
        A list of the streamers, located in the "streamer_ids" variable.
    """

    request_instances = len(get_streams_request["data"])
    for i in range(request_instances):
        if get_streams_request['data'][i]['user_name'].isascii():
            streamer_ids.append(get_streams_request['data'][i]['user_name'])
        else:
            streamer_ids.append(get_streams_request['data'][i]['user_login'])
    
    return streamer_ids

def choose_random(streamer_ids: list[int]) -> str:
    """Receives a list of streamers and returns a random individual.

    Args:
        streamer_ids: A list of Twitch streamers.

    Returns:
        None
    """

    return random.choice(streamer_ids)

def generate_token(*bearer: str) -> dict[str, str]:
    """Generates a Token which is necessary for some Twitch API calls.

    Initially is assigns the full request path to the "f" variable, and if a bearer was provided it assigns a URL which contains a grant_type
    of "authorization_code", a redirect_uri & arguments from the URL, provided by Twitch. Otherwise it just contains a grant type of "client_credentials".
    It then posts either URL as a request and returns the result.

    Args:
        *bearer: An optional argument which decides what kind of URL is created (that is then used to generate a token).

    Returns:
        A header received by the Twitch API.
    """

    full_url: str = furl(request.full_path)

    if bearer:
        auth_url: str = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=client_credentials"
    else:
        auth_url: str = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=authorization_code&redirect_uri=http://localhost:5000&code={full_url.args['code']}"
    
    posted_url: dict = httpx.post(auth_url).json()
    header: dict[str, str] = {'Authorization': 'Bearer ' + posted_url["access_token"], 'Client-ID': Config.CLIENT_ID}

    return header

def twitch_login(header: dict[str, str]) -> dict[str, str]:
    """This function is called whenever utilizing Twitch's OAuth measure, either when logging in or updating followers.

    By default is sets an empty streamer dict, as well as a default users_url which points to the Twitch API for users. It determines whether the user has a session or not,
    and depending on that it sets the needed variables. It sends a request to the Twitch API for the streamers that the user follows, and lastly called the twitchSignup()
    method.

    Args:
        header: The header received by the Twitch API. *necessary to send the GET request.
    
    Returns:
        A dict mapping keys to the corresponding values, in this example, the keys are
        the streamer username and the values are the corresponding streamer URLs. For example:

        {
            "GMHikaru":"https://www.twitch.tv/GMHikaru"
        }
    """

    streamer_list: dict = {}
    users_url: str = "https://api.twitch.tv/helix/users"

    if session:
        user_data_id: int = session["user"]["_id"]
    else:
        response_result: dict = httpx.get(users_url, headers=header).json()
        user_data_id: int = response_result["data"][0]["id"]

    users_followed_url: str = f"https://api.twitch.tv/helix/users/follows?from_id={user_data_id}"
    follow_request: dict = httpx.get(users_followed_url, headers=header).json()
    streamers_followed: int = len(follow_request["data"])

    for value in range(streamers_followed):
        streamer_name: str = follow_request["data"][value]["to_name"]
        if streamer_name.isascii():
            streamer_list[streamer_name] = f"https://twitch.tv/{streamer_name}"
        else:
            streamer_name: str = follow_request["data"][value]["to_login"]
            streamer_list[streamer_name] = f"https://twitch.tv/{streamer_name}"
    
    User().twitch_signup(user_data_id, streamer_list)
    return streamer_list 

async def send_requests(streamer_data: dict, streamer_list: dict[str, str], top_streamer_data: dict, clips_data: dict):
    """An asynchronous function which serves as a middleman and it's necessary function is to call other functions.

    First, it generates a token and stores it in the "header" variable, and proceeds to call
    index_streamer_data(), load_streamers(), load_top_streamers() and lastly load_clips()

    Args:
        streamer_data: Contains an (empty) dictionary of the data held on streamers.
        streamer_list: Contains a dictionary which holds the streamer names as keys, and the URLs as their values.
        top_streamer_data: Contains an (empty) dictionary of the top streamers' data.
        clips_data: Contains an (empty) dictionary of the data necessary to render the top circulating clips.
    
    Returns:
        None
    """

    header: dict[str, str] = generate_token("bearer")
    await index_streamer_data(header, streamer_list, streamer_data)
    load_streamers(header, streamer_list, streamer_data)
    load_top_streamers(header, top_streamer_data)
    load_clips(clips_data)

def load_top_streamers(header: dict[str, str], top_streamer_data: dict):
    """Sends a GET request to the Twitch API with the headers provided, to get a collection of top streamers actively live on the platform.

    After the request is sent, show_top_streamer_data() is called passing the empty dictionary as well as the result from the GET request.

    Args:
        header: The header returned by Twitch containing the token.
        top_streamer_data: The empty dictionary which will hold the data of the top streamers.

    Returns:
        None
    """

    get_details: dict = httpx.get("https://api.twitch.tv/helix/streams", headers=header).json()
    index_top_streamer_data(get_details['data'])
    show_top_streamer_data(top_streamer_data, get_details['data']) 

def index_top_streamer_data(streamer_data: dict):
    """This function indexes top streamers into the database.

    Considering that we do not have to traverse a query, this directly returns an id & the username,
    so it can be indexed in an independent function. This is necessary as we allow the user
    to have favourites outside of followed users, which allows for quicker loading times if we
    connect the id to the username.

    This function loops over the returned data from Twitch and indexes the streamers to the database.

    Args:
        streamer_data: The dictionary returned by Twitch containing streamer details.

    Returns:
        None

    """

    for n in range(len(streamer_data)):
        System().index_streamer(streamer_data[n]["user_id"], streamer_data[n]["user_login"])

def load_clips(clips_data: dict):
    """Sends a GET request to the Reddit API, to get a collection of top posts on r/livestreamfail, a popular twitch-related subreddit.

    After the request is sent, show_top_clips() is called passing the empty dictionary..

    Args:
        clips_data: The empty dictionary which will hold the data of the top circulating posts on the platform.

    Returns:
        None
    """

    get_details: dict = httpx.get("https://www.reddit.com/r/livestreamfail/hot.json?limit=20").json()
    show_top_clips(clips_data, get_details['data']) 

def load_streamers(header: dict[str, str], streamer_list: dict[str, str], streamer_data: dict):
    """Loads the streamers which will be rendered on the /dashboard/ part of the web app.

    The function creates two lists: a list of live streamers, and not live streamers, as both have to be rendered,
    either as LIVE or NOT LIVE. The streamers which are passed from the streamer_list
    argument are added as variables on the URL which will be sent as a GET request to the Twitch API. 
    After the request is sent, a check is made on each user_name to see if it's Ascii compatible,
    as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.
    
    Args:
        header: A header holding the token generated by Twitch.
        streamer_data: Contains an (empty) dictionary of the data held on streamers.
        streamer_list: Contains a dictionary which holds the streamer names as keys, and the URLs as their values.
    
    Returns:
        None
    """

    stream_url: str = "https://api.twitch.tv/helix/streams?"
    live_streamers: list = []
    not_live_streamers: list = []

    for streamer in streamer_list:
        stream_url += "user_login=" + streamer + "&"

    get_details = httpx.get(stream_url, headers=header)
    get_details_json: dict = get_details.json()

    for n in get_details_json['data']:
        if n['user_name'].isascii():
            live_streamers.append(n['user_name'])
        else:
            live_streamers.append(n['user_login'])
    
    for n in streamer_list:
        if n not in live_streamers:
            not_live_streamers.append(n)

    show_streamer_data(streamer_data, get_details_json['data'], not_live_streamers)

def show_streamer_data(streamer_data: dict, get_details_json: dict, not_live_streamers: list[str]) -> dict[str, list]:
    """This function ensures that the streamer data dictionary passed through is populated.

    It loops through the jsonified returned request and again, it checks whether it is ascii compatible,
    as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.

    It also loops through the not live streamers, and sets different parameters for them.

    Args:
        streamer_data: Contains an empty dictionary which will map twitch usernames to keys to a list of values.
        get_details_json: Contains the returned JSON object from the GET request sent to Twitch, which contains the data of streamers.
        not_live_streamers: Contains a list which contains the usernames of the streamers that the user follows which are not currently live.

    Returns:
        A dict mapping keys to the corresponding values, with the keys being the Twitch usernames
        and the values are a list, which contains their live status, game name & time streamed. For example:

        {
            'TommyKayLIVE': ['LIVE', 'EA Sports UFC 4', '5:39:42'], 
            'BLASTPremier': ['NOT LIVE', 'none', 'none']
        }
    """

    for n in get_details_json:
        if n['user_name'].isascii():
            streamer_data[n['user_name']] = ["LIVE", n["game_name"], epoch_conversion(data = n)]
        else:
            streamer_data[n['user_login']] = ["LIVE", n["game_name"], epoch_conversion(data = n)]

    for n in not_live_streamers:
        streamer_data[n] = ["NOT LIVE", "none", "none"]

    return streamer_data

def show_top_streamer_data(top_streamer_data: dict, get_details_json: dict):
    """This function ensures that the top streamer data dictionary passed through is populated.

    It loops through the jsonified returned request and again, it checks whether it is ascii compatible,
    as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.

    Args:
        top_streamer_data: Contains an empty dictionary which will map twitch usernames to keys to a list of values.
        get_details_json: Contains the returned JSON object from the GET request sent to Twitch, which contains the data of top streamers.

    Returns:
        None
    """

    for n in get_details_json:
        if n['user_name'].isascii():
            top_streamer_data[n['user_name']] = ["LIVE", n["game_name"], epoch_conversion(data = n)]
        else:
            top_streamer_data[n['user_login']] = ["LIVE", n["game_name"], epoch_conversion(data = n)]

def show_top_clips(clips_data: dict, get_details: dict):
    """This function ensures that clips data dictionary passed through is populated.

    It loops through the request object returned by the GET request, and populates the clips_data dictionary with the relevant information.

    Args:
        clips_data: Contains an empty dictionary which will map the keys to a list of values.
        get_details: Contains the returned JSON object from the GET request sent to Reddit, which contains the data of the subreddits' posts.

    Returns:
        None
    """
    for n in get_details['children']:
        clips_data[n["data"]["title"]] = [n["data"]["permalink"], n["data"]["score"], n["data"]["num_comments"]]

async def index_streamer_data(header: dict[str, str], streamer_list: dict[str, str], streamer_data: dict):
    """Asynchronously indexes streamer data, to ensure faster loading times.

    Using async, it loops through the list of streamer and checks whether they exists by querying MongoDB with the name of the streamer,
    if the streamer exists (that is, already indexed) then the for loop passes, and proceeds to check the next username, otherwise it
    sends a GET request to Twitch and calls indexStreamer() with a list of items returned with a specific query, the query being the username
    of the streamer.

    Args:
        header: A header holding the token generated by Twitch.
        streamer_list: A dictionary holding streamers' information, with the username as keys and the streamer URL as their respective value.
        streamer_data: An empty dictionary which will be populated.

    Returns:
        None
    """

    async with httpx.AsyncClient() as client:
        for streamer in streamer_list:
            streamer_exists = database.twitch_streamer_data.find_one({'broadcaster_name': streamer.lower()})

            if streamer_exists:
                pass
            else:
                stream_url: str = "https://api.twitch.tv/helix/search/channels?query=" + streamer
                get_details = await client.get(stream_url, headers=header)
                get_details_json: dict = get_details.json()
                results: int = len(get_details_json["data"])
                index_streamer(results, streamer_data, get_details_json, streamer)

def index_streamer(results: int, streamer_data: dict, get_details_json: dict, streamer: str) -> dict[str, list]:
    """Indexes the streamer data.

    Loops through an arbitrary number of times, depending on the length of results passed through. Due to the way Twitch API works,
    it returns multiple channels that may not always match the streamer, so we confirm the login is equal to the streamer username passed through.
    If it matches, try and index the streamer and populate data if the streamer is live, otherwise populate with differnet data.

    Args:
        results: Number of results for a specific streamer, default is 20.
        streamer_data: An empty dictionary that will be populated with streamer data.
        get_details_json: The json object Twitch returns from a GET request containing the data.
        streamer: The username of the streamer to be found and indexed.

    Returns:
        A dict mapping keys to the corresponding values, with the keys being the Twitch usernames
        and the values are a list, which contains their live status, game name & time streamed. For example:

        {
            'forsen': ['NOT LIVE', 'none', 'none']
        }

    Raises:
        parser.ParserError: A parser error is raised.
    """

    for numb in range(results):
        if get_details_json["data"][numb]["broadcaster_login"] == streamer.lower():
            try:
                System().index_streamer(get_details_json["data"][numb]["id"], get_details_json["data"][numb]["broadcaster_login"])
                if get_details_json["data"][numb]["is_live"] == True:
                    streamer_data[streamer] = ["LIVE", get_details_json["data"][numb]["game_name"], epoch_conversion(json_data=get_details_json, index=numb)]
                else:
                    streamer_data[streamer] = ["NOT LIVE", "none", "none"]
            except parser.ParserError:
                pass
            break
        else:
            pass
    
    return streamer_data

async def get_vod(header: dict[str,str], streamer: str, *multiple_streamers: str) -> dict[int, list]:
    """Gets VOD data from a specific streamer that is passed through as an argument.

    This asynchronous function starts of by checking whether *multiple_streamers is passed, if so, the length of the loop
    is diminished to 3 rather than 20 which is by default. It then sends a query via loadID() to check if the streamer
    is indexed as an ID is necessary for this function, if not then it finds the id. It then asynchronously gets
    the videos for each streamer passed through.

    Args:
        header: A header necessary for getting the data from Twitch.
        streamer: Contains a string of the streamer name.
        *multiple_streamers: An optional arg, determines whether it's for a single streamer or multiple, which in turn determines the number of VODs to be found.

    Returns:
        It returns a list of lists with each list containing data for a specific video. For example:

        [
            [
                'https://static-cdn.jtvnw.net/cf_vods/dgeft87wbj63p/ea762441364c25cb372d_bobross_44181880156_1640535689//thumb/thumb0-1920x1080.jpg', 
                'https://www.twitch.tv/videos/1243955144', 
                'Weekend Marathon! Beginning Fridays at 12pm ET.', 
                '24h46m34s', 
                '26 Dec, 16:21', 
                '123,236', 
                'BobRoss'
            ]
        ]
    """

    vod_data: list = []
    loop_length: int = 0

    if multiple_streamers:
        loop_length = 3
    else: loop_length = 20

    load_streamer_id = System.load_id(streamer)

    if load_streamer_id == None:
        user_id_url: str = f"https://api.twitch.tv/helix/users?login={streamer}"
        request_id: int = httpx.get(user_id_url, headers=header).json()["data"][0]["id"]
    else:
        request_id = load_streamer_id['_id']
    
    async with httpx.AsyncClient() as client:
        find_video_url: str = f"https://api.twitch.tv/helix/videos?user_id={request_id}&type=archive"
        api_data: dict = await client.get(find_video_url, headers=header)
        data = indexVOD(loop_length, api_data, vod_data)
    
    return data

def indexVOD(loop_length: int, api_data: dict, vod_data: list) -> list[list]:
    """This function aggregates the data from the Twitch object.

    It loops over either 3, or 20 times, and fills in a list per video found with the details necessary.
    If a thumbnail_url is not found (usually, in the case of a livestream still going on), it sets a default one
    otherwise it gets it from the Twitch returned object. Lastly, appends the list to another list which
    contains all of the data.

    Args:
        loop_length: The length of the for loop, decided by the optional arg in getVOD().
        api_data: The Twitch object that is returned.
        vod_data: A list which contains lists of data (the videos).

    Returns:
        It returns a list of lists with each list containing data for a specific video. For example:

        [
            [
                'https://static-cdn.jtvnw.net/cf_vods/dgeft87wbj63p/ea762441364c25cb372d_bobross_44181880156_1640535689//thumb/thumb0-1920x1080.jpg', 
                'https://www.twitch.tv/videos/1243955144', 
                'Weekend Marathon! Beginning Fridays at 12pm ET.', 
                '24h46m34s', 
                '26 Dec, 16:21', 
                '123,236', 
                'BobRoss'
            ]
        ]
        
    Raises:
        IndexError: This usually occurs when the streamer has <20 (or 3) vods available.
    """

    try:
        for n in range(loop_length):
            thumbnail_url: str = api_data.json()["data"][n]["thumbnail_url"]
            vod_url: str = api_data.json()["data"][n]["url"]
            title: str = api_data.json()["data"][n]["title"]
            duration: str = api_data.json()["data"][n]["duration"]
            creation: str = api_data.json()["data"][n]["created_at"]
            view_count: str = api_data.json()["data"][n]["view_count"]
            username: str = api_data.json()["data"][n]["user_name"]
            if thumbnail_url == "":
                vod_data.append(["https://ffwallpaper.com/card/tv-static/tv-static--12.jpg", vod_url, title, duration, date_conversion(creation), ("{:,}".format(view_count)), username])
            else:
                thumbnail_url = thumbnail_url.replace("%{width}x%{height}.jpg", "1920x1080.jpg")
                vod_data.append([thumbnail_url, vod_url, title, duration, date_conversion(creation), ("{:,}".format(view_count)), username])
    except IndexError:
        pass
    
    return vod_data

def sort_vod(vod_data):
    """Returns a sorted version of the list of lists by date descending.

    Args:
        vod_data: A list of lists containing data on the streams, incl. the date to be sorted.
    
    Returns:
        It returns a list of lists sorted by date. For example:

        [
            [
                "https://static-cdn.jtvnw.net/cf_vods/dgeft87wbj63p/6fb581a75082f57bca9e_bobross_44115748764_1639932593//thumb/thumb0-1920x1080.jpg",
                "https://www.twitch.tv/videos/1237868145",
                "Weekend Marathon! Beginning Fridays at 12pm ET.",
                "24h15m36s",
                "19 Dec, 16:50",
                "107,471",
                "BobRoss"
            ]
        ]
    """

    return sorted(vod_data, key=lambda x: datetime.datetime.strptime(x[4], "%d %b, %H:%M"), reverse=True)


def get_streamer_id(header: dict[str, str], streamer_username: str) -> int:
    """Gets a streamer ID from the streamer username.

    Sends a GET request to Twitch and retrives the id returned.

    Args:
        header: A header containing the token necessary for this GET request.
        streamer_username: A string containing the streamer username.
    
    Returns:
        Depending on whether an IndexError is caught, the id is returned, for example:

        39393023

        Otherwise, a 0 is returned.

    Raises:
        IndexError: This usually occurs when for some reasons no id is available at index 0.
    """

    get_details: dict = httpx.get(f"https://api.twitch.tv/helix/users?login={streamer_username}", headers=header).json()

    try:
        return get_details["data"][0]["id"]
    except IndexError:
        return 0

def get_clips(header: dict[str, str], b_id: int) -> list[list]:
    """Gets clips from a specific twitch streamer.

    If the b_id passed through is equal to 0, then an empty list is returned (it's only equal to 0 if an ID cannot be found, usually in the case of
    non-existing streamer usernames). Otherwise, a GET request is sent to Twitch with the header provided.

    Args:
        header: A header containing the token necessary for this GET request.
        b_id: Short for broadcaster ID, the ID of the twitch channel.

    Returns:
        This functions returns a list of clips, which contained a list inside the list (if the bID is not equal to 0). For example:

        [
            ['76,912', 11.6, 'LIGHTNING FAST', '31 May, 15:19', 'https://clips.twitch.tv/PreciousMoralAnacondaDatSheffy', 'https://clips-media-assets2.twitch.tv/AT-cm%7C732699532-preview-480x272.jpg'], 
            ['36,932', 8, 'senny snez', '26 Dec, 18:21', 'https://clips.twitch.tv/FaintHealthyBeeDendiFace-rwIg6bsmvdfgyNtz', 'https://clips-media-assets2.twitch.tv/AT-cm%7C7k3EeK8CIOm7Jr3X4Mjbcw-preview-480x272.jpg'], 
            ['25,169', 44, 'Kenny about ZywOo', '11 May, 13:24', 'https://clips.twitch.tv/PopularNimbleGarageRickroll', 'https://clips-media-assets2.twitch.tv/AT-cm%7C706807069-preview-480x272.jpg']
        ]
    """
    
    clip_list: list = []

    if b_id == 0:
        return clip_list
    else:
        get_details: dict = httpx.get(f"https://api.twitch.tv/helix/clips?broadcaster_id={b_id}&first=3", headers=header).json()

    for i in get_details['data']:
        clip_list.append([("{:,}".format(i['view_count'])), i['duration'], i['title'], date_conversion(i['created_at']), i['url'], i['thumbnail_url']])

    return clip_list

def get_data(streamer: str)-> dict[str, list]:
    """Gets streamer data.

    This function takes in a streamer username, and stores certain data returned from the Twitchtracker API, such as their follower counts, max attained viwers in the last 30 days,
    and more.

    Args:
        streamer: The streamer who the data will be searched for.

    Returns:
        A dict mapping keys to the corresponding values, with the keys being a streamer username
        and the data being a list of values (if a KeyError is not caught). For example:

        {
            'kennyS': [793, '3,244', '6,931', '16,747', '844,233', '18,684,096']
        }

    Raises:
        KeyError: An error is raised if the key is not in the dictionary.
    """

    streamer_dict: dict = {}
    get_details: dict = httpx.get(f"https://twitchtracker.com/api/channels/summary/{streamer}", headers={'User-Agent': 'Chrome'}).json()

    try:
        streamer_dict[streamer] = [get_details['rank'], ("{:,}".format(get_details['avg_viewers'])), ("{:,}".format(get_details['max_viewers'])), 
                             ("{:,}".format(get_details['followers'])), ("{:,}".format(get_details['followers_total'])), ("{:,}".format(get_details['views_total']))]
    except KeyError:
        streamer_dict[streamer] = []

    return streamer_dict

def get_bans(streamer: str) -> dict:
    """Gets ban information about a specific streamer.

    This function sends a GET request to streamerbans with a specific name and scrapes the data of the website, which in turn
    finds out previous ban history about a streamer.

    Args:
        streamer: The streamer who the ban data will be searched for.
    
    Returns:
        A dict mapping keys to the corresponding values, with the keys being a streamer username
        and the data being a list of values (if a IndexError is not caught). For example:

        {
            'forsen': [['3', 'a year ago', 'a month'], 0]
        }
    
    Raises:
        IndexError: Can be raised under multiple conditions, whether a specific css class is not found.
    """

    bans_dict: dict = {}
    ban_information: list = []
    get_ban_status: str = ""
    get_details: str = httpx.get(f"https://streamerbans.com/user/{streamer}").text

    try:
        bs4_obj = BeautifulSoup(get_details, 'lxml')
        total_bans = bs4_obj.find_all("dd", {"class": "text-3xl"})
        get_ban_status = bs4_obj.find_all(("p"), {"class": "text-sm"})[-1]
    except IndexError:
        bans_dict[streamer] = [[], 0]
        return bans_dict

    try:
        get_track_status = bs4_obj.find_all(("h1"), {"class": "my-24"})[0]
    except IndexError:
        get_track_status = ""

    for n in total_bans:
        ban_information.append(n.text)

    if "Unbanned" in get_ban_status.text or get_track_status:
        current_ban = 0
    else: current_ban = 1

    if get_track_status:
        bans_dict[streamer] = [[], current_ban]
    else:    
        bans_dict[streamer] = [ban_information, current_ban]

    return bans_dict

def epoch_conversion(**kwargs: dict):
    """Converts time to a specific format.

    This function takes in a 'kwargs' argument, which is an optional argument which takes in an arbitrary number of keyword arguments,
    then depending on whether it's passed through or not, a different parsing method is used for the time conversion.

    Args:
        **kwargs: An optional argument, which if passed, passes through a data object containing information about a streamer.

    Returns:
        A time, in the format: '%d.%m.%Y %H:%M:%S' casted as a string. For example:

        0:02:02

    Raises:
        KeyError: A KeyError is raised when the kwargs['jsonData']['data'] is not found.
    """

    try:
        twitch_api_date_parsed = parser.parse(kwargs['jsonData']["data"][kwargs['index']]["started_at"]).strftime("%d.%m.%Y %H:%M:%S")
    except KeyError: 
        twitch_api_date_parsed = parser.parse(kwargs['data']["started_at"]).strftime("%d.%m.%Y %H:%M:%S")

    epoch_current = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    epoch_difference = epoch_current - int(time.mktime(time.strptime(twitch_api_date_parsed, "%d.%m.%Y %H:%M:%S")))
    return str(datetime.timedelta(seconds = epoch_difference))

def date_conversion(created_at: str):
    """Converts time to a specific format.

    This function sets a specific formatter, proceeds to create an object with that format given a date and returns it.

    Args:
        created_at: A 'Z' formatted date, which is to be formatted.
    
    Returns:
        A converted date format, for example:

        15 Dec, 11:40
    """

    formatter: str = '%Y-%m-%dT%H:%M:%SZ'
    dt_obj = datetime.datetime.strptime(created_at, formatter)
    converted_date = dt_obj.strftime("%#d %b, %H:%M")

    return converted_date

def add_to_favourites(streamer_name: str):
    user_data_id: int = session["user"]["_id"]
    User.add_delete_favourites(user_data_id, streamer_name)