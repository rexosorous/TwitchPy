import json
import TwitchBot
import Commands
import Events
import Logger
import asyncio



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
        await bot.kill()



class EvenTestierBot(Commands.Cog):
    def __init__(self, IRC):
        super().__init__(prefix='$')
        self.IRC = IRC

    @Commands.create(name='ping')
    async def ping(self, chat):
        await self.IRC.send('pong pong')



class MyLoop:
    def __init__(self, irc):
        self.irc = irc

    async def badprinter(self):
        while True:
            await asyncio.sleep(2)
            await self.irc.send('wowzers')




if __name__ == '__main__':
    with open('login_info.json', 'r') as file:
        login_info = json.load(file)

    bot = TwitchBot.Client(**login_info)
    bot.add_cog(TestBot(bot))
    bot.add_cog(EvenTestierBot(bot.get_IRC()))
    gg = MyLoop(bot.get_IRC())
    bot.run([gg.badprinter])