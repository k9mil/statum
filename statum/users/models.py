from flask import jsonify, session
from statum import database

class User:
    def startSession(self, user):
        session["logged_in"] = True
        session["user"] = user
        return jsonify(user), 200

    def twitchSignup(self, user_id, follower_list):
        user = {
            "_id": user_id,
            "follower_list": follower_list
        }
        
        if database.twitch_user_data.count_documents({'_id': user_id}) != 0:
            database.twitch_user_data.find_one_and_update(
                {"_id": user_id},
                {"$set":
                    {"follower_list": follower_list}
                }
            )
            return self.startSession(user)
        else:
            database.twitch_user_data.insert_one(user)
            return self.startSession(user)

class System:
    def indexStreamer(self, broadcaster_id, broadcaster_username):
        broadcaster = {
            "_id": broadcaster_id,
            "broadcaster_name": broadcaster_username
        }

        if database.twitch_streamer_data.count_documents({'_id': broadcaster_id}) != 0:
            pass
        else:
            database.twitch_streamer_data.insert_one(broadcaster)
            return 1
