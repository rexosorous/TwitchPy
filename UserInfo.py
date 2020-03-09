'''
more or less just a container for basic information about a viewer
we could've used a dict, but i want to keep this open to adding more functionality
'''



class User:
    def __init__(self, name: str, uid: str, isbroadcaster: bool, ismod: bool, issub: bool, sublength: int, isfollower: str, badges: [str]):
        self.name = name
        self.id = uid
        self.broadcaster = isbroadcaster
        self.moderator = ismod
        self.subscriber = issub
        self.sub_length = sublength
        self.follower = isfollower
        self.badges = badges