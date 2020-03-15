class User:
    """More or less just a container to hold information on the viewer who sent a message.

    Parameters
    -----------
    name : str
        The username of the viewer.

    uid : str
        The user ID of the viewer.

    broadcaster : bool
        True if this viewer is the broadcaster (streamer).

    moderator : bool
        True if this viewer is a moderator of the channel.

    subscriber : bool
        True if this viewer is a subscriber of the channel.

    sub_legnth : int
        If the viewer is a subscriber, how long in months they've been subscribed.
        If they are not a subscriber, this will be 0.

    badges : [str]
        A list of all the chat badges the viewer has.


    Attributes
    ------------
    See Parameters


    Note
    ------------
    Does not keep track of follower status because that requries an API call.
    """
    def __init__(self, name: str, id: str, broadcaster: bool, moderator: bool, subscriber: bool, sub_length: int, badges: [str]):
        # variables given
        self.name = name
        self.id = uid
        self.broadcaster = broadcaster
        self.moderator = moderator
        self.subscriber = subscriber
        self.sub_length = sub_length
        self.badges = badges





        ###################### GETTER FUNCTIONS ######################

        def get_name(self) -> str:
            return self.name

        def get_id(self) -> str:
            return self.name

        def is_broadcaster(self) -> bool:
            return self.broadcaster

        def is_mod(self) -> bool:
            return self.moderator

        def is_sub(self) -> bool:
            return self.subscriber

        def get_sub_length(self) -> int:
            return self.sub_length

        def get_badges(self) -> [str]:
            return self.badges