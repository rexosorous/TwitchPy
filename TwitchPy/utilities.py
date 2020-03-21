"""Utility functions for use in multiple modules.

Includes functions with very generic and/or basic use that multiple modules want/need to use.
"""



def makeiter(var):
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



def check_param(var, datatype):
    """Checks if a variable is the correct data type.

    If it's not correct, return the error message to raise.

    Parameters
    -----------
    var
        the variable to check.

    datatype
        the data type to compare against.


    Returns
    ----------
    str
        the error message to raise.
    """
    if isinstance(var, datatype):
        return ''
    return f"{[name for name, value in locals().items() if var == value][0]} expects '{datatype.__name__}' not '{type(var)}'"