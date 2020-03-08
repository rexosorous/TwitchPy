import asyncio

import ChatInfo



'''
handles the IRC connection to the twitch chat
responsible for reading and sending messages
reference: https://dev.twitch.tv/docs/irc/guide
'''



class WebSocket:
    def __init__(self, API, token: str, user: str, channel: str):
        self.reader = None
        self.writer = None

        self.API = API              # API connection
        self.token = token          # oauth token. MUST start with 'oauth:'
        self.user = user            # bot's username
        self.channel = channel      # channel to connect to



    async def connect(self):
        '''
        connects to and sends twitch IRC all the info it needs to connect to chat with appropriate permissions
        '''
        self.reader, self.writer = await asyncio.open_connection('irc.chat.twitch.tv', 6667)
        await self.basic_send('CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership')
        await self.basic_send(f'PASS {self.token}')
        await self.basic_send(f'NICK {self.user}')
        await self.basic_send(f'JOIN #{self.channel}')



    async def basic_send(self, msg: str):
        '''
        sends a message to the twitch irc at it's most basic level
        NOTE won't send anything to twitch chat, for that use send()
        '''
        self.writer.write(f'{msg}\r\n'.encode())
        await self.writer.drain()



    async def send(self, msg: str):
        '''
        sends a message to twitch chat
        '''
        self.writer.write(f'PRIVMSG #{self.channel} :{msg}\r\n'.encode())



    async def disconnect(self):
        '''
        disconnects from twitch IRC
        '''
        self.writer.close()
        await self.writer.wait_closed()



    async def listen(self):
        '''
        gets chat messages as they come in.
        ONLY gets messages in chat. shouldn't get things like subscription or follows or bit messages
        '''
        while True:
            # msg = self.irc.recv(2048).decode('utf-8')
            msg = await self.reader.readline()
            msg = msg.decode()

            if 'PRIVMSG' in msg:
                chat = ChatInfo.Chat(self.API)
                await chat.parse(msg)
                print(f'{chat.user.name}: {chat.message}')
                await self.send('pong')
                # log
                # execute commands


            # TEMP
            # tells twitch that we want our connection to stay alive
            if 'PING' in msg:
                await self.basic_send('PONG :tmi.twitch.tv')

            # TEMP
            # kills the bot 'gracefully'
            if 'stop' in msg:
                await self.disconnect()
                return