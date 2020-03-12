'''
TODO
    * make get_user_info able to take a list of strings
    * allow get_user_info to also allow user ids via kwargs
'''



# python standard modules
import asyncio
import json
from urllib import request

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
        # log
        self.logger = logger
        asyncio.run(self.logger.log(11, 'init', 'initializing API...'))

        # variables given
        self.header = {'Client-ID': cid}
        self.broadcaster_name = channel

        # variables made
        self.base_url = 'https://api.twitch.tv/helix'
        self.broadcaster_id = None

        # additional setup
        asyncio.run(self._test_connection())    # test first to avoid an indexerror due to invalid broadcaster name

        # log
        asyncio.run(self.logger.log(11, 'init', 'successfully intialized API'))



    async def _test_connection(self):
        '''
        used to see if credentials (channel and client id) are valid and working
        if bad channel/broadcaster name, response will be: {"data":[]}
        if bad client id, response will be: {"error":"Unauthorized","status":401,"message":"Must provide a valid Client-ID or OAuth token"}
        '''
        await self.logger.log(11, 'init', 'testing API credentials...')

        response = await self.get_endpoint(f'/users?login={self.broadcaster_name}')
        if 'status' in response:
            if response['status'] == 401:
                await self.logger.log(40, 'error', f'{response}')
                await self.logger.log(40, 'error', 'test failed! invalid client ID')
                raise InvalidClientID

        if not response['data']:
            await self.logger.log(40, 'error', f'{response}')
            await self.logger.log(40, 'error', 'test failed! channel does not exist')
            raise InvalidChannel

        self.broadcaster_id = response['data'][0]['id']
        await self.logger.log(11, 'init', 'API credentials are good')




    async def get_endpoint(self, endpoint: str) -> dict:
        '''
        the most basic use of the API handler
        lets you get any endpoint in the API translated to a dict via json
        note: automatically takes care of the headers for you

        arg     endpoint    (required)  MUST ONLY be the part after 'twitch.tv/helix'
                                        AND MUST start with '/'
                                        ex: GOOD /users?login=someuser
                                            BAD  https:api.twitch.tv/helix/users?login=someuser
                                            BAD  users?login=someuser
        '''
        await self.logger.log(9, 'request_get', f'GET: {self.base_url}{endpoint}')
        req = request.Request(f'{self.base_url}{endpoint}', headers=self.header)
        response = json.loads(request.urlopen(req).read().decode())
        await self.logger.log(9, 'request_response', f'response: {response}')
        return response



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
        response = await self.get_endpoint(f'/users?login={username}')
        return response['data']



    async def get_my_followers(self) -> dict:
        '''
        gets all viewers who follow the broadcaster by the broadcaster id (cannot use username)
        returns a dict whose keys are the usernames and whose values are the user's id
        '''
        await self.logger.log(19, 'basic', 'getting followers')
        followers = dict()
        response  = await self.get_endpoint(f'/users/follows?to_id={self.broadcaster_id}&first=100')

        while response['data']:
            for user in response['data']:
                followers[user['from_name']] = user['from_id']
            response = await self.get_endpoint(f'/users/follows?to_id={self.broadcaster_id}&first=100&after={response["pagination"]["cursor"]}')
        return followers



    async def follows_me(self, user_id: str) -> bool:
        '''
        checks to see if a viewer is following the broadcaster by user id (cannot use username)
        returns a bool value
        '''
        await self.logger.log(19, 'basic', f'determing if {user_id} is a follower')
        response = await self.get_endpoint(f'/users/follows?to_id={self.broadcaster_id}&from_id={user_id}')
        return bool(response['total'])



    async def get_viewers(self) -> dict:
        '''
        gets all viewers who are currently in chat for channel_name
        does not call self.get_endpoint() because the base url is different
        note: does not need headers
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
        req = json.loads(request.urlopen(f'https://tmi.twitch.tv/group/user/{self.broadcaster_name}/chatters').read().decode())
        await self.logger.log(9, 'request_response', f'response: {response}')
        return response