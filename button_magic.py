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

class ButtonMagic:
    '''Class to handle button magic operations'''
    def __init__(self, num_buttons, mapping):
        '''Initialize with button names and mapping definition'''
        self.buttons = [False for _ in range(num_buttons)]
        self.mapping = mapping
        self.time = 0
        

    def update(self, active_buttons, current_time_ms):
        '''Update button states and return activations'''
        activations = []
        # Update internal button states based on active_buttons
        for name in self.button_names:
            self.button_states[name] = name in active_buttons
        
        # Process the mapping definition to determine activations
        # This is where the magic happens based on taps, holds, combos, etc.
        # For now, we will just return an empty list
        return activations