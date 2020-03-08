import json
import TwitchBot
import Commands



class TestBot(Commands.Handler):
    def __init__(self, bot):
        super().__init__(prefix='!')
        self.bot = bot



    @Commands.create(name='ping')
    async def ping(self, chat):
        await self.bot.connection.send('pong')





if __name__ == '__main__':
    with open('login_info.json', 'r') as file:
        login_info = json.load(file)

    bot = TwitchBot.Client(**login_info)
    test = TestBot(bot)
    bot.add_commands(test)
    bot.run()