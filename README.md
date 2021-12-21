# What is statum? 🏗️

statum, a small side project, is a web app built in Flask which servers as a tool to make the usage of Twitch more enjoyable, with unique features & the ability to get in-depth information of your most beloved streamers.

## Features 😂

- Incorporated Twitch OAuth which allows for your followers to be loaded instantaneously.
- List of VODs for each streamer.
- Displays whether the streamer is live.
- If the streamer is live, it displays the category they are in & length of stream.
- Displays a list of top streamers of the platform.
- List of the current most popular twitch clips, alongside with their metrics.
- Utilization of MongoDB for indexing streamers to minimize the amount of requests & user sessions.
- Ability to view a random twitch stream between 10 and 100 viewers to help to support smaller streamers.

& more.

## Working on 🦸‍♂️

The backlog of the features yet to be implemented are available on a public Trello workspace which can be viewed at [statum, board](https://trello.com/b/b6WPU1j8/statum-board).

## Installation process 🤓

As for now, [Python](https://www.python.org/) is **necessary** for you to be able to run this web application.

[MongoDB](https://www.mongodb.com/) is necessary for the functionality of the web app, so some knowledge is required and MongoDB is required to be installed on your local machine.

1. To host this web app, you need to register a [Twitch](https://dev.twitch.tv/console/apps/create) Application which will server as the basis of this program.
2. After you have registered the Twitch Application, you have to click "Manage" and locate the "CLIENT ID" which you can paste in the config.py file.
3. Generate an OAuth token, after that, you have to put that in the config.py file aswell.
4. Open your terminal/command line where the source code for statum is located.
5. Install the dependencies needed via "pip install -r requirements.txt" (if that doesn't work, try pip3 instead of pip)
6. Setup the app for flask: $env:FLASK_APP="statum"
7. Setup the environment variables for flask: "$env:FLASK_ENV="development" (optional, debug mode)
8. Run the flask web app via "flask run". 

After that, you're set.

## Preview 👓

Below you can see a few screenshots from the current UI, though subject to change.

Home Page             |  Dashboard
:-------------------------:|:-------------------------:
![Home Page](https://i.imgur.com/NqqKMH1.jpg)  |  ![Dashboard](https://i.imgur.com/SVqe6y2.jpg)
Random             |  VODs
![Home Page](https://i.imgur.com/cGVqeg6.jpeg)  |  ![VODs](https://i.imgur.com/CnyTsqP.jpg)

## Contributing 🤠

If you wish to contribute, f.e, making an improvement to this web app then feel free to make a pull request as this app definitely has a lot of flaws. Or, alternatively, you can open an issue :)

## License 📖

Licensed under the MIT License - see the [LICENSE file](https://github.com/k9mil/statum/blob/master/LICENSE) for more details.
