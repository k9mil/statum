from flask import request, session
from statum.users.models import User, System
from statum.config import Config
from furl import furl
from bs4 import BeautifulSoup
from dateutil import parser
from statum import create_app, database
import json, httpx, random, datetime, time

def load_default_data():
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

    with open("statum\static\streamers.json", "r") as json_data:
        streamer_list = json.load(json_data)
        json_data.close()
        return streamer_list

def randomIndexedStream(streamers):
    """Receives a list of streamers and returns a random individual.

    Args:
        streamers: A list of Twitch streamers.
    
    Returns:
        None
    """

    return random.choice(streamers)

def randomStream():
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

    MAX_VIEWERS = 100
    MIN_VIEWERS = 10
    request_status = True
    streamerIDs = []

    header = generateToken("bearer")
    usersFollowedURL = "https://api.twitch.tv/helix/streams"
    getStreamsRequest = httpx.get(usersFollowedURL, headers=header).json()

    while request_status != False:
        usersFollowedURL = f"https://api.twitch.tv/helix/streams?first=100&after={getStreamsRequest['pagination']['cursor']}"
        getStreamsRequest = httpx.get(usersFollowedURL, headers=header).json()
        requestInstances = (len(getStreamsRequest["data"]) - 1)

        if (getStreamsRequest['data'][0]['viewer_count'] < MAX_VIEWERS):
            print('balls')
            indexRandom(getStreamsRequest, streamerIDs)

        if (getStreamsRequest['data'][requestInstances]['viewer_count'] < MIN_VIEWERS):
            request_status = False
        else: 
            pass
    
    System.indexRandomDB(streamerIDs)
    randomStreamer = chooseRandom(streamerIDs)
    return randomStreamer

def indexRandom(getStreamsRequest, streamerIDs):
    """This function iterates over a sequence * times depending on the length of the GET request returned.

    It assigns the length of the GET request to a variable and loops over that amount of times, and checks whether the
    username of the streamer is compatible with Ascii, as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.

    Args:
        getStreamsRequest: Jsonified GET request return from the Twitch API.
        streamerIDs: A list of the streamers (to be later picked random from).
    
    Returns:
        A list of the streamers, located in the "streamerIDs" variable.
    """

    requestInstances = len(getStreamsRequest["data"])
    for i in range(requestInstances):
        if getStreamsRequest['data'][i]['user_name'].isascii():
            streamerIDs.append(getStreamsRequest['data'][i]['user_name'])
        else:
            streamerIDs.append(getStreamsRequest['data'][i]['user_login'])
    
    return streamerIDs

def chooseRandom(streamerIDs):
    """Receives a list of streamers and returns a random individual.

    Args:
        streamersIDs: A list of Twitch streamers.

    Returns:
        None
    """

    return random.choice(streamerIDs)

def generateToken(*bearer):
    """Generates a Token which is necessary for some Twitch API calls.

    Initially is assigns the full request path to the "f" variable, and if a bearer was provided it assigns a URL which contains a grant_type
    of "authorization_code", a redirect_uri & arguments from the URL, provided by Twitch. Otherwise it just contains a grant type of "client_credentials".
    It then posts either URL as a request and returns the result.

    Args:
        *bearer: An optional argument which decides what kind of URL is created (that is then used to generate a token).

    Returns:
        A header received by the Twitch API.
    """

    f = furl(request.full_path)

    if bearer:
        URL = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=client_credentials"
    else:
        URL = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=authorization_code&redirect_uri=http://localhost:5000&code={f.args['code']}"
    
    postedURL = httpx.post(URL).json()
    header = {'Authorization': 'Bearer ' + postedURL["access_token"], 'Client-ID': Config.CLIENT_ID}

    return header

def twitch_login(header):
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

    streamer_list = {}
    users_url = "https://api.twitch.tv/helix/users"

    if session:
        user_data_id = session["user"]["_id"]
    else:
        response_result = httpx.get(users_url, headers=header).json()
        user_data_id = response_result["data"][0]["id"]

    usersFollowedURL = f"https://api.twitch.tv/helix/users/follows?from_id={user_data_id}"
    followRequest = httpx.get(usersFollowedURL, headers=header).json()
    streamersFollowed = len(followRequest["data"])

    for value in range(streamersFollowed):
        streamerName = followRequest["data"][value]["to_name"]
        if streamerName.isascii():
            streamer_list[streamerName] = f"https://twitch.tv/{streamerName}"
        else:
            streamerName = followRequest["data"][value]["to_login"]
            streamer_list[streamerName] = f"https://twitch.tv/{streamerName}"
    
    User().twitchSignup(user_data_id, streamer_list)
    return streamer_list 

async def send_requests(streamer_data, streamer_list, top_streamer_data, clips_data):
    """An asynchronous function which serves as a middleman and it's necessary function is to call other functions.

    First, it generates a token and stores it in the "header" variable, and proceeds to call
    indexStreamerData(), loadStreamers(), loadTopStreamers() and lastly loadClips()

    Args:
        streamer_data: Contains an (empty) dictionary of the data held on streamers.
        streamer_list: Contains a dictionary which holds the streamer names as keys, and the URLs as their values.
        top_streamer_data: Contains an (empty) dictionary of the top streamers' data.
        clips_data: Contains an (empty) dictionary of the data necessary to render the top circulating clips.
    
    Returns:
        None
    """

    header = generateToken("bearer")
    await indexStreamerData(header, streamer_list, streamer_data)
    loadStreamers(header, streamer_list, streamer_data)
    loadTopStreamers(header, top_streamer_data)
    loadClips(clips_data)

def loadTopStreamers(header, top_streamer_data):
    """Sends a GET request to the Twitch API with the headers provided, to get a collection of top streamers actively live on the platform.

    After the request is sent, showTopStreamerData() is called passing the empty dictionary as well as the result from the GET request.

    Args:
        header: The header returned by Twitch containing the token.
        top_streamer_data: The empty dictionary which will hold the data of the top streamers.

    Returns:
        None
    """

    getDetails = httpx.get("https://api.twitch.tv/helix/streams", headers=header).json()
    showTopStreamerData(top_streamer_data, getDetails['data']) 

def loadClips(clips_data):
    """Sends a GET request to the Reddit API, to get a collection of top posts on r/livestreamfail, a popular twitch-related subreddit.

    After the request is sent, showTopClips() is called passing the empty dictionary..

    Args:
        clips_data: The empty dictionary which will hold the data of the top circulating posts on the platform.

    Returns:
        None
    """

    getDetails = httpx.get("https://www.reddit.com/r/livestreamfail/hot.json?limit=20").json()
    showTopClips(clips_data, getDetails['data']) 

def loadStreamers(header, streamer_list, streamer_data):
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

    stream_url = "https://api.twitch.tv/helix/streams?"
    liveStreamers = []
    notLiveStreamers = []

    for streamer in streamer_list:
        stream_url += "user_login=" + streamer + "&"

    getDetails = httpx.get(stream_url, headers=header)
    getDetailsJSON = getDetails.json()

    for n in getDetailsJSON['data']:
        if n['user_name'].isascii():
            liveStreamers.append(n['user_name'])
        else:
            liveStreamers.append(n['user_login'])
    
    for n in streamer_list:
        if n not in liveStreamers:
            notLiveStreamers.append(n)

    showStreamerData(streamer_data, getDetailsJSON['data'], notLiveStreamers)

def showStreamerData(streamer_data, getDetailsJSON, notLiveStreamers):
    """This function ensures that the streamer data dictionary passed through is populated.

    It loops through the jsonified returned request and again, it checks whether it is ascii compatible,
    as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.

    It also loops through the not live streamers, and sets different parameters for them.

    Args:
        streamer_data: Contains an empty dictionary which will map twitch usernames to keys to a list of values.
        getDetailsJSON: Contains the returned JSON object from the GET request sent to Twitch, which contains the data of streamers.
        notLiveStreamers: Contains a list which contains the usernames of the streamers that the user follows which are not currently live.

    Returns:
        A dict mapping keys to the corresponding values, with the keys being the Twitch usernames
        and the values are a list, which contains their live status, game name & time streamed. For example:

        {
            'TommyKayLIVE': ['LIVE', 'EA Sports UFC 4', '5:39:42'], 
            'BLASTPremier': ['NOT LIVE', 'none', 'none']
        }
    """

    for n in getDetailsJSON:
        if n['user_name'].isascii():
            streamer_data[n['user_name']] = ["LIVE", n["game_name"], epochConversion(data = n)]
        else:
            streamer_data[n['user_login']] = ["LIVE", n["game_name"], epochConversion(data = n)]

    for n in notLiveStreamers:
        streamer_data[n] = ["NOT LIVE", "none", "none"]

    return streamer_data

def showTopStreamerData(top_streamer_data, getDetailsJSON):
    """This function ensures that the top streamer data dictionary passed through is populated.

    It loops through the jsonified returned request and again, it checks whether it is ascii compatible,
    as isascii() returns either True or False. This is to help properly
    manage Twitch streamers with, Chinese characters for instance. If it returns True, the user_name is appended from the GET request
    other wise it's user_login.

    Args:
        top_streamer_data: Contains an empty dictionary which will map twitch usernames to keys to a list of values.
        getDetailsJSON: Contains the returned JSON object from the GET request sent to Twitch, which contains the data of top streamers.

    Returns:
        None
    """

    for n in getDetailsJSON:
        if n['user_name'].isascii():
            top_streamer_data[n['user_name']] = ["LIVE", n["game_name"], epochConversion(data = n)]
        else:
            top_streamer_data[n['user_login']] = ["LIVE", n["game_name"], epochConversion(data = n)]

def showTopClips(clips_data, getDetails):
    """This function ensures that clips data dictionary passed through is populated.

    It loops through the request object returned by the GET request, and populates the clips_data dictionary with the relevant information.

    Args:
        clips_data: Contains an empty dictionary which will map the keys to a list of values.
        getDetails: Contains the returned JSON object from the GET request sent to Reddit, which contains the data of the subreddits' posts.

    Returns:
        None
    """
    for n in getDetails['children']:
        clips_data[n["data"]["title"]] = [n["data"]["permalink"], n["data"]["score"], n["data"]["num_comments"]]

async def indexStreamerData(header, streamer_list, streamer_data):
    """Asynchronously indexes streamer data, to ensure faster loading times.

    Using async, it loops through the list of streamer and checks whether they exists by querying MongoDB with the name of the streamer,
    if the streamer exists (that is, already indexed) then the for loop passes, and proceeds to check the next username, otherwise it
    sends a GET request to Twitch and calls indexStreamer() with a list of items returned with a specific query, the query being the username
    of the streamer.

    Args:
        header: A header holding the token generated by Twitch.
        streamer_list: A dictionary holding streamers' information, with the username as keys and a list of values per user.
        streamer_data: An empty dictionary which will be populated.

    Returns:
        None
    """

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

def indexStreamer(results, streamer_data, getDetailsJSON, streamer):
    """Indexes the streamer data.

    Loops through an arbitrary number of times, depending on the length of results passed through. Due to the way Twitch API works,
    it returns multiple channels that may not always match the streamer, so we confirm the login is equal to the streamer username passed through.
    If it matches, try and index the streamer and populate data if the streamer is live, otherwise populate with differnet data.

    Args:
        results:
        streamer_data:
        getDetailsJSON:
        streamer:

    Returns:
        .

    Raises:
        parser.ParserError: 

    """

    for numb in range(results):
        if getDetailsJSON["data"][numb]["broadcaster_login"] == streamer.lower():
            try:
                System().indexStreamer(getDetailsJSON["data"][numb]["id"], getDetailsJSON["data"][numb]["broadcaster_login"])
                if getDetailsJSON["data"][numb]["is_live"] == True:
                    streamer_data[streamer] = ["LIVE", getDetailsJSON["data"][numb]["game_name"], epochConversion(jsonData=getDetailsJSON, index=numb)]
                else:
                    streamer_data[streamer] = ["NOT LIVE", "none", "none"]
            except parser.ParserError:
                pass
            break
        else:
            pass
    return streamer_data

def getVOD(streamer):
    """Gets VOD data from a specific streamer that is passed through as an argument.

    As usual, it generates a token, and then proceeds to send two GET requests to Twitch, 
    one which retrieves the id for the streamer and the other one which gets the users' videos (vods).
    It then proceeds to loop through a set number of 20 times and assign the logical retrieved data to variables,
    and lastly assign then to a dictionary which will be returned.

    Args:
        streamer: Contains a string of the streamer name.

    Returns:
        A dict mapping keys to the corresponding values, with the keys being a number ranging
        from 0 to 20, and the data being a list of values. For example:

        {
            0: ['https://ffwallpaper.com/card/tv-static/tv-static--12.jpg', 'https://www.twitch.tv/videos/1243998438', 
            'DIA DE RAFT E NBA! !sorteio - Siga @Gaules nas redes sociais', '25h46m2s', '26 Dec, 17:21', '7,751']
        }
    
    Raises:
        IndexError: This usually occurs when the streamer has < 20 vods available.
    """

    vod_data = {}
    header = generateToken("bearer")

    userIDURL = f"https://api.twitch.tv/helix/users?login={streamer}"
    requestID = httpx.get(userIDURL, headers=header).json()["data"][0]["id"]

    findVideoURL = f"https://api.twitch.tv/helix/videos?user_id={requestID}&type=archive"
    responseC = httpx.get(findVideoURL, headers=header)

    try:
        for n in range(20):
            thumbnail_url = responseC.json()["data"][n]["thumbnail_url"]
            vod_url = responseC.json()["data"][n]["url"]
            title = responseC.json()["data"][n]["title"]
            duration = responseC.json()["data"][n]["duration"]
            creation = responseC.json()["data"][n]["created_at"]
            view_count = responseC.json()["data"][n]["view_count"]
            if thumbnail_url == "":
                vod_data[n] = ["https://ffwallpaper.com/card/tv-static/tv-static--12.jpg", vod_url, title, duration, dateConversion(creation), ("{:,}".format(view_count))]
            else:
                thumbnail_url = thumbnail_url.replace("%{width}x%{height}.jpg", "1920x1080.jpg")
                vod_data[n] = [thumbnail_url, vod_url, title, duration, dateConversion(creation), ("{:,}".format(view_count))]
    except IndexError:
        pass
    
    return vod_data

def getStreamerID(header, streamerUsername):
    """Gets a streamer ID from the streamer username.

    Sends a GET request to Twitch and retrives the id returned.

    Args:
        header: A header containing the token necessary for this GET request.
        streamerUsername: A string containing the streamer username.
    
    Returns:
        Depending on whether an IndexError is caught, the id is returned, for example:

        39393023

        Otherwise, a 0 is returned.

    Raises:
        IndexError: This usually occurs when for some reasons no id is available at index 0.
    """
    getDetails = httpx.get(f"https://api.twitch.tv/helix/users?login={streamerUsername}", headers=header).json()

    try:
        return getDetails["data"][0]["id"]
    except IndexError:
        return 0

def getClips(header, bID):
    """Gets clips from a specific twitch streamer.

    If the bID passed through is equal to 0, then an empty list is returned (it's only equal to 0 if an ID cannot be found, usually in the case of
    non-existing streamer usernames). Otherwise, a GET request is sent to Twitch with the header provided.

    Args:
        header: A header containing the token necessary for this GET request.
        bID: Short for broadcaster ID, the ID of the twitch channel.

    Returns:
        This functions returns a list of clips, which contained a list inside the list (if the bID is not equal to 0). For example:

        [
            ['76,912', 11.6, 'LIGHTNING FAST', '31 May, 15:19', 'https://clips.twitch.tv/PreciousMoralAnacondaDatSheffy', 'https://clips-media-assets2.twitch.tv/AT-cm%7C732699532-preview-480x272.jpg'], 
            ['36,932', 8, 'senny snez', '26 Dec, 18:21', 'https://clips.twitch.tv/FaintHealthyBeeDendiFace-rwIg6bsmvdfgyNtz', 'https://clips-media-assets2.twitch.tv/AT-cm%7C7k3EeK8CIOm7Jr3X4Mjbcw-preview-480x272.jpg'], 
            ['25,169', 44, 'Kenny about ZywOo', '11 May, 13:24', 'https://clips.twitch.tv/PopularNimbleGarageRickroll', 'https://clips-media-assets2.twitch.tv/AT-cm%7C706807069-preview-480x272.jpg']
        ]
    """
    
    clipList = []

    if bID == 0:
        return clipList
    else:
        getDetails = httpx.get(f"https://api.twitch.tv/helix/clips?broadcaster_id={bID}&first=3", headers=header).json()

    for i in getDetails['data']:
        clipList.append([("{:,}".format(i['view_count'])), i['duration'], i['title'], dateConversion(i['created_at']), i['url'], i['thumbnail_url']])

    return clipList

def getData(streamer):
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

    streamerDict = {}
    getDetails = httpx.get(f"https://twitchtracker.com/api/channels/summary/{streamer}", headers={'User-Agent': 'Chrome'}).json()

    try:
        streamerDict[streamer] = [getDetails['rank'], ("{:,}".format(getDetails['avg_viewers'])), ("{:,}".format(getDetails['max_viewers'])), 
                             ("{:,}".format(getDetails['followers'])), ("{:,}".format(getDetails['followers_total'])), ("{:,}".format(getDetails['views_total']))]
    except KeyError:
        streamerDict[streamer] = []

    return streamerDict

def getBans(streamer):
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

    bansDict = {}
    banInformation = []
    getBanStatus = ""
    getDetails = httpx.get(f"https://streamerbans.com/user/{streamer}").text

    try:
        bs4Obj = BeautifulSoup(getDetails, 'lxml')
        totalBans = bs4Obj.find_all("dd", {"class": "text-3xl"})
        getBanStatus = bs4Obj.find_all(("p"), {"class": "text-sm"})[-1]
    except IndexError:
        bansDict[streamer] = [[], 0]
        return bansDict

    try:
        getTrackStatus = bs4Obj.find_all(("h1"), {"class": "my-24"})[0]
    except IndexError:
        getTrackStatus = ""

    for n in totalBans:
        banInformation.append(n.text)

    if "Unbanned" in getBanStatus.text or getTrackStatus:
        currentBan = 0
    else: currentBan = 1

    if getTrackStatus:
        bansDict[streamer] = [[], currentBan]
    else:    
        bansDict[streamer] = [banInformation, currentBan]

    return bansDict

def epochConversion(**kwargs):
    """Converts time to a specific format.

    This function takes in a 'kwargs' argument, which is an optional argument which takes in an arbitrary number of keyword arguments,
    then depending on whether it's passed through or not, a different parsing method is used for the time conversion.

    Args:
        **kwargs: An optional argument, which if passed, passes through a data object containing information about a streamer.

    Returns:
        A time, in the format: '%d.%m.%Y %H:%M:%S' casted as a string. For example:

        0:02:02
    """

    print(kwargs)

    if not kwargs['data']:
        twitch_api_date_parsed = parser.parse(kwargs['jsonData']["data"][kwargs['index']]["started_at"]).strftime("%d.%m.%Y %H:%M:%S")
    else: 
        twitch_api_date_parsed = parser.parse(kwargs['data']["started_at"]).strftime("%d.%m.%Y %H:%M:%S")

    epochCurrent = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    epochDifference = epochCurrent - int(time.mktime(time.strptime(twitch_api_date_parsed, "%d.%m.%Y %H:%M:%S")))
    return str(datetime.timedelta(seconds = epochDifference))

def dateConversion(created_at):
    """Converts time to a specific format.

    This function sets a specific formatter, proceeds to create an object with that format given a date and returns it.

    Args:
        created_at: A 'Z' formatted date, which is to be formatted.
    
    Returns:
        A converted date format, for example:

        15 Dec, 11:40
    """

    formatter = '%Y-%m-%dT%H:%M:%SZ'
    dtobj = datetime.datetime.strptime(created_at, formatter)
    convertedDate = dtobj.strftime("%#d %b, %H:%M")

    return convertedDate