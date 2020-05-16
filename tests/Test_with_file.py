
from pyhiveapi import Pyhiveapi
import json

HiveAPI = Pyhiveapi()
HiveDevice = Pyhiveapi.Light()

print('Using File')
devices = (input("Enter path for the devices file : ") or None)
if devices != None:
    JSON_File = open(devices, 'r')
    devices_t = JSON_File.read()
    JSON_File.close()
    devices = json.loads(devices_t)

products = (input("Enter path for the products file : ") or None)
if products != None:
    JSON_File = open(products, 'r')
    products_t = JSON_File.read()
    JSON_File.close()
    products = json.loads(products_t)
print()

for a_product in products:
    print(a_product["type"] + " : " + a_product["id"])
print()
node_id = input("Enter Node ID : " )
nodetype = input("Enter Node type : " )
result = HiveAPI.test_use_file(devices, products)
info = HiveDevice.set_color_temp(node_id, nodetype, new_color_temp=370)
print(info)