# Wireless Networking RFID Challenge
# Jack Mackintosh - 4537475
# Danielle van der Werff - 4422171


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
    translated_tag_message = tag_pramble_finder(AE_count_list)

    trimmed_reader_message = message_trimmer(translated_reader_message)
    trimmed_tag_message = message_trimmer(translated_tag_message)    
    
    # combine into 1 list
    # for i,v in enumerate(trimmed_tag_message):
    #     trimmed_reader_message.insert(2*i+1,v)

    # works on one element at a time
    for i in range(len(trimmed_reader_message)):
    	reader_type = reader_command_decoder(trimmed_reader_message[i])
        print 'Reader message type:', reader_type
        print 'Tag message type:', tag_command_decoder(reader_type, trimmed_tag_message[i])

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

    # Finds the preables of the reader and returns the Tari
def reader_pramble_finder(count_list):

    reader_translated_message = []
    tari = 0
    pramble_check = count_list[:2]

    for val in count_list[2:]:
         
         # Check for the unique preamble sequence
        if( (pramble_check[1] >= 2.5*pramble_check[0]) & (pramble_check[1] <= 3.0*pramble_check[0])): 

            tari = pramble_check[0]  
            reader_translated_message.append('Preamble')       
            
       
        reader_translated_message.append(reader_message_decoder(val, tari))

        pramble_check.append(val)                   # Add the new value to the end of the list
        pramble_check = pramble_check[1:]           # Slice off the oldest value 

    return reader_translated_message
    
    # Finds the preambles of the tag
def tag_pramble_finder(count_list):

	# Note: not sure if line below is a fair assumption
	pw = min(count_list) 		# Pulse width 

	tag_translated_message = []
	temp = []
	
	# Make temp array with decoded bitstream
	i = 0
	while i < len(count_list):	
	
		value = tag_message_decoder(count_list[i],pw)
		temp.append(value)		

		# if current element is data-0, check if next element is part of it too
		# if not, it is a 'v' (violation) 
		if ((value == 0) & (i < len(count_list)-1)):
			if (tag_message_decoder(count_list[i+1],pw) == 0): 	
				i+=1
		i+=1
	
	# Look for preamble combination in the bitstream
	# If found, replace sequence with 'Preamble'
	i = 0
	while i < len(temp):
		if (i < len(temp)-5):
			if ([temp[i],temp[i+1],temp[i+2],temp[i+3],temp[i+4],temp[i+5]] == [1,0,1,0,'v',1]):
				tag_translated_message.append('Preamble')
				i += 5
				continue
				
		tag_translated_message.append(temp[i])
		i += 1 
		
	return tag_translated_message

	# Takes the count_list segment and decides the relative message encoded
def tag_message_decoder(val, pw):
	
	# Error is a bit arbitrary now, we may have to choose a better error margin
	error = 0.1
	
	# if the value is approximately 2 times the pulse width it is taken as data-1
	if ((val/pw <= 2 + error) & (val/pw >= 2 - error) ): 
		decoded_val = 1
	
	# if the value is approximately equal to the pulse width it is taken as data-0 
	elif ((val/pw <= 1 + error) & (val/pw >= 1 - error)):
		decoded_val = 0
		
    # raise ValueError('Value not within desired range')
	else:
		decoded_val = 'v'
			
	return decoded_val

	


    # Takes the count_list segment and decides the realtive message encoded 
def reader_message_decoder(val, tari):

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
        decoded_val = 'v'


    return decoded_val

    # Take the translated reader message and decide the real physical message
def message_trimmer(translated_reader_message):

    # remove everything up to the first preabmle 
    target_index = translated_reader_message.index('Preamble')
    translated_reader_message = translated_reader_message[target_index:]

    # Split the full message into the individual parts
    key = lambda sep: sep == 'Preamble'
    message_list = [list(group) for is_key, group in itertools.groupby(translated_reader_message, key) if not is_key]
    
    trimmed_message_list = []

    for message in message_list:
        
        if 'v' in message:
            target_index = message.index('v')
        else:
            target_index = np.size(message)
        trimmed_message_list.append(message[:target_index])
            
    return trimmed_message_list

    # takes the bit stream and decides the command, works on one element at a tiem
def reader_command_decoder(trimmed_reader_message):

	if(trimmed_reader_message[:2]==[0,0]):
		reader_type = 'QueryRep'
	elif(trimmed_reader_message[:2]==[0,1]):
		reader_type = 'ACK'
	elif(trimmed_reader_message[:4]==[1,0,0,0]):
		reader_type = 'Query'
	elif(trimmed_reader_message[:4]==[1,0,0,1]):
		reader_type = 'QueryAdjust'
	elif(trimmed_reader_message[:4]==[1,0,1,0]):
		reader_type = 'Select'
	elif(trimmed_reader_message[:4]==[1,0,1,1]):
		reader_type = '-'
	elif(trimmed_reader_message[:8]==[1,1,0,0,0,0,0,0]):
		reader_type = 'NAK'
	elif(trimmed_reader_message[:8]==[1,1,0,0,0,0,0,1]):
		reader_type = 'Req_RN'
	elif(trimmed_reader_message[:8]==[1,1,0,0,0,0,1,0]):
		reader_type = 'Read'
	elif(trimmed_reader_message[:8]==[1,1,0,0,0,0,1,1]):
		reader_type = 'Write'
	else:
		raise ValueError('Error, command not recognised. Error is string')

	return reader_type
	
	# takes the reader and tag bitstream and decides the command
def tag_command_decoder(reader_type, trimmed_tag_message):

	# Tag response depends on reader message and tag state.
	# For full scalability of the script, the code below should be 
	# extended significantly to be able to decode all possible tag type options,
	# and the tag state should be included. This is left for future work.
	if(reader_type == 'QueryRep'):
		tag_type = 'To be implemented'
		
	elif(reader_type == 'ACK'):
		
		# This is only one of the 32 options for responses to ACK
		if(trimmed_tag_message[:5] == [1,0,0,1,1]):
			tag_type = 'Disallowed'
		else:
			tag_type = 'To be implemented'
		
	elif(reader_type == 'Query'):
		tag_type = 'To be implemented'
		
	elif( reader_type == 'QueryAdjust'):
		 tag_type = 'To be implemented'
		 
	elif(reader_type == 'Select'):
		 tag_type = 'To be implemented'
		 
	elif(reader_type == '-'):
		 tag_type = 'To be implemented'
		 
	elif(reader_type == 'NAK'):
		tag_type = 'To be implemented'
		
	elif(reader_type == 'Req_RN'):
	   	tag_type = 'Backscatter handle'
	   	
	elif(reader_type == 'Read'):
	   	tag_type = 'To be implemented'
	   	
	elif(reader_type == 'Write'):
		tag_type = 'To be implemented'
		
	else:
		raise ValueError('Error, command not recognised. Error is string')

	return tag_type	

# Decode the input value to HI or LO on the thereshold value
def threshold(input_val, threshold_val):

	if(input_val>=threshold_val):
		return 1
	elif( input_val< threshold_val):
		return 0 


if __name__ == "__main__":
	main()
