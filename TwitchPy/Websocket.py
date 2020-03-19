# python standard modules
import asyncio
import sys

# TwitchPy modules
from .ChatInfo import Chat
from .errors import *
from .UserInfo import User



class IRC:
    """Handles the IRC connection to twitch chat.

    Is responsible for reading and sending messages and selecting which commands to execute.

    Reference: https://dev.twitch.tv/docs/irc/guide


    Parameters
    -----------
    logger : Logger.Logger
        The bot's custom logger.

    commands : (Commands.Cog)
        A set of all the command cogs.

    events : Event.Handler
        The event handler.

    token : str
        The bot's oauth token.

    user : str
        The bot's username.

    channel : str
        The channel to connect to.


    Attributes
    --------------
    See parameters

    reader : asyncio.StreamReader
        The object that's responsible for reading from twitch chat.

        See https://docs.python.org/3/library/asyncio-stream.html#streamreader

    writer : asyncio.StreamWriter
        The object that sends messages to twitch IRC

        See https://docs.python.org/3/library/asyncio-stream.html#streamwriter
    """
    def __init__(self, logger, commands, events, token: str, user: str, channel: str):
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
        '''Connects to and sends twitch IRC all the info it needs to connect to chat with appropriate permissions
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
        '''Sends a message to the twitch IRC at it's most basic level.

        Note
        --------
        This isn't for sending messages to twitch chat. For that use Websocket.IRC.send()

        Parameters
        -------------
        msg : str
            The message that IRC is expecting like 'CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership'.
        '''
        await self.logger.log(9, 'send', f'SEND: "{msg}"')
        self.writer.write(f'{msg}\r\n'.encode())
        await self.writer.drain()



    async def send(self, msg: str):
        '''Sends a message to twitch chat.

        Parameters
        -----------
        msg : str
            The message that you want to show up in twitch chat.
        '''
        chat = Chat(self.channel)
        chat.msg = msg
        chat.user = User(self.user, '', False, False, False, False, [])
        await self.logger.log(21, 'outgoing', chat)
        await self.logger.log(9, 'send', f'SEND: "PRIVMSG #{self.channel} :{msg}"')
        self.writer.write(f'PRIVMSG #{self.channel} :{msg}\r\n'.encode())



    async def disconnect(self):
        '''Closes all connections to twitch IRC.
        '''
        await self.logger.log(19, 'basic', f'disconnecting from {self.channel}')
        self.writer.close()
        await self.writer.wait_closed()



    async def listen(self):
        '''An infinite loop that listens to twitch chat.

        Also responsible for parsing chat messages and deciding which commands to execute (if any).
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

                    for cog in self.commands:
                            await cog._choose_command(chat)
        finally:
            await self.disconnect()