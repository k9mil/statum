from flask import jsonify, session
from statum import database

class User:
    """This class deals mostly with the User part of the database.

    Contains a function which aims to start a session, as well as a function which deals with storing one's
    followers in MongoDB.

    """

    def startSession(self, user):
        """Starts a session.

        With session being imported from flask, it assigns the logged_in var to true and the user to the user passed through to the function.

        Args:
            user: A user object.
        
        Returns:
            A jsonified object of the user with a 200 return code.
        """

        session["logged_in"] = True
        session["user"] = user
        return jsonify(user), 200

    def twitchSignup(self, user_id: int, follower_list: dict[str, str]):
        """Adds, or inserts data into the database with the users' follows.

        Creates a user object comprised of an id (the user id) as well as the follower list passed through
        as an argument. A query is made on MongoDB, if a result is found for a user the DB is updated,
        else an entry is created. A session is returned.

        Args:
            user_id: A user (id) which serves as a unique identifier.
            follower_list: A dictionary which contains twitch usernames as keys, and URLs as their values.
        
        Returns:
            A session is returned.
        """
        user: dict[int, dict[str, str]] = {
            "_id": user_id,
            "follower_list": follower_list,
            "favourites": []
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

    def addDeleteFavourites(user_id: int, streamer_name: str):
        """Adds/deleted a favourite streamer to the user id.

        A query is made to see whether the user exists, if it does, it finds the users' object
        in the 'twitch_user_data' table, and pushes the streamer that is favourited
        onto the database object. If it does exist, it acts as the inverse and deleted
        the streamer from the favourites.

        Args:
            user_id: A user (id) which serves as a unique identifier.
            streamer_name: The twitch username of the streamer to be added as a favourite.
        
        Returns:
            None
        """

        if database.twitch_user_data.count_documents({'_id': user_id}) != 0:
            if database.twitch_user_data.count_documents({'favourites': streamer_name}) == 0:
                database.twitch_user_data.find_one_and_update(
                    {"_id": user_id},
                    {"$push": {'favourites': streamer_name }}
                )
            else:
                database.twitch_user_data.find_one_and_update(
                    {"_id": user_id},
                    {"$pull": {'favourites': streamer_name }}
                )
        else:
            pass
        
    def loadFavourites(user_id: int) -> list[str]:
        """Loads a list of the users' favourite streamer.

        It queries the database and if the count isn't 0 (that is, if something is in the database),
        it returns a dictionary with the MongoDB object, containing the user_id and the list
        of streamers.

        Args:
            user_id: A user (id) which serves as a unique identifier.

        Returns:
            A list of the users' favourite streamers. For example:

            [
                'summit1g', 'BobRoss', 'summit1g'
            ]
        """

        if database.twitch_user_data.count_documents({'_id': user_id}) != 0:
            return database.twitch_user_data.find_one({'_id': user_id})['favourites']
        else:
            pass

