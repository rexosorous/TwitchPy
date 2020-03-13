'''
TO DO:
    * be smart enough to make choose_command() cleaner. especially with those return statements
    * maybe give commands access to events and logger? this would mean i don't have to return
      those numbers and can have more detailed logs and events
    * maybe give commands access to irc and api? just to make it easier for the user to do
      things in their commands?
    * sort commands by their args, to get rid of placeholder_command
'''



# python standard modules
import inspect



'''
all command related functionalities
uses a cog system so that users can create multiple classes (cogs)
each with their own functions to add commands to the bot
NOTE: two cogs can have commands with the same name and both will execute
NOTE: cogs can have different prefixes
'''



class Cog:
    '''
    handles command interataction including
        * storing commands
        * choosing which command to execute

    in order to create functions, user must do the following:
    class MyClass(Commands.Handler):
        def __init__(self):
            super().__init__(prefix='prefix')
    '''
    def __init__(self, *, prefix: str):
        '''
        kwarg   prefix  (required)  the prefix that will let the bot know to try to execute commands
                                    ex: if the prefix is '!', then the bot will ignore all messages that don't start with '!'
        '''
        # variables given
        self.prefix = prefix

        # variables created
        self.all_commands = dict()

        # additional setup
        self.__init_functions()



    def __init_functions(self):
        '''
        populates all_commands
            keys are command names and aliases
            values are command objects
        '''
        members = inspect.getmembers(self)
        for _, obj in members:
            if isinstance(obj, Command):
                obj.instance = self
                self.all_commands[(obj.name, obj.argcount)] = obj
                for alias in obj.aliases:
                    self.all_commands[(alias, obj.argcount)] = obj



    async def choose_command(self, chat):
        '''
        determines which command to execute, if any
        '''
        if not chat.msg.startswith(self.prefix):   # first determine if the bot is even being called
            return 1  # indicates that the cog isn't called

        msg = chat.msg[len(self.prefix):]          # remove the prefix from the message
        placeholder_command = None                      # used for instances with argcount


        for command, argcount in self.all_commands:
            # determine which command to execute
            # we do it this way instead of
            #   if command in self.all_commands
            # because we want to allow users to have commands with spaces in it
            # we need to check for a space after the 'command' or if there's nothing after the 'command'
            # if we have two commands: 'test' and 'test2'
            # a viewer who tries to do !test, will invariably trigger test2 as well if we didn't check for a space after
            # so we check if '!test' has a space after it or if there's nothing after to avoid it
            if msg.startswith(command) and (len(msg) == len(command) or msg[len(command)] == ' '):
                chat.args = msg[len(command)+1:]
                chat.split_args = msg[len(command)+1:].split(' ')

                if argcount == -1:
                    # if there are two funcs with the same name and one has argcount defined, but the other doesn't,
                    # the bot should prioritize the one that has a matching argcount before the one that doesn't define it
                    placeholder_command = self.all_commands[(command, argcount)]

                elif argcount == len(chat.split_args): # check if the chat message has the correct amount of arguments
                    obj = self.all_commands[(command, argcount)]

                    # check if the viewer is allowed to use this command
                    if self._check_permissions(chat.user, obj):
                        await obj.func(obj.instance, chat)
                        return 0   # indicates successful execution

        if placeholder_command: # execute the command without argcount defined if we found one
            if self._check_permissions(chat.user, placeholder_command):
                await placeholder_command.func(placeholder_command.instance, chat)
                return 0 # indicates successful execution

        # if we've reached this point, then there exists no command
        # that the user is trying to call
        return 2 # indicates failure to find command to execute



    def _check_permissions(self, user, command):
        '''
        makes sure the viewer has the correct permissions to execute this command.
        checks both permission level and whitelist (by calling self._check_whitelist())

        arg     user        (required)  the whole UserInfo.User object. this is most likely sent in as chat.user
        arg     command     (required)  the whole command object. most likely sent in as obj
        '''
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
        '''
        makes sure the user is either in the whitelist or the whitelist doesn't exist

        arg     username    (required)  only the UserInfo.User.name portion. most likely sent in as user.name
        arg     whitelist   (required)  whitelist portion of command. most likely sent in as command.whitelist
        '''
        if not whitelist: # if there is no whitelist, don't sweat it
            return True
        if username in whitelist:
            return True
        return False






class Command:
    '''
    more or less just a struct to contain basic info on the command
    '''
    def __init__(self, func, name: str, aliases: [str], argcount: int, permission: str, whitelist: [str]):
        self.func = func
        self.name = name
        self.aliases = aliases
        self.argcount = argcount
        self.permission = permission
        self.whitelist = whitelist






def create(*, name: str='', aliases: [str]=[], argcount: int=-1, permission: str='notset', whitelist: [str]=[]):
    '''
    a decorator function to create new commands
    must use the following syntax:
        @Commands.create(kwargs):
        async def function_name(chat):   <-- REQUIRES chat


    kwarg   name        (optional)  what the user needs to type to execute the command
                                    if not given, will default to the function name
    kwarg   aliases     (optional)  any additional name to execute this command
    kwarg   argcount    (optional)  how many arguments the command should expect
                                    if specified, bot will not execute the command if the argcounts don't match
                                        ex: @commands.create(name='test', argcount=2)
                                                async def myfunc(self, chat):
                                                    print('hello world')

                                            >> !test lorem ipsum     <--- this is the only chat message that will execute myfunc
                                            << 'hello world'
                                            >> !test
                                            >> !test lorem
                                            >> !test lorem ipsum dolor
                                    if not specified, bot will execute the command regardless of how many args there are
                                    NOTE:   two commands can have the same name but different argcounts

                                        ex: @commands.create(name='test', argcount=1)
                                            async def func1(self, chat):
                                                print('in func1')

                                            @commands.create(name='test', argcount=2)
                                            async def func2(self, chat):
                                                print('in func2')

                                            >> !test lorem
                                            << 'in func1'
                                            >> !test lorem ipsum
                                            << 'in func2'

                                    NOTE:   if one command does not specify argcount, but the other does,
                                            the bot will prioritize the one with the exact argcount match if possible

                                        ex: @commands.create(name='test')
                                            async def func1(self, chat):
                                                print('in func1')

                                            @commands.create(name='test', argcount=2)
                                            async def func2(self, chat):
                                                print('in func2')

                                            >> !test
                                            << 'in func1'
                                            >> !test lorem
                                            << 'in func1'
                                            >> !test lorem ipsum
                                            << 'in func2'
                                            >> !test lorem ipsum dolor
                                            << 'in func1'

    kwarg   permission  (optional)  based on their 'loyalty' to the channel, which viewers can use this command
                                    can be 'broadcaster', 'moderator', 'subscriber', or 'everyone'
                                    a permission level implies that any viewer with a higher level can also use the command
                                        ex: permission='moderator' implies that both broadcasters and moderators can use it, but not subscribers or everyone
                                    note: does not support followers. see UserInfo.User.__init__() comments for more info on why.

    kwarg   whitelist   (optional)  which viewers (defined by username) can use this command
                                    if defined, no other viewers can use this
                                    not mutually exclusive with permission. permissions take precedence over whitelist.
                                        ex: assume permission='moderator', whitelist='someviewer'
                                            this means that broadcasters, moderators, and anyone names 'someviewer' can use this command
    '''
    def decorator(func):
        cmd_name = name or func.__name__
        cmd = Command(func, name=cmd_name, aliases=aliases, argcount=argcount, permission=permission, whitelist=whitelist)
        return cmd
    return decorator