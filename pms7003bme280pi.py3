import serial
import time
import datetime
import csv
import http.client, urllib
from Adafruit_BME280 import *
import subprocess

port = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=2.0)

def read_pm_line(_port):
    rv = b''
    while True:
        ch1 = _port.read()
        if ch1 == b'\x42':
            ch2 = _port.read() 
            if ch2 == b'\x4d':
                rv += ch1 + ch2
                rv += _port.read(28)
                return rv

# THINGSPEAK set up

def update_thingspeak(data1, data2, data3, data4, data5, data6, data7):
        params = urllib.parse.urlencode({"field1": data1, "field2": data2, "field3": data3, 
                   "field4": data4, "field5": data5, "field6": data6, "field7": data7,
                   'key':'JDHQKRAO83EPRZ5K'}) # Put your write key here.
        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = http.client.HTTPConnection("api.thingspeak.com:80")
        try:
                conn.request("POST", "/update", params, headers)
                response = conn.getresponse()
#               print(response.status, response.reason)
                data = response.read()
                conn.close()
        except:
                pass
                # error handler if needed

# End of THINGSPEAK

# Needed to open the correct outputfile for the 1st time.

old_date = "-1"

# Sleep 30 second for the PM sensor to heat up.

time.sleep(30)

# We collect data every 1 second, but THINGSPEAK can only take 15s data without
# fancy round-robin writing to several channels.  So, we only write the 15th 
# iteration to THINGSPAK.  All data are written to the output file.

iter = 0

while True:
    iter += 1
    try:

# Read the PMS7003.
        rcv = read_pm_line(port)

# Read the BMP280.
        sensor = BME280(t_mode=BME280_OSAMPLE_8, p_mode=BME280_OSAMPLE_8, h_mode=BME280_OSAMPLE_8)

        degrees = sensor.read_temperature()
        pascals = sensor.read_pressure()
        hectopascals = pascals / 100
        humidity = sensor.read_humidity()

# Set up output files
        time_now = str.split(time.ctime())
        if (time_now[2] !=  old_date):
           try:
              myfile.close()
           except:
              pass
           outfile = "/home/pi/UCD_AQ_UAV/UCD_1-" + time_now[1]+time_now[2]+time_now[4]+".txt"
           myfile = open(outfile, "a")
           wr = csv.writer(myfile)
           old_date = time_now[2]

# Pretty date/time string
        dtstr = time_now[4] + " " + time_now[0] + " " + time_now[1] +\
              " " + time_now[2] + " " + time_now[3]
#       print(dtstr)

# List of values to be written to the csv file
        res = {'timestamp': datetime.datetime.now(),
               'apm10': rcv[4] * 256 + rcv[5],
               'apm25': rcv[6] * 256 + rcv[7],
               'apm100': rcv[8] * 256 + rcv[9],
               'pm10': rcv[10] * 256 + rcv[11],
               'pm25': rcv[12] * 256 + rcv[13],
               'pm100': rcv[14] * 256 + rcv[15],
               'gt03um': rcv[16] * 256 + rcv[17],
               'gt05um': rcv[18] * 256 + rcv[19],
               'gt10um': rcv[20] * 256 + rcv[21],
               'gt25um': rcv[22] * 256 + rcv[23],
               'gt50um': rcv[24] * 256 + rcv[25],
               'gt100um': rcv[26] * 256 + rcv[27]
               }

# Measure core temperature of the RPi3B+

        proc = subprocess.Popen("/opt/vc/bin/vcgencmd measure_temp", stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        core_T = str(str(out).split("=")[1]).split("'")[0]

        mylist = [dtstr,
                  res['apm10'], res['apm25'], res['apm100'],
                  res['pm10'], res['apm25'], res['pm100'],
                  res['gt03um'], res['gt05um'], res['gt10um'],
                  res['gt25um'], res['gt50um'], res['gt100um'],
                  degrees, hectopascals, humidity, core_T]
        wr.writerow(mylist)

# Update THINGSPEAK

        if (iter == 15):
           update_thingspeak(res['pm10'], res['apm25'], res['pm100'],
                          degrees, hectopascals, humidity, core_T) 
           iter = 0

#Sleep 0.5 seconds so that time stamps are not identical for two consecutive records. 

        time.sleep(0.5)

    except KeyboardInterrupt:
        break
