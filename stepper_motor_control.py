import RPi.GPIO as GPIO
import time
# The numbers are the pun numbers of the GPIO pins on the pi
DIR = 11 #pulses when set to 0 + moves 1 step
CLK = 13 #direction, 0 = CCW, 1 = CW
ENA = 15 #0 = off, 1 = on
delay = 0.000001 # the clock pulses + time between them has to be this many seconds minimum

trash = 40 # of steps to take
recycling = 80
compost = 120
stuff = {"trash": trash, "recycling":recycling, "compost": compost}

def initialize_gpio():
    GPIO.setmode(GPIO.BOARD) #as opposed to GPIO.BCM, which uses a different pin numbering scheme
    for pin in [CLK, DIR, ENA]:
      GPIO.setup(pin, GPIO.OUT)

def move(category, direction):
    GPIO.output(ENA, 1) # turn it on
    GPIO.output(DIR, direction) # set direction
    for x in range(stuff[category]):
        GPIO.output(CLK, 1)
        time.sleep(delay)
        GPIO.output(CLK, 0)
        time.sleep(delay)
    GPIO.output()

def main():
    initialize_gpio()
    while True:
        try:
            category = input() #replace this with function for receiving actual classification, should also
                          #wait on this line
            move(category, 1)
            #something with the linear actuator
            time.sleep(1) #placeholder, we need a delay for motor to change direction probably
            move(category, 0)
        except KeyboardInterrupt:
            GPIO.cleanup()
            exit()
main()
