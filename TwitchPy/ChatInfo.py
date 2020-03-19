# TwitchPy modules
from .UserInfo import User



"""
an object created whenever a viewer sends a message
which contains information regarding the message like
the message being sent, who sent it, and whatever else is associated with the message
"""



class Chat:
    """Parses and holds basic information about the chat message being sent.

    An object of this gets instantiated whenever a viewer sends a message through the IRC chat.


    Parameters
    -------------
    channel : str
        The channel that the bot is connected to.


    Attributes
    ------------
    channel : str
        See parameters.

    tags : dict
        Tags associated with the message.

        See https://dev.twitch.tv/docs/irc/tags#privmsg-twitch-tags

    raw_message : str
        The raw message received from IRC. This is probably not what you want to be accessing unless you know what you're looking for.

        ex: '@badge-info=subscriber/12;badges=subscriber/12,premium/1;color=#FF0000; ... PRIVMSG #someviewer :!foobar lorem ipsum'

    msg : str
        The actual message that you would see on twitch chat.

        ex: '!foobar lorem ipsum'

    arg_msg : str
        msg without the command prefix or command name.

        ex: 'lorem ipsum'

    args : [str]
        arg_msg split by spaces. This is what you'll probably use the most in your commands.

        ex: ['lorem', 'ipsum']

    user : User
        Object containing basic information about the viewer who sent the message


    Note
    ----------
    You shouldn't have to make an instance of this class.
    """
    def __init__(self, channel: str):
        # variables given
        self.channel = channel

        # variables created
        self.tags = dict()
        self.raw_message = ''   # the raw message received from twitch
        self.msg = ''           # includes bot prefix and command name
        self.arg_msg = ''       # msg without prefix or command name
        self.args = []          # arg_msg split by spaces to better access them
        self.user = None



    async def _parse(self, raw_message: str):
        """
        parses a raw message from twitch irc client into readable/iterable data structures
        basic form of a raw message: <tags> PRIVMSG #<user> :<msg>
        EXAMPLE FORMATTED RAW MESSAGE (this would all be one line when we get it from twitch)
            @
            badge-info=subscriber/17;
            badges=broadcaster/1,subscriber/12,premium/1;
            color=#FF0000;
            display-name=Gay_Zach;
            emotes=;
            flags=;
            id=17124c80-93d4-4937-9448-aca5d6c265dc;
            mod=0;
            room-id=75202804;
            subscriber=1;
            tmi-sent-ts=1583607640375;
            turbo=0;
            user-id=75202804;
            user-type= :gay_zach!gay_zach@gay_zach.tmi.twitch.tv

            PRIVMSG #gay_zach :lorem ipsum
        https://dev.twitch.tv/docs/irc/tags#privmsg-twitch-tags
        """
        self.raw_message = raw_message
        msg = raw_message
        tags = msg[1:msg.find('PRIVMSG ')].split(';')
        msg = msg[msg.find('PRIVMSG ')+9:]
        username = msg[:msg.find(':')-1]
        msg = msg[msg.find(':')+1:-2]
        self.msg = msg

        for t in tags:
            key = t[:t.find('=')]
            val = t[t.find('=')+1:]
            self.tags[key] = val

        self.user = await self.__create_user()



    async def __create_user(self) -> User:
        """
        creates a user object from the viewer who types in chat
        contains basic information about them:
            username
            user id
            if they're a broadcaster
            if they're a moderator
            if they're a subscriber
            how long they've been subscribed
            their chat badges
        """
        username = self.tags['display-name']
        user_id = self.tags['user-id']
        broadcaster = 'broadcaster' in self.tags['badges']
        moderator = bool(int(self.tags['mod']))
        subscriber = bool(int(self.tags['subscriber']))
        sub_length = int(self.tags['badge-info'][self.tags['badge-info'].find('/')+1:]) if self.tags['subscriber'] else 0
        badges = self.tags['badges'].split(',')
        return User(name=username, uid=user_id, broadcaster=broadcaster, moderator=moderator, subscriber=subscriber, sub_length=sub_length, badges=badges)





    ###################### GETTER FUNCTIONS ######################

    def get_channel(self) -> str:
        return self.channel

    def get_tags(self) -> dict:
        return self.tags

    def get_msg(self) -> str:
        return self.msg

    def get_full_args(self) -> str:
        return self.full_args

    def get_split_args(self) -> [str]:
        return self.split_args

    def get_user(self) -> User:
        return self.user