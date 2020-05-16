from pyhiveapi import Hive

a = Hive()
token = '7e/HpjiVI320n4+bq7G9aepVPUfuwWsbEOROE114nLE='

# token
t = a.remove_token("VKkzHJhFtFOFalo6uinTzj/wHZm/YjClljqNlbGnirk=",
                   "82a7cd0c-cd8a-4f12-91ac-5f9e20a4b87c")
# devices = await a.initialise_api(20, token, None, None)
# devices = a.initialise_api(
#    30, None, 'khole_47@hotmail.co.uk', 'Aubree01062017')
print(t)
print("Complete")
