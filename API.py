'''
TODO
    * make get_user_info able to take a list of strings
    * allow get_user_info to also allow user ids via kwargs
    * figure out a more graceful way to obtain broadcaster id
'''



import asyncio
import requests

# TwitchPy modules
from errors import *



'''
handles any twitch API calls
used to get basic information about things like viewers, followers, user info, etc.
reference: https://dev.twitch.tv/docs/api/reference
'''



class Helix:
    def __init__(self, logger, channel: str, cid: str):
        '''
        arg     channel     (required)  the channel that the bot connects to. aka: the broadcaster of channel
        arg     cid         (required)  bot's client id
        '''
        self.logger = logger
        asyncio.run(self.logger.log(11, 'init', 'initializing API...'))

        self.base_url = 'https://api.twitch.tv/helix'
        self.header = {'Client-ID': cid}
        self.broadcaster_name = channel
        self._test_connection()     # test first to avoid an indexerror due to invalid broadcaster name
        self.broadcaster_id = requests.get(f'{self.base_url}/users?login={self.broadcaster_name}', headers=self.header).json()['data'][0]['id']

        asyncio.run(self.logger.log(11, 'init', 'successfully intialized API'))



    def _test_connection(self):
        '''
        used to see if credentials (channel and client id) are valid and working
        if bad channel/broadcaster name, response will be: {"data":[]}
        if bad client id, response will be: {"error":"Unauthorized","status":401,"message":"Must provide a valid Client-ID or OAuth token"}
        '''
        asyncio.run(self.logger.log(11, 'init', 'testing API credentials...'))

        response = requests.get(f'{self.base_url}/users?login={self.broadcaster_name}', headers=self.header).json()
        if 'status' in response:
            if response['status'] == 401:
                asyncio.run(self.logger.log(40, 'error', f'{response}'))
                asyncio.run(self.logger.log(40, 'error', 'test failed! invalid client ID'))
                raise InvalidClientID

        if not response['data']:
            asyncio.run(self.logger.log(40, 'error', f'{response}'))
            asyncio.run(self.logger.log(40, 'error', 'test failed! channel does not exist'))
            raise InvalidChannel

        asyncio.run(self.logger.log(11, 'init', 'API credentials are good'))




    async def get_endpoint(self, endpoint: str) -> str:
        '''
        the most basic use of the API handler
        lets you get any endpoint in the API in its rawest form
        here mainly for posterity and has almost no real use
        does no attempt to parse the text at all
        '''
        await self.logger.log(9, 'request_get', f'GET: {self.base_url}/{endpoint}')
        response = requests.get(f'{self.base_url}/{endpoint}', headers=self.header)
        await self.logger.log(9, 'request_response', f'response: {response.text}')
        return response.text



    async def get_user_info(self, username: str) -> dict:
        '''
        gets viewer info based on their username, not user id
        expected response (not output):
        {
            'data':
                [ # the reason this is a list is because we can request more than one user's info at a time
                    {   'broadcaster_type': 'affiliate', # can be 'partner', 'affiliate',  or ''
                        'description': 'example '
                                       'description ',
                        'display_name': 'johndoe',
                        'id': '1234567890',
                        'login': 'johndoe',
                        'offline_image_url': 'url',
                        'profile_image_url': 'url',
                        'type': '', # can be 'staff', 'admin', 'global_mod', or ''
                        'view_count': 12345
                    }
                ]
        }
        '''
        await self.logger.log(19, 'basic', f'getting info on user: {username}')
        await self.logger.log(9, 'request_get', f'GET {self.base_url}/users?login={username}')
        response = requests.get(f'{self.base_url}/users?login={username}', headers=self.header).json()
        await self.logger.log(9, 'request_response', f'response: {response}')
        return response['data']



    async def get_my_followers(self) -> dict:
        '''
        gets all viewers who follow the broadcaster by the broadcaster id (cannot use username)
        returns a dict whose keys are the usernames and whose values are the user's id
        '''
        await self.logger.log(19, 'basic', 'getting followers')
        await self.logger.log(9, 'request_get', f'GET {self.base_url}/users/follows?to_id={self.broadcaster_id}&first=100')
        followers = dict()
        response  = requests.get(f'{self.base_url}/users/follows?to_id={self.broadcaster_id}&first=100', headers=self.header).json()
        await self.logger.log(9, 'request_response', f'response: {response}')

        while response['data']:
            for user in response['data']:
                followers[user['from_name']] = user['from_id']
            await self.logger.log(9, 'request_get', f'GET {self.base_url}/users/follows?to_id={self.broadcaster_id}&first=100&after={response["pagination"]["cursor"]}')
            response = requests.get(f'{self.base_url}/users/follows?to_id={self.broadcaster_id}&first=100&after={response["pagination"]["cursor"]}', headers=self.header).json()
            await self.logger.log(9, 'request_response', f'response: {response}')
        return followers



    async def follows_me(self, user_id: str) -> bool:
        '''
        checks to see if a viewer is following the broadcaster by user id (cannot use username)
        returns a bool value
        '''
        await self.logger.log(19, 'basic', f'determing if {user_id} is a follower')
        await self.logger.log(9, 'request_get', f'GET {self.base_url}/users/follows?to_id={self.broadcaster_id}&from_id={user_id}')
        response = requests.get(f'{self.base_url}/users/follows?to_id={self.broadcaster_id}&from_id={user_id}', headers=self.header).json()
        await self.logger.log(9, 'request_response', f'response: {response}')
        return bool(response['total'])



    async def get_viewers(self) -> dict:
        '''
        gets all viewers who are currently in chat for channel_name
        expected output:
        {
            "_links": {},
            "chatter_count": 1, # how many users there are
            "chatters":
            {
                "broadcaster": ["broadcaster username"],
                "vips": [],
                "moderators": [],
                "staff": [],
                "admins": [],
                "global_mods": [],
                "viewers": ["viewer1", "viewer2"]
            }
        }
        '''
        await self.logger.log(19, 'basic', 'getting viewers')
        await self.logger.log(9, 'request_get', f'GET tmi.twitch.tv/group/user/{self.broadcaster_name}/chatters')
        response = requests.get(f'tmi.twitch.tv/group/user/{self.broadcaster_name}/chatters').json()
        await self.logger.log(9, 'request_response', f'response: {response}')
        return response