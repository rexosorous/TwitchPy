class ExpectedExit(Exception):
    '''
    raised when the bot wants to shutdown gracefully
    '''
    pass



class InvalidClientID(Exception):
    '''
    raised when an API object is created with invalid credentials
    '''
    pass



class InvalidChannel(Exception):
    '''
    raised when an API object is created with a channel/user that does not exist
    '''
    pass



class BadAuthFormat(Exception):
    '''
    raised when an IRC object connects to chat and the oauth token
    doesn't start with 'oauth:'
    '''
    pass



class InvalidAuth(Exception):
    '''
    raised when an IRC object connects to chat and twitch
    does not accept the oauth token
    '''
    pass



class InvalidLogger(Exception):
    '''
    raised when the user tries to set a logger with an object
    not created from the logging module
    '''
    pass