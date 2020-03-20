# TO DO:
#     * give API auth token so it can do things that require it (ie. mod commands).
#         * for instance, if i wanted to implement a feature that allowed a user to spend 500 points to ban someone or something, i can do that
#     * for all functions that take a list, make a check to see if they're a list and fix it if it's not.
#     * do more input sanitization and throw errors
#     * write examples for docs
#     * should twitchbot save chat history? it would help a mock function



# python standard module
import asyncio
import json
import sys

# TwitchPy modules
from .API import Helix
from .errors import *
from .Events import Handler
from .Logger import Logger
from .Websocket import IRC



class Client:
    """The central part of the TwitchPy bot.

    This is responsible for creating many parts of the bot as well as running everything.
    Every bot should create an instance of this bot.


    Keyword Arguments
    -------------------
    token : str
        The bot's oauth token. MUST start with 'oauth:' .

        For example, if your oauth was 123456, then this should be 'oauth:123456'

    user : str
        The username of the account the bot logs in to.

    client_id : str
        The bot's client ID.

    channel : str
        The channel you want the bot to connect to.

    logger : Logger.Logger (optional)
        The bot's custom logger. If not given, TwitchPy will give you a very basic logger (see Logger.Logger preset='default').

        If you don't want any logger, create an instance of Logger.Logger without filling in any fields.

        Example: bot = TwitchBot.Client(logger=Logger))

    eventhandler : Events.Handler (optional)
        An event handler if you wanted to set one up. If you do, make sure you create a class that inherits from Events.Handler .
        For more info see Events.Handler


    Attributes
    -----------
    events : Event.Handler
        See eventhandler in keyword arguments

    logger : Logger.Logger
        See keyword arguments.

    command_cogs : (Command.Cog)
        A set of all the command cogs you added.

    API : API.Helix
        The API handler.

    IRC : Websocket.IRC
        The IRC handler.

    tasks : list
        A list of functions to execute concurrently with the bot.
        See TwitchBot.Client.run() for more info.
    """
    def __init__(self, *, token: str, user: str, client_id: str, channel: str, logger=Logger(preset='default'), eventhandler=Handler()):
        # variables given
        self.events = eventhandler
        self.logger = logger

        # logger setup
        self.logger.set_eventhandler(self.events)
        asyncio.run(self.logger.log(11, 'init', 'initializing all components...'))

        # variables created
        self.command_cogs = set()
        self.API = Helix(logger=self.logger, channel=channel, cid=client_id)
        self.IRC = IRC(logger=self.logger, commands=self.command_cogs, events=self.events, token=token, user=user, channel=channel)
        self.events._init_events(logger=self.logger, API=self.API, IRC=self.IRC)
        self.tasks = []     # for asyncio concurrency
        self._listen_loop = None

        # log
        asyncio.run(self.logger.log(11, 'init', 'successfully initialized all components'))
        asyncio.run(self.logger.log(20, 'init', 'bot is ready to run'))
        self.events.on_ready()



    def add_cogs(self, cogs: list):
        """Adds commands to the bot.

        Commands follow a cog system that lets you categorize groups of commands, mostly for organization.


        Parameters
        ---------------
        cog : [Commands.Cog]
            The cogs to add to the bot. To see how to make a cog, see Commands.Cog .
        """
        for cog in cogs:
            asyncio.run(self.logger.log(11, 'init', f'adding cog {type(cog).__name__} ...'))
            cog._init_attributes(self.logger, self.events)
            self.command_cogs.add(cog)
            asyncio.run(self.logger.log(11, 'init', f'successfully added cog {type(cog).__name__}'))



    def run(self, funcs: list=[]):
        """Starts the main functions of the bot.

        After initializing everything, calling this will start the bots listener to start listening to
        twitch chat and determing which commands (if any) to execute. This will also start running
        any async functions you want to run concurrently with the other functions of the bot.


        Parameters
        -------------
        funcs : list
            A list of async functions that you want to run alongside (concurrently) with the bot's
            other functions. Some common uses for this is if you wanted the bot do something
            every x seconds.

            These async functions must follow these rules:

                * Must have at least one call to asyncio.sleep(x) where x is an amount of time in seconds. This is what allows the concurrency. If you don't have this, the bot will get hung up on one of the tasks and not function properly.
                * Must **NOT** take any arguments.
        """
        try:
            asyncio.run(self.logger.log(20, 'basic', 'starting bot...'))
            self.events.on_run()
            self._listen_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._listen_loop)

            self._listen_loop.run_until_complete(self.IRC.connect())
            self._listen_loop.run_until_complete(self._start(funcs))
        except ExpectedExit as e:
            self._listen_loop.run_until_complete(self.events.on_expected_death())
        except Exception as err:
            exc_info = sys.exc_info()
            self._listen_loop.run_until_complete(self.logger.log(40, 'error', 'bot received an unknown error', exc_info))
            self._listen_loop.run_until_complete(self.events.on_unexpected_death(err, exc_info))
        finally:
            self._listen_loop.run_until_complete(self.events.on_death())
            self._listen_loop.run_until_complete(self.logger.log(20, 'basic', 'bot is shutting down...'))
            self._listen_loop.close()



    async def _start(self, funcs: []):
        """
        starts all tasks we wish to run concurrently
        https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
        see self.run() for info on funcs args
        """
        self.tasks.append(asyncio.create_task(self.IRC.listen()))
        for func in funcs:
            self.tasks.append(asyncio.create_task(func()))
        await asyncio.gather(*self.tasks)



    async def change_channel(self, channel: str):
        """Moves the bot from one twitch channel to another.

        Parameters
        -----------
        channel : str
            The channel to connect to.
        """
        await self.logger.log(19, 'basic', f'changing channels to {channel}')
        self.API.broadcaster_name = channel
        self.API._test_connection()
        await self.IRC._join(channel)



    async def kill(self):
        """Gracefully shuts down the bot and it's IRC connections.
        """
        await self.logger.log(20, 'basic', 'killing bot...')
        raise ExpectedExit





    ###################### GETTER FUNCTIONS ######################

    def get_Logger(self) -> Logger:
        return self.logger



    def get_API(self) -> Helix:
        return self.API



    def get_IRC(self) -> IRC:
        return self.IRC