# python standard modules
import asyncio
import json
from urllib import request

# TwitchPy modules
from .errors import *
from .utilities import *



class Helix:
    """Handles calls to Twitch's New API: Helix

    Reference: https://dev.twitch.tv/docs/api/reference


    Parameters
    --------------
    logger : Logger
        Logger to log things as they happen. Useful for debugging.

    channel : str
        The name of the channel that the bot connects to.

    cid : str
        The bot's client ID.


    Note
    -------------
    You should't have to make an instance of this class.
    """
    def __init__(self, logger, channel: str, cid: str):
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
        """Used to see if credentials (channel and client ID) are valid and working.


        Note
        ----------
        If the channel is invalid, the response will be: {"data":[]}
        If the client ID is invalid, the response will be: {"error":"Unauthorized","status":401,"message":"Must provide a valid Client-ID or OAuth token"}
        """
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
        """Lets you get any endpoint in the API.

        Also translates the response into a dict via json.
        Reference: https://dev.twitch.tv/docs/api/reference


        Parameters
        -------------
        endpoint : str
            The part of the endpoint link after 'twitch.tv/helix'.

            note: MUST start with '/'

            ex: GOOD  '/users?login=someviewer'

                BAD   'user?login=someviewer'

                BAD   'https:api.twitch.tv/helix/user?login=someviewer'


        Returns
        ------------
        dict
            The data received from the endpoint in dict format.


        Raises
        -------------
        TypeError
            Raised if endpoint parameter is not a string
        """
        # input sanitization
        if (err_msg := check_param(endpoint, str)):
            raise TypeError(f'TwitchPy.API.Helix.get_endpoint(): {err_msg}')

        await self.logger.log(9, 'request_get', f'GET: {self.base_url}{endpoint}')
        req = request.Request(f'{self.base_url}{endpoint}', headers=self.header)
        response = json.loads(request.urlopen(req).read().decode())
        await self.logger.log(9, 'request_response', f'response: {response}')
        return response



    async def get_user_info(self, user: str or [str]) -> list:
        """Gets viewer info based on either their username or id.

        Reference: https://dev.twitch.tv/docs/api/reference#get-users


        Parameters
        -------------
        user : str or [str]
            A list of strings of viewers to get info on. These strings can be the viewers' usernames or user IDs or a mixture of both.

            note: they MUST be strings, even though their user ID might be an int.


        Returns
        ------------
        list
            An example: ``[{'broadcaster_type': 'affiliate', 'description': 'example ' 'description ', 'display_name': 'johndoe',
            'id': '1234567890', 'login': 'johndoe', 'offline_image_url': 'url here', 'profile_image_url': 'url here', 'type': 'staff',
            'view_count': 12345}]``


        Raises
        -------------
        TypeError
            Raised if any element in user parameter is not a str
        """
        user = makeiter(user)

        await self.logger.log(19, 'basic', f'getting info on user(s): {user}')
        endpoint = ''
        for u in user:
            # input sanitization
            if not isinstance(u, str):
                raise TypeError(f"TwitchPy.API.Helix.get_user_info(): user expects 'str' not '{type(u)}'")

            if u.isdigit():
                endpoint += f'&id={u}'
            else:
                endpoint += f'&login={u}'
        response = await self.get_endpoint(f'/users?login={endpoint}')
        return response['data']



    async def get_my_followers(self) -> ((str, str)):
        """Gets all the viewers who follow the broadcaster.

        reference: https://dev.twitch.tv/docs/api/reference#get-users-follows


        Returns
        -----------
        tuple
            contains tuples whose first elements are usernames and second elements are user IDs.
        """
        await self.logger.log(19, 'basic', 'getting followers')
        followers = tuple()
        response  = await self.get_endpoint(f'/users/follows?to_id={self.broadcaster_id}&first=100')

        while response['data']:
            for user in response['data']:
                followers.add((user['from_name'], user['from_id']))
            response = await self.get_endpoint(f'/users/follows?to_id={self.broadcaster_id}&first=100&after={response["pagination"]["cursor"]}')
        return followers



    async def follows_me(self, user_id: str) -> bool:
        """Checks to see if a viewer is following the broadcaster.

        Reference: https://dev.twitch.tv/docs/api/reference#get-users-follows


        Parameters
        -------------
        user_id : str
            The user ID of the viewer whose follow status you want to know.


        Returns
        ----------
        bool
            True if the viewer does follow you. False if they don't.


        Raises
        -------------
        TypeError
            Raised if user_id parameter is not a string
        """
        # input sanitization
        if (err_msg := check_param(user_id, str)):
            raise TypeError(f'TwitchPy.API.Helix.follows_me(): {err_msg}')

        await self.logger.log(19, 'basic', f'determing if {user_id} is a follower')
        response = await self.get_endpoint(f'/users/follows?to_id={self.broadcaster_id}&from_id={user_id}')
        return bool(response['total'])



    async def get_viewers(self) -> dict:
        """Gets all viewers who are currently in chat


        Returns
        ------------
        dict
            An example: ``{"_links": {}, "chatter_count": 1, "chatters": {"broadcaster": ["broadcaster username"], "vips": [],
            "moderators": ["mod1"], "staff": [], "admins": [], "global_mods": [], "viewers": ["viewer1", "viewer2"]}}``


        Note
        -----------
        This is not a Helix endpoint and does not call get_endpoint()
        """
        await self.logger.log(19, 'basic', 'getting viewers')
        await self.logger.log(9, 'request_get', f'GET tmi.twitch.tv/group/user/{self.broadcaster_name}/chatters')
        req = json.loads(request.urlopen(f'https://tmi.twitch.tv/group/user/{self.broadcaster_name}/chatters').read().decode())
        await self.logger.log(9, 'request_response', f'response: {response}')
        return response