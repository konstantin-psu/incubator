#!/usr/bin/python
import RPi.GPIO as GPIO
import os
import time
import sys
import threading
import subprocess
import calendar

exitFlag = 0
lock = threading.Lock()
temp_sensor = '/sys/bus/w1/devices/28-021600a8d4ff/w1_slave'
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


def temp_raw():

    f = open(temp_sensor, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = temp_raw()
    temp_output = lines[1].find('t=')

    if temp_output != -1:
        temp_string = lines[1].strip()[temp_output+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f
# init list with pin numbers

#pinList = [02,04,14,15]
lampPin = 3

pinList = [3,14]

# loop through pins and set mode and state to 'low'


# time to sleep between operations in the main loop

SleepTimeL = 30
ideal = 97.9
low = 85
high = 96.5
lampON = False

def warmUp(f,run_event):
    global pinList
    global temp_sensor

    global lampON
    lock.acquire()
    print "Warming up"
    if not lampON:
        #print "Turning the lamp on for warmup"
        GPIO.output(3, GPIO.LOW)
        GPIO.output(14, GPIO.LOW)
        lampON = not lampON
    lock.release()
        
    while f < high and run_event.is_set():
        print str(calendar.timegm(time.gmtime())) + " " + str(f)
        sys.stdout.flush()
        time.sleep(1)
        temp = read_temp()
        f = temp[1]
            
    lock.acquire()
    try:
        if lampON:
            GPIO.output(3, GPIO.HIGH)
            GPIO.output(14, GPIO.HIGH)
            lampON = not lampON
    finally:
        lock.release()
    print "Warming up is done"

# main loop
def incubator(name, delay, run_event):
    global low
    while run_event.is_set():
        try:        
            temp = read_temp()
            f = temp[1]
            print str(calendar.timegm(time.gmtime())) + " " + str(f)
            sys.stdout.flush()
            if f < low:
                warmUp(f, run_event)
            time.sleep(1)
        except KeyboardInterrupt:
          print "  Quit"

          # Reset GPIO settings
          GPIO.cleanup()
          sys.exit(0)
    GPIO.cleanup()

def time_laps(name, delay, run_event):
    global lampON
    global pinList

    counter = 0
    timeout = 10 * 60
    #timeout = 25
    need_to_turn_off = False
    while run_event.is_set():
        lock.acquire()
        #print "the lamp is " + str(lampON) + " should turn off? " +str(need_to_turn_off)
        if not lampON:
            #print "Turning the lamp on for timelaps"
            GPIO.output(3, GPIO.LOW)
            GPIO.output(14, GPIO.LOW)
            need_to_turn_off = True

        time.sleep(1)
        #print "Taking Picture"
        com = "raspistill -o /home/pi/incubator/expreimentPic" + str(counter) +".jpg"
        counter = counter + 1
        process = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE)
        process.wait()
        #print process.returncode
        #print "Picture DONE"

        if need_to_turn_off:
            GPIO.output(3, GPIO.HIGH)
            GPIO.output(14, GPIO.HIGH)
            need_to_turn_off = False

        lock.release()
        
        time.sleep(timeout)
    GPIO.cleanup()
    

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    exp_len = 24*3*60*60

    for i in pinList: 
        GPIO.setup(i, GPIO.OUT) 
        GPIO.output(i, GPIO.HIGH)

    run_event = threading.Event()
    run_event.set()
    d1 = 1
    t1 = threading.Thread(target = incubator, args = ("bob",d1, run_event))

    d2 = 2
    t2 = threading.Thread(target = time_laps, args = ("paul",d2,run_event))

    t1.start()
    time.sleep(.5)
    t2.start()

    try:
        time.sleep(exp_len)
    except KeyboardInterrupt:
        print "attempting to close threads. Max wait =",max(d1,d2)
        run_event.clear()
        t1.join()
        t2.join()
        print "threads successfully closed"
        GPIO.cleanup()
        sys.exit(0)

    print "attempting to close threads. Max wait =",max(d1,d2)
    run_event.clear()
    t1.join()
    t2.join()
    print "threads successfully closed"
    GPIO.cleanup()
    sys.exit(0)

#thread2.start()
#for i in pinList:
#    try:
#      GPIO.output(i, GPIO.LOW)
#      print i
#      time.sleep(SleepTimeL); 
#      GPIO.output(i, GPIO.HIGH)
#
#      print "Good bye!"
#
#    # End program cleanly with keyboard
#    except KeyboardInterrupt:
#      print "  Quit"
#
#      # Reset GPIO settings
#      GPIO.cleanup()


# find more information on this script at
# http://youtu.be/oaf_zQcrg7g
