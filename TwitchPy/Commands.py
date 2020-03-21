# TO DO:
#   * allow sub length and badges for command permissions



# python standard modules
import inspect

# TwitchPy modules
from .Events import Handler
from .Logger import Logger
from .utilities import *



class Cog:
    """A structure to hold commands defined by you.

    Cogs hold commands you created using the decorator @Commands.create()
    (see Commands.create() for more details on what this is and how to use it),
    and determines which commands to execute based on permissions and arguments.


    Keyword Arguments
    ------------------
    prefix : str
        The prefix for these commands so the bot knows that the following message is meant for it.
        For example, most bots use '!' as their prefix.

    logger : Logger.Logger (optional)
        TwitchPy's logger. If not given, TwitchPy will give whatever instance of Logger.Logger that
        TwitchBot.Client has when TwitchBot.Client.add_cog() is called.

    eventhandler : Events.Handler (optional)
        The eventhandler. If not given, TwitchPy will give whatever instance of Events.Handler that
        TwitchBot.Client has when TwitchBot.Client.add_cog() is called.


    Attributes
    -----------
    prefix : str
        See keyword arguments.

    all_commands : dict
        A dictionary containing all of your commands whose keys are ('commandname', argcount) and
        whose values are the Commands.Command objects. What's argcount? see Commands.create() for more info.

    logger : Logger.Logger
        See keyword arguments

    events : Events.Handler
        See keyword arguments


    Raises
    ---------
    TypeError
        Raised if prefix, logger, and eventhandler are not the correct data types.


    Note
    -----------
    For the most part, you won't need to use these attributes in any meaningful way because TwitchPy
    should do all the work of selecting the command for you. But they're here if you do want to use
    them for something.

    Note
    -----------
    You should **not** be creating an instance of Commands.Cog, instead you should be creating your
    own classes that inherit this class. Make sure to call super().__init__()


    Examples
    -----------
    >>> from TwitchPy import TwitchBot, Commands
    >>>
    >>> class MyClass(Commands.Cog):
    >>>     def __init__(self, IRC):
    >>>         super().__init__(prefix='%')
    >>>         self.IRC = IRC
    >>>
    >>>     @Commands.create(name='ping')
    >>>     async def mycommand():
    >>>         self.IRC.send('pong')
    >>>
    >>> mybot = TwitchBot.Client(yourBotLoginInfoHere)
    >>> mycog = MyClass(mybot.get_IRC())
    >>> mybot.add_cog(mycog)
    >>> mybot.run()

    This will create a bot with prefix '%' and one command named 'ping' that sends 'pong' in chat.

    >>> %ping
    pong
    """
    def __init__(self, *, prefix: str, logger=None, eventhandler=None):
        """
        kwarg   prefix  (required)  the prefix that will let the bot know to try to execute commands
                                    ex: if the prefix is '!', then the bot will ignore all messages that don't start with '!'
        """
        # input sanitization
        if (err_msg := check_param(prefix, str)):
            raise TypeError(f'TwitchPy.Commands.Cog: {err_msg}')
        if logger and (err_msg := check_param(logger, Logger)):
            raise TypeError(f'TwitchPy.Commands.Cog: {err_msg}')
        if eventhandler and (err_msg := check_param(eventhandler, Handler)):
            raise TypeError(f'TwitchPy.Commands.Cog: {err_msg}')

        # variables given
        self.prefix = prefix

        # variables created
        self.all_commands = set()
        self.logger = logger
        self.events = eventhandler

        # additional setup
        self.__init_functions()



    def __init_functions(self):
        """
        populates all_commands
            keys are command names and aliases
            values are command objects
        """
        members = inspect.getmembers(self)
        for _, obj in members:
            if isinstance(obj, Command):
                obj.instance = self
                self.all_commands.add(obj)

        self.all_commands = sorted(self.all_commands, key=lambda command: command.func.__code__.co_argcount, reverse=True)
            # sort commands by argcount to make selecting one easier
            # because they are sorted in reverse, self.choose_command will
            # prioritize the one with more args
            # so if we have two funcs
            #   def func1(arg1, *args):
            #   def func2(arg1, arg2, arg3, *args):
            # and we have 5 args to pass, it'll prefer func2 over func1



    def _init_attributes(self, logger, events):
        """
        if the user hasn't given this cog a logger and/or eventhandler, give this cog whatever TwitchBot.Client has
        """
        if not self.logger:
            self.logger = logger
        if not self.events:
            self.events = events



    async def _choose_command(self, chat):
        """
        determines which command to execute, if any
        """
        if not chat.msg.startswith(self.prefix):   # first determine if the bot is even being called
            await self.events.on_no_cmd(chat)
            return

        msg = chat.msg[len(self.prefix):]          # remove the prefix from the message

        for command in self.all_commands:
            if (command_name := [n for n in command.names if msg.startswith(n)]):   # checks if chat message starts with the command name
                arg_msg = msg[len(command_name[0])+1:]
                args = arg_msg.split(' ') if arg_msg else []

                if len(args) >= command.func.__code__.co_argcount-2:   # checks if there are even enough args
                    chat.arg_msg = arg_msg
                    chat.args = args
                    try:
                        await command.func(command.instance, chat, *args) # attempt to call the function which might fail
                        await self.events.on_cmd(chat)
                        return
                    except TypeError:
                        # this might happen if we send the command too many args
                        pass


        await self.logger.log(30, 'error', 'unable to find command')
        await self.events.on_bad_cmd(chat)



    def _check_permissions(self, user, command):
        """
        makes sure the viewer has the correct permissions to execute this command.
        checks both permission level and whitelist (by calling self._check_whitelist())

        arg     user        (required)  the whole UserInfo.User object. this is most likely sent in as chat.user
        arg     command     (required)  the whole command object. most likely sent in as obj
        """
        if command.permission == 'notset':
            # i know this seems counterintuitive, but that's only because we're going to check this AND _check_whitelist
            # so if a user defines a command like command(whitelist='someviewer'), then the permission is going to default
            # to 'everyone'. without this if statement, this function would return True and regardless of the whitelist,
            # any user could use the command. but with this, the command can only be executed by viewers defined in the whitelist.
            # this also works if the user defines a command without a permission level or a whitelist
            return self._check_whitelist(user.name, command.whitelist)

        permission_hierarchy = ['broadcaster', 'moderator', 'subscriber', 'everyone']

        user_level = 3   # everyone. aka: user is not broadcaster, mod, or sub
        if user.broadcaster:
            user_level = 0
        elif user.moderator:
            user_level = 1
        elif user.subscriber:
            user_level = 2

        if user_level <= permission_hierarchy.index(command.permission) or user.name in command.whitelist:
            return True



    def _check_whitelist(self, username, whitelist):
        """
        makes sure the user is either in the whitelist or the whitelist doesn't exist

        arg     username    (required)  only the UserInfo.User.name portion. most likely sent in as user.name
        arg     whitelist   (required)  whitelist portion of command. most likely sent in as command.whitelist
        """
        if not whitelist: # if there is no whitelist, don't sweat it
            return True
        if username in whitelist:
            return True
        return False






class Command:
    """Just a struct to contain basic info on the command created.

    One of these is instantiated for every command created using the decorator Commands.create()


    Parameters
    -------------
    func : function
        The function that the command will execute when it's called.

    names : [str]
        All the names the command will execute by.

    permission : {'notest', 'everyone', 'subscriber', 'moderator', 'broadcaster'}
        Who is allowed to use this command based on their affiliation with the channel.

    whitelist : [str]
        Who is allowed to use this command based on username. If used alongside permission,
        permissions will take precedence over whitelist.


    Note
    ------------
    For more information on what these mean, see Commands.create()


    Attributes
    --------------
    See parameters


    Note
    ---------
    You shouldn't have to make an instance of this class. But it might be useful for you to know
    what attributes this Class has if you plan on making your own command parser.
    """
    def __init__(self, func, names: [str], permission: str, whitelist: [str]):
        self.func = func
        self.names = names
        self.permission = permission
        self.whitelist = whitelist






def create(*, name: str or [str]=[], permission: str='notset', whitelist: str or [str]=[]):
    """A decorator function used to create new commands.

    Requirements for creating your own command:

    1. MUST be used in a class that inherits from Commands.Cog

    2. MUST use the @ decorator syntax: @Commands.create()

    3. MUST be an async function

    4. MUST take one parameter: chat


    Keyword Arguments
    -------------------
    name : str or [str] (optional)
        The name(s) of the command. AKA: what the viewer will type after the prefix to execute the command.
        If not given, the command name will be the name of the function.

    permission : {'notset', 'everyone', 'subscriber', 'moderator', 'broadcaster'} (optional)
        Based on their affiliation to the channel, which users are allowed to use this command.
        Specifying any permission level implies that users with higher permission levels will be able to use the command.
        For example, permission='moderator' implies that both channel moderators and broadcasters can use it.

    whitelist : str or [str] (optional)
        Which viewers can use this command by name. If specified along with permission, permission will take
        precedence over whitelist.


    Raises
    -------------
    TypeError
        Raised if kwargs are not the data types they should be.


    Examples
    -----------
    For all of these examples, assume they're part of a class defined as such:

    >>> from TwitchPy import Commands
    >>> class MyClass(Commands.Cog):
    >>>     def __init__(self, IRC):
    >>>         super().__init__(syntax='!'')
    >>>         self.IRC = IRC  # received from TwitchBot.Client().get_IRC()

    >>> @Command.create()
    >>> async def ping(self, chat):
    >>>     self.IRC.send('pong')

    The simplest example of how to create a command. This well execute whenever a viewer types in chat
    '!ping' and the bot will respond with 'pong' in chat. Because name is not defined, the command name
    defaults to the function name: 'ping'. Because argcount is not defined, this command will execute
    no matter how many arguments are sent. So '!ping lorem ipsum' will still work. And because permission
    and whitelist are not defined, there's no restrictions on who can use this command.

    >>> @Command.create(name=['hello', 'hi', 'howdy'])
    >>> async def sayhello(self, chat):
    >>>     self.IRC.send('HeyGuys')

    This command says in chat 'HeyGuys' whenever a viewer says '!hello' or '!hi' or '!howdy'. Because
    name is defined, the command name won't be set to the function name: sayhello. Because aliases is
    defined with two strings, this command can be executed using any of the 3 names.

    >>> @Command.create(name=['hello', 'hi', 'howdy'])
    >>> async def advancedhello(self, chat, arg1, arg2, arg3):
    >>>     self.IRC.send('VoHiYo')

    This command says in chat 'VoHiYo' whenever a viewer says '!hello' followed by three words (arg1, arg2, arg3)
    So '!hello all my friends' or '!hello to everyone here' or '!hello a b c' would all work because there are
    three words (args) after the command nane. Note that we now have two commands with the name '!hello'. This is
    allowed because they work on two different argcounts. The function advancedhello is called only if there
    is three args and the function sayhello will get called whenever there's no args.

    >>> @Command.create(name=['hello', 'hi', 'howdy'])
    >>> async def mediumhello(self, chat, arg1, *args):
    >>>     self.IRC.send('wassup')

    Because of *args, this command will execute if there's 1 or more args. There needs to be at least
    1 arg because of arg1 any extra args will be captured by *args as a list. TwitchPy will prioritize
    commands with more args, so TwitchPy will try to execute advancedhello before mediumhello.
    So if there's 3 args, advancedhello will be called even though mediumhello can take any number of
    args > 1. If there's 4 args, mediumhello is called. If there's 2 args, mediumhello is called. If
    there's 1 arg, mediumhello is called.

    NOTE: If two commands have the same name and argcounts (*args does not count toward argcount), then
    only one will be executed.

    >>> @Command.create(permisison='moderator')
    >>> async def permissionhello(self, chat):
    >>>     self.IRC.send('hello mod or broadcaster')

    This command will only execute if a moderator or a broadcaster says '!mod'.

    >>> @Command.create(whitelist=['someviewer'])
    >>> async def whitelisthello(self, chat):
    >>>     self.IRC.send('hello someviewer')

    This command will only execute if the viewer who sent the message is named 'someviewer'

    >>> @Command.create(permission='moderator', whitelist=['someviewer'])
    >>> async def reallyspecifichello(self, chat):
    >>>     self.IRC.send('hello mod, broadcaster, or someviewer')

    This command will execute if **any** moderator or broadcaster sends the message as specified by
    permission. Additionally, if any viewer named 'someviewer', regardless of if they're are a mod
    or a broadcaster or not, will also be able to execute the command.
    """
    def decorator(func):
        nonlocal whitelist
        cmd_name = name or func.__name__
        cmd_name = makeiter(cmd_name)
        whitelist = makeiter(whitelist)

        # input sanitization
        for n in cmd_name:
            if not isinstance(n, str):
                raise TypeError(f"TwitchPy.Commands.create(): name expects all elements to be 'str' not '{type(n)}'")
        if (err_msg := check_param(permission, str)):
            raise TypeError(f'TwitchPy.Commands.create(): {err_msg}')
        for w in whitelist:
            if not isinstance(w, str):
                raise TypeError(f"TwitchPy.Commands.create(): whitelist expects str not {type(w)}")

        cmd = Command(func, names=cmd_name, permission=permission, whitelist=whitelist)
        return cmd
    return decorator