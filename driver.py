import json
import TwitchBot
from time import sleep


with open('login_info.json', 'r') as file:
    login_info = json.load(file)


bot = TwitchBot.Client(**login_info)
bot.start()