# intake system list from EVE ESI, pull values in to dictionary, sort dictionary by npc kills, show top 10
# add options for more data retrieval later

#imports
import re
import requests
import sqlite3
import json
import operator
import itertools
from pprint import pprint
from operator import itemgetter

#in case of unexpected CCP URL change fix this
base_system_url = "https://esi.evetech.net/latest/universe/system_kills/?datasource=tranquility"

#eve sde connect boilerplate - assumes SQLITE SDE is in same directory as this python script
#if not you should fix that cause I'm not changing this
#download latest EVE SDE from https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2  
database = r"sqlite-latest.sqlite"
conn = sqlite3.connect(database)
cur = conn.cursor()

#get eve esi response and convert to json object
system_data = requests.get(base_system_url)
systems_json = system_data.json()

#make 2 lists at the same time in the same for loop that we can then convert to a dict of key value pairs
#where the key is the systemID and the value is the npc kills
sys_id = []
npc_kills = []

i = 0
for system in systems_json:
    name = systems_json[i]["system_id"]
    cur.execute("SELECT solarSystemName FROM mapSolarSystems WHERE solarSystemID=?", (name,))
    name = cur.fetchone() 
    sys_id.append(str(name))
    npc_kills.append(systems_json[i]["npc_kills"])
    i += 1

master_dict = {sys_id[i]: npc_kills[i] for i in range(len(sys_id))} 

#format the dicts and return top N systems

N = 50

sorted_dict = {k: v for k, v in sorted(master_dict.items(), key=lambda x: x[1], reverse=True)}

out = dict(itertools.islice(sorted_dict.items(), N))

top25 = sorted(out.items(), key=operator.itemgetter(1), reverse=True)

for k,v in top25:
    string = k + " - " + str(v)
    #string = string.strip('()')
    pprint(string)
