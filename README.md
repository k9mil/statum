## What is statum? 🏗️

statum, a small side project, is a web app built in Flask which servers as a tool to make the usage of Twitch more enjoyable, with unique features & the ability to get in-depth information of your most beloved streamers.

## Features 😂

- Incorporated Twitch API which allows for your followers to be loaded instantaneously.
- List of VODs for each streamer.
- Displays whether the streamer is live.
- If the streamer is live, it displays the category they are in & length of stream.
- Utilization of MongoDB for indexing streamers to minimize the amount of requests & user sessions.

## Working on 🦸‍♂️

The backlog of the features yet to be implemented are available on a public Trello workspace which can be viewed at [statum, board](https://trello.com/b/b6WPU1j8/statum-board).

## Installation process 🤓

As for now, [Python](https://www.python.org/) is **necessary** for you to be able to run this script.

[MongoDB](https://www.mongodb.com/) is necessary for the functionality of the web app, so some knowledge is required and MongoDB is required to be installed on your local machine.

1. Open your terminal/command line where the source code for Oculus is located.
2. Install the dependencies needed via "pip install -r requirements.txt" (if that doesn't work, try pip3 instead of pip)
3. Setup the app for flask: $env:FLASK_APP="statum"
4. Setup the environment variables for flask: "$env:FLASK_ENV="development" (optional, debug mode)
5. Run the flask web app via "flask run". 

After that, you're set.

## Preview 👓

Below you can see a few screenshots from the current UI, though subject to change.

Home Page             |  Dashboard
:-------------------------:|:-------------------------:
![Home Page](https://i.imgur.com/NqqKMH1.jpg)  |  ![Dashboard](https://i.imgur.com/CIq7wUa.jpg)

## Contributing 🤠

If you wish to contribute, f.e, making an improvement to this web app then feel free to make a pull request as this app definitely has a lot of flaws. Or, alternatively, you can open an issue :)

## License 📖

Licensed under the MIT License - see the [LICENSE file](https://github.com/k9mil/statum/blob/master/LICENSE) for more details.
