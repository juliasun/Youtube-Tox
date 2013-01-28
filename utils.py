from numpy import *
from scipy import *

#from readabilitytests import ReadabilityTool
from zlib import compress
from numpy.random import rand


import couchdb
import cPickle	

import xlwt

#------Adaptation of Flesch-Kincaid grade level for tweets-----------
#Instead of words per sentence, we consider words per tweet
#--------------------------------------------------------------------

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
verboten = ['@','RT','http://','#']

def FK(tweet):
	return ReadabilityTool(clean(tweet)).FleschKincaidGradeLevel()

def clean(tweet,keepTags = False):
	if not keepTags:
		handles = set(filter(lambda x: 1 in [symbol in x for symbol in verboten], tweet.split(' ')))
		tweet= ' '.join([filter(lambda x: ord(x)<128,word) for word in tweet.split(' ') if word not in handles])
        return ' '.join([word.translate(None, delchars).lower() for word in tweet.encode('ascii','ignore').split()])
	
def lexdiv(tweet):
	return round(len(set(clean(tweet)))/float(len(clean(tweet))),3)

def LZC(tweet):
  return len(clean(tweet))/float(len(compress(clean(tweet)))) 

def rand_chars(length):
	import random
	import string
	
	return ''.join(random.choice(string.letters) for i in range(length))


def grab_locs_from(filename):
	if filename.endswith('.xls'):
		from xlrd import open_workbook
		wb = open_workbook(filename)
		#ZIP code is col 1, Lat is col 4, long is col 5
		#grab first sheet
		sh = wb.sheet_by_index(0)
		zipcodes = sh.col_values(0)
		latitudes = sh.col_values(3)
		longis = sh.col_values(4)
	else: #Assume it is in CSV format
		data = genfromtxt(filename,delimiter=',', dtype = str)
		zipcodes = data[:,0]
		latitudes = data[:,3]
		longis = data[:,4]
	return {str(int(zipcode)):','.join([str(lat),str(lon)]) for zipcode,lat,lon in zip(zipcodes,latitudes,longis)}


def test():
	tweet = 'The quick brown RT 12. jumped over l3zy f)z'
	print clean(tweet)
	print lexdiv(tweet)
	print FK(tweet)
	print LZC(tweet)

def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
           key = key.encode('utf-8')
        if isinstance(value, unicode):
           value = value.encode('utf-8')
        elif isinstance(value, list):
           value = _decode_list(value)
        elif isinstance(value, dict):
           value = _decode_dict(value)
        rv[key] = value
    return rv

def flatten(lst):
	return [item for sublist in lst for item in sublist]

def broadcast(x, idx,count=False):
	print x if not count else idx
	return x

def score(tweet, topics,weights, percentile = 99): #words is a list of lists. Each inner list is a topic
	from scipy.stats import percentileofscore
	answer = []
	for i,topic in enumerate(topics):
		score = 0
		for j,word in enumerate(topic):
			if word in tweet: #Be careful, this is Python but only works if word and tweet are the same data type
				score += float(weights[i][j])
		answer.append((i,round(score,3)))
	scores = [x[1] for x in answer]
	return sorted([datum for datum in answer if percentileofscore(scores,datum[1]) >= percentile] , key = lambda x:x[1], reverse=True)

#
#From: http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
def chunks(lst,n): #This will only work if the length of the list is defined
	for i in xrange(0,len(lst),n):
		yield lst[i:i+n]

#
#From: Mining the Social Web p12
def get_rt_source(tweet):
	import re
	rt_patterns = re.compile(r"(RT|via)((?:\b\W*@\w+)+)",re.IGNORECASE)
	return [source.strip() for tup in rt_patterns.findall(tweet) for source in tup if source not in ("RT","via")]

def grouper(n, iterable, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    from itertools import izip_longest
    # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

#From http://blog.marcus-brinkmann.de/2011/09/17/a-better-iterator-for-python-couchdb/
def couchdb_pager(db, view_name='_all_docs',
                  startkey=None, startkey_docid=None,
                  endkey=None, endkey_docid=None, bulk=5000):
    # Request one extra row to resume the listing there later.
    options = {'limit': bulk + 1}
    if startkey:
        options['startkey'] = startkey
        if startkey_docid:
            options['startkey_docid'] = startkey_docid
    if endkey:
        options['endkey'] = endkey
        if endkey_docid:
            options['endkey_docid'] = endkey_docid
    done = False
    while not done:
        view = db.view(view_name, **options)
        rows = []
        # If we got a short result (< limit + 1), we know we are done.
        if len(view) <= bulk:
            done = True
            rows = view.rows
        else:
            # Otherwise, continue at the new start position.
            rows = view.rows[:-1]
            last = view.rows[-1]
            options['startkey'] = last.key
            options['startkey_docid'] = last.id

        for row in rows:
            yield row.id
            
def add_random_fields():
	server = couchdb.Server()
	databases = [database for database in server if not database.startswith('_')]
	for database in databases:
		print database
		count = 0
		for document in couchdb_pager(server[database]):
			result = server[database][document]
			if 'results' in result:
				#
				for tweet in result['results']:
					if tweet and 'rand_num' not in tweet:
						tweet['rand_num'] = rand()
						server[database].save(tweet)
			elif 'text' in result and result['text'] and 'rand_num' not in result:
					results['rand_num'] = rand()
					count = count +1
		print count
def select_random(drug,fraction = 0.10):
	import csv
	server = couchdb.Server()
	#databases = [database for database in server if not database.startswith('_')]
	databases = ['toxtweet']
	count = 0
	selected = 0
	for database in databases:
		print database
		with open(database+"_for_rating.csv",'w') as file:
			writer = csv.writer(file)
			for document in couchdb_pager(server[database]):	
				result = server[database][document]
				if 'results' in result:
					for tweet in result['results']:
						if tweet and 'rand_num' in tweet and drug in query:
							if tweet['rand_num'] < fraction:
								row_data = [clean(tweet['text']),tweet['rand_num'],document]
								writer.writerow(row_data)
								selected = selected + 1
				elif 'text' in result and result['rand_num'] and result['rand_num'] < fraction:
					row_data = [clean(result['text']),result['rand_num'],document]
					writer.writerow(row_data)
					selected = selected + 1
			count = count + 1 
			if count%10000==0:
				print "In ",database,selected,' of ',count,'selected'
	wbk.save(database+"_for_rating.xls")
	
def find_all_document_tweets( server=couchdb.Server() ):
    databases = [database for database in server if not database.startswith('_')]
    for database in databases:
        for document in couchdb_pager(server[database]):
            if 'results' in server[database][document]:
                for tweet in server[database][document]['results']:
                    yield database, document, tweet
                    

#Accessory function for NaiveBayesClassifier, perhaps better as a lambda function

def extract_features(tweet,features):
	return {"has(%s)"%feature: (feature in tweet) for feature in features}

def csv_to_corpora(filename): #To allow LSA, LDA from gensim
	import csv
	from gensim import corpora, models, similarities
	from os.path import basename
	as_list=[]
	print 'Loading Tweets'
	with open(filename,'rb') as f:
		reader = csv.reader(f)
		as_list = [row[0].split() for row in reader] #gensim expects a list of words for each document
	print 'Loaded Tweets'
	dictionary = corpora.Dictionary(as_list)
	print 'Made id2word'
	dictionary.save(basename(filename)+'.dict')
	print 'Saved id2word'
	corpus = [dictionary.doc2bow(text) for text in as_list]
	print 'Made corpus'
	corpora.MmCorpus.serialize(basename(filename)+'.mm',corpus) #store for later use
	print 'Saved corpus'
	
	#tfidf = models.TfidfModle(corpus) #LSA and LDA both assume the text has a vector space representation
	#print 'made tfidf'
	
	lda = gensim.models.ldamodel.LdaModel(corpus=corpus,id2word = dictionary, num_topics = 20, 
							update_every=1, chunksize=100000, passes =1) 	
	print 'made LDA'
	
	lda.print_topics(50)
	
#Update the local copy of the CouchDB so that each tweet has a field called rating
def classify_tweets(drug='cocaine'):
	server = couchdb.Server() #default option is local host
	try:
		db = server[drug]
	except: #Can add in specific exceptions later
		print drug,' not in Server'
	
	features,extract_features,classifier = cPickle.load(open(drug+'_classifier.pkl','rb'))
	print 'Unpickled Classifier'		
	
	print 'Loading Relevant Tweets'
	targets = [id for id in db if drug in db[id].keys()]
	print 'Loaded All Relevant Tweets'
	print 'Filtering out tweets that were already rated'
	targets = filter(lambda tweet: 'classification' in tweet.keys() and not tweet['classification'], targets)
	print 'Passing filtered list to classifier'
	for idx, tweet in enumerate(targets):
		#Original queries used just the drug name and no synonyms. 
		#There may be a more efficient Map/Reduce

		#couchdb-python makes all this updating easy
		print tweet
		tweet['classification'] = classifier.classify(extract_features(tweet,features))		
		db.save(tweet)
		print idx/float(len(targets))
	