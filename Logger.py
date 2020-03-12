'''
TO DO:
    * if i'm smart enough, figure out a system to allow multiple logger types
        for instance, i want to set one console logger, and two file loggers
        the console logger will show init+ stuff
        one file logger will show EVERYTHING
        the other file logger will only store chat messages
        >>> the problem with this is how is the user going to use filters effectively?
            if they've got 4 different loggers, how are they going to specify the filters for each?
'''



import inspect
import logging
from sys import stdout

from errors import *
import ChatInfo



'''
built-in logger to help debug and save information.
features:
    * chat formatting to change how you want your twich chat messages to look in the log
    * custom filters for both console and file loggers to filter out what messages you do and do not want to see for both individually
    * presets ('default', 'recommended')
    * create basic loggers so you don't have to import logging
    * supports creating your own logger via logging and using it in this

note: while we don't inherently support more than two loggers (one for the console and one for file),
the console logger and file logger names are purely cosmetic. we make no checks to ensure that
those loggers have purely consolehandlers or filehandlers. additionally, we support you defining
your own logger (via the logging module) and using the Logger.set[loggertype]() function. so you could make
a logger, add a filehandler, and pass it to Logger.set_console_logger() and that would work without problem.
this means that if you wanted to do things like printing to multiple files at the same time, or other
things that might require more than two loggers, you might be able to find some crafty solutions at:
https://docs.python.org/3/howto/logging-cookbook.html

alternatively, if that's too confusing or doesn't quite allow you to do what you want to do,
you can always catch the on_log event which will be called whenever the bot tries to log something.
the on_log event will receive the same information that the logger would
'''



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
    def __init__(self, *, preset: str='', chatfmt: str='%(user.name)s: %(msg)s', eventhandler=None):
        '''
        arg     preset          (optional)  determines what kind of preset logger to make
                                            can be 'default' or 'recommended'
                                            default = only console logger
                                            recommended = our recommended loggers
                                            if not provided, will make an empty logger so nothing will get logged

        arg     chatfmt         (optional)  the % string format to dictate how the logger logs twitch chat messages
                                            the %(variables) should be in scope UserInfo.User
                                            so if you wanted to only get the full twitch message, you would use
                                                '%(msg)s'      not     '%(chat.msg)s'
                                            the default is '%(user.name)s: %(msg)s' which would print
                                                someuser: lorem ipsum
                                            another example: '%(user.name)s says "%(msg)s"' which would print
                                                someuser says "lorem ipsum"
                                            note: information is very limited for outgoing messages. you'll only get
                                            chat.msg, chat.channel, chat.user.name
                                            while other fields might exist, they won't be accurate

        arg     eventhandler    (optional)  an Events.Events() object just so this module can call the on_log event
                                            you can instantiate this class with one and then pass it onto Client like
                                                mylogger = Logger.Logger(eventhandler=myeventhandler)
                                                mybot = TwitchPy.Client(logger=mylogger, eventhandler=myeventhandler)
                                            but this is not necessary. see set_eventhandler() below
        '''
        self.chatfmt = chatfmt
        self.events = eventhandler

        self.console = None
        self.file = None
        self.filter = dict()

        self._choose_preset(preset)



    def _choose_preset(self, preset: str):
        '''
        chooses a preset by str
        should only really be done during Logger.__init__()
        presets are defined by me
        '''
        if preset == 'default':
            self.create_console_logger(level=19)
        elif preset == 'recommended':
            self.create_console_logger()
            self.create_file_logger()



    def create_console_logger(  self, *,
                                fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s',
                                datefmt='%H:%M:%S',
                                level=11):
        '''
        a convenient function to create a logger without the user having to import logging

        kwarg   fmt     (optional)  the format of the log messages. see https://docs.python.org/2/library/logging.html#logrecord-attributes
        kwarg   datefmt (optional)  the format of time gotten by %(asctime)s. see https://docs.python.org/3/library/time.html#time.strftime
        kwarg   level   (optional)  the level of the logger, it can be one of loggin's levels (https://docs.python.org/3/library/time.html#time.strftime)
                                    or the ones defined above
        '''
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
        '''
        see create_console_logger for kwargs not listed here

        kwarg   filename    (optional)  the path/name of the file to log to
        kwarg   filemode    (optional)  the writing mode. basically just 'w' or 'a'
        '''
        self.file = logging.getLogger('file')
        file_handler = logging.FileHandler(filename, filemode)
        file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        file_handler.setLevel(level)
        self.file.addHandler(file_handler)



    def console_filter(self, filter_: [str]):
        '''
        NOT to be confused with logging filters: https://docs.python.org/3/library/logging.html#filter-objects
        filter should be things the user does NOT want to see
        each filter should be structured as so:
            [Module]-[Type]
            Helix-init
        a full example might be:
            ['API-request_get', 'API-request_response', 'Websocket-send', 'Websocket-recv']

        we also support users setting up filters for their own log messages. see log() for more details

        full filter structure with all the types

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
        }
        '''

        for fil in filter_:
            module = fil[:fil.find('-')]
            type_ = fil[fil.find('-')+1:]
            if module not in self.filter or type_ not in self.filter[module]:
                self.filter[module] = {type_:(self.console)}
            else:
                self.filter[module][type_].add(self.console)



    def file_filter(self, filter_: [str]):
        '''
        see console_filter for a detailed explanation
        '''
        for fil in filter_:
            module = fil[:fil.find('-')]
            type_ = fil[fil.find('-')+1:]
            if module not in self.filter or type_ not in self.filter[module]:
                self.filter[module] = {type_:(self.file)}
            else:
                self.filter[module][type_].add(self.file)



    async def log(self, level: int, type_: str, msg: str, exc = None):
        '''
        makes a logging record object (https://docs.python.org/3/library/logging.html#logrecord-objects)
        by filling in the fields with information gathered from inspect frames (https://docs.python.org/3/library/inspect.html#the-interpreter-stack)
        then logs with the appropriate loggers according to the filters
        then passes on the record to the on_log event

        we support users sending their own log messages to the logger. they obviously must provide the required args as listed below.
        they are free to add their own logging levels with logging.addLevelName() as described in https://docs.python.org/3/library/logging.html#logging.addLevelName
        they just need to keep in mind not to make levels that clash with ours:
            LOWLVL  9
            INIT    11
            BASIC   19
            MSG     21
        they must also keep in mind that we have defined type_'s that might cause logic errors (see above)

        arg     level   (required)  the logging level to log by
        arg     type_   (required)  the type of log message (see constants above)
        arg     msg     (required)  the message of the log. can either be string or chat object
                                    we want to be able to catch the chat object to allow users
                                    to format how chat messages are sent to the logger
        arg     exc     (optional)  exception info obtained from sys.exc_info()
        '''

        # the following is a really cooky way to get information about the calling function
        # i don't rightly understand it too well, but it works
        stack = inspect.stack()
        frame = [frame for frame in stack if '\\lib\\asyncio' not in frame.filename]
        frame = frame[1]


        if isinstance(msg, ChatInfo.Chat): # check if this is a string or a twitch chat message
            '''
            we get dicts for the chat object which is exactly what we need to use for string formatting
            see https://realpython.com/python-string-formatting/#1-old-style-string-formatting-operator
            this would be good enough, but the variable chat.user is an object itself and so we need
            to add chat.user's dict to chat.__dict__
            we also need to adjust the key names in chat.user.__dict__ so that they all begin with 'user.'
            just for clarity for the user
            '''
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
        '''
        if the user does not define an eventhandler on their own or forgets to pass it to this class,
        TwitchPy.Client is designed to give this it's eventhandler
        '''
        self.events = events



    def set_chatfmt(self, chatfmt: str):
        '''
        allows the user to set the irc chat format in % string formatting
        see __init__ comments for more details
        '''
        self.chatfmt = chatfmt



    def set_console_logger(self, logger):
        '''
        allows a user to define their own logger using the logging module
        note: MUST be from the logging module
        '''
        if not isinstance(logger, logging.Logger):
            raise InvalidLogger
        self.console = logger



    def set_file_logger(self, logger):
        '''
        see set_console_logger
        '''
        if not isinstance(logger, logging.Logger):
            raise InvalidLogger
        self.file = logger