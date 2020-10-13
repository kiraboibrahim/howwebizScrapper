# HowweScrapper package
# Version 0.1.0
# Author Kirabo Ibrahim
# copyright 2020 Kirabo Developer

import requests, os, csv
from bs4 import BeautifulSoup as bs
from Model import HowweModel
from settings import DEFAULT_DIR, DB_NAME

#Artist data type
class Artist:
    def __init__(self, artistName, artistBio, artistAvatar, socialMediaIcons):
        self.artistName = artistName.replace(" ", "").lower()
        self.artistBio = artistBio
        self.artistAvatar = artistAvatar
        self.socialMediaIcons = socialMediaIcons
#Track Datatype
class Track:
    def __init__(self, trackName, trackThumbnail, URL = ''):
        self.trackName = trackName
        self.trackAvatar = trackThumbnail
        self.size = ""
        self.data = None
        self.artistID = None
        self.URL = URL
        self.downloadLink = None
        
# Queue datatype
class Queue:
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
    def __init__(self, artistName):
        #Will talk to database
        self.model = HowweModel()
        #Other attributes to be filled in later, initialized with empty strings for the start
        self.artistObj = Artist(artistName, "", "", "")
        self.howwebizUrl = "https://www.howwebiz.ug"
        self.musicUrl = "{}/{}/music".format(self.howwebizUrl, self.artistObj.artistName)
        self.fileType = "mp3" # Default filet ype for howwebiz website
        self.queue = Queue() # Will hold the all track Objects
    def download(self, pageUrl = None, binary = False):
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
        nextLink = bsObj.find("div", id = "pagination_controls").findAll("a")[-1]
        if nextLink is None:
            return None
        else:
            return nextLink.get("href")
    def save(self, trackObj):
       
        try:
            with open("{}/{}.{}".format(DEFAULT_DIR, trackObj.trackName, self.fileType), "wb") as f:
                f.write(trackObj.data)
        except Exception as e:
            self.__printError("Failed to save file: {}".format(e.message))
            exit(0)
        return True
    def __logPartialDownloads(self, Obj):
        with open("./partialDownloads.csv", "a+", newline = '') as partialDownloadFile:
            csvWriter = csv.writer(partialDownloadFile, delimeter="|", quotechar = '"')
            if isinstance(Obj, Artist):
                csvWriter.writerow([Obj.artistName, Obj.artistBio, Obj.artistAvatar, Obj.socialMediaIcons])
            elif isinstance(Obj, Track):
                csvWriter.writerow([Obj.artistID, Obj.trackName, Obj.trackAvatar, Obj.trackURL, Obj.size])
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
            
        # Create queue object to store all tracks to download
        self.queue = Queue()
        # Get the track that is always put on the left in the a-music-left container
        track = bsObj.find("div", class_="a-music-left").find("a")
        # Get all the track details: trackName, trackAvatar, trackURL
        trackName = str(track.find("h3").getText(), "utf-8")
        trackAvatar = str(track.fing("img").get("src"), "utf-8")
        trackURL = str(track.get("href"), "utf-8")
        # Create Track object to store all the details
        trackObj = Track(trackName, trackAvatar, URL = trackURL)
        if  not self.model.trackExists(trackName) and not os.path.exists("{}/{}.{}".format(DEFAULT_DIR, trackObj.trackName, self.fileType)):
            # There are some other deatils requierd like downloadSize, Track Download link, Binary data of the track
            otherTrackDetails = self._getTrackDetails(trackObj.URL)
            trackObj.downloadLink = otherTrackDetails[0]
            trackObj.size = otherTrackDetails[1]
            trackObj.data = otherTrackDetails[2]
            # Add to queue
            self.queue.enqueue(trackObj)
        
        #  Get the rest of the songs that are contained in the newreleases container
        musicContainers = bsObj.findAll("div", class_="newreleases")
        #Iterate over the containers and extract all song details
        for container in musicContainers:
            # Get all the tracks container div elements
            trackContainers = container.findAll("div", class_= "span_1_of_4")
            for trackContainer in trackContainers:
                track= trackContainer.find("a")
                trackName = str(track.find("h3"), "utf-8")
                trackURL = str(track.get("href"), "utf-8")
                trackAvatar = str(track.find("img").get("src"), "utf-8")
                # Create Track Object to hold details
                trackObj = Track(trackName, trackAvatar, URL = trackURL)
                #Check if a track exists in the database and its downloaded before adding it to a queue
                if (self.model.trackExists(trackObj) and os.path.exists("{}/{}.{}".format(DEFAULT_DIR, trackObj.trackName, self.fileType))):
                    continue
                # There are some other deatils requierd like downloadSize, Track Download link, Binary data of the track
                otherTrackDetails = self._getTrackDetails(trackObj.URL)
                trackObj.downloadLink = otherTrackDetails[0]
                trackObj.size = otherTrackDetails[1]
                trackObj.data = otherTrackDetails[2]
                self.queue.enqueue(trackObj)
        #Check if there is a next page
        if nextPageURL is None:
            # Exit the function
            return 
        else:
            # Parse the next Page
            return self.searchSongs(bs(self.download(pageUrl = nextPageURL), "html.parser"))
    def _getTrackDetails(self, trackURL):
        trackDownloadLinkContainer = self.download(pageUrl = trackURL).find("div", class_= "download--link")
        trackDownloadLink = str(trackDownloadLinkContainer.find("div", class_ = "download-song").get("href"), "utf-8")
        trackDownloadSize = str(trackDownloadLinkContainer.find("span").getText(), "utf-8").strip().strip("MB")
        # Get Binary data to write to file
        trackBinaryData = self.download(pageUrl = trackDownloadLink)
        return [trackDownloadLink, trackDownloadSize, trackBinaryData]
    def run(self):
        # Get all songs for the artist
        self.searchSongs(bs(self.download(pageUrl = self.musicUrl), "html.parser"))
        print "[+] Discovered {} songs of {}.".format(self.queue.length(), self.artistObj.artistName)
        # Iterate throght the queue until its empty
        while not self.queue.is_empty():
            # Retrieve track Object
            trackObj = self.queue.dequeue()
            
            print "[+] Saving {} to {}".format(trackObj.trackName, DEFAULT_DIR)
            # Save file to the hard disk
            self.save(trackObj)
            # Write to Database
            print "[+] Writing {} to {}".format(trackObj.trackName, DB_NAME)
            self.model.writeTrack(trackObj)
scrapper = Scrapper("winnie nwagi")
scrapper.run()
        