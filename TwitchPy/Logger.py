# TO DO:
#     * if i'm smart enough, figure out a system to allow multiple logger types
#         for instance, i want to set one console logger, and two file loggers
#         the console logger will show init+ stuff
#         one file logger will show EVERYTHING
#         the other file logger will only store chat messages
#         >>> the problem with this is how is the user going to use filters effectively?
#             if they've got 4 different loggers, how are they going to specify the filters for each?
#               >>> we could create a class for loggers that hold a filter attribute



# python standard modules
import inspect
import logging
from sys import stdout

# TwitchPy Modules
from .errors import *
from .Events import Handler
from .ChatInfo import Chat
from .utilities import *



# logging level constants
LOWLVL = 9
INIT = 11
BASIC = 19
MSG = 21

# adding the levels to the logging module
logging.addLevelName(LOWLVL, 'LOWLVL')
logging.addLevelName(INIT, 'INIT')
logging.addLevelName(BASIC, 'BASIC')
logging.addLevelName(MSG, 'MSG')



class Logger:
    """Semi-Custom Logger to log things as they happen.

    Uses logging library's logger, but with some extra features added on top.
    If you want to utilize this feature, you should make an instance of this class,
    configure it to how you like it, and then pass it into TwitchBot.Client like
    TwitchBot.Client(logger=MyLogger).

    Features:

        * chat formatting to change how you want your twich chat messages to look in the log
        * custom filters for both console and file loggers to filter out what messages you do and do not want to see for both individually
        * presets ('default', 'recommended')
        * lets you create basic loggers so you don't have to import logging
        * supports creating your own logger via logging and using it in this


    Keyword Arguments
    -----------------
    preset : {'default', 'recommended'} (optional)
        If you're too lazy to customize your logger or just don't have many strong feelings about what you want,
        we offer two presets that you can use.

        'default' is a very basic, console-only logger that only shows basic functions the bot is doing.

        'recommended' is what we built the logger with in mind. It prints to console all the init messages and
        above, but logs to a file 'TwitchBot.log' only basic functions and above.

    chatfmt : str (optional)
        The % string format to dictate how the logger should log chat messages. The variables should be in the
        scope of ChatInfo.Chat . So if you wanted to access the username of who sent the message you would use
        '%(user.name)s'. If not given, chatfmt will default to '%(user.name)s: %(msg)s'.


    Note
    ------------
    If you don't want the bot to have a logger, you **must still create an instance of this class**.
    When you do, don't define any of the paramters and the bot won't log anything.


    Attributes
    -----------
    console : logging.Logger
        An instance of logging.Logger used specifically to log to the console.

    file : logging.Logger
        An instance of logging.Logger used specifically to log to files.

    filter : dict
        A filter so you can decide what the console and file loggers can and can't log.
        Note: This is not the filter from the logging library.


    Raises
    -------
    TypeError
        Raised if kwargs are not the correct data types.

    ValueError
        Raised if the kwarg, preset, is not the correct value.


    Note
    ---------
    We hold two instances of loggers (console and file) so you can more precisely control the behaviors of each,
    allowing the console logger to act differently than the file logger.

    Note
    --------
    While we don't inherently support more than two loggers (one for the console and one for file),
    the console logger and file logger names are purely cosmetic. We make no checks to ensure that
    those loggers have purely consolehandlers or filehandlers. Additionally, we support you defining
    your own logger (via the logging module) and using the Logger.set[loggertype]() function. So you could make
    a logger, add a filehandler, and pass it to Logger.set_console_logger() and that would work without problem.
    This means that if you wanted to do things like printing to multiple files at the same time, or other
    things that might require more than two loggers, you might be able to find some crafty solutions at:
    https://docs.python.org/3/howto/logging-cookbook.html

    Alternatively, if that's too confusing or doesn't quite allow you to do what you want to do,
    you can always catch the on_log event which will be called whenever the bot tries to log something.
    The on_log event will receive the same information that the logger would.
    """
    def __init__(self, *, preset: str='', chatfmt: str='%(user.name)s: %(msg)s'):
        # input sanitization
        if (err_msg := check_param(preset, str)):
            raise TypeError(f"TwitchPy.Logger.Logger: {err_msg}")
        if (err_msg := check_param(chatfmt, str)):
            raise TypeError(f"TwitchPy.Logger.Logger: {err_msg}")
        if preset not in ['default', 'recommended']:
            raise ValueError(f"TwitchPy.Logger.Logger: preset expects 'default' or 'recommended' not '{preset}'")

        # variables given
        self.chatfmt = chatfmt

        # variables created
        self.console = None
        self.file = None
        self.filter = dict()
        self.events = None

        # additional setup
        self._choose_preset(preset)



    def _choose_preset(self, preset: str):
        """
        chooses a preset by str
        should only really be done during Logger.__init__()
        presets are defined by me
        """
        if preset == 'default':
            self.create_console_logger(level=19)
        elif preset == 'recommended':
            self.create_console_logger()
            self.create_file_logger()



    def create_console_logger(  self, *,
                                fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s',
                                datefmt='%H:%M:%S',
                                level=11):
        """A convenient function to create a logger without you having to import the loggin module.

        Note: This will set Logger.Logger.console


        Keyword Arguments
        -------------------
        fmt : str (optional)
            See https://docs.python.org/2/library/logging.html#logrecord-attributes

            If not given, will default to '[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s'

        datefmt : str (optional)
            See see https://docs.python.org/3/library/time.html#time.strftime

            If not given, will default to '%H:%M:%S'

        level : int (optional)
            The minimum value for log levels that the bot will pay attention to.
            See https://docs.python.org/2/library/logging.html#logging-levels for logging's levels and
            see Logging for TwitchPy's custom levels.
            If not given, will default to 11 or Logging.INIT


        Raises
        --------
        TypeError
            Raised if kwargs are not the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(fmt, str)):
            raise TypeError(f'TwitchPy.Logger.Logger.create_console_logger(): {err_msg}')
        if (err_msg := check_param(datefmt, str)):
            raise TypeError(f'TwitchPy.Logger.Logger.create_console_logger(): {err_msg}')
        if (err_msg := check_param(level, int)):
            raise TypeError(f'TwitchPy.Logger.Logger.create_console_logger(): {err_msg}')

        self.console = logging.getLogger('console')
        console_handler = logging.StreamHandler(stdout)
        console_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        console_handler.setLevel(level)
        self.console.addHandler(console_handler)



    def create_file_logger(     self, *,
                                filename='TwitchBot.log',
                                filemode='a',
                                fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s',
                                datefmt='%Y/%m/%d - %H:%M:%S',
                                level=19):
        """See Logger.Logger.create_console_logger() for any missing information

        Note: This will set Logger.Logger.file


        Keyword Arguments
        ------------------
        filename : str (optional)
            The path / filename of the file to log to. If not given, will default to 'TwitchBot.log'

        filemode : {'w', 'a'} (optional)
            The writing mode. If not given, will default to 'w'.


        Raises
        --------
        TypeError
            Raised if kwargs are not the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(fmt, str)):
            raise TypeError(f'TwitchPy.Logger.Logger.create_file_logger(): {err_msg}')
        if (err_msg := check_param(datefmt, str)):
            raise TypeError(f'TwitchPy.Logger.Logger.create_file_logger(): {err_msg}')
        if (err_msg := check_param(level, int)):
            raise TypeError(f'TwitchPy.Logger.Logger.create_file_logger(): {err_msg}')

        self.file = logging.getLogger('file')
        file_handler = logging.FileHandler(filename, filemode)
        file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        file_handler.setLevel(level)
        self.file.addHandler(file_handler)



    def console_filter(self, filter_: [str]):
        """Lets you set custom filters to decide what you do and do not want your logger to see.

        For most purposes, just setting the logger's level is good enough, but this is here to give you even
        finer control than that.

        Note: This will only effect Logger.Logger.console


        Note
        -----------
        **NOT** to be confused with logging filters: https://docs.python.org/3/library/logging.html#filter-objects


        Parameters
        ------------
        filter_ : [str]
            A list of all the things you do **NOT** want the logger to see.
            Each entry should be structured as so: Module-Type

            A list of all bot filters:
                * 'TwitchBot-init' : init related messages
                * 'TwitchBot-basic' : the basic function of the module
                * 'TwitchBot-error' : error messages
                * 'API-init'
                * 'API-basic'
                * 'API-request_get' : exactly what the bot is sending via requests
                * 'API-request_response' : the exact response from the twitch API endpoint
                * 'API-error'
                * 'Websocket-init'
                * 'Websocket-basic'
                * 'Websocket-incoming' : only the incoming messages from twitch chat
                * 'Websocket-outgoing' : only the outgoing messages from twitch chat
                * 'Websocket-send' : exactly what the bot sends via websocket
                * 'Websocket-recv' : what twitch IRC sends back at us
                * 'Websocket-error'
                * 'Events-init'
                * 'Commands-error'


            A full example might be: ['API-request_get', 'API-request_response', 'Websocket-send', 'Websocket-recv']

            We also support you setting up your own system of log types which is why we leave this field open ended
            instead of forcing you to stick to TwitchPy's filters.


        Raises
        ---------
        TypeError
            Raised if parameters are not the correct data type.
        """

        """
        full filter structure
        'TwitchBot': {
            'init': (),
            'basic': ()
        },
        'API': {
            'init': (),
            'basic': (),
            'request_get': (self.console, self.file),
            'request_response': (self.console, self.file),
            'error': (self.file)
        },
        'Websocket': {
            'init': (),
            'basic': (),
            'incoming': (),
            'outgoing': (),
            'send': (self.console, self.file),
            'recv': (self.console, self.file),
            'error': (self.file)
        },
        'Events': {
            'init': ()
        },
        'Commands': {
            'error': ()
        }
        """
        for fil in filter_:
            # input sanitization
            if (err_msg := check_param(fil, str)):
                raise TypeError(f'TwitchPy.Logger.Logger.console_filter(): {err_msg}')

            module = fil[:fil.find('-')]
            type_ = fil[fil.find('-')+1:]
            if module not in self.filter or type_ not in self.filter[module]:
                self.filter[module] = {type_:(self.console)}
            else:
                self.filter[module][type_].add(self.console)



    def file_filter(self, filter_: [str]):
        """See Logger.Logger.console_filter() for a detailed explanation

        Note: this will only effect Logger.Logger.file
        """
        for fil in filter_:
            # input sanitization
            if (err_msg := check_param(fil, str)):
                raise TypeError(f'TwitchPy.Logger.Logger.file_filter(): {err_msg}')

            module = fil[:fil.find('-')]
            type_ = fil[fil.find('-')+1:]
            if module not in self.filter or type_ not in self.filter[module]:
                self.filter[module] = {type_:(self.file)}
            else:
                self.filter[module][type_].add(self.file)



    async def log(self, level: int, type_: str, msg: str, exc = None):
        """Checks filters and logs your messages accordingly.

        Makes a logging record object (https://docs.python.org/3/library/logging.html#logrecord-objects)
        by filling in the fields with information gathered from inspect frames (https://docs.python.org/3/library/inspect.html#the-interpreter-stack),
        then logs with the appropriate loggers according to the filters, and finally passes on the record to the on_log event.


        Parameters
        -------------
        level : int
            The level of the log message. See https://docs.python.org/2/library/logging.html#logging-levels-attributes for logging's levels
            and Logger.Logger for TwitchPy's levels. Alternatively, you can send your own level independent of both of.

        type_: str
            The type of log message. You can use the bot's system of message types if you want, but we also support you setting
            up your own system of message types.

        msg : str
            The message that's going to be logged.

        exc : sys.exc_info() (optional)
            You only need this if you're logging an error and must be obtained from sys.exc_info()


        Raises
        ----------
        TypeError
            Raised if parameters are not the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(level, int)):
            raise TypeError(f'TwitchPy.Logger.Logger.log(): {err_msg}')
        if (err_msg := check_param(type_, str)):
            raise TypeError(f'TwitchPy.Logger.Logger.log(): {err_msg}')
        if not isinstance(msg, str) and not isinstance(msg, Chat):
            raise TypeError(f"TwitchPy.Logger.Logger.log(): msg expects 'str' or 'TwitchPy.ChatInfo.Chat' not {type(msg)}")

        # the following is a really cooky way to get information about the calling function
        # i don't rightly understand it too well, but it works
        stack = inspect.stack()
        frame = [frame for frame in stack if '\\lib\\asyncio' not in frame.filename]
        frame = frame[1]


        if isinstance(msg, Chat): # check if this is a string or a twitch chat message
            """
            we get dicts for the chat object which is exactly what we need to use for string formatting
            see https://realpython.com/python-string-formatting/#1-old-style-string-formatting-operator
            this would be good enough, but the variable chat.user is an object itself and so we need
            to add chat.user's dict to chat.__dict__
            we also need to adjust the key names in chat.user.__dict__ so that they all begin with 'user.'
            just for clarity for the user
            """
            user_vars = msg.user.__dict__
            fixed_user_vars = dict()
            for var in user_vars:   # dict keys are immutable, so in order to put 'user.' in front of the keys, we need to make a new dict
                fixed_user_vars[f'user.{var}'] = user_vars[var]
            all_vars = msg.__dict__
            all_vars.update(fixed_user_vars) # combine chat.__dict__ with the fixed chat.user.__dict__
            msg = self.chatfmt % all_vars

        record = logging.LogRecord(name='root', level=level, pathname=frame.filename, lineno=frame.lineno,
                                    msg=msg, args=None, exc_info=exc, func=frame.function)

        for logger in [self.console, self.file]: # check the filters
            if logger:
                if record.module not in self.filter or type_ not in self.filter[record.module]: # if the module or the type aren't in the filter, then they aren't filtered out
                    logger.handle(record)
                elif logger not in self.filter[record.module][type_]: # if the logger isn't in the appropriate location, then that means it isn't filtered out
                    logger.handle(record)

        await self.events.on_log(type_, record)





    ###################### SETTER FUNCTIONS ######################

    def set_eventhandler(self, events):
        """Allows you to set the event handler.


        Parameters
        ------------
        events : Events.Handler
            This should be an instance of a class that inherits from Events.Handler .
            Normally, you shouldn't have to use this as the bot will do this for you, but this is here to give you
            more control over the bot if you want to do something very specific.


        Raises
        ---------
        TypeError
            Raised if parameters are no the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(events, Handler)):
            raise TypeError(f"TwitchPy.Logger.Logger.set_eventhandler(): {err_msg}")

        self.events = events



    def set_chatfmt(self, chatfmt: str):
        """Allows you to set how IRC chat is displayed when it's logged.


        Parameters
        ---------------
        chatfmt : str
            See Logger.Logger for more details.


        Raises
        ---------
        TypeError
            Raised if parameters are no the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(chatfmt, str)):
            raise TypeError(f'TwitchPy.Logger.Logger.set_chatfmt(): {err_msg}')

        self.chatfmt = chatfmt



    def set_console_logger(self, logger):
        """An alternative way to set the console logger.

        Instead of creating one using Logger.Logger.create_console_logger(), you can define your own
        logging logger outside of this class, and use this function to give it to the bot.


        Parameters
        ------------
        logger : logging.Logger
            MUST be a logger created by the logging module.


        Raises
        ---------
        TypeError
            Raised if parameters are no the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(logger, Logger)):
            raise TypeError(f'TwitchPy.Logger.Logger.set_console_logger(): {err_msg}')

        self.console = logger



    def set_file_logger(self, logger):
        """See Logger.Logger.set_console_logger()


        Raises
        ---------
        TypeError
            Raised if parameters are no the correct data type.
        """
        # input sanitization
        if (err_msg := check_param(logger, Logger)):
            raise TypeError(f'TwitchPy.Logger.Logger.set_eventhandler(): {err_msg}')

        self.file = logger