'''
TO DO:
    * should Commands have access to logger?
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
'''



# python standard module
import asyncio
import json

# TwitchPy modules
import API
import Commands
from errors import *
import Events
import Logger
import Websocket



'''
a driver class for the whole twitch chat bot
the most top level structure
'''



class Client:
    def __init__(self, *, token: str, user: str, channel: str, client_id: str, logger=Logger.Logger(preset='default'), eventhandler=Events.Handler()):
        '''
        kwarg   token       (required)  bot's oauth token. note: MUST start with 'oauth:'. ex: 'oauth:123456'
        kwarg   user        (required)  bot's username
        kwarg   channel     (required)  the channel the bot connects to
        kwarg   client_id   (required)  the bot's client id
        kwarg   logger      (optional)  logger object. if not specified, will default to one.
        kwarg   events      (optional)  events object that the bot will send event info to
        '''
        # variables given
        self.events = eventhandler
        self.logger = logger

        # logger setup
        self.logger.set_eventhandler(self.events)
        asyncio.run(self.logger.log(11, 'init', 'initializing all components...'))

        # variables created
        self.command_cogs = set()
        self.API = API.Helix(logger=self.logger, channel=channel, cid=client_id)
        self.IRC = Websocket.IRC(logger=self.logger, commands=self.command_cogs, events=self.events, token=token, user=user, channel=channel)
        self.events._init_events(logger=self.logger, API=self.API, IRC=self.IRC)
        self.tasks = []     # for asyncio concurrency
        self._listen_loop = None

        # log
        asyncio.run(self.logger.log(11, 'init', 'successfully initialized all components'))
        asyncio.run(self.logger.log(20, 'init', 'bot is ready to run'))
        self.events.on_ready()



    def add_cog(self, cog):
        '''
        adds command cogs to the bot
        this basically just adds commands to the parts of the bot that needs access to them
        '''
        asyncio.run(self.logger.log(11, 'init', f'adding cog {type(cog).__name__} ...'))
        self.command_cogs.add(cog)
        asyncio.run(self.logger.log(11, 'init', f'successfully added cog {type(cog).__name__}'))



    def run(self, funcs: []):
        '''
        sets up async event loops to listen to twitch chat

        arg     funcs   (required)  a list of functions the user may want to run concurrently with Websocket.IRC.listen()
                                    usually with some kind of infinite or long-running loop
                                    these functions MUST abide by the following...
                                        * be an async function
                                        * asyncio.sleep(#)
                                        * must NOT take any arguments
                                        * must be part of a list (even if there's only one function)
                                        * must be passed without calling it
                                            ex: GOOD bot.run([myfunc])
                                                BAD  bot.run([myfunc()])
        '''
        try:
            asyncio.run(self.logger.log(20, 'basic', 'starting bot...'))
            self.events.on_run()
            self._listen_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._listen_loop)

            self._listen_loop.run_until_complete(self.IRC.connect())
            self._listen_loop.run_until_complete(self.start(funcs))
        finally:
            asyncio.run(self.logger.log(20, 'basic', 'bot is shutting down...'))
            self._listen_loop.close()



    async def start(self, funcs: []):
        '''
        starts all tasks we wish to run concurrently
        https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
        see self.run() for info on funcs args
        '''
        self.tasks.append(asyncio.create_task(self.IRC.listen()))
        for func in funcs:
            self.tasks.append(asyncio.create_task(func()))
        await asyncio.gather(*self.tasks)



    async def change_channel(self, channel: str):
        '''
        allows the bot to disconnect from the current chat and connect to another one
        having the bot connected to one chat at a time is by design
        '''
        await self.logger.log(19, 'basic', f'changing channels to {channel}')
        self.API.broadcaster_name = channel
        self.API._test_connection()
        await self.IRC.connect(channel)



    async def kill(self):
        '''
        gracefully shuts down the bot and it's IRC connections
        '''
        await self.logger.log(20, 'basic', 'killing bot...')
        raise ExpectedExit





    ###################### GETTER FUNCTIONS ######################

    def get_Logger(self) -> Logger.Logger:
        '''
        returns the logger so the user can use it if they were too lazy to make their own
        '''
        return self.logger



    def get_API(self) -> API.Helix:
        '''
        returns the APIHandler so the user can do:
            API = bot.get_API()
            API.get_viewers()
        '''
        return self.API



    def get_IRC(self) -> Websocket.IRC:
        '''
        returns the websocket connection so the user can do:
            conn = bot.get_connection()
            conn.send(msg)
        '''
        return self.IRC