'''
TO DO:
    * make getters and setters instead of accessing variables directly
    * allow the bot to join and leave channels at will
    * allow for predefined logger
    * print/log startup information
    * add permissions to commands?
        so something like       @Commands.create(permission='moderator')
        would mean that any viewer with UserInfo.User.moderator == True can use it
        some questions:
            1. should permission='moderator' assume that anyone higher (like broadcaster) can use it?
                1a. what would the hierarchy be?
                1b. should we allow a custom hierarchy?
            2. should the user have to define each level they want like permission=['broadcaster', 'moderator', 'subscriber']
            3. should we automatically assume that 'broadcaster' can use any command regardless?
                3a. should we allow the user to state whether or not they want that functionality?
                ethical note: if someone uses the bot to join someone else's twitch channel, then should
                    should the broadcaster be able to use commands (like kill) regardless?
    * raise exceptions involving invalid login info / bad connection / etc
    * have events do something by default. maybe loggers tuff?
    * automatically produce help msg? (require functions to have "description" variable)
'''



import asyncio
import json
import requests

# TwitchPy modules
import API
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
        self.API = API.Helix(name=channel, cid=client_id)
        self.IRC = Websocket.IRC(self.commands, self.events, token=token, user=user, channel=channel)
        self._listen_loop = None
        self.__init_events()
        self.events.on_ready()



    def __init_events(self):
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
            self._listen_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._listen_loop)

            self._listen_loop.run_until_complete(self.IRC.connect())
            self._listen_loop.run_until_complete(self.IRC.listen())
        finally:
            self._listen_loop.close()



    def get_IRC(self) -> Websocket.IRC:
        '''
        returns the websocket connection so the user can do:
            conn = bot.get_connection()
            conn.send(msg)
        '''
        return self.IRC



    def get_API(self) -> API.Helix:
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