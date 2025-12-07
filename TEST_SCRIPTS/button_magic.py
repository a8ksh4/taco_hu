'''This module has code to handle gpio button operations.  It's
basically a keyboard firmware, but intended to use with the taco hu 
service for hudiy!.  

We define a class here that does stuff. 
* init takes a number of buttons and a mapping defiintion.
* .update is called on button state change and/or randomly and given
   the active_buttons and current time in millisseconds and it returns
   any activations based on the provided mapping. 
   
The magic fun behavior we support here is:
* Single tap
* One, two, multiple taps for alternate operations
* Long press/hold for alternate or repeaded operations (e.g. hold to
  keep turning volume down)
* Combo/chord presses for alternate operations. (e.g. press vol up and
  down together to mute)
  
For simplicity... let's not do layers at all.  That makes this simple, right?

Development pathway:
* Start with activation on button press, don't worry about release.
* ...????????? 
'''

import time

VALID_OPERATIONS = (
    'bl_up',  # backlight up
    'bl_down',  # backlight down
    'shutdown',
    'volume_up',
    'volume_down',
    'mute',
    'play_pause',
    'next_track',
    'prev_track',
    ''
)

class ButtonMagic:
    '''Class to handle button magic operations.  In all cases,
    we depend on repeated calls to .update since we don't have any 
    timer functionality here.  We check the time on each call to 
    decide what to do'''
    def __init__(self, num_buttons, mapping, mode='simple', hold_delay=0.5, tap_delay=0.2):
        '''Initialize with button names and mapping definition'''
        self.num_buttons = num_buttons
        self.active_buttons = set()
        self.events = []
        self.mapping = mapping
        self.time = 0
        if mode == 'simple':
            self.update = self.update_simple
        elif mode == 'tap hold':
            self.update = self.update_tap_hold
      
    def update_tap_hold(self, pressed_buttons):
        '''Tap hold mode 
        If func is prefixed with r_, it will generate a repeat activation
        each time the update func is called, rate limeted to once per 200ms.
        Hold beyond hold_delay results in check for entry in a hold layer in the
        mapping.  Mapping looks like:
        [[func1, r_func2, func3, func5],
         [None,  None,    func4, r_func6]]  # hold layer
        '''
        time_s = time.ticks_ms() / 1000
        pending_activations = set(pressed_buttons) - self.active_buttons
        pending_funcs = [self.mapping[0][n] for n in pending_activations]
        pending_holds = [felf.mapping[1][n] for n in pending_activations]
        

    def update_simple(self, pressed_buttons):
        '''Simple button mode - activatoin on new button press only.
        Mapping looks like:
        [func1, func2, func3, func4, ..., funcN]'''
        time_s = time.ticks_ms() / 1000

        new_presses = set(pressed_buttons) - self.active_buttons
        activations = [self.mapping[n] for n in new_presses]
        self.active_buttons += new_presses

        return activations
    
if __name__ == '__main__':
    # Test cases defined here
    # mapping = {
    pass
