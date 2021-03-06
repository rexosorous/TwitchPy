Guides & Help
*************


Installation
=============

TwitchPy only uses python standard libraries and shouldn't need you to install anything else.

Because TwitchPy is not a PyPi package, you should use::

    pip install git+https://github.com/rexosorous/TwitchPy






Registering a Bot With Twitch
===============================

You can follow this guide: https://dev.twitch.tv/docs/authentication/#registration or any other countless
guides on the internet to register your bot with twitch. Just make sure to save your bot's username,
client ID, and OAuth token.






Your First Bot
==================

Now that you've registered a bot on twitch and gotten all the login credentials, we can build our first bot! ::

    from TwitchPy import TwitchBot

    login = {   "token": "your auth token",
                "user": "your bot name",
                "client_id": "the bot's client ID",
                "channel": "the channel to connect to"
    }

    bot = TwitchBot.Client(**login)
    bot.run()

This is the minimal amount of effort you need to run a bot without any errors - we've created
an instance of ``TwitchPy.TwitchBot.Client()`` and passed it our login information. Right now, we haven't
programmed in any features so the bot doesn't do anything but sit in twitch chat.

In this example, we've hardcoded in our login credentials, but you may want to avoid doing this
if you're going to make your source code publicly available (like if you're going to have a
public git repo for it).

From here, we can start adding in some or all of TwitchPy's features.






Creating Commands
==================

Quickstart
---------------
To set up your own commands, TwitchPy requires you to create a class that inherits from ``TwitchPy.Commands.Cog`` and use
``@Commands.create()`` to create your commands.

Here's a basic example::

    from TwitchPy import TwitchBot, Commands

    class MyCommands(Commands.Cog):         # make sure to inherit Commands.Cog
        def __init__(self, IRC):
            super().__init__(prefix='!')    # calling Commands.Cog's init is required!
            self.IRC = IRC                  # obtained from TwitchBot.Client so we can interact with chat

        @Commands.create()                  # decorator used to create the command
        async def ping(self, ctx):         # the function must take one argument: chat
            await self.IRC.send('pong')

    bot = TwitchBot.Client(**login)
    my_commands = MyCommands(bot.get_IRC())
    bot.add_cogs(my_commands)                # don't forget to add the cog to the bot
    bot.run()

Let's break this down.

``class MyCommands(Commands.Cog):`` - If you want to create your own commands, TwitchPy requires you to create a
class that inherits from ``TwitchPy.Commands.Cog``.

``super().__init__(prefix='!)`` - You have to call ``TwitchPy.Commands.Cog``'s init function which only has one argument.
``prefix`` is the part of the message at the beginning that let's the bot know that the message is meant for it.

``self.IRC = IRC`` - ``IRC`` is received from ``TwitchPy.TwitchBot.Client.get_IRC()`` and is an instance of
``TwitchPy.Websocket.IRC`` which is how you'll be interacting and sending messages to twitch chat. For more
information on this, check out `Interacting With IRC`_.

``@Commands.create()`` - A function decorator that creates commands and should precede every command function.

``async def ping(self, ctx):`` - Command functions must be asynchronous (``async``) and accept only one
argument, ``ctx`` , which is an instance of ``TwitchPy.ChatInfo.Chat`` which contains all the information
about the message sent. You can access that information via its attributes which can be found in the references.

``await self.IRC.send('pong')`` - ``TwitchPy.Websocket.IRC.send()`` is an asynchronous function and must be
``await`` ed. In this case, this function sends 'pong' to twitch chat.

``bot.add_cogs(my_commmands)`` - After creating an instance of your command class, you have to add it to the
bot via ``TwitchPy.Client.add_cogs()``.

With this we've created a bot with a command cog that uses the prefix '!' and has one command called 'ping' that
causes the bot to reply in chat with 'pong'. So whenever a viewer types in chat '!ping', the bot will say 'pong'.



Naming Commands
-----------------

In the last example, the bot used the function name as the command name, but that doesn't have to be the case.
``TwitchPy.Commmands.create()`` has a kwarg field, ``name``, which you can use to separate the function name
from the command name. ::

    @Commands.create(name='hello')
    async def say_hello(self, ctx):
        await self.IRC.send('HeyGuys')

This command is executed whenever a viewer says '!hello' and *won't* execute when a viewer says '!say_hello'.

``name`` can also take a list of strings which allows you to create functions with several names. ::

    @Commands.create(name=['hello', 'hi', 'howdy'])
    async def say_hello(self, ctx):
        await self.IRC.send('HeyGuys')

Here's the same command as before, but with multiple names. So now the command will execute whenever a viewer says
'!hello' or '!hi' or '!howdy'.

.. note:: Command names with spaces in it *should* work, but this isn't something we test for, so use at
          your own risk.


Using Arguments
----------------

If you want a command to expect some arguments, then all you have to do is add arguments to the function definition
like you normally would. ::

    @Commands.create(name='mock'):
    async def mock_user(self, ctx, user):
        msg = get_last_message(user)    # not a TwitchPy function. assume this exists somewhere in the program.
        mocked_msg = ''
        for char in msg:
            if random.choice([True, False]):
                mocked_msg += char.upper()
            else:
                mocked_msg += char.lower()
        await self.IRC.send(mocked_msg)

Here we have a command to mock a user's last message they sent in chat by randomizing the capitalization of each
character. Because of the nature of the command, we need one argument ``user``. So ``mock_user()`` will only get
called if a viewer types in chat '!mock {user}' and **not** if they type '!mock' or '!mock lorem ipsum'.

If you're unsure how many arguments a function might accept, you can use ``*args`` which will end up being
a list of strings (each being an arg). ::

    @Commands.create(name='mock'):
    async def mock_msg(self, ctx, *args):
        msg = ' '.join(args)
        mocked_msg = ''
        for char in msg:
            if random.choice([True, False]):
                mocked_msg += char.upper()
            else:
                mocked_msg += char.lower()
        await self.IRC.send(mocked_msg)

This is a command that mocks an entire message. So given the input '!mock hello world', the bot might respond
with 'hELLO WOrlD'. Because of ``*args`` this command will execute regardless of how many args we send it.

Notice that ``mock_user()`` and ``mock_msg()`` both create a command with the name 'mock'. This is completely
fine as long as they expect different amounts of args (not including ``*args``) - ``mock_user()`` has an argcount
of 1 while ``mock_msg()`` has an argcount of 0. So whenever the mock command is called with only one arg, then
``mock_user()`` is called and if there's *any* other argcounts, then ``mock_msg()`` will be called. That is to say,
commands with more args (not counting ``*args``) are prioritized first.

.. note:: If two commands have the same name and argcount, only one will execute
.. note:: TwitchPy makes no effort to convert any args into other data types (like ints or floats).



Permissions
---------------

Lastly, ``TwitchPy.Commands.create()`` let's you limit who is allowed to use a command with the kwargs ``permission`` and
``whitelist``.

``permission`` takes a string and sets a base level for who can use this command based on the viewers'
loyalty / affiliation. The hierarchy is: ``'broadcaster'`` > ``'moderator'`` > ``'subscriber'`` > ``'everyone'``. ::

    @Commands.create(permission='moderator')
    async def checkfollower(self, ctx, user):
        isfollower = self.API.follows_me(user)
        await self.IRC.send(str(isfollower))

This is a command that checks if a user is a follower of the channel or not. Because we don't want everyone to be
able to use this command, we set ``permission='moderator'`` which means that only moderators *and* broadcasters
(the streamer) can use this command. If anyone else tries to use this command, the function ``checkfollower()``
does not get called.



Whitelisting
---------------

The kwarg ``whitelist`` takes a list of strings with each element being a username of someone whom you explicitly
want to be able to use the command. ::

    @Commands.create(whitelist='someviewer')
    async def VIP(self, ctx):
        await self.IRC.send('PogChamp s in chat for someviewer!')

This is a command that can *only* be used by someviewer. If anyone else tries to use it (even the broadcaster),
the function ``VIP`` simply won't be called.



Using Both Permission & Whitelisting
-------------------------------------

If both ``permission`` and ``whitelist`` are defined, the ``permission`` will take precedence over
``whitelist``. ::

    @Commands.create(permission='moderator', whitelist='someviewer')
    async def AmISpecial(self, ctx):
        await self.IRC.send('yes')

This command can only be used by any moderator, any broadcaster, and any viewer named 'someviewer'.



Using Multiple Cogs
---------------------

For bigger and more complex bots, you may want to split up your commands amongst multiple cogs to better organize
your code. For example, you may want one cog dedicated for commands that send a constant/static messsage. ::

    class MainCommands(Commands.Cog)
    def __init__(self, IRC):
        super().__init__(prefix='!')
        self.IRC = IRC

    @Commands.create()
    async def foo(self, ctx):
        do_bar()


    class CopyPastaCommands(Commands.Cog)
    def __init__(self, IRC):
        super().__init__(prefix='?')
        self.IRC = IRC

    @Commands.create()
    async def help(self, ctx):
        await self.IRC.send('help message')


    bot = TwitchBot.Client(**login)
    main = MainCommands(bot.get_IRC())
    copypasta = CopyPastaCommands(bot.get_IRC())
    bot.add_cogs([main, copypasta])
    bot.run()

Here we have ``CopyPastaCommands`` that we are going to dedicate for commands that send a constant/static message.
We can use ``TwitchPy.TwitchBot.Client.add_cogs()`` to send both cogs in a list instead of calling ``add_cogs()``
twice.

Notice that the cogs have different prefixes from each other. This is the only possible with multiple cogs. So now
``help()`` won't be called if a viewer says '!help', but only if they say '?help' because the prefix is different.

.. note:: If multiple separate cogs have the same prefix and have commands with the same name(s) and argcounts, all
          of those command functions will be called when the command executed, not just one.






Interacting With IRC
======================


Sending Messages
-------------------

``TwitchPy.Websocket.IRC`` is the class that handles the IRC connection and is responsible for connecting
to a channel, reading twitch chat, and sending messages to twitch chat. Most of the class' functions aren't
useful or available to you, but the one that you should know is ``TwitchPy.Websocket.IRC.send(msg)``
where msg is the message you want sent to twitch chat. Because this function is an async function, it should
be awaited. ::

    from TwitchPy import TwitchBot, Commands

    class MyCommands(Commands.Cog)
        def __init__(self, IRC):
            super().__init__(prefix='!')
            self.IRC = IRC

        @Commands.create():
            async def ping(self, ctx):
                await self.IRC.send('pong')

    bot = TwitchBot.Client(**login)
    mycog = MyCommands(bot.get_IRC())
    bot.add_cogs([mycog])
    bot.run()

To obtain the instance of ``TwitchPy.Websocket.IRC`` that the bot uses, you can use ``TwitchPy.TwitchBot.Client.IRC``
to access the attribute directly or use a getter function ``TwitchPy.TwitchBot.Client.get_IRC()``. Either works and
is perfectly fine to use.


Receiving Messages
-------------------

Whenever a message is received from twitch chat, TwitchPy will create an instance of ``TwitchPy.ChatInfo.Chat``
which contains all the information about that message. This is the ``ctx`` parameter that's sent to any command
functions you create. You can read about all the attributes you can access in references, but here's a short
rundown of the important bits.

+------------------------+-------------+-----------------------------------------------------------------------------+
| field                  | data type   | description                                                                 |
+========================+=============+=============================================================================+
| ctx.msg                | str         | the message received. this includes any command prefixes and command names. |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.arg_msg            | str         | the message without the command prefix and name.                            |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.args               | list of str | ctx.arg_msg split by spaces.                                                |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author             | object      | an instance of ``TwitchPy.UserInfo.User``                                   |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.name        | str         | who sent the message.                                                       |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.id          | str         | the ID of the viewer who sent the message.                                  |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.broadcaster | bool        | whether or not the viewer is the broadcaster/streamer.                      |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.moderator   | bool        | whether or not the viewer is a moderator.                                   |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.subscriber  | bool        | whether or not the viewer is a subscriber.                                  |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.sub_length  | int         | how long the viewer has been a sub.                                         |
+------------------------+-------------+-----------------------------------------------------------------------------+
| ctx.author.badges      | list of str | what badges the viewer has.                                                 |
+------------------------+-------------+-----------------------------------------------------------------------------+


Here's an example that pings the user who calls the command '!pingme': ::

        @Commands.create():
            async def pingme(self, ctx):
                await self.IRC.send(f'@{ctx.user.name}')


Chat History
---------------

By default, TwitchPy will also keep a history of every chat message received (not messages sent by the bot)
during its runtime. This history is stored in the attribute ``TwitchPy.Websocket.IRC.chat_history``, which
is a list of ``TwitchPy.ChatInfo.Chat`` instances. Newest message will be stored in the front (position 0)
while the oldest message will be stored in the rear (the last position).

Because the chat history is stored in a list, you can iterate through it quite simply with a loop: ::

    @Commands.create()
    async def get_newest_message(self, ctx, viewer):
        # echoes the newest message sent by a viewer
        for chat in IRC.chat_history:
            if chat.user.name == viewer:
                await IRC.send(chat.msg)
                return

.. note:: TwitchPy will only save messages *after* command invocations (if there is one). So in the above
          example, ``IRC.chat_history[0]`` will *not* be '!get_newest_message someviewer' until after
          ``get_newest_message()`` has finished executing.

In most cases, this shouldn't use a noticeable amount of memory, but in case you have a very active chat
or streaming games that demand a lot of memory, or just don't have that much memory to begin with, you
can limit the number of messages saved to cut down on memory usage with ``TwitchPy.TwitchBot.Client``'s
kwarg, ``chatlimit`` which takes an int. For example ``TwitchPy.TwitchBot.Client(**login, chatlimit=100)``
will only save 100 messages at a time. When the limit is reached and a new message comes in, the oldest
message will be deleted to make room for the new one. If you didn't want to save any messages, just
set ``chatlimit`` to 0: ``TwitchPy.TwitchBot.Client(**login, chatlimit=0)``






Working With Twitch's API
===========================

``TwitchPy.API.Helix`` is the class that handles any calls to twitch's API endpoints. This is mainly used to get
information on certain viewers and to figure out who is following you. To get the instance of this that the bot
uses, you can access the attribute directly with ``TwitchPy.TwitchBot.Client.API`` or use a getter function like
``TwitchPy.TwitchBot.Client.get_API()``.

Here's a quick rundown of ``TwitchPy.API.Helix``'s functions.

+---------------------------------+-------------------------------------------------------------+
| function                        | description                                                 |
+=================================+=============================================================+
| ``get_user_info(user: [str])``  | returns a dict with all the information about the user(s)   |
+---------------------------------+-------------------------------------------------------------+
| ``get_my_followers()``          | get a list of all of your followers                         |
+---------------------------------+-------------------------------------------------------------+
| ``follows_me(user_id: str)``    | figure out if a user is following you                       |
+---------------------------------+-------------------------------------------------------------+
| ``get_viewers()``               | get a list of all of the people watching you                |
+---------------------------------+-------------------------------------------------------------+

This isn't everything and doesn't go quite in depth on what these functions are returning or what parameters
they're looking for. So if you're looking for more detailed explanations, take a look at the references.





Running Functions Concurrently
================================

You may find yourself wanting to run some function in the background or alongside the bot's normal functions.
Like maybe you'd like the bot to say 'Don\'t forget to SMASH that subscribe button!!!' every 10 minutes in chat.
For that you can create an async function and pass it to ``TwitchPy.TwitchBot.Client.run()`` in a list. ::

    from TwitchPy import TwitchBot
    import asyncio

    class MyBackgroundTask:
        def __init__(self, IRC):
            self.IRC = IRC

        async def smash_reminder(self):
            self.IRC.send('Don\'t forget to SMASH that subscribe button!!!')
            await asyncio.sleep(10 * 60)

    bot = TwitchBot.Client(**login_info)
    smash_class = MyBackgroundTask(bot.get_IRC())
    bot.run([smash_class.smash_reminder])

We support you sending in multiple functions to run concurrently which is why ``TwitchPy.TwitchBot.Client.run()``
expects a list.

.. note:: Any Functions you want to run concurrently CANNOT take any arguments, except for self if used
          correctly.

.. note:: Any functions you want to run concurrently MUST include ``await asyncio.sleep(x)`` where x
          is a time in seconds. This is what enables the concurrency. Without this, the bot will get
          stuck on one function and fail to work altogether.






Setting up a Logger
=====================

TwitchPy uses the ``logging`` library's logger (with some added functionality to it) to print information about the
bot's functioning to the console and/or a file. By default, TwitchPy provides you a very basic logger that only
prints to console. But of course, you can create your own loggers and customize the way they work.



Creating Loggers
--------------------

TwitchPy uses two separate loggers: one reserved for logging to the console and one reserved for logging to a file.
We simplistically just call these ``console`` and ``file``. We separate them like this so you can customize the
function of both separately, allowing one of the loggers to behave differently from the other. To create a logger,
you first need to create an instance of ``TwitchPy.Logger.Logger`` and call ``TwitchPy.Logger.Logger.create_console_logger()``
and/or ``TwitchPy.Logger.Logger.create_file_logger()`` depending on which ones you want. And don't forget to pass
the instance of ``TwitchPy.Logger.Logger`` to ``TwitchPy.TwitchBot.Client`` ::

    from TwitchPy import TwitchBot, Logger

    MyLoggers = Logger.Logger()
    MyLoggers.create_console_logger()
    MyLoggers.create_file_logger(filename='MyLog.log', filemode='w')

    bot = TwitchBot.Client(**login, logger=MyLoggers)

Notice here that ``TwitchPy.Logger.Logger.create_file_logger()`` has the kwargs ``filename`` and ``filemode``.
``filename`` takes a string which represents what file it writes to and ``filemode`` takes a string which
represents which file writing mode to use (which is basically just 'w' for write or 'a' for append).

.. note:: Both ``TwitchPy.Logger.Logger.create_console_logger()`` and ``TwitchPy.Logger.Logger.create_file_logger()``
          have more kwargs, but we'll discuss those in the coming sections.



Log Formatting
----------------

There are three different formatting options you can customize. All of which use python's % string formatting.
You can read about it here: https://docs.python.org/3/library/string.html#format-examples . But in short,
whenever you want to include a variable in your string, you follow this syntax ``%(varname)s`` where the ``s``
at the end signifies that varname is a string. While % formatting allows different data types, you'll only
need to use ``s`` for the bot.

The three formatting options available to you is the general log format, date format, and chat format.
In the following sections, we'll be talking about how to use all of these for the console logger, but that
doesn't mean that these features are unique to it - you'll be able to do all the same things with the file
logger.


General Format
^^^^^^^^^^^^^^^

This is how you want your log messages to appear when they print to your console/file. To set a logger's format,
you can use the ``TwitchPy.Logger.Logger.create_console_logger()``'s kwarg, ``fmt``, sending a % formatted string.

For a list of all the attributes you can use, you can reference:
https://docs.python.org/3/library/logging.html#logrecord-attributes

Here's an example ::

    MyLoggers.create_console_logger(fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s')

This is the default ``fmt`` value and produces logs that look kind of like::

    [INFO    ] [TwitchBot ] [18:29:22] bot is ready to run
    [INFO    ] [TwitchBot ] [18:29:22] starting bot...
    [BASIC   ] [Websocket ] [18:29:22] connecting to channel: loltyler1...
    [BASIC   ] [Websocket ] [18:29:22] successfully connected to channel: loltyler1
    [INFO    ] [Websocket ] [18:29:22] bot is now listening...

.. note:: Don't connect your bots to channels without the streamer's permission.


Date Format
^^^^^^^^^^^^^

This is how you want the date to be displayed when you use ``%(asctime)s``. We follow python's ``time.strftime()``'s
formatting so you can reference https://docs.python.org/3/library/time.html#time.strftime on all the ways you can
customize how it's formatted.

To set this, use the kwarg ``datefmt`` like so: ::

    MyLoggers.create_console_logger(datefmt='%Y/%m/%d - %H:%M:%S')

This is the default behavior of the file logger and will print time that looks like::

    2020/03/16 - 18:29:22


Chat Format
^^^^^^^^^^^^^

This is how you want chat messages to be formatted. This format is entirely TwitchPy, unlike the the others which
were all a part of the ``logging`` library. So your variables should be in the scope of ``TwitchPy.ChatInfo.Chat`` .
For a quick reference of the variables, you can look at `Interacting With IRC`_ , just make sure not to lead the
variable names with ``ctx`` . Also, this is the only format that has to be sent to ``TwitchPy.Logger.Logger``
directly instead of through ``TwitchPy.Logger.Logger.create_console_logger()`` which means that both loggers will
use this format.

To set this, use the kwarg ``chatfmt`` while intializing ``TwitchPy.Logger.Logger`` ::

    MyLoggers = TwitchPy.Logger.Logger(chatfmt='%(user.name)s: %(msg)s')

This is the default behavior and will print chat messages that look like::

    someviewer: PogChamp

Alternatively, you can set this later using ``TwitchPy.Logger.Logger.set_chatfmt()`` ::

    MyLoggers.set_chatfmt('%(user.name)s: %(msg)s')



Filters
----------

TwitchPy uses a custom filter (not to be confused with ``logging``'s filters) that checks for log types to give
you precise control over what each logger can and cannot see. For each message that TwitchPy tries to log, TwitchPy
associates the message with a log type. Here's a quick reference sheet for all of TwitchPy's log types:

+------------------------+-----------------------------------------------------------------+
| log type               | description                                                     |
+========================+=================================================================+
| 'TwitchBot-init'       | init related messages                                           |
+------------------------+-----------------------------------------------------------------+
| 'TwitchBot-basic'      | the basic function of the module                                |
+------------------------+-----------------------------------------------------------------+
| 'TwitchBot-error'      | error messages                                                  |
+------------------------+-----------------------------------------------------------------+
| 'API-init'             |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'API-basic'            |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'API-error'            |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'API-request_get'      | exactly what the bot sends via requests                         |
+------------------------+-----------------------------------------------------------------+
| 'API-request_response' | the response from the twitch API endpointin its rawest form     |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-init'       |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-basic'      |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-error'      |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-incoming'   | incoming messages from twitch chat                              |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-outgoing'   | outgoing messages to twitch chat                                |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-send'       | exactly what the bot sends via websocket                        |
+------------------------+-----------------------------------------------------------------+
| 'Websocket-recv'       | what twitch IRC sends to us                                     |
+------------------------+-----------------------------------------------------------------+
| 'Events-init'          |                                                                 |
+------------------------+-----------------------------------------------------------------+
| 'Commands-error'       |                                                                 |
+------------------------+-----------------------------------------------------------------+

You can filter out log messages by their log type by using ``TwitchPy.Logger.Logger.console_filter()`` and
``TwitchPy.Logger.Logger.file_filter()``, both of which take one argument: a list of of strings with each
string being a log type that you **do not** want to show up. For example, you may want all log types *except*
for 'API-request_get' and 'API_request_response' to show up in your console loger. ::

    from TwitchPy import Logger

    MyLoggers = Logger.Logger()
    MyLoggers.create_console_logger()
    MyLoggers.console_filter(['API-request_get', 'API-request_response'])

Each log type follows the same structure: {module}-{type name}. So 'API-request_get' comes from the ``API`` module
and the log type's name is ``request_get``. This is especially important to note because TwitchPy doesn't do
any input sanitization. If you misstype, TwitchPy won't throw any errors or let you know that what you've typed
might be wrong. This is because we wanted to let you set up your own log types for your program which you can
then use the filters on. More on this at `Implementing Loggers in Your Program`_

-------------------

A much simpler but less customizable way to control what your logger logs is with logging levels. Each message sent
to be logged has a logging level associated with it. When you create a logger, you can use the kwarg ``level`` which
takes an int and serves as a minimum value for your logger to pay attention to. ::

    from TwitchPy import Logger

    MyLoggers = Logger.Logger()
    MyLoggers.create_console_logger(level=20)

This creates a logger that will only log messages that have a level of 20 or above. The ``logging`` module has some
predefined levels which you can find at https://docs.python.org/3/library/logging.html#logrecord-attributes , but
TwitchPy also has some predefined levels. Here's a quick reference for all the levels.

+------------------------+-------+
| level                  | value |
+========================+=======+
| logging.CRITICAL       | 50    |
+------------------------+-------+
| logging.ERROR          | 40    |
+------------------------+-------+
| logging.WARNING        | 30    |
+------------------------+-------+
| TwitchPy.Logger.MSG    | 21    |
+------------------------+-------+
| logging.INFO           | 20    |
+------------------------+-------+
| TwitchPy.Logger.BASIC  | 19    |
+------------------------+-------+
| TwitchPy.Logger.INIT   | 11    |
+------------------------+-------+
| logging.DEBUG          | 10    |
+------------------------+-------+
| TwitchPy.Logger.LOWLVL | 9     |
+------------------------+-------+
| logging.NOTSET         | 0     |
+------------------------+-------+



Presets
-----------

If you're feeling lazy and don't really want to spend the time customizing a logger, you can use one of our presets.
Just use the kwarg ``preset`` when intializing ``TwitchPy.Logger.Logger`` . We have the following presets:

``'default'`` - This is what TwitchPy will default to, so you don't even need to specify this as your preset. But this
only uses a console logger to print ``TwitchPy.Logger.BASIC`` levels and above with
``fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s'`` and ``datefmt='%H:%M:%S'``

``'recommended'`` - This is our own personal preference that creates a console logger that prints ``TwitchPy.Logger.INIT``
levels and above with ``fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s'`` and ``datefmt='%H:%M:%S'`` .
This also creates a file logger that appends ``TwitchPy.Logger.BASIC`` and above messages to a file 'TwitchBot.log' with
``fmt='[%(levelname)-8s] [%(module)-10s] [%(asctime)s] %(message)s'`` and ``datefmt='%Y/%m/%d - %H:%M:%S'``

As an example, if you wanted to create a logger using the preset 'recommended', you would do::

    from TwitchPy import TwitchBot, Logger

    MyLoggers = Logger.Logger(preset='recommended')
    bot = TwitchBot.Client(logger=MyLoggers)



Set Functions
---------------

While TwitchPy provides functions to create your own loggers, you may find that it lacks some of the depth and
features that the ``logging`` library provides. So we have ``TwitchPy.Logger.Logger.set_console_logger()``
and ``TwitchPy.Logger.Logger.set_file_logger()`` that both take one argument, a logger created by the
``logging`` library. In this way you can customize your logger(s) just like you would for other programs.

As long as we're talking about the limitations of TwitchPy's loggers, you may find yourself wanting some
functionality that would need more than 2 loggers. If you wanted to work within the confines of TwitchPy's
logger, you might be able to find some crafty solutions here https://docs.python.org/3/howto/logging-cookbook.html .
If you're unable to find a solution, you can always catch the ``on_log`` event (see `Catching Events`_).

.. note:: The names ``console`` and ``file`` loggers are purely cosmetic. We make no checks to ensure that
          they're purely console / file handlers. So you could create a logger that writes to a file and send it to
          ``TwitchPy.Logger.Logger.set_console_logger()`` and that would work without any problems.



Implementing Loggers in Your Program
---------------------------------------

So far we've taught you how to set up loggers and change their behavior which is good if the only things you
wanted to log are the parts coded into TwitchPy, but chances are you want to be able to send your own log
messages. To do that, you should use ``TwitchPy.Logger.Logger.log()`` which takes 3 required arguments and
1 optional argument.

+----------+----------------+--------------------------------------------+
| argument | data type      | description                                |
+==========+================+============================================+
| level    | int            | the logging level (see `Filters`_)         |
+----------+----------------+--------------------------------------------+
| type\_   | str            | the type of log message (see `Filters`_)   |
+----------+----------------+--------------------------------------------+
| msg      | str            | the message you want logged                |
+----------+----------------+--------------------------------------------+
| exc      | sys.exc_info() | optional: if there was an exception thrown |
+----------+----------------+--------------------------------------------+

Let's take a look at a quick example: ::

    from TwitchPy import TwitchBot, Commands, Logger

    class MyCommands(Commands.Cog)
        def __init__(self, logger):
            super().__init__(prefix='!')
            self.logger = logger

        @Commands.create()
        async def ping(self, ctx):
            self.logger.log(20, 'connection_test', 'ping command executed.')

    MyLoggers = Logger.Logger()
    MyLoggers.create_console_logger(level=0)

    mycog = MyCommands(MyLoggers)

    bot = TwitchBot.Client(**login, logger=MyLoggers)
    bot.add_cogs(mycog)
    bot.run()

With this program, the message 'ping command executed.' will be logged with level 20 and type 'connection_test'
whenever a viewer says '!ping' in twitch chat. Notice here that log type 'connection_test' is a custom log type
and not something TwitchPy sets up. By creating your own system of log types, you can use TwitchPy's filters to
filter out your own logs if you'd like. Just follow the format: ``{module}-{type name}``

In this example, if we saved the file as 'mybot.py' and we didn't want any messages with type 'connection_test',
we would add the line ::

    MyLoggers.console_filter(['mybot-connection_test'])

right after creating the console logger and then nothing would show up in your console when a viewer says
'!ping' in twitch chat.






Catching Events
================

TwitchPy has certain events that it'll 'throw' during its runtime that you can 'catch' if you'd like to run a function
when something in specific happens. For example, you might want to count how many times commands were used. So instead
of having every single command function have the line ``use_count += 1``, we can catch the ``on_cmd`` event. To do this
we would need to create a class that inherits from ``TwitchPy.Events.Handler``, call ``super().__init__()``, overwrite
the ``on_cmd()`` function, and pass it to ``TwitchPy.TwitchBot.Client`` using the kwarg ``eventhandler`` ::

    from TwitchPy import TwitchBot, Events

    class MyEventHandler(Events.Handler):
        def __init__(self):
            super().__init__()
            self.use_count = 0

        async def on_cmd(self, ctx):
            self.use_count += 1

    bot = TwitchBot.Client(**login, eventhandler=MyEventHandler())

So whenever TwitchPy executes a command successfully, it will call ``MyEventHandler.on_cmd()``. For the different
events you can catch and what arguments they take, you can reference this quick chart or take a look at the references
for more detailed explanations.

+---------------------+-------------------------------+--------+----------------------------------------------------------+
| event               | arguments                     | async? | when it's called                                         |
+=====================+===============================+========+==========================================================+
| on_ready            | none                          | no     | after the bot has finished intializing                   |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_run              | none                          | no     | when ``TwitchPy.TwitchBot.Client.run()`` is called       |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_connect          | none                          | yes    | when the bot connects to a twitch channel                |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_log              | str, ``logging.LogRecord``    | yes    | whenever the bot tries to log something                  |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_msg              | ``TwitchPy.ChatInfo.Chat``    | yes    | whenever a message is sent via IRC                       |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_cmd              | ``TwitchPy.ChatInfo.Chat``    | yes    | whenever a command executes successfully                 |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_bad_cmd          | ``TwitchPy.ChatInfo.Chat``    | yes    | whenever the bot failes to find a command to execute     |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_no_cmd           | ``TwitchPy.ChatInfo.Chat``    | yes    | whenever a message is sent that is not meant for the bot |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_death            | none                          | yes    | when the bot dies                                        |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_expected_death   | none                          | yes    | when we mean kill the bot                                |
+---------------------+-------------------------------+--------+----------------------------------------------------------+
| on_unexpected_death | exception, ``sys.exc_info()`` | yes    | when the bot dies for some unknown reason                |
+---------------------+-------------------------------+--------+----------------------------------------------------------+






Need More Examples?
=====================

If you're looking to see more examples, you can check out the examples section of the github page:
https://github.com/rexosorous/TwitchPy . Each of the examples requires you to have a file 'login.json' that's
structured like so: ::

    login = {   "token": "your auth token",
                "user": "your bot name",
                "client_id": "the bot's client ID",
                "channel": "the channel to connect to"
    }

Assuming your login credentials are correct, they should all work. So you can have it connect to your own channel and
tinker with the code to help you better understand how everything works.






Read the References!
=====================

Hopefully these guides are all you need to understand and use the bot. But that doesn't mean we went over every function.
I'm sure you're tired of hearing us say it, but if you're looking for more information on something, then take a peak at the
references for a break down of the modules and all their classes, attributes, and functions.