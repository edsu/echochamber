echochamber
===========

This script downloads the social network that exists in the followers
of a given Twitter user and persists it as RDF using 
[SIOC](http://sioc-project.org/) and 
[FOAF](http://xmlns.com/foaf/spec/).

1. pip install -r requirements.txt
1. set environment variables for: OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
1. ./echochamber.py code4lib
1. cat code4lib.ttl

