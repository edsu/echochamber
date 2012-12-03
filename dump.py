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
if len(sys.argv) > 2:
    cutoff = int(sys.argv[2])
else: 
    cutoff = 0

graph_name = rdflib.URIRef("http://twitter.com/" + twitter_user)
g = rdflib.Graph(G.store, graph_name)

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
    if s == graph_name:
        continue
    data["nodes"].append({
        "url": str(s),
        "username": str(g.value(s, sioc.name)),
        "followerCount": 0
    })

node_ids = [n["url"] for n in data["nodes"]]
for s, o in g.subject_objects(sioc.follows):
    if s == graph_name or o == graph_name:
        continue
    source = node_ids.index(str(s))
    target = node_ids.index(str(o))
    data["nodes"][target]["followerCount"] += 1
    data["links"].append({"source": source, "target": target})

# limit presentation to just nodes with more than n followers
if cutoff:
    # filter out nodes < cutoff
    new_data = {"nodes": [], "links": []}
    for n in data["nodes"]:
        if n["followerCount"] >= cutoff:
            new_data["nodes"].append(n)

    # rewrite links
    new_node_ids = [n["url"] for n in new_data["nodes"]]
    for link in data["links"]:
        source = data["nodes"][link["source"]]
        target = data["nodes"][link["target"]]
        if source["url"] in new_node_ids and target["url"] in new_node_ids:
            new_data["links"].append({
                "source": new_node_ids.index(source["url"]),
                "target": new_node_ids.index(target["url"])
            })

    data = new_data
        
open(filename, "w").write(json.dumps(data, indent=2))
