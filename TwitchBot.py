'''
TO DO:
    * allow for predefined logger
    * allow for custom stopcode / kill command OR require kill command
    * print/log startup information
    * handle exceptions involving invalid login info / bad connection / etc
    * somehow find out when a user becomes a follower? or maybe make several checks all the time??
'''



import asyncio
import json
import requests

import APIHandler
import websocket



'''
a driver class for the whole twitch chat bot
the most top level structure
'''



class Client:
    def __init__(self, token: str, user: str, channel: str, client_id: str):
        self.API = APIHandler.Kraken(channel, client_id)
        self.connection = websocket.WebSocket(self.API, token, user, channel)
        self.listen_loop = None



    def start(self):
        self.listen_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.listen_loop)

        self.listen_loop.run_until_complete(self.connection.connect())
        self.listen_loop.run_until_complete(self.connection.listen())