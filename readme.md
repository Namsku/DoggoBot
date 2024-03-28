# DoggoBot - Twitch Bot 

## About

DoggoBot is a Twitch bot that is currently in development. It is written in Python and uses the [TwitchIO]()

## Features

- [x] Basic Twitch bot functionalities

## Installation

1. Clone the repository
2. Install the required packages using `pip install -r requirements.txt`

## Configuration

1. Create a file called `.env` in the root directory of the project
2. Add the following to the file:

```env
TWITCH_TOKEN_SECRET=XXXXX
TWITCH_CLIENT_SECRET=XXXXX
DECAPI_TOKEN_SECRET=XXXXX
DOGGOBOT_SERVER_DBG=0
```

6. Replace the values with your own 

### How can i get the Twitch token?

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Create a new application
3. Copy the `Client ID` in the `.env` file
4. **DO NOT EVER USE/SHARE/COPY THE SECRET** from the application page.
5. Generate a secret by clicking a button on the webapp.
6. Save the secret in the `.env` file or in the setting page of the bot
7. **DO NOT SHARE THE SECRET**
8. Exit the bot and restart it
9. Done!

### But can i get the DECAPI token?

1. Go to [DECAPI](https://beta.decapi.me/auth/twitch?redirect=followage&scopes=moderator:read:followers)
2. Authorize the bot account
3. Copy the token from the URL
4. Save the token in the `.env` file or in the setting page of the bot, **DO NOT SHARE THE TOKEN**
5. Exit the bot and restart it
6. Done!

## Usage

1. Run the bot using `python main.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

# Support

If you have any questions or issues with the bot, feel free to join the [Discord server](https://discord.gg/3QXkZPK) and ask in the `#doggo-bot` channel.

# Contributing

If you would like to contribute to the project, feel free to fork the repository and submit a pull request. If you have any questions, feel free to join the [Discord server](https://discord.gg/3QXkZPK) and ask in the `#doggo-bot` channel.

# Donation

If you would like to support the project, feel free to donate to the following:

