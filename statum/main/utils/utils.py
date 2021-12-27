from flask import request, session
from statum.users.models import User, System
from statum.config import Config
from furl import furl
from bs4 import BeautifulSoup
from dateutil import parser
from statum import database
import json, httpx, random, datetime, time

def load_default_data():
    with open("statum\static\streamers.json", "r") as json_data:
        streamer_list = json.load(json_data)
        json_data.close()
        return streamer_list

def randomIndexedStream(streamers):
    return random.choice(streamers)

def randomStream():
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
    requestInstances = len(getStreamsRequest["data"])
    for i in range(requestInstances):
        if getStreamsRequest['data'][i]['user_name'].isascii():
            streamerIDs.append(getStreamsRequest['data'][i]['user_name'])
        else:
            streamerIDs.append(getStreamsRequest['data'][i]['user_login'])
    
    print(getStreamsRequest['data'])
    print(getStreamsRequest['data'][0])
    print(streamerIDs[0])
    return streamerIDs

def chooseRandom(streamerIDs):
    return random.choice(streamerIDs)

def generateToken(*bearer):
    f = furl(request.full_path)

    if bearer:
        URL = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=client_credentials"
    else:
        URL = f"https://id.twitch.tv/oauth2/token?client_id={Config.CLIENT_ID}&client_secret={Config.AUTH_KEY}&grant_type=authorization_code&redirect_uri=http://localhost:5000&code={f.args['code']}"
    
    postedURL = httpx.post(URL).json()
    header = {'Authorization': 'Bearer ' + postedURL["access_token"], 'Client-ID': Config.CLIENT_ID}
    return header

def twitch_login(header):
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
        streamer_list[streamerName] = f"https://twitch.tv/{streamerName}"
    
    User().twitchSignup(user_data_id, streamer_list)
    return streamer_list 

async def send_requests(streamer_data, streamer_list, top_streamer_data, clips_data):
    header = generateToken("bearer")
    indexStreamerData(header, streamer_list, streamer_data)
    loadStreamers(header, streamer_list, streamer_data)
    loadTopStreamers(header, top_streamer_data)
    loadClips(clips_data)

def loadTopStreamers(header, top_streamer_data):
    getDetails = httpx.get("https://api.twitch.tv/helix/streams", headers=header).json()
    showTopStreamerData(top_streamer_data, getDetails['data']) 

def loadClips(clips_data):
    getDetails = httpx.get("https://www.reddit.com/r/livestreamfail/hot.json?limit=20").json()
    showTopClips(clips_data, getDetails['data']) 

def loadStreamers(header, streamer_list, streamer_data):
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
    for n in getDetailsJSON:
        if n['user_name'].isascii():
            streamer_data[n['user_name']] = ["LIVE", n["game_name"], epochConversion(data = n)]
        else:
            streamer_data[n['user_login']] = ["LIVE", n["game_name"], epochConversion(data = n)]

    for n in notLiveStreamers:
        streamer_data[n] = ["NOT LIVE", "none", "none"]

    return streamer_data

def showTopStreamerData(top_streamer_data, getDetailsJSON):
    for n in getDetailsJSON:
        if n['user_name'].isascii():
            top_streamer_data[n['user_name']] = ["LIVE", n["game_name"], epochConversion(data = n)]
        else:
            top_streamer_data[n['user_login']] = ["LIVE", n["game_name"], epochConversion(data = n)]

def showTopClips(clips_data, getDetails):
    for n in getDetails['children']:
        clips_data[n["data"]["title"]] = [n["data"]["permalink"], n["data"]["score"], n["data"]["num_comments"]]

async def indexStreamerData(header, streamer_list, streamer_data):
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
    getDetails = httpx.get(f"https://api.twitch.tv/helix/users?login={streamerUsername}", headers=header).json()

    try:
        return getDetails["data"][0]["id"]
    except IndexError:
        return 0

def getClips(header, bID):
    clipList = []

    if bID == 0:
        return clipList
    else:
        getDetails = httpx.get(f"https://api.twitch.tv/helix/clips?broadcaster_id={bID}&first=3", headers=header).json()

    for i in getDetails['data']:
        clipList.append([("{:,}".format(i['view_count'])), i['duration'], i['title'], dateConversion(i['created_at']), i['url'], i['thumbnail_url']])
    
    return clipList

def getData(streamer):
    streamerDict = {}
    getDetails = httpx.get(f"https://twitchtracker.com/api/channels/summary/{streamer}", headers={'User-Agent': 'Chrome'}).json()

    try:
        streamerDict[streamer] = [getDetails['rank'], ("{:,}".format(getDetails['avg_viewers'])), ("{:,}".format(getDetails['max_viewers'])), 
                             ("{:,}".format(getDetails['followers'])), ("{:,}".format(getDetails['followers_total'])), ("{:,}".format(getDetails['views_total']))]
    except KeyError:
        streamerDict[streamer] = []

    return streamerDict

def getBans(streamer):
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
    if not kwargs['data']:
        twitch_api_date_parsed = parser.parse(kwargs['jsonData']["data"][kwargs['index']]["started_at"]).strftime("%d.%m.%Y %H:%M:%S")
    else: 
        twitch_api_date_parsed = parser.parse(kwargs['data']["started_at"]).strftime("%d.%m.%Y %H:%M:%S")

    epochCurrent = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    epochDifference = epochCurrent - int(time.mktime(time.strptime(twitch_api_date_parsed, "%d.%m.%Y %H:%M:%S")))
    return str(datetime.timedelta(seconds = epochDifference))

def dateConversion(created_at):
    formatter = '%Y-%m-%dT%H:%M:%SZ'
    dtobj = datetime.datetime.strptime(created_at, formatter)
    convertedDate = dtobj.strftime("%#d %b, %H:%M")
    return convertedDate