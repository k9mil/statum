from statum import database

class System:
    """This class mainly deals with the system part of the database, with indexing & loading.

    Contains three functions, a function to index streamers, temporarily indexing random streamers which get re-indexed
    every 10 minutes & loading a random streamer.

    """
    def indexStreamer(self, broadcaster_id, broadcaster_username):
        """Indexes a streamer into the database.

        Creates a broadcaster object comprised of an id (the streamer id), as well as the streamer (broadcaster) username,
        after that it queries the database to check if the broadcaster id is already present in the db, if it is then
        it passes, if not then it inserts the object into MongoDB.

        Args:
            broadcaster_id: The id of the streamer.
            broadcaster_username: The twitch username of the streamer.

        Returns:
            None
        """
        broadcaster = {
            "_id": broadcaster_id,
            "broadcaster_name": broadcaster_username
        }

        if database.twitch_streamer_data.count_documents({'_id': broadcaster_id}) != 0:
            pass
        else:
            database.twitch_streamer_data.insert_one(broadcaster)

    def indexRandomDB(streamerIDs):
        """Indexes streamers into the DB used for the /random/ endpoint.

        Creates a streams object comprised of an id (static, 1), as well as a streamer list
        under the name of "streamerIDs". It then queries the database to check if an id of "1"
        exists, that is, if random streamers are already indexed, if so, it passes. Else, it inserts
        the object into MongoDB.

        Args:
            streamerIDs: A list of streamers to be indexed.

        Returns:
            None
        """
        streams = {
            "_id": 1,
            "streamers": streamerIDs
        }

        if database.random_streamer_data.count_documents({'_id': 1}) != 0:
            pass
        else:
            database.random_streamer_data.insert_one(streams)

    def loadRandom():
        """Loads a random streamer from the database.

        It queries the database and if the count isn't 0 (that is, if something is in the database),
        it returns a random streamer name via "find_one()", else it passes.

        Args:
            None

        Returns:
            None
        """
        if database.random_streamer_data.count() != 0:
            return database["random_streamer_data"].find_one()
        else:
            pass
