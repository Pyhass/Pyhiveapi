from pyhiveapi import Hive2fa

u = Hive2fa(username='khole_47@hotmail.co.uk', password='romhYq-facbyk-tehzi2')

test = u.authenticate_user()

print(test)
