#!/usr/bin/env python

"""
This script takes a seed Twitter username and captures
the relations between its followers, and saves them off
as RDF using SIOC and FOAF.

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
sioc = rdflib.Namespace("http://rdfs.org/sioc/ns#")
g.bind("sioc", sioc)

def twitter_uri(screen_name):
    return rdflib.URIRef("http://twitter.com/" + screen_name)

def add_user(user):
    uri = twitter_uri(user.screen_name)
    graph.add((uri, rdflib.RDF.type, sioc.UserAccount))
    graph.add((uri, sioc.id, rdflib.Literal(user.id))
    graph.add((uri, sioc.name rdflib.Literal(user.screen_name)))

    person = rdflib.BNode()
    graph.add((uri, sioc.account_of, person))
    graph.add((person, foaf.name, rdflib.Literal(user.name)))
    if user.url:
        graph.add((person, foaf.homepage, rdflib.URIRef(user.url)))

    print "added %s" % uri
    return uri

def id2uri(id):
    return graph.value(None, sioc.id, rdflib.Literal(id))

def check_rate_limit():
    rl = api.rate_limit_status()
    if rl["remaining_hits"] == 0:
        reset_time = rl["reset_time_in_seconds"]
        secs = reset_time - int(time.time()) 
        print "sleeping for %s seconds" % secs
        time.sleep(secs)

def load(twitter_user):
    # add the seed user
    check_rate_limit()
    user = api.get_user(screename=twitter_user)
    add_user(user)

    # add all of its followers
    for user in Cursor(api.followers, screen_name=twitter_user).items():
        check_rate_limit()
        user_uri = add_user(user)

    # add the in network following relations
    for user_uri, username in graph.subject_objects(predicate=sioc.name):
        try:
            check_rate_limit()
            for friend_id in Cursor(api.friends_ids, screen_name=username).items():
                friend_uri = id2uri(friend_id)
                if friend_uri:
                    print user_uri, "follows", friend_uri
                    graph.add((user_uri, sioc.follows, friend_uri))
        except TweepError:
            print "unable to see friends for ", user.screen_name
    graph.serialize(open(twitter_user + ".ttl", "w"), format="turtle")

if __name__ == "__main__":
    twitter_user = sys.argv[1]
    load(twitter_user)
    graph.close()
