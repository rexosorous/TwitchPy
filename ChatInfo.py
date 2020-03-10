import UserInfo



'''
an object created whenever a viewer sends a message
which contains information regarding the message like
the message being sent, who sent it, and whatever else is associated with the message
'''



class Chat:
    def __init__(self, API, channel):
        '''
        arg     API     (required)  the API connection so we can tell if the user is a follower
        arg     channel (required)  the channel the bot is connected to
        '''
        self.API = API
        self.channel = channel
        self.tags = dict()
        self.full_msg = ''      # includes bot prefix and command name
        self.msg = ''           # includes the message without prefix or command name
        self.split_msg = []     # msg split by spaces
        self.user = None



    async def parse(self, raw_message: str):
        '''
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
        '''
        msg = raw_message
        tags = msg[1:msg.find('PRIVMSG ')].split(';')
        msg = msg[msg.find('PRIVMSG ')+9:]
        username = msg[:msg.find(':')-1]
        msg = msg[msg.find(':')+1:-2]
        self.full_msg = msg

        for t in tags:
            key = t[:t.find('=')]
            val = t[t.find('=')+1:]
            self.tags[key] = val

        self.user = await self.get_user()



    async def get_user(self) -> UserInfo:
        '''
        creates a user object from the viewer who types in chat
        contains basic information about them:
            username
            user id
            if they're a broadcaster
            if they're a moderator
            if they're a subscriber
            how long they've been subscribed
            if they're a follower
            their chat badges
        '''
        username = self.tags['display-name']
        user_id = self.tags['user-id']
        broadcaster = 'broadcaster' in self.tags['badges']
        moderator = bool(self.tags['mod'])
        subscriber = bool(self.tags['subscriber'])
        sub_length = int(self.tags['badge-info'][self.tags['badge-info'].find('/')+1:]) if self.tags['subscriber'] else 0
        follower = await self.API.follows_me(user_id)
        badges = self.tags['badges'].split(',')
        return UserInfo.User(name=username, uid=user_id, isbroadcaster=broadcaster, ismod=moderator, issub=subscriber, sublength=sub_length, isfollower=follower, badges=badges)