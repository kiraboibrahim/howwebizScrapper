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
        self.query = ""
        try:
            self.dbHandle = connect(host=host, user=user, password=password, database=database, autocommit=True)
            self.dbCursor = self.dbHandle.cursor(dictionary = True, buffered = True)
        except Error as e:
            print "[{}] {}".format(e.errno, e.msg)
            exit(0)
    def writeArtist(self, artistObj):
        self.query = 'INSERT INTO artists(artist_name, artist_thumbnail, artist_bio) VALUES("{}", "{}", "{}");'.format(artistObj.artistName, artistObj.artistAvatar, artistObj.artistBio.replace('"', "'"))
        if self.__run():
            # return the id of the last inserted artist
            return self.dbCursor.lastrowid
        else:
            raise ValueError("Failed to run query: {}".format(self.query))
    def writeTrack(self, trackObj):
        self.query = 'INSERT INTO tracks(artist_id, track_name, track_thumbnail, track_size) VALUES({}, "{}", "{}", "{}");'.format(trackObj.artist_id, trackObj.trackName, trackObj.trackAvatar, trackObj.size)
        self.__run()
    def __run(self):
        try:
            ret = self.dbCursor.execute(self.query)
        except Error as e:
            #output error
            print "[{}] Error: {}, {}".format(e.errno, e.msg, self.query)
            #exit program
            exit(0)
        else:
            if(ret is None):
                return True
        return False
    def artistExists(self, artistObj):
        self.query = "SELECT * FROM artists WHERE artist_name = '{}';".format(artistObj.artistName)
        if self.__run():
            # Check if the query returned any results 
            if self.dbCursor.rowcount:
                #get the artist_id
                artistID = self.dbCursor.fetchone()['artist_id']
            else:
                artistID = self.writeArtist(artistObj)
            return artistID
        else:
            raise ValueError("Failed to run query: {}".format(self.query))
    def trackExists(self, trackObj):
        self.query = "SELECT * FROM tracks WHERE track_name='{}';".format(trackObj.trackName)
        self.dbCursor.execute(self.query)
        if self.dbCursor.rowcount:
            return True
        return False
        
        