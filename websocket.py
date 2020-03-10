import asyncio

# TwitchPy modules
import ChatInfo
from errors import *



'''
handles the IRC connection to the twitch chat
responsible for reading and sending messages
reference: https://dev.twitch.tv/docs/irc/guide
'''



class IRC:
    def __init__(self, API, commands, events, token: str, user: str, channel: str):
        '''
        arg     API         (required)  the API connection
        arg     commands    (required)  a set of commands objects
        arg     events      (required)  the event handler
        arg     token       (required)  the bot's oauth token
        arg     user        (required)  the bot's username
        arg     channel     (required)  the channel the bot tries to connect to
        '''
        self.reader = None
        self.writer = None

        self.API = API              # API connection
        self.commands = commands    # command handler
        self.events = events        # event handler
        self.token = token          # oauth token
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
        await self.events.on_connect()



    async def basic_send(self, msg: str):
        '''
        sends a message to the twitch irc at it's most basic level
        NOTE won't send anything to twitch chat, for that use send()
        '''
        self.writer.write(f'{msg}\r\n'.encode())
        await self.writer.drain()



    async def send(self, msg: str):
        '''
        formats and sends a message to twitch chat
        https://dev.twitch.tv/docs/irc/guide#generic-irc-commands
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
        try:
            while True:
                # msg = self.irc.recv(2048).decode('utf-8')
                msg = await self.reader.readline()
                msg = msg.decode()


                # tells twitch that we want our connection to stay alive
                # twitch will occasionally send 'PING :tmi.twitch.tv' and expects 'PONG :tmi.twitch.tv' back to keep the connection alive
                # https://dev.twitch.tv/docs/irc/guide#connecting-to-twitch-irc
                if msg.startswith('PING'):
                    await self.basic_send('PONG :tmi.twitch.tv')

                # if a message has PRIVMSG in it, it's a public message in twitch chat
                elif 'PRIVMSG' in msg:
                    chat = ChatInfo.Chat(self.API, self.channel)
                    await chat.parse(msg)
                    await self.events.on_msg(chat)

                    error_code = 1
                    # cog.choose_command will return 0 if it found a command to execute
                    # so between multiple cogs, if any of them executed a command,
                    # then error_code will become 0 and we're in the clear
                    # if none of them return 0, then error code will be 1 and
                    # that means that no command was executed
                    for cog in self.commands:
                            error_code *= await cog.choose_command(chat)

                    # code 0 is normal, code 1 is failure to find command
                    if error_code == 0:
                        await self.events.on_cmd(chat)
                    elif error_code == 1:
                        await self.events.on_bad_cmd(chat)
                    # log
        except (KeyboardInterrupt, ExpectedExit) as e:
            await self.events.on_expected_death()
        except Exception as err:
            await self.events.on_unexpected_death(err)
        finally:
            await self.events.on_death()
            await self.disconnect()