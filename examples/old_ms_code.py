            now = datetime.now()

            start_date = str(now.day) + '.' + str(now.month) + \
                '.' + str(now.year) + ' 00:00:00'
            fromepoch = self.epochtime(start_date, None, 'to_epoch') * 1000
            end_date = str(now.day) + '.' + str(now.month) + '.' \
                + str(now.year) + ' 23:59:59'
            toepoch = self.epochtime(end_date, None, 'to_epoch') * 1000
            for sensor in Data.products:
                if Data.products[sensor]["type"] == "motionsensor":
                    p = Data.products[sensor]
                    resp = self.api.motion_sensor(Data.sess_id, p,
                                                  fromepoch, toepoch)

                    if str(resp['original']) == "<Response [200]>":
                        if len(resp['parsed']) > 0 and 'inMotion' \
                                in resp['parsed'][0]:
                            p["props"]["motion"]["status"] = resp['parsed'][0][
                                'inMotion']

                        self.log.log('core_http',
                                     "Sensor " + p["state"]["name"] +
                                     " - " + "HTTP call successful : " +
                                     resp['original'])
                    else:
                        self.log.log('core_http', "Sensor " +
                                     p["state"]["name"] + " - " +
                                     "HTTP call failed : " +
                                     resp['original'])