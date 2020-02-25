# intake system list from EVE ESI, pull values in to dictionary, sort dictionary by npc kills, show top 10
# add options for more data retrieval later

#imports
import re
import requests
import sqlite3
import json
import operator
import itertools
import texttable as tt
from pprint import pprint
from operator import itemgetter
###############################################################################
#Master Variables that the user can change
#Number of results to return:
N = 5
#System to start routing from (must appear exactly as it does in game):
origin = "D-PNP9"
##############################################################################

#in case of unexpected CCP URL change fix this
base_system_url = "https://esi.evetech.net/latest/universe/system_kills/?datasource=tranquility"

#eve sde connect boilerplate - assumes SQLITE SDE is in same directory as this python script
#if not you should fix that cause I'm not changing this
#download latest EVE SDE from https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2  
database = r"sqlite-latest.sqlite"
conn = sqlite3.connect(database)
cur = conn.cursor()

cur.execute("SELECT solarSystemID FROM mapSolarSystems WHERE solarSystemName=?", (origin,))
originID = cur.fetchone()
originID = originID[0]

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
    sys_id.append(name[0])
    npc_kills.append(systems_json[i]["npc_kills"])
    i += 1

master_dict = {sys_id[i]: npc_kills[i] for i in range(len(sys_id))} 

#format the dicts and return top N systems

sorted_dict = {k: v for k, v in sorted(master_dict.items(), key=lambda x: x[1], reverse=True)}

out = dict(itertools.islice(sorted_dict.items(), N))

top25 = sorted(out.items(), key=operator.itemgetter(1), reverse=True)

#Table format prep
numjum = "Number of Jumps from " + str(origin)
tab = tt.Texttable()
headings = ["Region Name","System Name","NPC Kills last 60 Mins",numjum]
tab.header(headings)
print(f"Showing results for {N} systems:")
#loop through values in our combined dict, resolve system names, report region
#names and do some route planning to show number of jumps from d-pnp9
for k,v in top25:
    cur.execute("SELECT regionID FROM mapSolarSystems WHERE solarSystemName=?", (k,))
    regionID = cur.fetchone()
    cur.execute("SELECT regionName FROM mapRegions WHERE regionID=?", (regionID[0],))
    regionName = cur.fetchone()
    cur.execute("SELECT solarSystemID FROM mapSolarSystems WHERE solarSystemName=?", (k,))
    destiID = cur.fetchone()
    URLstring = "https://esi.evetech.net/latest/route/" + str(originID) + "/" + str(destiID[0]) + "/?datasource=tranquility&flag=shortest"
    get_route_json = requests.get(URLstring)
    load_route_json = get_route_json.json()
    i = 0
    for hop in load_route_json:
        i += 1
    tab.add_row([regionName[0],k,str(v),str(i)])

s = tab.draw()
print(s)
