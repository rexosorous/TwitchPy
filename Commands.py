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
                self.all_commands[obj.name] = obj
                for alias in obj.aliases:
                    self.all_commands[alias] = obj



    async def choose_command(self, chat):
        '''
        determines which command to execute, if any
        '''
        if not chat.full_msg.startswith(self.prefix):  # first determine if the bot is even being called
            return

        msg = chat.full_msg[len(self.prefix):]         # remove the prefix from the message

        # determine which command to execute
        # we do it this way instead of
        #   if command in self.all_commands
        # because we want to allow users to have commands with spaces in it
        # we need to check for a space after the 'command' or if there's nothing after the 'command'
        # if we have two commands: 'test' and 'test2'
        # a viewer who tries to do !test, will invariably trigger test2 as well if we didn't check for a space after
        # so we check if '!test' has a space after it or if there's nothing after to avoid it
        for command in self.all_commands:
            if msg.startswith(command) and (len(msg) == len(command) or msg[len(command)] == ' '):
                chat.msg = msg[len(command)+1:]
                chat.split_msg = chat.msg.split(' ')
                inst = self.all_commands[command].instance
                await self.all_commands[command].func(inst, chat)
                return 0   # code 0 is normal function

        # if we've reached this point, then there exists no command
        # that the user is trying to call
        return 1    # code 1 is bad






class Command:
    '''
    more or less just a struct to contain basic info on the command
    '''
    def __init__(self, func, name: str='', aliases: [str]=[]):
        self.func = func
        self.name = name
        self.aliases = aliases






def create(name: str='', aliases: [str]=[]):
    '''
    a decorator function to create new commands
    must use the following syntax:
        @Commands.create(kwargs):
        async def function_name(chat):   <-- REQUIRES chat


    kwarg name (optional):      what the user needs to type to execute the command
                                if not given, will default to the function name
    kwarg aliases (optional):   any additional name to execute this command
    '''
    def decorator(func):
        cmd_name = name or func.__name__
        cmd = Command(func, name=cmd_name, aliases=aliases)
        return cmd
    return decorator