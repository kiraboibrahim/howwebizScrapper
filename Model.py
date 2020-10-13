#!/usr/bin/python
from mysql.connector import errorcode
from mysql.connector import connect
from mysql.connector import Error
import settings

class HowweModel:
    """
        This package will write data scrapped to the database

        Attributes:
            dbHandle (Object) The database connection Object
            dbCursor (Object) The cursor for executing queries
    """
    
    def __init__(self, host = settings.DB_HOST, user= settings.DB_USER, password= settings.DB_PWD, database= settings.DB_NAME):
        self.query = ""
        """
            The initialization function, Creates a connection Object and creates a cursor Object
            
            Parameters:
                host (str) The database server host
                user (str) The database user
                password (str) User's password
                database (str) The database name to use after connection

            Returns:
                void

            """
        
        try:
            self.dbHandle = connect(host=host, user=user, password=password, database=database)
            self.dbCursor = self.dbHandle.cursor(dictionary = True)
        except Error as e:
            print "[{}] {}".format(e.errno, e.msg)
            exit(0)
    def writeArtist(self, artistObj):
        self.query = "INSERT INTO artists(artist_name, artistAvatar, artistBio, socialMediaIcons) VALUES({}, {}, {}, {});".format(artistObj.artistNme, artistObj.artistAvatar, artistObj.artistBio, artistObj.socialMediaIcons)
        state = self.__run()
        return state
    def writeTrack(self, trackObj):
        self.query = "INSERT INTO tracks(artist_id, track_name, track_thumbnail, size) VALUES({}, {}, {}, {.1d});".format(trackObj.artistID, trackObj.trackName, trackObj.trackThumbnail, trackObj.size)
        self.__run()
    def __run(self):
        try:
            ret = self.dbCursor.execute(self.query)
        except Error as e:
            print "[{}] Error: {}".format(e.errno, e.msg)
            exit(0)
        else:
            if(ret == None):
                #Query was succesfully executed
                self.dbCursor.commit()
                return True
        return False
    def artistExists(self, artistName):
        self.query = "SELECT * FROM artist WHERE artist_name = {};".format(artistName)
        self.dbCursor.execute(self.query)
        # Check if the query returned any results 
        if self.dbCursor.rowcount:
            # Capture the artistID
            artistID = self.dbCursor.fetchone()['artistID']
            return artistID
        return False
    def trackExists(self, trackName):
        self.query = "SELECT * FROM tracks WHERE track_name = {};".format(trackName)
        self.dbCursor.execute(self.query)
        if self.dbCursor.rowcount:
            return True
        return False
        
        