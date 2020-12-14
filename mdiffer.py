#!/usr/bin/env python3

import subprocess
import os
import time


def setup():
    """
    If the output and log folders do not exist they are created
    """
    if (os.path.exists("./output") == False) or (
        os.path.exists("./log") == False
    ):  # checks to see if directories for ouput exist
        print("creating dirs")
        with open("initialization.txt", "w") as start:
            try:
                output = subprocess.Popen(
                    ["mkdir", "output"], stdout=start, universal_newlines=True
                )  # creates the output directory
                log = subprocess.Popen(
                    ["mkdir", "log"], stdout=start, universal_newlines=True
                )  # creates the log directory
            except:
                print("Something seems to have gone wrong. Check initialization.txt")
    else:
        print("setup complete")


def getFiles(dir1, dir2, CWD=os.getcwd()):
    """
    Gathers the name of the folders located in dir1 and dir2.
    Creates the files that need to be cleaned.
    dir1 is the the second movie directory.
    dir2 is the primary movie directory.
    """
    SUBDIR = CWD + "/output/"  # changes direcotory to the output folder
    with open(f"{SUBDIR}toMove.txt", "w") as d:
        process0 = subprocess.Popen(
            ["ls", dir1], stdout=d, universal_newlines=True
        )  # using subprocess to create the 'dirty' output of the second directory
        try:
            outs, errs = process0.communicate(timeout=15)
        except TimoutExpired as te:
            print(te, "Something went wrong")
            process0.kill()
            outs, errs = process0.communicate()

    with open(f"{SUBDIR}movies.txt", "w") as m:
        process1 = subprocess.Popen(
            ["ls", dir2], stdout=m, universal_newlines=True
        )  # using subprocess to create the 'dirty' output of the primary directory
        try:
            outs, errs = process1.communicate(timeout=15)
        except TimeoutExpired as te:
            print(te, "Something went wrong")
            process1.kill()
            outs, errs = process1.communicate()


def cleanFiles(direct, CWD=os.getcwd()):
    """
    removes the year and trailing white space, if there is a year
    direct holds the file name for the file of the contents of the directory
    @return list of the cleaned data
    """
    SUBDIR = CWD + "output/"  # change directory to ouput folder
    contents = os.listdir(SUBDIR)
    LOGDIR = CWD + "log/"  # change directory for logging
    log = open(f"{LOGDIR}log.txt", "w")  # opens log file
    for i in range(0, len(contents)):
        contents[i] = contents[i].strip("\n")  # remove trailing \n
        if (
            "(" in contents[i] or ")" in contents[i]
        ):  # if '(' or ')'exists in the file name to signify if there is a year
            old = contents[i]  # holds the name of the movie for logging purposes
            contents[i] = contents[i][
                :-7
            ]  # truncates the string to remove year and trailing whitespace
            log.write(
                f"Removing date from {old} -> {contents[i]})\n"
            )  # writes to the log file
    log.close()
    return contents


def writeCleanFile(file1, items, CWD=os.getcwd()):
    """
    writes a cleaned list to the file
    file1 is the name of the output file
    items is the list of the cleaned names
    """
    OUTPUTDIR = CWD + "/output/"  # change directory to output
    with open(f"{OUTPUTDIR}{file1}", "w") as cleanFile:
        for item in items:  # loop that writes all of the items to a clean file
            cleanFile.write(f"{OUTPUTDIR}{item}\n")


def differ(file1, file2, CWD=os.getcwd()):
    """
    finds the duplicate file names between the two files
    file1 is the movies that are in the second directory
    file2 is the movies that are in the primary directory
    @returns list containing duplicates
    """
    OUTPUTDIR = CWD + "/output/"  # change directory to output
    f1 = open(f"{OUTPUTDIR}{file1}", "r")
    contentsF1 = os.listdir(f1)
    f2 = open(f"{OUTPUTDIR}{file2}", "r")
    contentsF2 = os.listdir(f2)
    dupes = []  # initialize the dupes list
    for (
        item
    ) in (
        contentsF1
    ):  # bad nested loops for comparing the contents of the two directories
        for thing in contentsF2:
            if item == thing:
                dupes.append(item)  # appending duplicate file names to the dupes list
    return dupes


def getDir(directory):
    """
    Gets the directory names to be compared
    @returns string of path
    """
    path = input(f"Input path for {directory}:\t")
    return path


def main():
    """main"""
    dirs = [
        "primary movie directory",
        "secondary movie directory",
    ]  # movie directory prompts
    primaryMoviesDirectory = getDir(dirs[0])  # gets the primary directory
    secondaryMoviesDirectory = getDir(dirs[1])  # gets the secondary directory
    uncleanSecondaryMoviesFile = "toMove.txt"
    uncleanPrimaryMoviesFile = "movies.txt"
    cleanPrimaryMoviesFile = "cleanMovies.txt"
    cleanSecondaryMoviesFile = "cleanToMove.txt"
    duplicateMoviesFile = "dupes.txt"
    print("getting files")
    getFiles(
        secondaryMoviesDirectory, primaryMoviesDirectory
    )  # getting the files for comparison
    time.sleep(
        5
    )  # used to allow the getFiles() subprocesses to finish before continuing
    print("cleaning secondary movie file")
    cleanSecondaryFile = cleanFiles(
        uncleanSecondaryMoviesFile
    )  # cleans the secondary directory
    writeCleanFile(
        cleanSecondaryMoviesFile, cleanSecondaryFile
    )  # writes the secondary clean dir file
    print("cleaning primary movie file")
    cleanPrimaryFile = cleanFiles(
        uncleanPrimaryMoviesFile
    )  # cleans the primary directory
    writeCleanFile(
        cleanPrimaryMoviesFile, cleanPrimaryFile
    )  # writes the primary clean dir file
    print("finding similar files")
    final = duplicateMovies = differ(
        cleanSecondaryMoviesFile, cleanPrimaryMoviesFile
    )  # finds the duplicates
    print("writing dupes file\n\n")
    writeCleanFile(
        duplicateMoviesFile, duplicateMovies
    )  # writes the duplicates to a file
    print(
        f"The Dupes!\n Total: {len(duplicateMovies)]}\n"))
    )  # prints the total amount of duplicates
    for item in final:
        print(f"{item.strip(\"\n)}")  # prints the duplicate file names


if __name__ == "__main__":  # duh
    main()
