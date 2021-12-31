from statum import database

class System:
    """This class mainly deals with the system part of the database, with indexing & loading.

    Contains three functions, a function to index streamers, temporarily indexing random streamers which get re-indexed
    every 10 minutes & loading a random streamer.

    """
    def indexStreamer(self, broadcaster_id: int, broadcaster_username: str):
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
        broadcaster: dict[int, str] = {
            "_id": broadcaster_id,
            "broadcaster_name": broadcaster_username
        }

        if database.twitch_streamer_data.count_documents({'_id': broadcaster_id}) != 0:
            pass
        else:
            database.twitch_streamer_data.insert_one(broadcaster)

    def indexRandomDB(streamerIDs: list[str]):
        """Indexes streamers into the DB used for the /random/ endpoint.

        Creates a streams object comprised of an id (static, 1), as well as a streamer list
        under the name of "streamerIDs". It then queries the database to check if an id of "1"
        exists, that is, if random streamers are already indexed, if so, it updates the data. Else, it inserts
        a new object into MongoDB.

        Args:
            streamerIDs: A list of streamers to be indexed.

        Returns:
            None
        """
        streams: dict[int, list[str]] = {
            "_id": 1,
            "streamers": streamerIDs
        }

        if database.random_streamer_data.count_documents({"_id": 1}) != 0:
            database.random_streamer_data.update_one(
                {"_id" : 1},
                {"$set": {"streamers": streamerIDs}}
            )
        else:
            database.random_streamer_data.insert_one(streams)

    def loadRandom() -> dict[int, list[str]]:
        """Loads a random streamer from the database.

        It queries the database and if the count isn't 0 (that is, if something is in the database),
        it returns a dictionary with an id, and a list of streamers.

        Args:
            None

        Returns:
            An object is returned via MongoDB as explained above. For example:

            {
                '_id': 1, 
                'streamers': ['death_unites_us', 'Norihss', 'djjasonpalma',  'r0wincyy', 'zuka_TV', 'behram1312', 'Nisqyy']
            }
        """
        if database.random_streamer_data.count_documents({'_id': 1}) != 0:
            return database["random_streamer_data"].find_one()
        else:
            pass
    
    def loadID(streamer: str) -> id:
        """Loads the equivalent ID of an indexed streamer in the database.

        Contains a single line, returns an object where the streamer is matched,
        if it is matched it returns an object with the id & name, otherwise
        returns 'None' by default.

        Args:
            streamer: The streamer which the ID is to be searched for

        Returns:
            An object/dictionary is returned via MongoDB where the streamer is found. For example:

            {
                '_id': '87204022', 'broadcaster_name': 'disguisedtoast'
            }
        """

        return database.twitch_streamer_data.find_one(
            {
                'broadcaster_name': streamer.lower()
            }
        )