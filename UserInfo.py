'''
more or less just a container for basic information about a user
we could've used a dict, but i want to keep this open to adding more functionality
'''



class User:
    def __init__(self, name: str, user_id: str, broadcaster: bool, moderator: bool, subscriber: bool, sub_length: int, follower: str, badges: [str]):
        self.name = name
        self.id = user_id
        self.broadcaster = broadcaster
        self.moderator = moderator
        self.subscriber = subscriber
        self.sub_length = sub_length
        self.follower = follower
        self.badges = badges