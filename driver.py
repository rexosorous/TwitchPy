import json
import TwitchBot
import Commands
import Events



class EventHandler(Events.Events):
    def __init__(self):
        super().__init__()

    def on_ready(self):
        print('bot is ready to run')

    async def on_connect(self):
        await self.IRC.send('bot is live')

    async def on_cmd(self, chat):
        await self.IRC.send('command successful')

    async def on_bad_cmd(self, chat):
        await self.IRC.send('could not find command')

    async def on_no_cmd(self, chat):
        await self.IRC.send('you didn\'t call the bot, but i\'m here anyway')

    async def on_unexpected_death(self, err):
        await self.IRC.send('bot reached an unknown issue')
        print(err)

    async def on_expected_death(self):
        await self.IRC.send('gracefully killing bot...')

    async def on_death(self):
        await self.IRC.send('bot is no longer live')



class TestBot(Commands.Cog):
    def __init__(self, bot):
        super().__init__(prefix='!')
        self.bot = bot

    @Commands.create(name='ping')
    async def func1(self, chat):
        await self.bot.IRC.send('in func1')

    @Commands.create(name='ping', argcount=2)
    async def func2(self, chat):
        await self.bot.IRC.send('in func2')

    @Commands.create(name='ping', argcount=3)
    async def func3(self, chat):
        await self.bot.IRC.send('in func3')

    @Commands.create(aliases=['stop'])
    async def kill(self, chat):
        bot.kill()



class EvenTestierBot(Commands.Cog):
    def __init__(self, IRC):
        super().__init__(prefix='$')
        self.IRC = IRC

    @Commands.create(name='ping')
    async def ping(self, chat):
        await self.IRC.send('pong pong')





if __name__ == '__main__':
    with open('login_info.json', 'r') as file:
        login_info = json.load(file)

    bot = TwitchBot.Client(**login_info, eventhandler=EventHandler())
    bot.add_cog(TestBot(bot))
    bot.add_cog(EvenTestierBot(bot.get_IRC()))
    bot.run()