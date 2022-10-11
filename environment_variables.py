from os import environ
from json import loads

DISCORD_TOKEN = environ["DISCORD_TOKEN"]
IMGUR_TOKEN = loads(environ["IMGUR_TOKEN"])
DEEP_AI_KEY = environ["DEEP_AI_KEY"]
OPEN_AI_KEY = environ["OPEN_AI_KEY"]
OPEN_WEATHER_KEY = environ["OPEN_WEATHER_KEY"]
SCOPE = loads(environ["SCOPE"])
