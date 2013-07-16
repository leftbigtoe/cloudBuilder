# -*- coding: utf-8 -*-
"""
Created on Sat May 25 17:22:35 2013

@author: leftbigtoe
"""
import json, sys, tweepy
from thread import start_new_thread
from pytagcloud import create_tag_image, make_tags
from pytagcloud.lang.counter import get_tag_counts

class cloudBuilder(tweepy.StreamListener):

    def __init__(self, tracked, maxTweets = 600, interimResults = 100, 
                 minOcc = 4):    
        """
        maxTweets: maximum number of tweets used for the wordcloud
        interimResults: after so many tweets an intermediate tag cloud is built
        minOcc: minimal number of occurences to be included in tag cloud
        """
        
        # intialize variables
        self.counter = 0
        self.corpus = ''
        self.maxTweets = maxTweets
        self.interimResults = interimResults
        self.minOcc = minOcc
        self.tracked = tracked

        
    def on_data(self, data):
        """
        loads the new tweet and starts the filtering and saving in a new thread
        every so and so many tweets, make an intermediate tagcloud
        """
        tweet = json.loads(data)
        
        # save tweet
        start_new_thread(self.checkAndSave, (tweet,))
        
        # make tag cloud every 100 tweets
        if self.counter % self.interimResults == 0 and self.counter != 0:
            start_new_thread(self.makeTagCloud, (self.counter,))

        
    def checkAndSave(self, tweet):
        """ filter out replies and retweets and save to corpus """
        # only add tweet if not a retweet or reply
        try:
            if not("RT " in tweet["text"] or "RE " in tweet["text"]):
                self.counter += 1
                self.corpus += ' ' + tweet["text"]
                # give feedback to console
                start_new_thread(self.consolePrinter, 
                                 ("received "+str(self.counter),))
        # sometimes tweets have no text field, just ignore those
        except:
            return
        
        
    def makeTagCloud(self, counter = 0):
        """
        function building the tag clouds and shutting down after the 
        last one
        """
        # get tag count
        tagCount = get_tag_counts(self.corpus)
        
        # cut out low entries, short words, the tracked word & some more stuff
        tagCount = [x for x in tagCount if x[1] >= self.minOcc and not(x[0] in 
                    [self.tracked, 'http', 'https']) and len(x[0])>2]

        tags = make_tags(tagCount, maxsize =150)
        create_tag_image(tags, self.tracked[0] + '_cloud_'+ str(counter) \
                                               + '.png', size=(1000,1000))
        print "tag cloud built..."
        print ("current corpus size: lenght = ",len(self.corpus),
               ", memory = ",sys.getsizeof(self.corpus)/1000)
        
        # after the last tag clodu has been completed, shut down
        if counter >= self.maxTweets:
            print 'enough, I am shutting down'
            sys.exit()

                                            
    def consolePrinter(self, text):
        """ prints out the tweet """
        print text
        

def main():
    # load consumer token & secret key
    f = open('auth.txt','r')
    c_token, c_secret, a_token, a_secret = (line.strip() for line in f)
    f.close()

    # create OAuth handler and get access
    auth = tweepy.OAuthHandler(c_token, c_secret)
    auth.set_access_token(a_token, a_secret)
 
    # get word to search for
    tracked = [raw_input("Look for word: ")]
    
    # create cloudBuilder instance
    listener = cloudBuilder(tracked)
    
    # start up stream
    stream = tweepy.Stream(auth, listener)
    stream.filter(track = tracked)
    print "Streaming started..."
    

if __name__ == '__main__':
    main()
