def makeiter(var) -> iterable:
    """Converts a variable into a list of it's not already an iterable (not including strings.
    If it's already an iterable, don't do anything to it.

    Parameters
    ------------
    var
        the variable to check.

    Returns
    ------------
    var
        an iterable version of the parameter (if it's not already one)
    """
    if not hasattr(var, '__iter__') or isinstance(var, str):
        return [var]
    return var