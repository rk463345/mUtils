"""removes unwanted files by extension"""


import os


def remover(src, extension):
    """Removes files by file extension
    :param src: The root director of folders
    :type src: str
    :param extension: The file extension that will be removed
    :type extension: str
    :returns: True if completed False if failed
    :rtype: bool
    """
    
    try:
        default = os.getcwd()
        os.chdir(src)
        dirs = os.listdir(src)
        for path in dirs:
            currentDir = os.listdir(os.path.join(src, path))
            for item in currentDir:
                if item.endswith(extension):
                    os.remove(os.path.join(src, path, item))
        os.chdir(default)
        return True

    except:
        return False

