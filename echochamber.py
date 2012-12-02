#!/usr/bin/env python

"""
This script takes a seed Twitter username and captures
the relations between its followers, and saves them off
as a FOAF RDF file.

You'll need to set the following environment variables:

* OAUTH_CONSUMER_KEY
* OAUTH_CONSUMER_SECRET
* OAUTH_TOKEN
* OAUTH_TOKEN_SECRET
"""

import os
import sys
import json
import time
import rdflib

from tweepy import OAuthHandler, API, Cursor
from tweepy.error import TweepError

oauth_consumer_key = os.environ.get("OAUTH_CONSUMER_KEY")
oauth_consumer_secret = os.environ.get("OAUTH_CONSUMER_SECRET")
oauth_token = os.environ.get("OAUTH_TOKEN")
oauth_token_secret = os.environ.get("OAUTH_TOKEN_SECRET")
auth = OAuthHandler(oauth_consumer_key, oauth_consumer_secret)
auth.set_access_token(oauth_token, oauth_token_secret)
api = API(auth)

graph = rdflib.Graph("Sleepycat", identifier="twitter_user")
graph.open("store", create=True)
foaf = rdflib.Namespace("http://xmlns.com/foaf/0.1/")
graph.bind("foaf", foaf)
dct = rdflib.Namespace("http://purl.org/dc/terms/")
graph.bind("dct", dct)

txt = open("code4lib.ttl").read()

def twitter_uri(screen_name):
    return rdflib.URIRef("http://twitter.com/" + screen_name)

def twitter_id(id):
    return rdflib.URIRef("info:twitter/" + str(id))

def add_user(user):
    uri = twitter_uri(user.screen_name)
    graph.add((uri, rdflib.RDF.type, foaf.Person))
    graph.add((uri, foaf.name, rdflib.Literal(user.name)))
    graph.add((uri, foaf.nick, rdflib.Literal(user.screen_name)))
    graph.add((uri, dct.identifier, twitter_id(user.id)))
    if user.url:
        graph.add((uri, foaf.homepage, rdflib.URIRef(user.url)))
    return uri

def id2uri(id):
    return graph.value(None, dct.identifier, twitter_id(id))

def check_rate_limit():
    rl = api.rate_limit_status()
    if rl["remaining_hits"] == 0:
        reset_time = rl["reset_time_in_seconds"]
        secs = reset_time - int(time.time()) 
        print "sleeping for %s seconds" % secs
        time.sleep(secs)

def load(twitter_user):
    check_rate_limit()
    for user in Cursor(api.followers, screen_name=twitter_user).items():
        user_uri = add_user(user)
        try:
            check_rate_limit()
            for friend_id in Cursor(api.friends_ids, screen_name=user.screen_name).items():
                friend_uri = id2uri(friend_id)
                # only record in-network friendships
                if friend_uri:
                    print user_uri, "knows", friend_uri
                    graph.add((user_uri, foaf.knows, friend_uri))
        except TweepError:
            print "unable to see friends for ", user.screen_name
    graph.serialize(open(twitter_user + ".ttl", "w"), format="turtle")

if __name__ == "__main__":
    twitter_user = sys.argv[1]
    load(twitter_user)
    graph.close()
