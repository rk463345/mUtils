#!/usr/bin/env python3

import subprocess
import os
import time


def setup():
    if (os.path.exists('./output')==False) or (os.path.exists('./log')==False):
        print('creating dirs')
        with open('initialization.txt', 'w') as start:
            try:
                output = subprocess.Popen(['mkdir', 'output'], stdout=start, universal_newlines=True)
                log = subprocess.Popen(['mkdir', 'log'], stdout=start, universal_newlines=True)
            except:
                print('Something seems to have gone wrong. Check initialization.txt')
    else:
        print('setup complete')


def getFiles(dir1, dir2):
    default = os.getcwd()
    os.chdir('./output')
    with open('toMove.txt', 'w') as d:
        process0 = subprocess.Popen(['ls', dir1], 
                                    stdout=d, 
                                    universal_newlines=True)

    with open('movies.txt', 'w') as m:
        process1 = subprocess.Popen(['ls', dir2],
                                    stdout=m,
                                    universal_newlines=True)
    os.chdir(default)


def cleanFiles(direct):
    default = os.getcwd()
    os.chdir('./output')
    f = open(direct, 'r')
    contents = f.readlines()
    f.close()
    os.chdir('../log')
    log = open('log.txt', 'w')
    for i in range(0, len(contents)):
        contents[i] = contents[i].strip('\n')
        if '(' in contents[i] or ')' in contents[i]:
            temp = contents[i]
            contents[i] = contents[i][:-7]
            log.write('Removing date from {} -> {}\n'.format(temp, contents[i]))
    log.close()
    os.chdir(default)
    return contents


def writeCleanFile(file1, items):
    default = os.getcwd()
    os.chdir('./output')
    with open(file1, 'w') as cleanFile:
        for item in items:
            cleanFile.write('{}\n'.format(item))
    os.chdir(default)


def differ(file1, file2):
    default = os.getcwd()
    os.chdir('./output')
    f1 = open(file1, 'r')
    contentsF1 = f1.readlines()
    f1.close()
    f2 = open(file2, 'r')
    contentsF2 = f2.readlines()
    f2.close()
    dupes = []
    for item in contentsF1:
        for thing in contentsF2:
            if item == thing:
                dupes.append(item)
    os.chdir(default)
    return dupes


def getDir(d):
    x = input('Input path for {}:\t'.format(d))
    return x


def main():
    dirs = ['movie dir', 'second movie dir']
    d = getDir(dirs[1])
    m = getDir(dirs[0])
    x = 'toMove.txt'
    y = 'movies.txt'
    z = 'cleanMovies.txt'
    w = 'cleanToMove.txt'
    dupe = 'dupes.txt'
    print('getting files')
    getFiles(d, m)
    time.sleep(5)
    print('cleaning toMove file')
    cleanFile1 = cleanFiles(x)
    writeCleanFile(w, cleanFile1)
    print('cleaning dataset file')
    cleanFile2 = cleanFiles(y)
    writeCleanFile(z, cleanFile2)
    print('finding similar files')
    final = differ(w, z)
    print('writing dupes file\n\n')
    writeCleanFile(dupe, final)
    print('The Dupes!\n Total: {}\n'.format(len(final)))
    for item in final:
        print('{}'.format(item.strip('\n')))

if __name__=='__main__':
    main()
