# TO DO:
#   * be smart enough to make choose_command() cleaner. especially with those return statements
#   * maybe give commands access to events and logger? this would mean i don't have to return
#     those numbers and can have more detailed logs and events
#   * allow sub length and badges for command permissions
#   * make functions take arguments instead of having to do chat.split_args



# python standard modules
import inspect



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


    Attributes
    -----------
    prefix : str
        See keyword arguments.

    all_commands : dict
        A dictionary containing all of your commands whose keys are ('commandname', argcount) and
        whose values are the Commands.Command objects. What's argcount? see Commands.create() for more info.

    command_keys : list
        A list whose elements are the tuples that are used by all_commands and is sorted by
        argcount in reverse order.


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
    def __init__(self, *, prefix: str):
        """
        kwarg   prefix  (required)  the prefix that will let the bot know to try to execute commands
                                    ex: if the prefix is '!', then the bot will ignore all messages that don't start with '!'
        """
        # variables given
        self.prefix = prefix

        # variables created
        self.all_commands = dict()
        self.command_keys = list()

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
                self.all_commands[(obj.name, obj.argcount)] = obj
                for alias in obj.aliases:
                    self.all_commands[(alias, obj.argcount)] = obj

        self.command_keys = sorted(self.all_commands, key=lambda x: x[1], reverse=True)
            # sort commands by argcount to make selecting one easier
            # because they sorted in reverse, self.choose_command will
            # prioritize the one with more args
            # this is mainly to prefer commands with argcount defined
            # over commands without argcount defined
            # ex: command(name='mycommand', argcount=2)
            #       should be prioritized over
            #     command(name='mycommand')
            # note: these are only keys because you can't sort the whole dictionary
            #       so make sure to traverse the keys, not the dict



    async def _choose_command(self, chat):
        """
        determines which command to execute, if any
        """
        if not chat.msg.startswith(self.prefix):   # first determine if the bot is even being called
            return 1  # indicates that the cog isn't called

        msg = chat.msg[len(self.prefix):]          # remove the prefix from the message

        for command, argcount in self.command_keys:
            # determine which command to execute
            # we do it this way instead of
            #   if command in self.all_commands
            # because we want to allow users to have commands with spaces in it
            if msg.startswith(command) and (len(msg) == len(command) or msg[len(command)] == ' '):
                # we need to check for a space after the 'command' or if there's nothing after the 'command'
                # if we have two commands: 'test' and 'test2'
                # a viewer who tries to do !test, will invariably trigger test2 as well if we didn't check for a space after
                # so we check if '!test' has a space after it or if there's nothing after to avoid it
                chat.args = msg[len(command)+1:]
                chat.split_args = msg[len(command)+1:].split(' ')

                if argcount == len(chat.split_args) or argcount == -1: # check if the chat message has the correct amount of arguments
                    obj = self.all_commands[(command, argcount)]

                    # check if the viewer is allowed to use this command
                    if self._check_permissions(chat.user, obj):
                        await obj.func(obj.instance, chat)
                        return 0   # indicates successful execution

        # if we've reached this point, then there exists no command
        # that the user is trying to call
        return 2 # indicates failure to find command to execute



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

    name : str
        The name of the command.

    aliases : [str]
        Any other names that the command can be executed by.

    argcount : int
        How many arguments this command expects to receive.

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
    def __init__(self, func, name: str, aliases: [str], argcount: int, permission: str, whitelist: [str]):
        self.func = func
        self.name = name
        self.aliases = aliases
        self.argcount = argcount
        self.permission = permission
        self.whitelist = whitelist






def create(*, name: str='', aliases: [str]=[], argcount: int=-1, permission: str='notset', whitelist: [str]=[]):
    """A decorator function used to create new commands.

    Requirements for creating your own command:

    1. MUST be used in a class that inherits from Commands.Cog

    2. MUST use the @ decorator syntax: @Commands.create()

    3. MUST be an async function

    4. MUST take one parameter: chat


    Keyword Arguments
    -------------------
    name : str (optional)
        The name of the command. AKA: what the viewer will type after the prefix to execute the command.
        If not given, the command name will be the name of the function.

    aliases : [str] (optional)
        Any other names you want the command to be executed by.

    argcount: int (optional)
        How many arguments this command should expect. If not given, the command will execute regardless
        of how many arguments are given.

    permission : {'notset', 'everyone', 'subscriber', 'moderator', 'broadcaster'} (optional)
        Based on their affiliation to the channel, which users are allowed to use this command.
        Specifying any permission level implies that users with higher permission levels will be able to use the command.
        For example, permission='moderator' implies that both channel moderators and broadcasters can use it.

    whitelist : [str] (optional)
        Which viewers can use this command by name. If specified along with permission, permission will take
        precedence over whitelist.


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

    >>> @Command.create(name='hello', aliases=['hi', 'howdy'])
    >>> async def sayhello(self, chat):
    >>>     self.IRC.send('HeyGuys')

    This command says in chat 'HeyGuys' whenever a viewer says '!hello' or '!hi' or '!howdy'. Because
    name is defined, the command name won't be set to the function name: sayhello. Because aliases is
    defined with two strings, this command can be executed using any of the 3 names.

    >>> @Command.create(name='hello', argcount=2)
    >>> async def advancedhello(self, chat):
    >>>     self.IRC.send('VoHiYo')

    This command says in chat 'VoHiYo' whenever a viewer says '!hello' followed by two other words (argcount)
    So '!hello lorem ipsum' or '!hello my guys' or '!hello a b' would all work because there are two
    words (argcount) after the command. Note that we now have two commands with the name '!hello'.
    This is allowed because they work on two different argcounts. The function advancedhello is called
    only if there are two args and the function sayhello will get called whenever there's any other number
    of args. That is to say, if there are multiple functions with the same name, the bot will prioritize
    executing commands with argcount defined over ones without argcount defined.

    NOTE: If you have two commands with the same name and argcount, only one of them will execute.

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
        cmd_name = name or func.__name__
        cmd = Command(func, name=cmd_name, aliases=aliases, argcount=argcount, permission=permission, whitelist=whitelist)
        return cmd
    return decorator