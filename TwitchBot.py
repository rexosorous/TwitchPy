'''
TO DO:
    * allow for predefined logger
    * allow for custom stopcode / kill command OR require kill command
    * figure out how to do on_msg(), on_ready(), on_death(), etc
    * print/log startup information
    * raise exceptions involving invalid login info / bad connection / etc
    * somehow find out when a user becomes a follower? or maybe make several checks all the time??
    * automatically produce help msg? (require functions to have "description" variable)
'''



import asyncio
import json
import requests

import APIHandler
import Commands
import Websocket



'''
a driver class for the whole twitch chat bot
the most top level structure
'''



class Client:
    def __init__(self, *, token: str, user: str, channel: str, client_id: str):
        self.commands = set()
        self.API = APIHandler.Kraken(name=channel, cid=client_id)
        self.IRC = Websocket.IRC(self.API, self.commands, token=token, user=user, channel=channel)
        self.listen_loop = None



    def add_cog(self, cog):
        '''
        adds command cogs to the bot
        this basically just adds commands to the parts of the bot that needs access to them
        '''
        self.commands.add(cog)



    def run(self):
        '''
        sets up async event loops to listen to twitch chat
        '''
        self.listen_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.listen_loop)

        self.listen_loop.run_until_complete(self.IRC.connect())
        self.listen_loop.run_until_complete(self.IRC.listen())



    def get_IRC(self) -> Websocket.IRC:
        '''
        returns the websocket connection so the user can do:
            conn = bot.get_connection()
            conn.send(msg)
        '''
        return self.IRC



    def get_API(self) -> APIHandler.Kraken:
        '''
        returns the APIHandler so the user can do:
            API = bot.get_API()
            API.get_viewers()
        '''
        return self.API