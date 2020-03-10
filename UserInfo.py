'''
more or less just a container for basic information about a viewer
we could've used a dict, but i want to keep this open to adding more functionality
'''



class User:
    def __init__(self, name: str, uid: str, isbroadcaster: bool, ismod: bool, issub: bool, sublength: int, badges: [str]):
        '''
        arg     name            (required)  the username of the viewer
        arg     uid             (required)  the user id of the viewer
        arg     isbroadcaster   (required)  true if the viewer is the broadcaster of the channel else false
        arg     ismod           (required)  true if the viewer is a moderator of the channel else false
        arg     issub           (required)  true if the viewer is a subscriber to the channel else false
        arg     sublength       (required)  how long (in months) a subscriber has been subscribed
        arg     badges          (required)  a list of the all the badges the viewer has in the chat

        note: can't keep track of follower status because that requires an API call and isn't part of the chat message
        i could have User hold an instance of API or something similar, but it seems like overkill for one thing.
        '''
        self.name = name
        self.id = uid
        self.broadcaster = isbroadcaster
        self.moderator = ismod
        self.subscriber = issub
        self.sub_length = sublength
        self.badges = badges