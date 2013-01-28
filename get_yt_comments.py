# -*- coding: utf-8 -*-
import gdata.youtube
import gdata.youtube.service
import urlparse
import time
from lxml import etree
from xml.etree import cElementTree as ET
import urllib
#from bs4 import BeautifulSoup
import utils as tech
from sys import argv
from nltk import Text
from nltk import ContextIndex
from nltk.collocations import BigramAssocMeasures, TrigramAssocMeasures, BigramCollocationFinder, TrigramCollocationFinder
import json

yt_service = gdata.youtube.service.YouTubeService()

drug = argv[1]

def WriteCommentFeed(video_id=None): #, data_file  
	comment_feed_url = "http://gdata.youtube.com/feeds/api/videos/%s/comments"
	comments = []
	if video_id:
		url = comment_feed_url % video_id
		comment_feed = yt_service.GetYouTubeVideoCommentFeed(uri=url)		
		while comment_feed:
			try:
				comments.append([comment.content.text for comment in comment_feed.entry])
				comment_feed = yt_service.Query(comment_feed.GetNextLink().href) 
			except:
				break
	return [comment for user in comments for comment in user]

def get_video_data(xml):
	root = ET.fromstring(xml)
	ns = '{http://www.w3.org/2005/Atom}'
	results = [child.attrib.get('href') for child in root if child.tag == (ns+'link')]
    #print results
        answer = []
        url_list = []
        for link in results[:2]:
            url= urlparse.parse_qs(urlparse.urlparse(link).query)
            #print url
            url_list.append(url)
            video = url['v'][0] if 'v' in url else None
            #video = url['v'] if 'v' in url else None
            #print video
            answer.append(WriteCommentFeed(video))
            time.sleep(15)
        return answer, url_list
		
def getTopVideo(searchTerm):
	yt_service = gdata.youtube.service.YouTubeService()
	query = gdata.youtube.service.YouTubeVideoQuery()
	
	query.vq = searchTerm
	query.orderby = 'relevance'
	query.time = 'all_time'
	query.racy = 'include'
	
	feed = yt_service.YouTubeQuery(query).entry
	return get_video_data(str(feed[0]))

#-----------
import utils as tech
from nltk.corpus import stopwords
chatter,urls = getTopVideo(searchTerm=drug)[0]
comment_count = len(chatter)
search_query = ''.join(map(tech.clean,chatter)).split()
search_query = filter(lambda word: word not in stopwords.words('english') and word not in stopwords.words('italian') and word not in stopwords.words('spanish'),search_query)

#print 'Words similar to ' + drug + ' using Text method'
#Finds other words which appear in the same contexts
ytcomments = Text(search_query)
ytcomments.similar(drug)

#print 'Words similar to ' + drug + ' using ContextIndex method'
ytcomments2 = ContextIndex(search_query)
sim = ytcomments2.similar_words(drug)

#ytcomments.collocations()

#Finds the most frequent words to appear with drug
bi = BigramAssocMeasures()
bi_finder = BigramCollocationFinder.from_words(ytcomments, window_size = 20)
top_general = bi_finder.nbest(bi.pmi,30)
bi_finder.apply_ngram_filter(lambda w1,w2: w1 != drug and w2 != drug)
top_bi = bi_finder.nbest(bi.pmi, 30)

#Finds the two most frequent words to appear with drug
tri = TrigramAssocMeasures()
tri_finder = TrigramCollocationFinder.from_words(ytcomments)
tri_finder.apply_ngram_filter(lambda w1,w2,w3: w1 != drug and w2 != drug and w3 != drug)
top_tri = tri_finder.nbest(tri.pmi, 30)

result ={
    'n-grams': {
        '2': top_bi,
        '3': top_tri,
        },
    'collocations': top_general,
    'similarity':{
        'from_text':None,
        'from_context': sim,
                },
'search': {
        'corpus':search_query,
        'url': urls,
        'num_comments': comment_count
        }
}
json.dump(result, open('results_'+drug,'wb'))