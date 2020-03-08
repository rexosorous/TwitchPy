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
    def __init__(self, token: str, user: str, channel: str, client_id: str):
        self.commands = None
        self.API = APIHandler.Kraken(name=channel, cid=client_id)
        self.connection = Websocket.IRC(self.API, self.commands, token=token, user=user, channel=channel)
        self.listen_loop = None



    def add_commands(self, cmds):
        self.commands = cmds
        self.connection.add_commands(cmds)



    def run(self):
        self.listen_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.listen_loop)

        self.listen_loop.run_until_complete(self.connection.connect())
        self.listen_loop.run_until_complete(self.connection.listen())