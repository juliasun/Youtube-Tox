Python files for analyzing synonyms in Youtube comments

What it does:
-----
1. Gets comments from Youtube videos
2. Processes the comments for collocations, similar words, and n-grams
3. Writes results to a json file

How to run:
-----
Download all files to the same directory.	
Edit the drugs document to change the search terms of interest.		
Run the shell script from the terminal using the command:

sh yt_shell.sh

Alternatively, the python script can also be run directly from the terminal by using the command:

python get_yt_comments.py drug	
(drug can be any string of interest)


Neccessary dependencies:
-----
-Numpy/SciPy	
-NLTK	
-CouchDB	
-cPickle



===========
