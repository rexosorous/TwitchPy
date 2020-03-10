'''
holds all the events the bot will call
allows the user to "catch" these events by creating a child of this class like:
    class UserClass(Events.Events):
        def __init__(self):
            super().__init__()

        def on_ready(self):
            print('hello world!')
and then passing this created class to the twitch bot when it's instantiated like:
    bot = TwitchBot.Client(login_info, eventhandler=UserClass())

doing it this way means that the bot will prioritize using UserClass' events and if the user doesn't want
to do stuff with certain events or even make UserClass at all, then the bot will default to the functionality
as defined below.
'''



class Events:
    def __init__(self):
        self.API = None
        self.IRC = None



    def on_ready(self):
        '''
        called at the end of __init__ in TwitchBot.Client
        '''
        pass



    def on_run(self):
        '''
        called at the beginning when TwitchBot.Client.run() is called
        executes before the bot connects to chat or begins any of its loops
        '''
        pass



    async def on_connect(self):
        '''
        called right after the bot connects to twitch chat
        '''
        pass



    async def on_msg(self, chat):
        '''
        called whenever a viewer sends a message in twitch chat
        executes before any command can execute

        arg     chat    (required)  the chat object containing basic info on the message
        '''
        pass



    async def on_cmd(self, chat):
        '''
        called whenever a command executes successfully

        arg     chat    (required)  the chat object containing basic info on the message
        '''
        pass



    async def on_bad_cmd(self, chat):
        '''
        called whenever the bot fails to find a command to execute
        when the viewer uses the prefix but then can't find the command the viewer is trying to use

        arg     chat    (required)  the chat object containing basic info on the message
        '''
        pass



    async def on_no_cmd(self, chat):
        '''
        called whenever a user sends a message in chat that has nothing to do with the bot
        aka: the user didn't use any of the command prefixes

        arg     chat    (required)  the chat object containing basic info on the message
        '''
        pass



    async def on_death(self):
        '''
        called when the bot dies regardless of how it happens
        executes before connections are closed, allowing for the bot to send messages to chat
        '''
        pass



    async def on_expected_death(self):
        '''
        called when the bot dies as a part of normal function. aka: the user uses the kill command
        executes before on_death
        executes before connections are closed, allowing for the bot to send messages to chat
        '''
        pass



    async def on_unexpected_death(self, err):
        '''
        called when the bot dies unexpectedly. aka: when an error occurs
        executes before on_death
        executes before connections are closed, allowing for the bot to send messages to chat

        arg     err     (required)  the error that caused the unexpected death
        '''
        pass