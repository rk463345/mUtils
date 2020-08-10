""" renaming of movies """

def folderNameCleaner(name):
    """cleans up the name for the folder that holds the file"""
    resolutions = ['480p', '720p', '1080p', '4k']
    afterResolution = False
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
    newName = name[0]
    for count in range(1, len(name)):
        newName = newName + ' ' + name[count]

    newName = newName + ' ' + year
    return newName


def fileNameCleaner(name):
    """cleans up the name for the file and preserves the file type"""
    resolutions = ['480p', '720p', '1080p', '4k']
    afterResolution = False
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
    newName = name[0]
    for count in range(1, len(name)):
        newName = newName + ' ' + name[count]
        
    newName = newName + ' ' + year + extension
    return newName


def renamer(src, dest):
    """renames the folder and file)"""
    
