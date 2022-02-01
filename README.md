# What is statum? 🗺️

statum, a side project, is a web app built in Python, Flask + MongoDB which serves as a tool to make the usage of Twitch more enjoyable, with unique features & the ability to get in-depth information of your most beloved streamers.

## Preview

Below you can see a few screenshots from the current UI, though subject to change.

Home Page             |  Dashboard
:-------------------------:|:-------------------------:
![Home Page](https://i.imgur.com/K0mqVVe.jpg)  |  ![Dashboard](https://i.imgur.com/O1Qdh6s.jpg)
Random             |  VODs
![Random](https://i.imgur.com/XyaxDVV.jpg)  |  ![VODs](https://i.imgur.com/Dm7SFjY.jpg)
Streamer Page | Favourite VODs
![Streamer Page](https://i.imgur.com/5jUeZNk.jpg) | ![favVODs](https://i.imgur.com/FHKyAbs.jpg)

## Features

- Incorporated Twitch OAuth, which allows for your followers to be loaded instantaneously.
- Ability to view a random twitch stream between 10 and 100 viewers to help to support smaller streamers.
- An aesthetically pleasing dashboard with a list of your followed streamers, top streamers & top circulating LSF clips.
- If the streamer is live, it displays the category they are in & length of stream.
- List of VODs for each streamer.
- List of the current most popular twitch clips, alongside with their metrics.
- Unique Streamer Data insights for each streamer on the platform.
- Utilization of MongoDB for indexing streamers to minimize the amount of requests & user sessions.
- Ability to add streamers to favourites.
- See VODs of your favourite streamers.

& much more!

## Working on

The backlog of the features yet to be implemented are available on a public Trello workspace which can be viewed at [statum, board](https://trello.com/b/b6WPU1j8/statum-board).

## Demo Server

A demo server is available, on a Heroku deno: [statoom](https://statoom.herokuapp.com/). *note: may or may not be up-to-date.

## Installation process

If you wish to run this web app locally, [Python](https://www.python.org/) will be **necessary** for you to be able to run this web application.

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

## Contributing

If you wish to contribute, f.e, making an improvement to this web app, then feel free to make a pull request as this app definitely has a lot of flaws. Or, alternatively, you can open an issue :)

## License

Licensed under the MIT License - see the [LICENSE file](https://github.com/k9mil/statum/blob/master/LICENSE) for more details.
