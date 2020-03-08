'''
TODO
    * make get_user_info able to take a list of strings
    * figure out a more graceful way to obtain broadcaster id
'''



import requests



'''
handles any twitch API calls
used to get basic information about things like viewers, followers, user info, etc.
reference: https://dev.twitch.tv/docs/api/reference
'''



class Kraken:
    def __init__(self, name: str, cid: str):
        self.base_url = 'https://api.twitch.tv/helix'
        self.header = {'Client-ID': cid}
        self.broadcaster_name = name        # the channel that the bot is connecting to
        self.broadcaster_id = requests.get(f'{self.base_url}/users?login={self.broadcaster_name}', headers=self.header).json()['data'][0]['id']



    async def get_endpoint(self, endpoint: str) -> str:
        '''
        the most basic use of the API handler
        lets you get any endpoint in the API in its rawest form
        here mainly for posterity and has almost no real use
        does no attempt to parse the text at all
        '''
        response = requests.get(f'{self.base_url}/{endpoint}', headers=self.header)
        return response.text



    async def get_user_info(self, username: str) -> dict:
        '''
        gets user info based on their username, not user id
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
        response = requests.get(f'{self.base_url}/users?login={username}', headers=self.header)
        return response.json()['data']



    async def get_my_followers(self) -> dict:
        '''
        gets all users who follow the broadcaster by the broadcaster id (cannot use username)
        returns a dict whose keys are the usernames and whose values are the user's id
        '''
        followers = dict()
        response  = requests.get(f'{self.base_url}/users/follows?to_id={self.broadcaster_id}&first=100', headers=self.header).json()
        while response['data']:
            for user in response['data']:
                followers[user['from_name']] = user['from_id']
            response = requests.get(f'{self.base_url}/users/follows?to_id={self.broadcaster_id}&first=100&after={response["pagination"]["cursor"]}', headers=self.header).json()
        return followers



    async def follows_me(self, user_id: str) -> bool:
        '''
        checks to see if a user is following the broadcaster by user id (cannot use username)
        returns a bool value
        '''
        response = requests.get(f'{self.base_url}/users/follows?to_id={self.broadcaster_id}&from_id={user_id}', headers=self.header).json()
        return bool(response['total'])



    async def get_viewers(self) -> dict:
        '''
        gets all users who are currently in chat for channel_name
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
        response = requests.get(f'tmi.twitch.tv/group/user/{self.broadcaster_name}/chatters')
        return response.json()