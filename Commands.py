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
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.all_commands = dict()
        self._init_functions()



    def _init_functions(self):
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
        if not chat.full_msg.startswith(self.prefix):   # first determine if the bot is even being called
            return 1

        msg = chat.full_msg[len(self.prefix):]          # remove the prefix from the message
        placeholder_command = None                      # used for instances with argcount

        # determine which command to execute
        # we do it this way instead of
        #   if command in self.all_commands
        # because we want to allow users to have commands with spaces in it
        # we need to check for a space after the 'command' or if there's nothing after the 'command'
        # if we have two commands: 'test' and 'test2'
        # a viewer who tries to do !test, will invariably trigger test2 as well if we didn't check for a space after
        # so we check if '!test' has a space after it or if there's nothing after to avoid it
        for command, argcount in self.all_commands:
            if msg.startswith(command) and (len(msg) == len(command) or msg[len(command)] == ' '):
                chat.msg = msg[len(command)+1:]
                chat.split_msg = msg[len(command)+1:].split(' ')

                if argcount == -1:
                    # if there are two funcs with the same name and one has argcount defined, but the other doesn't,
                    # the bot should prioritize the one that has a matching argcount before the one that doesn't define it
                    placeholder_command = self.all_commands[(command, argcount)]

                elif argcount == len(chat.split_msg): # check if the chat message has the correct amount of arguments
                    obj = self.all_commands[(command, argcount)]
                    await obj.func(obj.instance, chat)
                    return 0   # code 0 is normal function

        if placeholder_command: # execute the command without argcount defined if we found one
            await placeholder_command.func(placeholder_command.instance, chat)
            return 0

        # if we've reached this point, then there exists no command
        # that the user is trying to call
        return 1    # code 1 is bad






class Command:
    '''
    more or less just a struct to contain basic info on the command
    '''
    def __init__(self, func, name: str='', aliases: [str]=[], argcount: int=-1):
        self.func = func
        self.name = name
        self.aliases = aliases
        self.argcount = argcount






def create(name: str='', aliases: [str]=[], argcount: int=-1):
    '''
    a decorator function to create new commands
    must use the following syntax:
        @Commands.create(kwargs):
        async def function_name(chat):   <-- REQUIRES chat


    kwarg name (optional):      what the user needs to type to execute the command
                                if not given, will default to the function name
    kwarg aliases (optional):   any additional name to execute this command
    kwarg argcount (optional):  how many arguments the command should expect
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

    '''
    def decorator(func):
        cmd_name = name or func.__name__
        cmd = Command(func, name=cmd_name, aliases=aliases, argcount=argcount)
        return cmd
    return decorator