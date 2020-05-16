from pyhiveapi.hive_session import Session

p = Session()

print("Using Sign on")
username = input("Enter username : ") or None

password = input("Enter password: ") or None


result = p.initialise_api(30, None, username, password)
print(result)
