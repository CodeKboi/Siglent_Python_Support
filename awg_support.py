# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 19:58:32 2023

@author: kevin

Arbitrary Waveform Generator Support for SDG2082X specifically but it can be
used with other models with no or little tinkering in this module

"""

"""
TODOs:
    1. Add Arbitrary Wavegeneration Code By File
    2. Add Arbitrary Wavegeneration Code By Numpy Array
    3. Add Remaining Basic Wavetypes on set wave
    4. Add Descriptions for each of the functions
"""

import pyvisa as visa
import numpy as np

def resourcer():
    """
    Initialising Resource manager. It manages all the instruments connected 
    to the system
    
    Parameters
    ----------
        None
    
    Returns
    -------
    ResourceManager
        
    
    Usage
    -----
        rm = resourcer()
        
    """
    return visa.ResourceManager()

# Oscilloscope commands
def initialise(ID:str,rm):
    """
    Initiliases a particular resource given a VISA ID
    Pass any invalid string to list all available resources
    
    Parameters
    ----------
        ID : str 
        rm : ResourceManager
    
    Returns
    -------
        Instrument object 
        
        or 
        
        Lists available resources
        
    Usage
    -----
        instrument = initialise(ID,rm) # rm is defined by resourcer()
        
    """
    avail_res = rm.list_resources()
    if ID in avail_res:
        return rm.open_resource(ID)
    else:
        print("These are the available resources:")
        print(avail_res)
        print("You can use the *IDN? command to check your connection.")

# TODOs : 3. Add Remaining Basic Wavetypes on set wave

def set_wave(instr,
             channel:int=1,
             form=None,
             val=None,
             freq=None,
             period=None,
             amp=None,
             mean=None,
             stdev=None,
             noise_bw=None,
             offset=None,
             duty=None,
             hlev=None,
             llev=None,
             width=None): # Creates the signal generator code 
    '''
    Sets an in-built waveform with required 
    parameters to specified channel.
    
    Currently does not support PULSE ARB PRBS IQ

    Parameters
    ----------
    instr : TYPE
        DESCRIPTION.
    channel : int, optional
        DESCRIPTION. The default is 1.
    form : str, optional
        Specify the waveform type. 
        Select from SINE SQUARE RAMP PULSE NOISE ARB DC PRBS IQ. 
        The default is None.
    val : TYPE, optional
        DESCRIPTION. The default is None.
    freq : TYPE, optional
        DESCRIPTION. The default is None.
    period : TYPE, optional
        DESCRIPTION. The default is None.
    amp : TYPE, optional
        DESCRIPTION. The default is None.
    mean : TYPE, optional
        DESCRIPTION. The default is None.
    stdev : TYPE, optional
        DESCRIPTION. The default is None.
    noise_bw : TYPE, optional
        DESCRIPTION. The default is None.
    offset : TYPE, optional
        DESCRIPTION. The default is None.
    duty : TYPE, optional
        DESCRIPTION. The default is None.
    hlev : TYPE, optional
        DESCRIPTION. The default is None.
    llev : TYPE, optional
        DESCRIPTION. The default is None.
    width : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    None.
    
    Usage
    -----
        set_wave(instrument,form = "SINE") 

    '''
    
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
        
    if form == forms[1]: # Square
        if duty is not None:
            basic_query += "DUTY,{},".format(duty)
            parameter_count+=1
            
    elif form == forms[2]: # Ramp
        if duty is not None:
            basic_query += "DUTY,{},".format(duty)
            parameter_count+=1
    elif form == forms[3]: # Pulse
        if period is not None:
            basic_query += "PERI,{},".format(period)
            parameter_count+=1
        if width is not None:
            basic_query += "WIDTH,{},".format(width)
            parameter_count+=1
        if hlev is not None:
            basic_query += "HLEV,{},".format(hlev)
            parameter_count+=1
        if llev is not None:
            basic_query += "LLEV,{},".format(llev)
            parameter_count+=1
            
    elif form == forms[4]: # noise
        if mean is not None:
            basic_query += "MEAN,{},".format(mean)
            parameter_count+=1
        if stdev is not None:
            basic_query += "STDEV,{},".format(stdev)
            parameter_count+=1
        if noise_bw is not None:
            basic_query += "BANDWIDTH,{},".format(noise_bw)
            parameter_count+=1
      
    # Other elif options    
    elif form == forms[6]: # DC
        if val is not None:
            basic_query += "OFST,{},".format(val)
            parameter_count+=1
    else:   
        if freq is not None:
            basic_query += "FRQ,{},".format(freq)
            parameter_count+=1
        if amp is not None:
            basic_query += "AMP,{},".format(amp)
            parameter_count+=1
        if offset is not None:
            basic_query += "OFST,{},".format(offset)
            parameter_count+=1

    if parameter_count > 0:
        final_query = basic_query.rstrip(",")
        instr.write(final_query)
    else:
        print("No Parameters Specified")
        return

# TODOs : 1. Add Arbitrary Wavegeneration Code By File

# TODOs : 2. Add Arbitrary Wavegeneration Code By Numpy Array
def arb_wave_constructor(instr,
                         wave,
                         dt,
                         freq = None,
                         channel=1,
                         wave_name='wave1',
                         offset=0.0,
                         phase=0.0):
    '''
    Sets an user-specified waveform from a numpy array
    with the time array

    Parameters
    ----------
    instr : TYPE
        DESCRIPTION.
    wave : TYPE
        DESCRIPTION.
    dt : TYPE
        DESCRIPTION.
    freq : TYPE, optional
        DESCRIPTION. The default is None.
    channel : TYPE, optional
        DESCRIPTION. The default is 1.
    wave_name : TYPE, optional
        DESCRIPTION. The default is 'wave1'.
    offset : TYPE, optional
        DESCRIPTION. The default is 0.0.
    phase : TYPE, optional
        DESCRIPTION. The default is 0.0.

    Raises
    ------
    RuntimeError
        DESCRIPTION.

    Returns
    -------
    None.
    
    Usage
    -----
        arb_wave_constructor(instrument,wave,dt) 

    '''

    # Encoding the wave into bytes
    vpp = max(abs(wave))
    if freq == None:
        dt = dt[1]-dt[0]
        freq = 1/dt

    if freq > 75e6: # This is for 2082 only
        raise RuntimeError("Exceeds sampling rate")
        
    wave_digitised = np.floor(wave/vpp*0x7FFF)
    wave_digitised[wave_digitised<0] += 0x10000 
    f = open("wave1.bin", "wb") 
    for a in wave_digitised: 
        b = int(a).to_bytes(2, "little")
        f.write(b) 
    f.close()
    f = open("wave1.bin", "rb")   
    data = f.read()
    f.close() 
    # Writing the wave into the generator
    query = f"C{channel}:WVDT WVNM,{wave_name},AMPL,{2*vpp},OFST,{offset},PHASE,{phase},WAVEDATA,"
    instr.write_raw(query.encode('ascii')+data)    
    #"X" series (SDG1000X/SDG2000X/SDG6000X/X-E) 
    instr.write("C{}:SRATE MODE,TARB,VALUE,{}".format(channel,freq))
    instr.write("C{}:ARWV NAME,{}".format(channel,wave_name))     

def set_output_state(instr,channel:int=1,val:str="OFF"):
    '''
    Sets the output state of a specified channel

    Parameters
    ----------
    instr : TYPE
        DESCRIPTION.
    channel : int, optional
        DESCRIPTION. The default is 1.
    val : str, optional
        DESCRIPTION. The default is "OFF".

    Returns
    -------
    None.
    
    Usage
    -----
        set_output_state(instrument,1,"ON") # to turn on
        set_output_state(instrument,1,"OFF") # to turn on

    '''
    instr.write("C{}:OUTP {}".format(channel,val))

def deinitialise(instr):
    '''
    Closes the instrument or resourcemanager
    Must be done at the end of the session or opening a new session

    Parameters
    ----------
    instr : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    
    Usage
    -----
        deinitialise(instrument)

    '''
    instr.close()

# Script goes here
if __name__ == "__main__":
    # VISA ID
    ID_signalgenerator = 'VISA ID'
    # Script goes here
    rm = resourcer()
    instrument = initialise(ID_signalgenerator,rm)
    set_wave(instrument,form = "SINE" ) 
    deinitialise(instrument)
