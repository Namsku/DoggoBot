# DoggoBot - Twitch Bot 

## About

DoggoBot is a Twitch bot that is currently in development. It is written in Python and uses the [TwitchIO]()

## Features

- [x] Basic chat commands
- [x] Basic moderation commands
- [x] Basic game commands
- [x] Basic channel point redemption commands
- [x] Basic Twitch API integration
- [x] Basic Twitch PubSub integration
- [x] Basic Twitch IRC integration
- [x] Basic Twitch Sound Alerts integration

## Installation

1. Clone the repository
2. Install the required packages using `pip install -r requirements.txt`

## Configuration

1. Create a file called `config.json` in the root directory of the project
2. Add the following to the file:

```json
{
    "nick": "doggo_bot",
    "prefix": "!",
    "initial_channels": [
        "doggo_bot"
    ]
}
```
3. Replace the values with your own
4. Create a file called `.env` in the root directory of the project
5. Add the following to the file:

```env
TWITCH_CLIENT_ID=
TWITCH_CLIENT_SECRET=
```
6. Replace the values with your own 

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

- [PayPal](https://paypal.me/itsdoggo)
- [Ko-fi](https://ko-fi.com/itsdoggo)
- [Patreon](https://patreon.com/itsdoggo)
