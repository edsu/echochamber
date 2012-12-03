#!/usr/bin/env python

"""
Dump out turtle, json-ld and d3 json for a given seed twitter user in the graph.
"""

import os
import sys
import json
import rdflib

G = rdflib.ConjunctiveGraph("Sleepycat", identifier="echochamber")
G.open("store")

twitter_user = sys.argv[1]
g = rdflib.Graph(G.store, rdflib.URIRef("http://twitter.com/" + twitter_user))

data_dir = os.path.join("examples", twitter_user)
if not os.path.isdir(data_dir):
    os.mkdir(data_dir)

filename = os.path.join(data_dir, "graph.ttl")
print "creating", filename
g.serialize(open(filename, "w"), format="turtle", indent=2)

filename = os.path.join(data_dir, "graph.json")
print "creating", filename
g.serialize(open(filename, "w"), format="json-ld", indent=2)

# generate d3 friend json

filename = os.path.join(data_dir, "d3.json")
print "creating", filename
sioc = rdflib.Namespace("http://rdfs.org/sioc/ns#")

data = {"nodes": [], "links": []}
for s in g.subjects(rdflib.RDF.type, sioc.UserAccount):
    data["nodes"].append({
        "url": str(s),
        "username": str(g.value(s, sioc.name)),
    })

node_ids = [n["url"] for n in data["nodes"]]
for s, o in g.subject_objects(sioc.follows):
    source = node_ids.index(str(s))
    target = node_ids.index(str(o))
    data["links"].append({"source": source, "target": target})

open(filename, "w").write(json.dumps(data, indent=2))
