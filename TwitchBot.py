'''
TO DO:
    * what happens if the user doesn't add a commands cog?
    * for UserInfo, only fill the follower field when we want it (don't make unnescessary API calls)
    * make getters and setters instead of accessing variables directly
    * allow the bot to join and leave channels at will
    * allow for predefined logger
    * print/log startup information
    * raise exceptions involving invalid login info / bad connection / etc
    * have events do something by default. maybe loggers tuff?
    * automatically produce help msg? (require functions to have "description" variable)
'''



import asyncio
import json
import requests

# TwitchPy modules
import APIHandler
import Commands
from errors import *
import Events
import Websocket



'''
a driver class for the whole twitch chat bot
the most top level structure
'''



class Client:
    def __init__(self, *, token: str, user: str, channel: str, client_id: str, eventhandler=Events.Events()):
        '''
        kwarg   token       (required)  bot's oauth token. note: MUST start with 'oauth:'. ex: 'oauth:123456'
        kwarg   user        (required)  bot's username
        kwarg   channel     (required)  the channel the bot connects to
        kwarg   client_id   (required)  the bot's client id
        kwarg   events      (optional)  events object that the bot will send event info to
        '''
        self.events = eventhandler
        self.commands = set()
        self.API = APIHandler.Kraken(name=channel, cid=client_id)
        self.IRC = Websocket.IRC(self.API, self.commands, self.events, token=token, user=user, channel=channel)
        self.listen_loop = None
        self._init_events()
        self.events.on_ready()



    def _init_events(self):
        '''
        passes API and IRC connections to events to allow the it to send messages to chat, among other things
        '''
        self.events.API = self.API
        self.events.IRC = self.IRC



    def add_cog(self, cog):
        '''
        adds command cogs to the bot
        this basically just adds commands to the parts of the bot that needs access to them
        '''
        self.commands.add(cog)



    def run(self):
        '''
        sets up async event loops to listen to twitch chat
        '''
        try:
            self.events.on_run()
            self.listen_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.listen_loop)

            self.listen_loop.run_until_complete(self.IRC.connect())
            self.listen_loop.run_until_complete(self.IRC.listen())
        finally:
            self.listen_loop.close()



    def get_IRC(self) -> Websocket.IRC:
        '''
        returns the websocket connection so the user can do:
            conn = bot.get_connection()
            conn.send(msg)
        '''
        return self.IRC



    def get_API(self) -> APIHandler.Kraken:
        '''
        returns the APIHandler so the user can do:
            API = bot.get_API()
            API.get_viewers()
        '''
        return self.API



    def kill(self):
        '''
        gracefully shuts down the bot and it's IRC connections
        '''
        raise ExpectedExit