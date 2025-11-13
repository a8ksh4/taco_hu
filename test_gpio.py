#!/usr/bin/env python3

import sys
import time


# Read from GPIO for ignition sensing


# Write to GPIO to turn amp on/off


if __name__ == '__main__':
    if 'read' in sys.argv:
        print('Reading from gpio to check car state.')
        state = None
        while True:
            # read the gpio
            if car_on and state in (False, None):
                state = True
                print('Car is on')
            elif not car_on and state in (True, None):
                state = False
                print('Car is off')
                
    elif 'write' in sys.argv:
        print("Writing to gpio to toggle amp")
        state = False
        while True:
            # write state
            if state:
                print('On...')
            else:
                print('Off...')
            time.sleep(3)

    else:
        print(f'Usage: {sys.argv[0]} [read|write]')
