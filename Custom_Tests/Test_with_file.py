from pyhiveapi import Pyhiveapi
import json

p = Pyhiveapi()
file = {}

print("Using File")
devices = input("Enter path for the devices file : ") or None
if devices is not None:
    JSON_File = open(devices, "r")
    devices_t = JSON_File.read()
    JSON_File.close()
    devices = json.loads(devices_t)
    file.update({"devices": {"parsed": devices}})

products = input("Enter path for the products file : ") or None
if products != None:
    JSON_File = open(products, "r")
    products_t = JSON_File.read()
    JSON_File.close()
    products = json.loads(products_t)
    file.update({"products": {"parsed": products}})
print()

result = p.initialise_api(None, None, 1, file, False)
for a_product in products:
    print(a_product["type"] + " : " + a_product["id"])
print()
node_id = input("Enter Node ID : ")
nodetype = input("Enter Node type : ")
info = p.light.get_state(node_id)
print(info)
