# encoding= utf-8
# HowweScrapper package
# Version 0.1.0
# Author Kirabo Ibrahim
# copyright 2020 Kirabo Developer

import requests, os, pickle
from bs4 import BeautifulSoup as bs
from Model import HowweModel
from argparse import ArgumentParser
# For saving songs, and writing them to the database
from settings import DEFAULT_DIR, DB_NAME

#Artist data type
class Artist:
    """All artists will have these attributes
    """
    def __init__(self, artistName, artistBio, artistAvatar, socialMediaIcons):
        self.artistName = artistName.replace(" ", "").lower()
        self.artistBio = artistBio
        self.artistAvatar = artistAvatar
        self.artist_id = None
        self.socialMediaIcons = socialMediaIcons
#Track Datatype
class Track:
    """All songs will have these properties, so this is the data type for the songs
    """
    def __init__(self, trackName, trackThumbnail, URL = ''):
        self.trackName = trackName
        self.trackAvatar = trackThumbnail
        self.size = ""
        self.data = None
        self.artist_id = None
        self.URL = URL
        self.downloadLink = None
        
# Queue datatype
class Queue:
    """Queue data type to store the songs to be downloaded
    """
    def __init__(self):
        self.items = []
    def enqueue(self, item):
        self.items.append(item)
    def dequeue(self):
        return self.items.pop(0)
    def is_empty(self):
        return self.items == []
    def length(self):
        return len(self.items)

class Scrapper:
    """Scrap all audio songs for an artiste from howwebiz website

    Returns:
        object: Scrapper Object
    """
    VERSION = "0.1.0"
    AUTHOR = "KIRABO IBRAHIM"
    DATE_PUBLISHED = "13/10/2020"
    GITHUB_LINK = "https:/github.io/kiraboibrahim/howwebizScrapper"
    COPYRIGHT = "ALL RIGHTS RESERVED 2020 KIRABO DEVELOPER"
    def __init__(self, artistName):
        """[summary]

        Args:
            artistName (string): The artist whose songs to download. NOTE: The name should be exact like the one used on howwebiz website
        """
        #Will talk to database
        self.model = HowweModel()
        self.howwebizUrl = "https://www.howwebiz.ug"
        #Other attributes to be filled in later, initialized with empty strings for the start
        self.artistObj = self.getArtistDetails(Artist(artistName, "", "", ""))
        #Prepare the artiste's directory
        self.createArtistDirectory()
        #This is link that goes to the page that contains the songs of the singer
        self.musicUrl = "{}/{}/music".format(self.howwebizUrl, self.artistObj.artistName)
        self.fileType = "mp3" # Default filet ype for howwebiz website
        self.queue = Queue() # Will hold the all track Objects
        #Check if the storage location exists
        if not os.path.exists(DEFAULT_DIR):
            self.__printError("File path: {} doesnot exist, you can change your settings to point to another directory or Create this file path.".format(DEFAULT_DIR))
            exit(0)
    def getArtistDetails(self, artistObj):
        print "[+] Checking artiste {}..".format(artistObj.artistName)
        page = bs(self.download(pageUrl=self.howwebizUrl+"/{}/biography".format(artistObj.artistName)), "html.parser")
        bio = page.select("div.biography")[0].getText().encode("utf-8")
        artistObj.artistBio = bio
        #The musician's avatar
        artistObj.artistAvatar = self.howwebizUrl +"/"+str(page.select("img.avatar")[0].get("src"))
        #Should be done last coz i shall need the bio if artist is not in DB 
        artist_id = self.model.artistExists(artistObj)
        #assign the artist id property to the artist Object
        artistObj.artist_id = artist_id    
        return artistObj 
    def createArtistDirectory(self):
        #Change to the current directory
        os.chdir(DEFAULT_DIR)  
        if not os.path.exists(DEFAULT_DIR + "/{}".format(self.artistObj.artistName)):
            #create the directory if it doesnot exist
            os.mkdir(self.artistObj.artistName)  
    def download(self, pageUrl = None, binary = False):
        """Downloads data 

        Args:
            pageUrl (str, optional): URL of the resource. Defaults to None.
            binary (bool, optional): It indicates if the data to be returned should be binary or not. Defaults to False.

        Returns:
            str: The html data or bytes for binary  
        """
        # All links in the howwebiz website are relative 
        if self.howwebizUrl not in pageUrl:
            pageUrl = self.howwebizUrl + "/" + pageUrl
        try:
            response  = requests.get(pageUrl).content if binary else requests.get(pageUrl).text
        except Exception as e:
            self.__printError("Failed to download URL {}: {}".format(pageUrl, e.message))
            exit(0)
        return response
    def __nextPage(self, bsObj):
        """Will provide the next page link if available

        Args:
            bsObj (BeautifulSoupObject): The BeautifulSoup Object having the page
        """
        # The container for page navigation links
        pageLinksContainer = bsObj.find("div", id = "pagination_controls")
        if pageLinksContainer is not None:
            pageLinks = pageLinksContainer.findAll("a")
            for link in pageLinks:
                if "Next" in link.getText():
                    nextLink = link
                    break
            else:
                nextLink = None
            # Check the value of the next link, and extract the href attribute
            if nextLink is None:
                return None
            else:
                return str(nextLink.get("href"))
    def save(self, trackObj):
        """Save file to hard disk

        Args:
            trackObj (object): Object with the track attributes like size, artistID, binary data

        Returns:
            bool: True for successfull saving
        """
       
        try:
            with open("{}/{}/{}.{}".format(DEFAULT_DIR, self.artistObj.artistName, trackObj.trackName, self.fileType), "wb") as f:
                f.write(trackObj.data)
        except Exception as e:
            self.__printError("Failed to save file: {}".format(e))
            exit(0)
        return True
    def logFailedDownloads(self):
        """Log partial downloads so that one can retrying downloading them 

        Args:
            trackObj (object): An instance of  Track 
        """
        with open("./partialDownloads.part", "w+") as failedDownloads:
            #Dump the queue Object in order to complete incomplete downloads
            pickle.dump(self.queue, failedDownloads)
    def __printError(self, message):
        """Prints error messages to the screen

        Args:
            message (string): Error message
        """
        print "[-] {}".format(message)
    def searchSongs(self, bsObj):
        """This method will parse the page having song lists to extract all track details

        Args:
            bsObj (BeautifulSoup Object): Will parse data to find all tracks on a page
        """
        nextPageURL = self.__nextPage(bsObj)
            
        # Get the track that is always put on the left in the a-music-left container
        track = bsObj.find("div", class_="a-music-left").find("a")
        # Get all the track details: trackName, trackAvatar, trackURL, song names contain a minus sign which results in error in mysql, so replacing it with . and when rendering output process will be reversed
        trackName = str(track.find("h3").getText())
        trackAvatar = str(track.find("img").get("src"))
        trackURL = str(track.get("href"))
        # Create Track object to store all the details
        trackObj = Track(trackName, trackAvatar, URL = trackURL)
        trackObj.artist_id = self.artistObj.artist_id
        #Check all the artist ids for the song downloading and check if the singer entered already has that song in the database
        artistIDs = self.model.trackExists(trackObj)
        if ((artistIDs is None) or (trackObj.artist_id not in [dict_['artist_id'] for dict_ in artistIDs])):
            # Add to queue
            self.queue.enqueue(trackObj)
        
        #  Get the rest of the songs that are contained in the newreleases container
        musicContainers = bsObj.findAll("div", class_="newreleases")
        #Iterate over the containers and extract all song details
        for container in musicContainers:
            # Get all the tracks container div elements
            trackContainers = container.findAll("div", class_= "span_1_of_4")
            for trackContainer in trackContainers:
                track= trackContainer.find("a") # Eah song is contained in an a tag
                trackName = str(track.find("h3").getText())# The song title is contained in h3 tag
                trackURL = str(track.get("href")) # Extract the url of the song, the url directs to download page
                trackAvatar = str(track.find("img").get("src")) # The image used for the song || album image
                # Create Track Object to hold details above
                trackObj = Track(trackName, trackAvatar, URL = trackURL)
                trackObj.artist_id = self.artistObj.artist_id
                #Check all the artist ids for the song downloading and check if the singer entered already has that song in the database
                artistIDs = self.model.trackExists(trackObj)
                if ((artistIDs is None) or (trackObj.artist_id not in [dict_['artist_id'] for dict_ in artistIDs])):
                    # Add to queue
                    self.queue.enqueue(trackObj)
        #Check if there is a next page
        if nextPageURL is None:
            # Exit the function
            return 
        else:
            # Parse the next Page
            return self.searchSongs(bs(self.download(pageUrl = nextPageURL), "html.parser"))
    def _getTrackDetails(self, trackObj):
        """There are details that require following a link like the download link, size of song, downloading binary data,
        This method takes care of that

        Args:
            trackObj (object): An instance of Track

        Returns:
            list: The remaining data is stored in the list
        """
        trackDownloadLinkContainer = bs(self.download(pageUrl = trackObj.URL), "html.parser").select("div.download--link")[0]
        trackDownloadLink = self.howwebizUrl +"/"+ str(trackDownloadLinkContainer.select("a.download-song")[0].get("href"))
        trackDownloadSize = str(trackDownloadLinkContainer.find("span").getText()).strip().strip("MB").strip()
        # if the file is already on the hard drive then skip downloading the data
        if os.path.exists("{}/{}/{}.{}".format(DEFAULT_DIR, self.artistObj.artistName, trackObj.trackName, self.fileType)):
            # return a list with the binary data given a value of None
            return [trackDownloadLink, trackDownloadSize, None]
        else:
            # Get Binary data to write to file
            print "[+] Downloading binary data for {}... DONOT EXIT".format(trackObj.trackName)
            trackBinaryData = self.download(pageUrl = trackDownloadLink, binary = True)
            return [trackDownloadLink, trackDownloadSize, trackBinaryData]
           
            
    def run(self):
        """The masterpiece of the class, it calls other methods of the class
        """
        print "[+] Searching songs for artiste {}. ID: {}".format(self.artistObj.artistName, self.artistObj.artist_id)
        # Get all songs for the artist
        self.searchSongs(bs(self.download(pageUrl = self.musicUrl), "html.parser"))
        print "[+] Discovered {} new songs of {}.\n".format(self.queue.length(), self.artistObj.artistName)
        # Iterate throght the queue until its empty
        while not self.queue.is_empty():
            # Retrieve track Object
            trackObj = self.queue.dequeue()
            #Find the other remaining song deatails like alternate download link, size, and the binary data of the song
            otherTrackDetails = self._getTrackDetails(trackObj)
            trackObj.downloadLink = otherTrackDetails[0]
            trackObj.size = otherTrackDetails[1]
            trackObj.data = otherTrackDetails[2]
            # Check the data attribute is None, It implies the song file was already downloaded to the hard disk 
            if trackObj.data is not None:
                print "[+] Saving {} to {}".format(trackObj.trackName, DEFAULT_DIR)
                # Save file to the hard disk
                self.save(trackObj)
            else:
                print "[=] {} already saved on the disk.".format(trackObj.trackName)
            print "[+] Writing {} to  {}.tracks".format(trackObj.trackName, DB_NAME)
            # Write to Database
            self.model.writeTrack(trackObj)
            
    def splashSCreen(self):
        """Prints the program detials
        """
        print "VERSION: {} {}".format(self.VERSION, self.COPYRIGHT)
        print "DEVELOPER: {}".format(self.AUTHOR)
        print "GITHUB: {}".format(self.GITHUB_LINK)
        print "DATE PUBLISHED: {}".format(self.DATE_PUBLISHED)
        print "\n"
# Incoporate argument parsing
parser = ArgumentParser(description="Download music for favourite Ugandan artiste")
parser.add_argument("-a", type=str, help="Singer's exact name", required=True)
args = parser.parse_args()
scrapper = Scrapper(args.a)
# Listen for a KeyboardInterrupt Exception to exit succesfully
try:
    scrapper.splashSCreen()
    print "Press CTRL + C to exit program."
    print "The artiste's name should be the exact one, you may leave out any spaces in the alias"
    scrapper.run()
except KeyboardInterrupt:
    print "[-] Process Interrupted"
    exit(0)
except:
    # Log the failed downloads if any error occurs
    scrapper.logFailedDownloads()
    print "[-] UNknown error has occured but unfinished downloads have been logged, you can resume by running downloadFix.py"
    exit(0)