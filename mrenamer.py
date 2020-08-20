""" renaming of movies """

import os

def folderNameCleaner(name):
    """cleans up the name for the folder that holds the file
    :param name: The name of the folder to be rename
    :type name: str
    :returns: A str that will be the new name of the folder
    :rtype: str
    """
    resolutions = ['proper', '480p', '720p', '1080p', '4k']
    afterResolution = False
    if '.' not in name:
        return name
    name = name.split(".")
    indexesToRemove = []

    for item in name:
        if afterResolution == True:
            indexesToRemove.append(item)

        if item in resolutions:
            afterResolution = True
            indexesToRemove.append(item)

    for item in indexesToRemove:
        name.remove(item)

    year = '(' + name.pop(-1) + ')'
    newName = ''
    for count in range(0, len(name)):
        newName = newName + name[count] + ' '

    newName = newName + year
    return newName


def fileNameCleaner(name):
    """cleans up the name for the file and preserves the file extension
    :param name: The name of the file that needs to be renamed
    :type name: str
    :returns: A str that will be the new name of the file
    :rtype: str
    """
    resolutions = ['proper', '480p', '720p', '1080p', '4k']
    afterResolution = False
    if '.' not in name:
        return name
    name = name.split(".")
    extension = '.' + name.pop(-1)
    indexesToRemove = []

    for item in name:              
        if afterResolution == True:        
            indexesToRemove.append(item)            

        if item in resolutions:
            afterResolution = True
            indexesToRemove.append(item)
    
    for item in indexesToRemove:
        name.remove(item)

    year = '(' + name.pop(-1) + ')'         
    newName = ''
    for count in range(0, len(name)):
        newName = newName + name[count] + ' '
        
    newName = newName + year + extension
    return newName


def renamer():
    """renames the folder and file"""
    source = input("Source Directory: ")
    items = os.listdir(source)
    for path in items:
        subItems = os.listdir(os.path.join(source, path))
        for item in subItems:
            if item.lower() != 'subs' and item.lower() != 'sample':
                newFileName = fileNameCleaner(item)
                print('renaming {} -> {}'.format(item, newFileName))
                os.rename(os.path.join(source, path, item), 
                          os.path.join(source, path, newFileName))
        newFolderName = folderNameCleaner(path)
        print('renaming {} -> {}'.format(path, newFolderName))
        os.rename(os.path.join(source, path), 
                  os.path.join(source, newFolderName))

