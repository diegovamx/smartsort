import RPi.GPIO as GPIO
import time
# The numbers are the pun numbers of the GPIO pins on the pi
DIR = 17 #direction, 0 = CCW, 1 = CW
DIR_maybe = 11
CLK = 27 #pulses when set to 0 + moves 1 step
CLK_maybe = 13
ENA = 22 #0 = off, 1 = on
ENA_maybe = 15
SOL = 18 #controls solenoid, 0 = down, 1 = up? idk it might be the opposite
SOL_maybe = 12
delay = 0.000001 # the clock pulses + time between them has to be this many seconds minimum
linear_actuator_delay = 1 #idk

trash = 40 # of steps to take
recycling = 80
compost = 120
num_and_dir_steps = {"trash": (trash, 1), "recycling":(recycling, 1), "compost": (compost, 1)}

def initialize_gpio():
    GPIO.setmode(GPIO.BCM) #as opposed to GPIO.BCM, which uses a different pin numbering scheme
    for pin in [CLK, DIR, ENA, SOL, DIR_maybe, CLK_maybe, ENA_maybe, SOL_maybe]:
      GPIO.setup(pin, GPIO.OUT)

def move(steps, direction):
    GPIO.output(ENA, 1) # turn it on
    GPIO.output(ENA_maybe, 1)
    GPIO.output(DIR, direction) # set direction
    GPIO.output(DIR_maybe, direction)
    for x in range(steps):
        GPIO.output(CLK, 1)
        GPIO.output(CLK_maybe, 1)
        time.sleep(delay)
        GPIO.output(CLK, 0)
        GPIO.output(CLK_maybe, 0)
        time.sleep(delay)
    GPIO.output(SOL, 1)
    GPIO.output(SOL_maybe, 1)
    time.sleep(linear_actuator_delay)
    GPIO.output(SOL, 0)
    GPIO.output(SOL_maybe, 0)
    GPIO.output(ENA, 0)
    GPIO.output(ENA_maybe, 0)

def main():
    initialize_gpio()
    print("initializegpio")
    while True:
        try:
            category = input() #replace this with function for receiving actual classification, should also
                          #wait on this line
            move(*num_and_dir_steps[category])
            #something with the linear actuator
            time.sleep(1) #placeholder, we need a delay for motor to change direction probably
            move(num_and_dir_steps[category][0], not num_and_dir_steps[category][1])
        except KeyboardInterrupt:
            GPIO.cleanup()
            exit()
main()
