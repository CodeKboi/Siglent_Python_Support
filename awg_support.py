# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 19:58:32 2023

@author: kevin
"""

import pyvisa as visa


ID_signalgenerator = 'USB0::0xF4EC::0x1102::SDG2XFBC7R0480::INSTR'

def resourcer():
    # Initialising Resource manager
    return visa.ResourceManager()

# Oscilloscope commands
def initialise(ID,rm): # Opening instrument
        return rm.open_resource(ID)

def set_wave(instr,channel=1,form=None,freq=None,amp=None): # Creates the signal generator code
    parameter_count = 0
    basic_query = "C{}:BSWV ".format(channel)
    forms = ["SINE", "SQUARE", "RAMP", "PULSE", "NOISE", "ARB", "DC", "PRBS", "IQ"]
    # Creating the string for transmission
    if form is not None:
        if form not in forms:
            print("Valid Arguments for form are :",forms)
            return
        basic_query += "WVTP,{},".format(form)
        parameter_count+=1
    if freq is not None:
        basic_query += "FRQ,{},".format(freq)
        parameter_count+=1
    if amp is not None:
        basic_query += "AMP,{},".format(amp)
        parameter_count+=1
    if parameter_count > 0:
        final_query = basic_query.rstrip(",")
        instr.write(final_query)
    else:
        print("No Parameters Specified")
        return
    
def set_output_state(instr,channel=1,val="OFF"): # Setting the output state
    instr.write("C{}:OUTP {}".format(channel,val))

def deinitialise(instr): # Close the instruments
    instr.close()

# Script goes here
if __name__ == "__main__":
    # VISA ID
    ID_signalgenerator = 'VISA ID'
        
    # Script goes here
    rm = resourcer()
    instrument = initialise(ID_signalgenerator,rm)
    set_wave(inst_awg,form = "SINE" ) 
    deinitialise(instrument)
