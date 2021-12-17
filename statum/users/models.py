from flask import jsonify, session
from statum import database

class User:
<<<<<<< HEAD
    def start_session(self, user):
=======
    def startSession(self, user):
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
        session["logged_in"] = True
        session["user"] = user
        return jsonify(user), 200

<<<<<<< HEAD
    def twitch_signup(self, user_id, follower_list):
=======
    def twitchSignup(self, user_id, follower_list):
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
        user = {
            "_id": user_id,
            "follower_list": follower_list
        }
        
<<<<<<< HEAD
        if database["twitch_user_data.user._id"]:
            database.twitch_user_data.find_one_and_update(
                {"_id": user_id,},
=======
        if database.twitch_user_data.count_documents({'_id': user_id}) != 0:
            database.twitch_user_data.find_one_and_update(
                {"_id": user_id},
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
                {"$set":
                    {"follower_list": follower_list}
                }
            )
<<<<<<< HEAD
            return self.start_session(user)
        else:
            database.twitch_user_data.insert_one(user)
            return self.start_session(user)
=======
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
>>>>>>> 937744f (long break from codebase. changed a lot. upgraded request system by optimizing twitch api limitations.)
