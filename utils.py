import os


def abs_create_path(path: str) -> str:
    """
    Makes sure that the given path is absolute and does exist.
    
    :param path: The path
    :type path: str
    
    :return: Absolute path
    :rtype: str
    
    :raises:
        FileNotFoundError: If the path couldn`t be found
    """
    absolute_path = path if os.path.isabs(path) else os.path.abspath(path)
    
    if not os.path.exists(absolute_path):
        raise FileNotFoundError(f"Path \"{absolute_path}\" couldn`t be found!")
    
    return path


def abs_path(*args) -> str:
    """
    Joins args to paths and makes it absolute.
    
    :param args: *args
    :type args: Any
    
    :return: Absolute path
    :rtype: str
    """
    return os.path.abspath(os.path.join(*args))
