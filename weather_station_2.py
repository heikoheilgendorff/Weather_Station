'''
Weather station:
        One script to rule them all...
HMH - 18/07/2018
HMH - 15/01/2019
      edit: remove wind and gas sensors and add pressure sensor
'''

import sys,time,os,urllib
import Adafruit_DHT, Adafruit_MCP3008
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import spidev
import numpy as np
from gpiozero import DigitalInputDevice
from time import sleep
import datetime,requests,json
import smtplib
from email.mime.text import MIMEText
import aqi
import platform, string
import bmp180 as bmp

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

def dust_helper():
    pm25 = []
    pm10 = []
    aqi.cmd_set_sleep(0)
    aqi.cmd_set_mode(1);
    for t in range(15):
        #print 'getting dust reading number ',t
        values = aqi.cmd_query_data();
        #print np.shape(values)
        try:
            pm25.append(values[0])
            pm10.append(values[1])
        except:
            print 'values is none'
            
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


def check_connectivity():
    status = None
    for i in range(0,10):
        print 'connectivity check attempt: ',i
        try:
            url = "https://www.google.com"
            urllib.urlopen(url)
            status = "Connected"
            if status == "Connected":
                break
        except:
            status = None
            print "no internet connection"
            time.sleep(60)
    print status

if __name__=="__main__":
    check_connectivity()
    data_loc = '/home/pi/Desktop/Weather_Station/data/'
    p = platform.system()
    if p == 'Windows':
        data_loc = string.replace(data_loc,'/','\\')
        
    error_log_name = data_loc+'error_log.txt'
    erf = open(error_log_name,'a+')
    etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    eline = 'Error log for '+etime
    erf.write('---------------------------------------------')
    erf.write('\n')
    erf.write(eline)
    erf.write('\n')
    erf.write('---------------------------------------------')
    erf.write('\n')
    erf.close()
    myname = os.uname()[1]

    print "Welcome to your local weather station." 
    
    Run = 'forever'
    while Run == 'forever': 
        timestamp = time.time() # UTC
        file_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y_%m_%d_%H_%M_%S')
        file_name = data_loc+'data_'+file_time+'.txt'
        time_interval = 24*60*60 # seconds
        time_later = time.time()

        # set operations flags:
        Temp_flag = 0
        Press_flag = 0
        Dust_flag = 0
        Error_count = 0
        try:
            # Send email to let human know I'm alive
            sendemail(from_addr = 'oddweatherstation@gmail.com',
                  to_addr_list = ['heiko@opendata.durban'],
                  subject = 'System has restarted',
                  message = 'Weather station '+myname+' has rebooted and the script is running! Recording data to '+file_name+'.',
                  login = 'oddweatherstation',
                  password = 'winteriscoming')
        except Exception as e:
            print "ERROR: Gmail doesn't like the machine"
            erf = open(error_log_name,'a+')
            etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            erf.write(etime)
            erf.write('\n')
            erf.write(str(e))
            erf.write('\n')
            erf.close()    
            
        while time_later < timestamp + time_interval:

            if Error_count > 3:
                try:
                    # Send email to let human know I'm alive
                    sendemail(from_addr = 'oddweatherstation@gmail.com',
                              to_addr_list = ['heiko@opendata.durban'],
                              subject = 'System has restarted',
                              message = 'Weather station '+myname+' has reached its max error count and will reboot.',
                              login = 'oddweatherstation',
                              password = 'winteriscoming')
                except Exception as e:
                    print "ERROR: Gmail doesn't like the machine"
                    erf = open(error_log_name,'a+')
                    etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    erf.write(etime)
                    erf.write('\n')
                    erf.write(str(e))
                    erf.write('\n')
                    erf.close()
                time.sleep(180) # pause for 3 min to give humans time to react    
                os.system('sudo reboot')

            # Pressure
            m_time = time.time()
            print "The time is...:", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            print "Checking pressure (and bonus temperature)"
            try:                
                (btemp,press) = bmp.readBmp180()
                
                press_time = time.time()
                print 'Temp={0:0.1f}*C  Pressure={1:0.1mbar}%'.format(btemp, press)
            except Exception as e:
                Error_count += 1
                print '---------------------------------------------'
                print 'ERROR: Failed to get pressure reading'
                print e
                print '---------------------------------------------'
                erf = open(error_log_name,'a+')
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                erf.close()
                if Press_flag == 0:
                    try:
                        sendemail(from_addr = 'oddweatherstation@gmail.com',
                                  to_addr_list = ['heiko@opendata.durban'],
                                  subject = 'Pressure sensor down',
                                  message = 'Weather station '+myname+' barometer is not working',
                                  login = 'oddweatherstation',
                                  password = 'winteriscoming')
                        Press_flag = 1
                    except:
                        print "ERROR: Failed to access Gmail"


                
            # Temperature and humidity:
            m_time = time.time()
            print "The time is...:", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            print "Checking temperature and humidity"
            try:                
                sensor2 = Adafruit_DHT.DHT22
                pin2=24
                humidity, temperature = get_temp_hum(sensor2,pin2)
                temp_time = time.time()
                print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
            except Exception as e:
                Error_count += 1
                print '---------------------------------------------'
                print 'ERROR: Failed to get temperature and humidity reading'
                print e
                print '---------------------------------------------'
                erf = open(error_log_name,'a+')
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                erf.close()
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
                        print "ERROR: Failed to access Gmail"
            
            # Dust
            print "Checking dust"
            try:
                pm10_array,pm25_array = dust_helper()
                pm10 = np.median(pm10_array) # 10 microns
                pm25 = np.median(pm25_array) # 2.5 microns
                dust_time = time.time()
                print 'pm 2.5 = {0:0.1f} micro_g/m^3, pm 10 = {1:0.1f} micro_g/m^3'.format(pm25,pm10)
                
            except Exception as e:
                Error_count += 1
                print '---------------------------------------------'
                print"ERROR: Failed to measure dust."
                print e
                print '---------------------------------------------'
                erf = open(error_log_name,'a+')
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                erf.close()
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
                        print "ERROR: Failed to access Gmail"
                
                        
            print 'recording data'
            f = open(file_name,'a+')
            line = str(press)+','+str(press_time)+','+str(temperature)+','+str(temp_time)+','+str(humidity)+','+str(temp_time)+','+str(pm10)+','+str(dust_time)+','+str(pm25)+','+str(dust_time)
            
            f.write(line)
            f.write('\n')
            f.close()
            
            print 'talking to server'
            # post to the village
            payload = {'pressure':press,'press_time':press_time,'temp': temperature,'temp_time':temp_time,'humid':humidity,'temp_time':temp_time,'pm_10':pm10,'dust_time':dust_time,'pm_25':pm25,'dust_time':dust_time,'ID':myname}
            headers = {'Content-Type': 'application/json', 'Accept':'application/json'}
            try:
                r = requests.post("http://citizen-sensors.herokuapp.com/ewok-village-5000", data=json.dumps(payload),headers=headers)
   
            except Exception as e:
                print "Server not listening to me - no one ever listens to me!!!"
                erf = open(error_log_name,'a+')
                etime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                erf.write(etime)
                erf.write('\n')
                erf.write(str(e))
                erf.write('\n')
                erf.close()
            time.sleep(10)
            
            time_later = time.time()
            
            


