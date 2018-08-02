'''
Weather station:
        One script to rule them all...
HMH - 18/07/2018
'''

import sys,time,os,urllib
import Adafruit_DHT, Adafruit_MCP3008
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import spidev
import numpy as np
from gpiozero import DigitalInputDevice
from time import sleep
#import math
#import subprocess
import datetime,requests,json
import smtplib
from email.mime.text import MIMEText
import simple_read_windspeed as srw
import read_gas as rg
import aqi
import platform, string

def sendemail(from_addr, to_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    header = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()
    return problems

def get_temp_hum(sensor,pin):
    t_array = np.zeros(10)
    h_array = np.zeros(10)
    for i in range(0,len(t_array)):
        h_array[i], t_array[i] = Adafruit_DHT.read_retry(sensor, pin)
    humidity = np.median(h_array)
    temperature = np.median(t_array)
    return humidity, temperature


def windspeed_helper():
    count = 0
    wind_speed_sensor = srw.DigitalInputDevice(5)
    wind_speed_sensor.when_activated = srw.spin
    time_interval = 4*60 # seconds
    time_later = time.time()
    timestamp = time.time()
    wind_array = []
    while time_later < timestamp + time_interval:
        srw.count = 0
        srw.sleep(5)
        instantaneous_windspeed = srw.get_windspeed()
        if count == 1:
            instantaneous_windspeed = 0.0
        wind_array.append(instantaneous_windspeed)
        time_later = time.time()
    #windspeed = srw.calculate_speed(5)
    #wind_array = simple_read_windspeed.wind_val
    #windspeed = np.mean(wind_array)
    #print "value from anemometer: ",wind_array
    return wind_array

def dust_helper():
    pm25 = []
    pm10 = []
    aqi.cmd_set_sleep(0)
    aqi.cmd_set_mode(1);
    for t in range(15):
        values = aqi.cmd_query_data();
        if values is not None:
            pm25.append(values[0])
            pm10.append(values[1])
            time.sleep(2)
    #print pm10
    #print pm25
    #print("Going to sleep for 5min...")
    aqi.cmd_set_mode(0);
    aqi.cmd_set_sleep()
    #time.sleep(300)
    return pm10,pm25


def read_analog(numSamples,pinVal):
    #Hardware SPI configuration:
    SPI_PORT = 0
    SPI_DEVICE = 0
    mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

    # Choose GPIO pin - not actually sure if we need this, but leaving it in for meow
    ledPin = 18

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ledPin,GPIO.OUT)

    samplingTime = 280.0
    deltaTime = 40.0
    sleepTime = 9680.0
    
    return_array = []
    try: 
        for i in range(0,numSamples):
            GPIO.output(ledPin,0)
            time.sleep(samplingTime*10.0**-6)
            # The read_adc function will get the value of the specified channel
            voMeasured = mcp.read_adc(pinVal)
            time.sleep(samplingTime*10.0**-6)
            GPIO.output(ledPin,1)
            time.sleep(samplingTime*10.0**-6)
            calcVoltage = voMeasured*(5.0/1024)
            return_array.append(calcVoltage)
            time.sleep(1)

    except KeyboardInterrupt:
        GPIO.cleanup()
    return return_array

def gas_helper():
    helper = rg.GPIOHelper()
    x = helper.readMQ135()
    return x


def check_connectivity():
    status = None
    while status == None:
        try:
            url = "https://www.google.com"
            urllib.urlopen(url)
            status = "Connected"
        except:
            status = None
            print "no internet connection"
            time.sleep(60)
    print status

if __name__=="__main__":
    check_connectivity()
    error_log_name = 'error_log.txt'
    erf = open(error_log_name,'a')
    myname = os.uname()[1]
    try:
        # Send email to let human know I'm alive
        sendemail(from_addr = 'oddweatherstation@gmail.com',
                  to_addr_list = ['heiko@opendata.durban'],
                  subject = 'System has restarted',
                  message = 'Weather station '+myname+' has rebooted and the script is running!',
                  login = 'oddweatherstation',
                  password = 'winteriscoming')
    except Exception as e:
        print "Gmail doesn't like the machine"
        etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        erf.write(etime)
        erf.write('\n')
        erf.write(str(e))
        erf.write('\n')
    erf.close()    
    print "Welcome to your local weather station." 

    # set operations flags:
    Temp_flag = 0
    WS_flag = 0
    WD_flag = 0
    Gas_flag = 0
    Dust_flag = 0

    # prep for wind direction stuff
    directions = {3.84:'N',1.98:'NNE',2.25:'NE',0.41:'ENE',0.45:'E',0.32:'ESE',0.90:'SE',0.62:'SSE',1.40:'S',1.19:'SSW',3.08:'SW',2.93:'WSW',4.62:'W',4.04:'WNW',4.78:'NW',3.43:'NNW'}
    #d = {3.84:'N',1.98:'NNE',2.25:'NE',0.41:'ENE',0.45:'E',0.32:'ESE',0.90:'SE',0.62:'SSE',1.40:'S',1.19:'SSW',3.08:'SW',2.93,4.62,4.04,4.78,3.43}
    d = directions.keys()
    sortd = np.sort(d)
    midp = (sortd[1:] + sortd[:-1])/2
    midp = np.insert(midp,0,0)
    midp = np.insert(midp,len(midp),5.0)
        
    data_loc = '/home/pi/Desktop/Weather_Station/data/'
    p = platform.system()
    if p == 'Windows':
        data_loc = string.replace(data_loc,'/','\\')

    Run = 'forever'
    while Run == 'forever': 
        timestamp = time.time() # UTC
        file_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y_%m_%d_%H_%M_%S')
        file_name = data_loc+'data_'+file_time+'.txt'
        f = open(file_name,'a')
        erf = open(error_log_name,'a')
        time_interval = 24*60*60 # seconds
        time_later = time.time()

        while time_later < timestamp + time_interval:
    
            # Temperature and humidity:
            m_time = time.time()
            print "The time is...:", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            print "Checking temperature and humidity"
            try:
                sensor2 = Adafruit_DHT.DHT22
                pin2=24
                humidity, temperature = get_temp_hum(sensor2,pin2)
                print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
            except Exception as e:
                print 'Failed to get temperature and humidity reading'
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                if Temp_flag == 0:
                    try:
                        sendemail(from_addr = 'oddweatherstation@gmail.com',
                                  to_addr_list = ['heiko@opendata.durban'],
                                  subject = 'Temperature sensor down',
                                  message = 'Weather station '+myname+' temperature gauge is not working',
                                  login = 'oddweatherstation',
                                  password = 'winteriscoming')
                        Temp_flag = 1
                    except:
                        print "Failed to access Gmail"
            
            # Gas
            print "Checking gas"
            try:
                gas_array = read_analog(numSamples=10,pinVal=1) # returns a voltage that can be calibrated with RS and RL etc to produce a ppm value. While uncalibrated, it simply tells you if there's a lot of pollution in the air or not. Voltage ranges from 0 - 5 V corresponding to low to high air pollution.
                #gas_array = gas_helper()
                gas = np.median(gas_array)
                print 'Gas = {0:0.1f}'.format(gas)
            except Exception as e:
                print "We have a gas issue..."
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                
                if Gas_flag == 0:
                    try:
                        sendemail(from_addr = 'oddweatherstation@gmail.com',
                                  to_addr_list = ['heiko@opendata.durban'],
                                  subject = 'Gas sensor down',
                                  message = 'Weather station '+myname+' gas gauge is not working',
                                  login = 'oddweatherstation',
                                  password = 'winteriscoming')
                        Gas_flag = 1
                    except:
                        print "Failed to access Gmail"
            # Dust
            print "Checking dust"
            try:
                pm10_array,pm25_array = dust_helper()
                pm10 = np.median(pm10_array) # 10 microns
                pm25 = np.median(pm25_array) # 2.5 microns
                print 'pm 2.5 = {0:0.1f} micro_g/m^3, pm 10 = {1:0.1f} micro_g/m^3'.format(pm25,pm10)
            except Exception as e:
                print"Failed to measure dust."
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                if Dust_flag == 0:
                    try:
                        sendemail(from_addr = 'oddweatherstation@gmail.com',
                                  to_addr_list = ['heiko@opendata.durban'],
                                  subject = 'Dust sensor down',
                                  message = 'Weather station '+myname+' dust gauge is not working',
                                  login = 'oddweatherstation',
                                  password = 'winteriscoming')
                        Dust_flag = 1
                    except:
                        print "Failed to access Gmail"
                
            # Windspeed
            print "Checking wind speed"
            try:
                windspeed_array = windspeed_helper()
                windspeed = np.median(windspeed_array)
                print 'Wind={0:0.1f} kph'.format(windspeed)
            except Exception as e:
                print 'Failed to detect windspeed'
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                if WS_flag == 0:
                    try:
                        sendemail(from_addr = 'oddweatherstation@gmail.com',
                                  to_addr_list = ['heiko@opendata.durban'],
                                  subject = 'Wind speed sensor down',
                                  message = 'Weather station '+myname+' windspeed gauge is not working',
                                  login = 'oddweatherstation',
                                  password = 'winteriscoming')
                        WS_flag = 1
                    except:
                        print "Failed to access Gmail"
    
            # Wind Direction
            print "Checking wind direction"
            try:
                wind_dir_array = read_analog(numSamples=10,pinVal=3)
                windval = np.median(wind_dir_array)
                c = round(windval,2)
                for i in range(1,len(midp)-1):
                    beg = midp[i-1]
                    end = midp[i+1]
                    if c > 3.90 and c < 3.95: # mechanical glitch
                        direction = 4.78
                        break
                    elif c > beg and c < end:
                        direction = sortd[i]
                        break
                    
                
                winddir = directions.get(direction)
                print 'Wind direction = {0:0.1f}'.format(windval), winddir
            except Exception as e:
                print "Failed to measure wind direction"
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                if WD_flag == 0:
                    try:
                        sendemail(from_addr = 'oddweatherstation@gmail.com',
                                  to_addr_list = ['heiko@opendata.durban'],
                                  subject = 'Wind direction sensor down',
                                  message = 'Weather station '+myname+' wind direction gauge is not working',
                                  login = 'oddweatherstation',
                                  password = 'winteriscoming')
                        WD_flag = 1
                    except:
                        print "Failed to access Gmail"
            
            print 'recording data'
            line = str(temperature)+','+str(humidity)+','+str(windspeed)+','+str(winddir)+','+str(gas)+','+str(pm10)+','+str(pm25)+','+str(m_time)
            
            f.write(line)
            f.write('\n')

            print 'talking to server'
            # post to the village
            payload = {'temp': temperature,'humid':humidity,'rain' : 0.0, 'press': 0.0}
            headers = {'Content-Type': 'application/json', 'Accept':'application/json'}
            try:
                r = requests.post("http://citizen-sensors.herokuapp.com/ewok-village-5000", data=json.dumps(payload),headers=headers)
   
            except Exception as e:
                print "Server not listening to me - no one ever listens to me!!!"
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
            
            time.sleep(10)
            time_later = time.time()
            
            
        f.close()
        erf.close()
