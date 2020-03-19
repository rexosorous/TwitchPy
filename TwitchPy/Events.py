# python standard modules
import asyncio



"""
holds all the events the bot will call
allows the user to "catch" these events by creating a child of this class like:
    class UserClass(Events.Handler):
        def __init__(self):
            super().__init__()

        def on_ready(self):
            print('hello world!')
and then passing this created class to the twitch bot when it's instantiated like:
    bot = TwitchBot.Client(login_info, eventhandler=UserClass())

doing it this way means that the bot will prioritize using UserClass' events and if the user doesn't want
to do stuff with certain events or even make UserClass at all, then the bot will default to the functionality
as defined below.
"""



class Handler:
    """Holds all the events the bot will call.

    Inheriting this class allows you to overwrite its functions so you can "catch" these events.


    Attributes
    -----------
    logger : Logger
        Logger object.

    API : API.Helix
        An instance of API.Helix that allows you to access twitch endpoints.

    IRC : Websocket.IRC
        An instance of Websocket.IRC that allows you to interact with twitch chat.


    Examples
    ----------
    >>> from TwitchPy import TwitchBot, Events
    >>>
    >>> class MyClass(Events.Handler):
    >>>     def __init__(self):
    >>>     super().__init__()
    >>>
    >>>     def on_ready(self):
    >>>         print('the bot is ready')
    >>>
    >>> bot = TwitchBot.Client(**login_info, eventhandler=MyClass())
    """
    def __init__(self):
        self.logger = None
        self.API = None
        self.IRC = None



    def _init_events(self, logger, API, IRC):
        """
        receiver logger, API, and IRC to allow the Events to log things and interact with chat
        must be done here and not in __init__ because events will be initialiated before
        logger, API, or IRC are created.
        """
        # log
        self.logger = logger
        asyncio.run(self.logger.log(11, 'init', 'initializing Events...'))

        # given variables
        self.API = API
        self.IRC = IRC

        # log
        asyncio.run(self.logger.log(11, 'init', 'successfully initialized Events'))



    def on_ready(self):
        """
        Called at the end of __init__ in TwitchBot.Client
        """
        pass



    def on_run(self):
        """
        Called at the beginning of when TwitchBot.Client.run() is called.
        Executes before the bot connects to chat or begins any of its loops.
        """
        pass



    async def on_connect(self):
        """
        Called right after the bot connects to a twitch channel.
        """
        pass



    async def on_msg(self, chat):
        """
        Called whenever a viewer sends a message in twitch chat.
        Executes before any command can execute


        Parameters
        -------------
        chat : ChatInfo.Chat
            The chat object containing basic info on the message that was sent.
        """
        pass



    async def on_cmd(self, chat):
        """
        Called after a command executes successfully.


        Parameters
        -------------
        chat : ChatInfo.Chat
            The chat object containing basic info on the message that was sent.
        """
        pass



    async def on_bad_cmd(self, chat):
        """
        Called whenever the bot fails to find a command to execute.
        AKA: when the viewer uses the prefix but then can't find the command the viewer is trying to use


        Parameters
        -------------
        chat : ChatInfo.Chat
            The chat object containing basic info on the message that was sent.
        """
        pass



    async def on_no_cmd(self, chat):
        """
        Called whenever a viewer sends a message in chat that has nothing to do with a command cog.
        AKA: when the viewer doesn't use that cog's prefix.


        Parameters
        -------------
        chat : ChatInfo.Chat
            The chat object containing basic info on the message that was sent.
        """
        pass



    async def on_death(self):
        """
        Called when the bot dies regardless of how it happens.
        Executes before connections are closed, allowing for the bot to send messages to chat
        """
        pass



    async def on_expected_death(self):
        """
        Called when the bot dies as a part of normal function. AKA: the user uses the kill command.
        Executes before on_death.
        Executes before connections are closed, allowing for the bot to send messages to chat.
        """
        pass



    async def on_unexpected_death(self, err, exc_info):
        """
        Called when the bot dies unexpectedly. AKA: when an error occurs.
        Executes before on_death.
        Executes before connections are closed, allowing for the bot to send messages to chat.


        Parameters
        ------------
        err : Exception
            The exception that caused the bot to die unexpectedly.

        exc_info : sys.exc_info()
            More info on the exception that caused the bot to die. Acquired from sys.exc_info()
        """
        pass



    async def on_log(self, log_type: str, record):
        """
        Called whenever the bot attempts to log something.


        Parameters
        -------------
        log_type : str
            The type of log it was. Ex: 'init' or 'msg'. See Logger for more information.

        record : logging.LogRecord
            The log record object that is sent to the logger. See
            https://docs.python.org/3/library/logging.html#logrecord-objects for more information.
        """
        pass