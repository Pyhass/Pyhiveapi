from pyhiveapi import Session

token = '7e/HpjiVI320n4+bq7G9aepVPUfuwWsbEOROE114nLE='

a = Session()
loop = a.initialise_api(50, token, None, None)

print(loop)
print("Complete")
