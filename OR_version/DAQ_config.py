
from usb_1208FS import *
import time
import sys
import fcntl
import os
import math
from psychopy import core

def initDAQ():
    # Identify DAQ
    port = usb_1208FS()
    # Initialize - configure both ports fo routput
    port.DConfig(port.DIO_PORTA, port.DIO_DIR_OUT)
    port.DConfig(port.DIO_PORTB, port.DIO_DIR_IN)
    return port 

def sendTrigger(port, trigger):
    #rest_hex = int(hex(0), 16)
    reset_int = 0 
    port.DOut(port.DIO_PORTA, trigger)
    core.wait(0.05)
    port.DOut(port.DIO_PORTA, reset_int)

def testDAQ():
    # Init DAQ
    port = initDAQ()
    # Test digital I/O
    print('Testing Digital I/O ...')
    print('Connect pins 21 through 28 <--> 32 through 39  (Port A to Port B)')
    # Send a 45 through port 
    num_hex = int(hex(100), 16)
    usb1208FS.DOut(usb1208FS.DIO_PORTA, num_hex)
    # Send int through port
    num_int = 45
    usb1208FS.DOut(usb1208FS.DIO_PORTA, num_int)
    return   