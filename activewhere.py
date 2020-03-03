# intake system list from EVE ESI, pull values in to dictionary, sort dictionary by npc kills, show top 10
# add options for more data retrieval later

#imports
import requests
import sqlite3
import json
import operator
import itertools
import pandas as pd
from operator import itemgetter
###############################################################################
#Master Variables that the user can change
#System to start routing from (must appear exactly as it does in game):
origin = "Jita"
##############################################################################

#in case of unexpected CCP URL change fix this
base_system_url = "https://esi.evetech.net/latest/universe/system_kills/?datasource=tranquility"

#eve sde connect boilerplate - assumes SQLITE SDE is in same directory as this python script
#if not you should fix that cause I'm not changing this
#download latest EVE SDE from https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2  
print("\nConnecting to local database and requesting/parsing EVE ESI data...")
database = r"sqlite-latest.sqlite"
conn = sqlite3.connect(database)
cur = conn.cursor()

cur.execute("SELECT solarSystemID FROM mapSolarSystems WHERE solarSystemName=?", (origin,))
originID = cur.fetchone()
originID = originID[0]

print("Getting system data json...")
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
print("Looped through system ids, creating dictionary...")
master_dict = {sys_id[i]: npc_kills[i] for i in range(len(sys_id))} 

#playing with pandas instead of attempting to sort dicts seems smart here
df = pd.Series(master_dict)
df.index.name = 'System'
region_list = []
print("Creating region name list...")
for key in master_dict:
    cur.execute("SELECT regionID FROM mapSolarSystems WHERE solarSystemName=?", (key,))
    regionID = cur.fetchone()
    cur.execute("SELECT regionName FROM mapRegions WHERE regionID=?", (regionID[0],))
    regionName = cur.fetchone()
    region_list.append(regionName[0])

print("Creating presorted master dataframe...")
pddata = { 'Region': region_list, 'System': sys_id, 'Kills': npc_kills, }

df1 = pd.DataFrame(pddata)

jumps = []
region = []
system = []
npcs = []
print("Sorting by kills and obtaining routing data from origin system specified to top 30 systems...")
df1.sort_values(by=['Kills'], ascending=False, inplace=True)
for item in df1.head(30).itertuples():
    region.append(item.Region)
    system.append(item.System)
    npcs.append(item.Kills)
    sys = item.System
    cur.execute("SELECT solarSystemID FROM mapSolarSystems WHERE solarSystemName=?", (sys,))
    destiID = cur.fetchone()
    URLstring = "https://esi.evetech.net/latest/route/" + str(originID) + "/" + str(destiID[0]) + "/?datasource=tranquility&flag=shortest"
    get_route_json = requests.get(URLstring)
    load_route_json = get_route_json.json()
    i = len(load_route_json)
    jumps.append(i)


finaldata = { "Region": region, "System": system, "NPC Kills": npcs, "Jumps": jumps, }
print("Inserting jump data to short dataframe...")
newframe = pd.DataFrame(finaldata)
newframe.assign(region=region)
newframe.assign(system=system)
newframe.assign(kills=npcs)
newframe.assign(jumps=jumps)
newframe.reset_index()

print("\n\n\nSorted by npc kills:")
print(newframe.to_string(index=False))
newframe.sort_values(by='Jumps', ascending=True, inplace=True)
print("\n\nSorted by jumps from origin system:")
print(newframe.to_string(index=False))
