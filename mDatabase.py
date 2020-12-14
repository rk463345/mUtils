import sqlite3

class DB:
    __init__(self):
        self.connection = sqlite3.connect('media.db')
