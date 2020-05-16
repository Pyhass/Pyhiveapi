import os
import json


def open_file(file):
    path = os.getcwd() + "/tests/responses/" + file
    json_data = open(path).read()

    return json.loads(json_data)


nodes = []

t = open_file("devicelist.json")
for a in t:
    for b in t[a]:
        if "Mode" in b["HA_DeviceType"]:
            nodes.append(b["Hive_NodeID"])

print(nodes)

with open(os.getcwd() + "/tests/responses/MODES.json", "w+", encoding="utf8") as f:
    json.dump(nodes, f)
