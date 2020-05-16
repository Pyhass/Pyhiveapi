from pyhiveapi import Pyhiveapi

HiveAPI = Pyhiveapi()
heating = Pyhiveapi.Heating()
hotwater = Pyhiveapi.Hotwater()
light = Pyhiveapi.Light()
sensor = Pyhiveapi.Sensor()
switch = Pyhiveapi.Switch()
weather = Pyhiveapi.Weather()

HiveUserName = "Your_Hive_UserName"
HivePassword = "Your_Hive_Password"
UpdateIntervalInMinutes = 2

print("Attempt to log in to the Hive API")
api_device_list_all = {}
api_device_list_all = HiveAPI.initialise_api(HiveUserName, HivePassword, UpdateIntervalInMinutes)

if len(api_device_list_all) == 0:
    print("**** Return from initialise_api :: None")
else:
    api_device_list_sensor = []
    api_device_list_climate = []
    api_device_list_light = []
    api_device_list_plug = []

    if 'device_list_sensor' in api_device_list_all:
        api_device_list_sensor = api_device_list_all["device_list_sensor"]

    if 'device_list_climate' in api_device_list_all:
        api_device_list_climate = api_device_list_all["device_list_climate"]

    if 'device_list_light' in api_device_list_all:
        api_device_list_light = api_device_list_all["device_list_light"]

    if 'device_list_plug' in api_device_list_all:
        api_device_list_plug = api_device_list_all["device_list_plug"]

    Heating_Name_Zone_1 = "Downstairs"
    Heating_Name_Zone_2 = "Upstairs"
    
    HubID = ""
    HotwaterNodeID = ""
    Heating_NodeID_SingleZone = ""
    Heating_NodeID_Zone_1 = ""
    Heating_NodeID_Zone_2 = ""


    for adevice in api_device_list_sensor:
        print("sensor :: " + str(adevice["Hive_NodeName"]) + " : " + str(adevice["HA_DeviceType"]) + " : " + str(adevice["Hive_NodeID"]))
        
    for adevice in api_device_list_climate:
        print("climate :: " + str(adevice["Hive_NodeName"]) + " : " + str(adevice["HA_DeviceType"]) + " : " + str(adevice["Hive_NodeID"]))
        if str(adevice["HA_DeviceType"]) == "HotWater" and str(adevice["Hive_NodeName"]) == "None":
            HotwaterNodeID = str(adevice["Hive_NodeID"])
        if str(adevice["HA_DeviceType"]) == "Heating" and str(adevice["Hive_NodeName"]) == "None":
            Heating_NodeID_SingleZone = str(adevice["Hive_NodeID"])
        if str(adevice["HA_DeviceType"]) == "Heating" and str(adevice["Hive_NodeName"]) == Heating_Name_Zone_1:
            Heating_NodeID_Zone_1 = str(adevice["Hive_NodeID"])
        if str(adevice["HA_DeviceType"]) == "Heating" and str(adevice["Hive_NodeName"]) == Heating_Name_Zone_2:
            Heating_NodeID_Zone_2 = str(adevice["Hive_NodeID"])

    print("")
    print("")
    
    if Heating_NodeID_SingleZone != "":
        print("Attempt to get heating current temperature")
        Heating_Current = heating.current_temperature(Heating_NodeID_SingleZone)
        print("Heating Current = " + str(Heating_Current))
        
        print("Attempt to get heating target temperature")
        Heating_Target = heating.get_target_temperature(Heating_NodeID_SingleZone)
        print("Heating Target = " + str(Heating_Target))

        print("Attempt to get heating mode")
        Heating_Mode = heating.get_mode(Heating_NodeID_SingleZone)
        print("Heating Mode = " + str(Heating_Mode))

        print("Attempt to get heating state")
        Heating_State = heating.get_state(Heating_NodeID_SingleZone)
        print("Heating State = " + str(Heating_State))
        
        print("Attempt to get heating boost")
        Heating_Boost = heating.get_boost(Heating_NodeID_SingleZone)
        print("Heating Boost = " + str(Heating_Boost))
        
        print("")
        print("Attempt to set heating boost for 5 minutes at 17.5c")
        Heating_Boost = heating.turn_boost_on(Heating_NodeID_SingleZone, 5, 17.5)
        print("Heating Boost On = " + str(Heating_Boost))
        
        print("")
        
        print("Attempt to get heating target temperature")
        Heating_Target = heating.get_target_temperature(Heating_NodeID_SingleZone)
        print("Heating Target = " + str(Heating_Target))
        
        print("Attempt to get heating boost")
        Heating_Boost = heating.get_boost(Heating_NodeID_SingleZone)
        print("Heating Boost = " + str(Heating_Boost))
        
        print("Attempt to get heating remaining boost time")
        print("Boost ends in " + str(heating.get_boost_time(Heating_NodeID_SingleZone)) + " minutes")
        
    if Heating_NodeID_Zone_1 != "":
        print("Attempt to get " + Heating_Name_Zone_1 + " heating current temperature")
        Heating_Current = heating.current_temperature(Heating_NodeID_Zone_1)
        print("Heating " + Heating_Name_Zone_1 + " Current = " + str(Heating_Current))
    
    if Heating_NodeID_Zone_2 != "":
        print("Attempt to get " + Heating_Name_Zone_2 + " heating current temperature")
        Heating_Current = heating.current_temperature(Heating_NodeID_Zone_2)
        print("Heating " + Heating_Name_Zone_2 + " Current = " + str(Heating_Current))

    print("")

    print("Attempt to get Outside temperature")
    Weather_Temperature = weather.temperature()
    print("Outside Temperature = " + str(Weather_Temperature))

    print("")
    print("Update Data")
    result = HiveAPI.update_data(Heating_NodeID_SingleZone)
    print("Update Data result = " + str(result))
    print("An update result of False = data is cached and a Hive API call was not made")
    print("An update result of True = Hive API called data was retrieved and cached")
