# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 09:16:06 2023

@author: kevin
"""


# Convert this entire thing using numpy arrays
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
import struct
import gc

# Some env variables
tdiv_enum = [100e-12, 200e-12, 500e-12, 1e-9,
 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, \
 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, \
 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, \
 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

HORI_NUM = 10

def resourcer():
    # Initialising Resource manager
    return visa.ResourceManager()

# Oscilloscope commands
def initialise(ID,rm): # Opening the Resource

    # Opening instrument
    return rm.open_resource(ID)

def main_desc(recv):
     WAVE_ARRAY_1 = recv[0x3c:0x3f + 1]
     wave_array_count = recv[0x74:0x77 + 1]
     first_point = recv[0x84:0x87 + 1]
     sp = recv[0x88:0x8b + 1]
     v_scale = recv[0x9c:0x9f + 1]
     v_offset = recv[0xa0:0xa3 + 1]
     interval = recv[0xb0:0xb3 + 1]
     code_per_div = recv[0xa4:0Xa7 + 1]
     adc_bit = recv[0xac:0Xad + 1]
     delay = recv[0xb4:0xbb + 1]
     tdiv = recv[0x144:0x145 + 1]
     probe = recv[0x148:0x14b + 1]
     data_bytes = struct.unpack('i', WAVE_ARRAY_1)[0]
     point_num = struct.unpack('i', wave_array_count)[0]
     fp = struct.unpack('i', first_point)[0]
     sp = struct.unpack('i', sp)[0]
     interval = struct.unpack('f', interval)[0]
     delay = struct.unpack('d', delay)[0]
     tdiv_index = struct.unpack('h', tdiv)[0]
     probe = struct.unpack('f', probe)[0]
     vdiv = struct.unpack('f', v_scale)[0] * probe
     offset = struct.unpack('f', v_offset)[0] * probe
     code = struct.unpack('f', code_per_div)[0]
     adc_bit = struct.unpack('h', adc_bit)[0]
     tdiv = tdiv_enum[tdiv_index]
     return vdiv, offset, interval, delay, tdiv, code, adc_bit

 def readwaveform(instr,channel=1,s_interval=1,start_point=0):
    # Setting the initial parameters
    
    # Add the points stuff here
    
    # Set the channel to be read from
    instr.write(":WAVeform:SOURce C"+str(channel))
    # Ask for preamble of that channel
    instr.write("WAV:PREamble?")
    recv_all = instr.read_raw()
    # Ask for the data from that channel
    instr.write(":WAVeform:DATA?")
    recv_rtn = instr.read_raw().rstrip()
    # Processing the preamble
    recv = recv_all[recv_all.find(b'#') + 11:]
    vdiv, ofst, interval, trdl, tdiv, vcode_per, adc_bit = main_desc(recv)
    # Procesing the data using the preamble
    block_start = recv_rtn.find(b'#')
    data_digit = int(recv_rtn[block_start + 1:block_start + 2])
    data_start = block_start + 2 + data_digit
    recv_data = list(recv_rtn[data_start:])
    convert_data =[]
    if adc_bit > 8:
        for i in range(0, int(len(recv_data) / 2)):
            data = recv_data[2 * i + 1] * 256 + recv_data[2 * i]
            convert_data.append(data)
    else:
        convert_data = recv_data
    volt_value = []
    for data in convert_data:
        if data > pow(2, adc_bit - 1) - 1:
            data = data - pow(2, adc_bit)
        else:
            pass
        volt_value.append(data)
    del recv, recv_data, convert_data
    gc.collect()
    # Time array
    time_value = []
    for idx in range(0, len(volt_value)):
        volt_value[idx] = volt_value[idx] / vcode_per * float(vdiv) - float(ofst)
        time_data = - (float(tdiv) * HORI_NUM / 2) + idx * interval + float(trdl)
        time_value.append(time_data)
    
    return volt_value,time_value
    
def burst_read(instr,channel=1,s_interval=1,start_point=0): # For reading Multiple channels quickly
    if type(channel) == int:
        readwaveform(instr,channel,s_interval,start_point)
    else:
        recv_rtn = {}
        recv_all = {}
        print("Burst Mode")
        points = instr.query(":WAV:MAXP?")
        instr.write(":WAV:POIN {}".format(points))
        instr.write(":WAV:INT {}".format(s_interval))
        instr.write(":TRIG:MOD SING")
        # Grab all the data in one stroke
        for i in range(len(channel)):
            instr.write(":WAVeform:SOURce C"+str(channel[i]))
            instr.write("WAV:PREamble?")
            # Might need delays in between for some reason
            recv_all[i] = instr.read_raw()
            instr.write(":WAVeform:DATA?")
            recv_rtn[i] = instr.read_raw().rstrip()
        instr.write(":TRIGger:RUN")    
        # Processing the channel data
        volt_value = {}
        for i in range(len(channel)): 
            # Processing the preamble
            recv = recv_all[i][recv_all[i].find(b'#') + 11:]
            vdiv, ofst, interval, trdl, tdiv, vcode_per, adc_bit = main_desc(recv)
            # Procesing the data using the preamble
            block_start = recv_rtn[i].find(b'#')
            data_digit = int(recv_rtn[i][block_start + 1:block_start + 2])
            data_start = block_start + 2 + data_digit
            recv_data = list(recv_rtn[i][data_start:])
            convert_data =[]
            #
            if adc_bit > 8:
                for i in range(0, int(len(recv_data) / 2)):
                    data = recv_data[2 * i + 1] * 256 + recv_data[2 * i]
                    convert_data.append(data)
            else:
                convert_data = recv_data
            volt_value[i] = []
            for data in convert_data:
                if data > pow(2, adc_bit - 1) - 1:
                    data = data - pow(2, adc_bit)
                else:
                    pass
                volt_value[i].append(data)
            del recv, recv_data, convert_data
            gc.collect()
            for idx in range(0, len(volt_value[i])):
                volt_value[i][idx] = volt_value[i][idx] / vcode_per * float(vdiv) - float(ofst)
        
        # Time Values
        time_value = []
        for idx in range(0, len(volt_value[i])):
            time_data = - (float(tdiv) * HORI_NUM / 2) + idx * (interval*s_interval) + float(trdl)
            time_value.append(time_data)
        
        return volt_value,time_value
    
def average_read(instr,channel=1,s_interval=1,start_point=0,averages=2): # For reading Multiple channels quickly
    if type(channel) == int:
        readwaveform(instr,channel,s_interval,start_point)
    else:
        recv_rtn = {}
        recv_all = {}
        print("Burst Mode")
        points = instr.query(":WAV:MAXP?")
        instr.write(":WAV:POIN {}".format(points))
        instr.write(":WAV:INT {}".format(s_interval))
        for j in range(averages):
            instr.write(":TRIG:MOD SING")
            recv_rtn[j] = {}
            recv_all[j] = {}
            # Grab all the data in one stroke
            for i in range(len(channel)):
                instr.write(":WAVeform:SOURce C"+str(channel[i]))
                instr.write("WAV:PREamble?")
                # Might need delays in between for some reason
                recv_all[j][i] = instr.read_raw()
                instr.write(":WAVeform:DATA?")
                recv_rtn[j][i] = instr.read_raw().rstrip()
        instr.write(":TRIGger:RUN")    
        # Processing the channel data
        volt_value = {}
        volt_buff = {}
        print("Yay done")
        for j in range(averages):
            for i in range(len(channel)): 
                # Processing the preamble
                recv = recv_all[j][i][recv_all[j][i].find(b'#') + 11:]
                vdiv, ofst, interval, trdl, tdiv, vcode_per, adc_bit = main_desc(recv)
                # Procesing the data using the preamble
                block_start = recv_rtn[j][i].find(b'#')
                data_digit = int(recv_rtn[j][i][block_start + 1:block_start + 2])
                data_start = block_start + 2 + data_digit
                recv_data = list(recv_rtn[j][i][data_start:])
                convert_data =[]
                #
                if adc_bit > 8:
                    for i in range(0, int(len(recv_data) / 2)):
                        data = recv_data[2 * i + 1] * 256 + recv_data[2 * i]
                        convert_data.append(data)
                else:
                    convert_data = recv_data
                volt_value[i] = []
                for data in convert_data:
                    if data > pow(2, adc_bit - 1) - 1:
                        data = data - pow(2, adc_bit)
                    else:
                        pass
                    volt_value[i].append(data)
                del recv, recv_data, convert_data
                gc.collect()
                if j == 0:
                    volt_buff[i] = list(volt_value[i])
                    for idx in range(0,len(volt_value[i])):
                        volt_buff[i][idx] = 0
                for idx in range(0, len(volt_value[i])):
                    volt_buff[i][idx] += volt_value[i][idx] / vcode_per * float(vdiv) - float(ofst)
                
        for j in range(len(channel)):
            for idx in range(0, len(volt_value[i])):
                volt_buff[j][idx]/=averages
        # Time Values
        time_value = []
        for idx in range(0, len(volt_value[i])):
            time_data = - (float(tdiv) * HORI_NUM / 2) + idx * (interval*s_interval) + float(trdl)
            time_value.append(time_data)
        
        return volt_buff,time_value    

def set_scale(instr,channel=None,vert=None,hori=None):
    if hori is not None:
        instr.write(":TIM:SCAL {}".format(hori))
    if vert is not None:
        if channel is not None:
            instr.write(":CHAN{}:SCAL {}".format(channel,vert))
        else:
            print("Invalid Input")
    else:
        print("Invalid Input")

def deinitialise(instr): # Close the instruments
    instr.close()


# Script goes here
if __name__ == "__main__":
    # VISA ID
    ID_oscilloscope = 'VISA ID'
        
    # Script goes here
    rm = resourcer()
    instrument = initialise(ID_oscilloscope,rm)
    #instrument.write(":WAVeform:POINt 10000000") 
    instrument.timeout = 30000 # default value is 2000(2s)
    instrument.chunk_size = 20 * 1024 * 1024 # default value is 20*1024(20k bytes)
    channel_to_be_measured = [1,2]
    #instrument.write(":TRIG:MOD SING")
    # Returns three column matrix with 2 voltage channels and 1 time array
    voltage,time = burst_read(instrument, channel_to_be_measured,s_interval = 10)
    #instrument.write(":TRIGger:RUN")
    
    my_data = [["time"]+time,["V1"]+voltage[0],["V2"]+voltage[1]]    

    Figure = plt.figure()
    for i in range(len(channel_to_be_measured)):
        plt.plot(time,voltage[i],label = "C"+str(channel_to_be_measured[i]))
        
    plt.legend()
    plt.show()
    deinitialise(instrument)
