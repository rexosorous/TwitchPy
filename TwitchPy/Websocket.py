# python standard modules
import asyncio
import sys

# TwitchPy modules
from .ChatInfo import Chat
from .errors import *
from .UserInfo import User



'''
handles the IRC connection to the twitch chat
responsible for reading and sending messages
reference: https://dev.twitch.tv/docs/irc/guide
'''



class IRC:
    def __init__(self, logger, commands, events, token: str, user: str, channel: str):
        '''
        arg     logger      (required)  logger
        arg     commands    (required)  a set of commands objects
        arg     events      (required)  the event handler
        arg     token       (required)  the bot's oauth token
        arg     user        (required)  the bot's username
        arg     channel     (required)  the channel the bot tries to connect to
        '''
        # log
        self.logger = logger
        asyncio.run(self.logger.log(11, 'init', 'initializing IRC...'))

        # variables given
        self.commands = commands    # command handler
        self.events = events        # event handler
        self.token = token          # oauth token
        self.user = user            # bot's username
        self.channel = channel      # channel to connect to

        # variables created
        # these will be set during self.connect()
        self.reader = None
        self.writer = None

        # log
        asyncio.run(self.logger.log(11, 'init', 'successfully initialized IRC'))



    async def connect(self):
        '''
        connects to and sends twitch IRC all the info it needs to connect to chat with appropriate permissions
        '''
        await self.logger.log(11, 'init', f'sending credentials...')
        self.reader, self.writer = await asyncio.open_connection('irc.chat.twitch.tv', 6667)
        await self.basic_send('CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership')
        await self.basic_send(f'PASS {self.token}')
        await self.basic_send(f'NICK {self.user}')

        # raise exceptions if we did not successfully connect
        # also, apparently NICK doesn't matter, we can change it to whatever and twitch will accept it
        response = (await self.reader.readline()).decode() # we have to 'burn' a readline due to the response from CAP REQ
        response = (await self.reader.readline()).decode()

        if 'NOTICE' in response:
            await self.logger.log(40, 'error', response)
            if 'Improperly formatted auth' in response:
                # full twitch response ":tmi.twitch.tv NOTICE * :Improperly formatted auth"
                await self.logger.log(40, 'error', 'improperly formatted auth token. did you forget to put "oauth:" at the start of the token?')
                raise BadAuthFormat
            if 'Login authentication failed' in response:
                # full twitch response ":tmi.twitch.tv NOTICE * :Login authentication failed"
                await self.logger.log(40, 'error', 'invalid auth token')
                raise InvalidAuth

        await self.logger.log(11, 'init', f'credentials accepted')
        await self._join(self.channel)



    async def _join(self, channel: str):
        '''
        joins a twitch channel's chat
        note: the user should not be using this. the user should use TwitchBot.Client.change_channel() function
              because we also need to update information in API.Helix
        note: there's no good way to check if we successfully connection to the channel,
              but we check if channel is a valid channel name when we update API.Helix

        arg     channel     (required)  the channel to connect to
        '''
        await self.logger.log(19, 'basic', f'connecting to channel: {self.channel}...')
        self.channel = channel
        await self.basic_send(f'JOIN #{self.channel}')
        await self.logger.log(19, 'basic', f'successfully connected to channel: {self.channel}')
        await self.events.on_connect()



    async def basic_send(self, msg: str):
        '''
        sends a message to the twitch irc at it's most basic level
        NOTE won't send anything to twitch chat, for that use self.send()
        '''
        await self.logger.log(9, 'send', f'SEND: "{msg}"')
        self.writer.write(f'{msg}\r\n'.encode())
        await self.writer.drain()



    async def send(self, msg: str):
        '''
        formats and sends a message to twitch chat
        https://dev.twitch.tv/docs/irc/guide#generic-irc-commands
        '''
        chat = Chat(self.channel)
        chat.msg = msg
        chat.user = User(self.user, '', False, False, False, False, [])
        await self.logger.log(21, 'outgoing', chat)
        await self.logger.log(9, 'send', f'SEND: "PRIVMSG #{self.channel} :{msg}"')
        self.writer.write(f'PRIVMSG #{self.channel} :{msg}\r\n'.encode())



    async def disconnect(self):
        '''
        disconnects from twitch IRC
        '''
        await self.logger.log(19, 'basic', f'disconnecting from {self.channel}')
        self.writer.close()
        await self.writer.wait_closed()



    async def listen(self):
        '''
        gets chat messages as they come in.
        ONLY gets messages in chat. shouldn't get things like subscription or follows or bit messages
        '''
        await self.logger.log(20, 'basic', 'bot is now listening...')
        try:
            while True:
                await asyncio.sleep(0)  # this allows tasks to run concurrently
                msg = (await self.reader.readline()).decode()
                await self.logger.log(9, 'recv', msg)

                # tells twitch that we want our connection to stay alive
                # twitch will occasionally send 'PING :tmi.twitch.tv' and expects 'PONG :tmi.twitch.tv' back to keep the connection alive
                # https://dev.twitch.tv/docs/irc/guide#connecting-to-twitch-irc
                if msg.startswith('PING'):
                    await self.basic_send('PONG :tmi.twitch.tv')

                # if a message has PRIVMSG in it, it's a public message in twitch chat
                elif 'PRIVMSG' in msg:
                    chat = Chat(self.channel)
                    await chat._parse(msg)
                    await self.logger.log(21, 'incoming', chat)
                    await self.events.on_msg(chat)

                    error_code = 1

                    # Commands.Cog.choose_command() will return 0 if it found a command to execute
                    # so between multiple cogs, if any of them executed a command,
                    # then error_code will become 0, indicating normal function

                    # Commands.Cog.choose_command() will return 1 if the message doesn't start with
                    # the appropriate prefix. aka: the message is unrelated to the cog's commands
                    # so ONLY if all cogs return 1, then the error_code will remain 1,
                    # indiciating that the chat message has nothing to do with the bot

                    # Commands.Cog.choose_command() will return 2 if it didn't find a command to execute
                    # so assuming that no cog executes a command (which returns 0), then regardless
                    # of if certain cogs are ignored (which returns 1), or if all cogs fail to find
                    # a command (which returns 2), then error_code > 1, indicating that the a viewer
                    # tried to talk to the bot, but the bot couldn't find the right command

                    for cog in self.commands:
                            error_code *= await cog.choose_command(chat)

                    # error_code == 0: successfully executed a command
                    # error_code == 1: chat message is unrelated to the bot
                    # error_code >= 2: failure to find a command to execute
                    if error_code == 0:
                        await self.events.on_cmd(chat)
                    elif error_code == 1:
                        await self.events.on_no_cmd(chat)
                    elif error_code > 1:
                        await self.logger.log(30, 'error', 'unable to find command')
                        await self.events.on_bad_cmd(chat)
        finally:
            await self.disconnect()