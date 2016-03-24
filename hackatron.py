
import json
import pandas as pd
import numpy as np
import itertools

def main():

    threshold_val = 0.625

    # Read in the txt file 
    txt_input_frame = pd.read_table('signal', names=["values"]) 
   
    # Decode the signals to HI's and LO's 
    txt_input_frame['bin_values'] = txt_input_frame['values'].apply(lambda x: threshold(x, threshold_val))

    RE_count_list, AE_count_list = edge_counter(txt_input_frame)

    translated_reader_message = reader_pramble_finder(RE_count_list)

    decoded_reader_message = reader_message_decoder(translated_reader_message)

    
    
    print(translated_reader_message)
    print(AE_count_list)

def edge_counter(txt_input_frame):

    RE_count_list =[]
    AE_count_list =[]
    RE_counter = 0
    AE_counter = 0
    prev_val = 0

    # Count the samples taken between '01' combinations. Essentially counting samples between rising edges
    for i in range(len(txt_input_frame['bin_values'])):

        if ((txt_input_frame['bin_values'][i] == 1))&(prev_val == 0):       #rising edge
            RE_count_list.append(RE_counter)
            AE_count_list.append(AE_counter)
            RE_counter = 0
            AE_counter = 0
        elif((txt_input_frame['bin_values'][i] == 0))&(prev_val == 1):      #falling edge
            AE_count_list.append(AE_counter)
            AE_counter = 0
            RE_counter+=1
        else:
            RE_counter+=1
            AE_counter+=1
        prev_val = txt_input_frame['bin_values'][i]

    return RE_count_list, AE_count_list

    # Finds the preables and returns the Tari
def reader_pramble_finder(count_list):

    reader_translated_message = []
    tari = 0
    pramble_check = count_list[:2]

    for val in count_list[2:]:
         
         # Check for the unique preamble sequence
        if( (pramble_check[1] >= 2.5*pramble_check[0]) & (pramble_check[1] <= 3.0*pramble_check[0])): 

            tari = pramble_check[0]  
            print(tari)
            reader_translated_message.append('Preamble')       
            
       
        reader_translated_message.append(message_decoder(val, tari))

        pramble_check.append(val)                   # Add the new value to the end of the list
        pramble_check = pramble_check[1:]           # Slice off the oldest value 

    return reader_translated_message
    


    # Takes the count_list segment and decides the realtive message encoded 
def message_decoder(val, tari):

    # error of 10%
    error = tari*0.1               
    
    # if the value is within the bounds of our tari it in taken as data-0
    if((val>tari-error)&(val<tari+error)):          
        decoded_val = 0

    # if the value is within the bounds of 1.5*tari < val < 2*tari (plus errors) it is taken as data-1
    elif((val>tari*1.5-error)&(val<tari*2+error)):
        decoded_val = 1

    else:
        # raise ValueError('Value not within desired range')
        decoded_val = 'x'


    return decoded_val

    # Take the translated reader message and decide the real physical message
def reader_message_decoder(translated_reader_message):

    # Split the full message into the individual parts
    key = lambda sep: sep == 'Preamble'
    message_list = [list(group) for is_key, group in itertools.groupby(translated_reader_message, key) if not is_key]
    
    trimmed_message_list = []

    for message in message_list:
        target_index = message.index('x')

        trimmed_message_list.append(message[:target_index])

    # Match the parts to the what they mean

    

    


# Decode the input value to HI or LO on the thereshold value
def threshold(input_val, threshold_val):

    if(input_val>=threshold_val):
        return 1
    elif( input_val< threshold_val):
        return 0 


if __name__ == "__main__":
    main()