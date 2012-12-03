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
import logging

from tweepy import OAuthHandler, API, Cursor
from tweepy.error import TweepError

logging.basicConfig(filename="echochamber.log", 
                    level=logging.INFO,
                    format='%(asctime)-15s %(message)s')

oauth_consumer_key = os.environ.get("OAUTH_CONSUMER_KEY")
oauth_consumer_secret = os.environ.get("OAUTH_CONSUMER_SECRET")
oauth_token = os.environ.get("OAUTH_TOKEN")
oauth_token_secret = os.environ.get("OAUTH_TOKEN_SECRET")
auth = OAuthHandler(oauth_consumer_key, oauth_consumer_secret)
auth.set_access_token(oauth_token, oauth_token_secret)
api = API(auth)
remaining_hits = 0

foaf = rdflib.Namespace("http://xmlns.com/foaf/0.1/")
sioc = rdflib.Namespace("http://rdfs.org/sioc/ns#")
G = rdflib.ConjunctiveGraph("Sleepycat", identifier="echochamber")
G.open("store", create=True)
G.bind("foaf", foaf)
G.bind("sioc", sioc)

def twitter_uri(screen_name):
    return rdflib.URIRef("http://twitter.com/" + screen_name)

def add_user(user, g, reload=False):
    uri = twitter_uri(user.screen_name)

    # don't add again if we already know about the user, this avoids
    # multiple BNodes being added on re-runs
    if len(list(g.predicate_objects(uri))) > 0 and not reload:
        return

    g.add((uri, rdflib.RDF.type, sioc.UserAccount))
    g.add((uri, sioc.id, rdflib.Literal(user.id)))
    g.add((uri, sioc.name, rdflib.Literal(user.screen_name)))

    person = rdflib.BNode()
    g.add((uri, sioc.account_of, person))
    g.add((person, foaf.name, rdflib.Literal(user.name)))
    if user.url:
        g.add((person, foaf.homepage, rdflib.URIRef(user.url)))

    logging.info("added %s" % uri)
    return uri

def check_rate_limit():
    global remaining_hits
    if remaining_hits > 0:
        return
    while True:
        rl = api.rate_limit_status()
        if rl["remaining_hits"] == 0:
            print rl["remaining_hits"]
            reset_time = rl["reset_time_in_seconds"]
            t = time.time()
            secs = reset_time - int(t) 
            logging.info("sleeping for %s seconds" % secs)
            if secs > 0:
                time.sleep(secs)
        else:
            remaining_hits = rl["remaining_hits"]
            break

def load(twitter_user):
    # name the graph for the assertions related to a particular user
    g = rdflib.Graph(G.store, twitter_uri(twitter_user))

    # add the seed user
    check_rate_limit()
    user = api.get_user(screen_name=twitter_user)
    add_user(user, g)

    # add all of its followers
    for user in Cursor(api.followers, screen_name=twitter_user).items():
        check_rate_limit()
        user_uri = add_user(user, g)

    # add the in network following relations
    for user_uri, username in g.subject_objects(predicate=sioc.name):
        try:
            check_rate_limit()
            for friend_id in Cursor(api.friends_ids, screen_name=username).items():
                friend_uri = g.value(None, sioc.id, rdflib.Literal(friend_id))
                if friend_uri:
                    logging.info("%s follows %s", user_uri, friend_uri)
                    g.add((user_uri, sioc.follows, friend_uri))
        except TweepError:
            logging.warn("unable to see friends for %s", user.screen_name)

    G.serialize(open(twitter_user + ".ttl", "w"), format="turtle")
    G.serialize(open(twitter_user + ".json", "w"), format="json-ld")

if __name__ == "__main__":
    twitter_user = sys.argv[1].strip()
    load(twitter_user)
    g.close()
