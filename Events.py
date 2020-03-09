'''
holds all the events the bot will call
allows the user to "catch" these events by creating a child of this class like:
    class UserClass(Events.Events):
        def __init__(self):
            super().__init__()

        async def on_ready(self):
            print('hello world!')
and then passing on this created class when the twitch bot is instantiatied like:
    bot = TwitchBot.Client(login_info, UserClass)

doing it this way means that the bot will prioritize using UserClass' events and if the user doesn't want
to do stuff with certain events or even make UserClass at all, then the bot will default to the functionality
as defined below.
'''



class Events:
    def __init__(self):
        self.API = None
        self.IRC = None


    def on_ready(self):
        pass

    def on_run(self):
        pass

    async def on_connect(self):
        pass

    async def on_msg(self, chat):
        pass

    async def on_cmd(self, chat):
        pass

    async def on_bad_cmd(self, chat):
        pass

    async def on_death(self):
        pass

    async def on_expected_death(self):
        pass

    async def on_unexpected_death(self):
        pass