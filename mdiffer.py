#!/usr/bin/env python3

import subprocess
import os
import time


def setup():
    """
    If the output and log folders do not exist they are created
    """
    if (os.path.exists('./output')==False) or (os.path.exists('./log')==False):     # checks to see if directories for ouput exist
        print('creating dirs')
        with open('initialization.txt', 'w') as start:
            try:
                output = subprocess.Popen(['mkdir', 'output'], stdout=start, universal_newlines=True)   # creates the output directory
                log = subprocess.Popen(['mkdir', 'log'], stdout=start, universal_newlines=True)         # creates the log directory
            except:
                print('Something seems to have gone wrong. Check initialization.txt')
    else:
        print('setup complete')


def getFiles(dir1, dir2):
    """
    Gathers the name of the folders located in dir1 and dir2.
    Creates the files that need to be cleaned.
    dir1 is the the second movie directory.
    dir2 is the primary movie directory.
    """
    default = os.getcwd()   # sets the default directory as the location of the mdiffer.py
    os.chdir('./output')    # changes direcotory to the output folder
    with open('toMove.txt', 'w') as d:
        process0 = subprocess.Popen(['ls', dir1], 
                                    stdout=d, 
                                    universal_newlines=True) # using subprocess to create the 'dirty' output of the second directory
        try:
            outs, errs = process0.communicate(timeout=15)
        except TimoutExpired:
            print("something went wrong")
            process0.kill()
            outs, errs = process0.communicate()

    with open('movies.txt', 'w') as m:
        process1 = subprocess.Popen(['ls', dir2],
                                    stdout=m,
                                    universal_newlines=True)    # using subprocess to create the 'dirty' output of the primary directory
        try:
            outs, errs = process1.commuicate(timeout=15)
        except TimeoutExpired:
            print("something went wrong")
            process1.kill()
            outs, errs = process1.communicate()
    os.chdir(default)   # change directory back to original 


def cleanFiles(direct):
    """
    removes the year and trailing white space, if there is a year
    direct holds the file name for the file of the contents of the directory
    @return list of the cleaned data 
    """
    default = os.getcwd()       # set default directory as the location of mdiffer.py
    os.chdir('./output')        # change directory to ouput folder
    f = open(direct, 'r')       # opens a 'dirty' directory for read only
    contents = f.readlines()
    f.close()
    os.chdir('../log')          # change directory for logging
    log = open('log.txt', 'w')  # opens log file
    for i in range(0, len(contents)):               
        contents[i] = contents[i].strip('\n')       # remove trailing \n
        if '(' in contents[i] or ')' in contents[i]:    # if '(' or ')'exists in the file name to signify if there is a year
            temp = contents[i]                          # holds the name of the movie for logging purposes
            contents[i] = contents[i][:-7]              # truncates the string to remove year and trailing whitespace
            log.write('Removing date from {} -> {}\n'.format(temp, contents[i]))       # writes to the log file 
    log.close()
    os.chdir(default)       # changes back to dir of mdiffer.py
    return contents


def writeCleanFile(file1, items):
    """
    writes a cleaned list to the file
    file1 is the name of the output file
    items is the list of the cleaned names
    """
    default = os.getcwd()   # set default directory as the location of mdiffer.py
    os.chdir('./output')    # change directory to output
    with open(file1, 'w') as cleanFile:
        for item in items:  # loop that writes all of the items to a clean file
            cleanFile.write('{}\n'.format(item))
    os.chdir(default)       # change directory to default directory


def differ(file1, file2):
    """
    finds the duplicate file names between the two files
    file1 is the movies that are in the second directory
    file2 is the movies that are in the primary directory
    @returns list containing duplicates
    """
    default = os.getcwd()   # set default directory as the location of mdiffer
    os.chdir('./output')    # change directory to output folder
    f1 = open(file1, 'r')
    contentsF1 = f1.readlines() # get the contents of second directory
    f1.close()
    f2 = open(file2, 'r')
    contentsF2 = f2.readlines() # get the contents of the primary directory
    f2.close()
    dupes = [] # initialize the dupes list
    for item in contentsF1:     # bad nested loops for comparing the contents of the two directories
        for thing in contentsF2:
            if item == thing:
                dupes.append(item)  # appending duplicate file names to the dupes list
    os.chdir(default)   # change back to default directory
    return dupes


def getDir(directory):
    """
    Gets the directory names to be compared
    @returns string of path
    """
    path = input('Input path for {}:\t'.format(directory))
    return path


def main():
    """main"""
    dirs = ['primary movie directory', 'secondary movie directory'] # movie directory prompts
    primaryMoviesDirectory = getDir(dirs[0]) # gets the primary directory
    secondaryMoviesDirectory = getDir(dirs[1]) # gets the secondary directory
    uncleanSecondaryMoviesFile = 'toMove.txt'
    uncleanPrimaryMoviesFile = 'movies.txt'
    cleanPrimaryMoviesFile = 'cleanMovies.txt'
    cleanSecondaryMoviesFile = 'cleanToMove.txt'
    duplicateMoviesFile = 'dupes.txt'
    print('getting files')
    getFiles(secondaryMoviesDirectory, primaryMoviesDirectory)  # getting the files for comparison
    time.sleep(5)   # used to allow the getFiles() subprocesses to finish before continuing
    print('cleaning secondary movie file')
    cleanSecondaryFile = cleanFiles(uncleanSecondaryMoviesFile)  # cleans the secondary directory
    writeCleanFile(cleanSecondaryMoviesFile, cleanSecondaryFile)   # writes the secondary clean dir file
    print('cleaning primary movie file')
    cleanPrimaryFile = cleanFiles(uncleanPrimaryMoviesFile)      # cleans the primary directory
    writeCleanFile(cleanPrimaryMoviesFile, cleanPrimaryFile)   # writes the primary clean dir file
    print('finding similar files')
    duplicateMovies = differ(cleanSecondaryMoviesFile, cleanPrimaryMoviesFile)            # finds the duplicates
    print('writing dupes file\n\n')
    writeCleanFile(duplicateMoviesFile, DuplicateMovies)     # writes the duplicates to a file
    print('The Dupes!\n Total: {}\n'.format(len(duplicateMovies)))    # prints the total amount of duplicates
    for item in final:
        print('{}'.format(item.strip('\n')))    # prints the duplicate file names

if __name__=='__main__':    # duh
    main()
