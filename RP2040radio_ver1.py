
####Working code for RDA5807 Radio with SSD1306 128x32 OLED , displays FM radio frequency

from machine import Pin,I2C
import utime , uarray

# Global Variables Initialization
data = 0  # Initialize data to an appropriate default value
scratch = 0  # Initialize scratch to an appropriate default value

FRAM_address= 0x50		# Fujitsu MB85RC256V FRAM device address , all registers are 16bit address
seqWaddress=  0x10		# RDA5807 sequential data write address
seqRaddress=   0x10		# RDA5807 sequential data read address
randomWaddress=   0x11		# RDA5807 random data write address
randomRaddress=   0x11		# RDA5807 random data read address
OLEDaddress=  0x3C		# OLED device address
command=  0x00			# this tells the OLED the next byts are device commands
data_cmd=  0x40			# this tells OLED the following bytes are data that should be displayed
last_press_time = 0		# variable to hold last press time for switch debounce logic
debounce_delay = 200  		# Set an appropriate debounce delay in milliseconds

#to be written at RDA5807 sequential data write address, initializes RDA5807 radio chip
init_RDA=uarray.array('B',[0xC1,0x03,0x00,0x00,0x0A,0x00,0x88,0x0F,0x00,0x00,0x42,0x02]) 

# OLED initialization bytes , to be sent with "command" .vertical addressing , page = 0-3, column =0-127
OLED_INIT_BYTES = uarray.array('B',[0xA8,0x1f, 0x20,0x01, 0x21,0x00, 0x7F,0x22, 0x00,0x03, 0xDA,0x02, 0x8D,0x14, 0xAF])

#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
#;FONTS   fonts below is 16X16. 0-9 and space/decimal point
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


font0=uarray.array('B',[0x00,0x00, 0xE0,0x0f, 0x10,0x10, 0x08,0x20, 0x08,0x20, 0x10,0x10, 0xE0,0x0f, 0x00,0x00])

font1=uarray.array('B',[ 0x00,0x00, 0x10,0x20, 0x10,0x20, 0xF8,0x3F, 0x00,0x20, 0x00,0x20, 0x00,0x00, 0x00,0x00])

font2=uarray.array('B',[0x00,0X00, 0x70,0X30, 0x08,0X28, 0x08,0X24, 0x08,0X22, 0x88,0X21, 0x70,0X30, 0x00,0X00])

font3=uarray.array('B',[ 0x00,0X00, 0x30,0X18, 0x08,0X20, 0x88,0X20, 0x88,0X20, 0x48,0X11, 0x30,0X0E, 0x00,0X00])

font4=uarray.array('B',[ 0x00,0X00, 0x00,0X07, 0xC0,0X04, 0x20,0X24, 0x10,0X24, 0xF8,0X3F, 0x00,0X24, 0x00,0X00])

font5=uarray.array('B',[ 0x00,0x00, 0xF8,0x19, 0x08,0x21, 0x88,0x20, 0x88,0x20, 0x08,0x11, 0x08,0x0e, 0x00,0x00])

font6=uarray.array('B',[ 0x00,0x00, 0xE0,0x0f, 0x10,0x11, 0x88,0x20, 0x88,0x20, 0x18,0x11, 0x00,0x0e, 0x00,0x00])

font7=uarray.array('B',[ 0x00,0x00, 0x38,0x00, 0x08,0x00, 0x08,0x3f, 0xC8,0x00, 0x38,0x00, 0x08,0x00, 0x00,0x00])

font8=uarray.array('B',[ 0x00,0x00, 0x70,0x1c, 0x88,0x22, 0x08,0x21, 0x08,0x21, 0x88,0x22, 0x70,0x1c, 0x00,0x00])

font9=uarray.array('B',[ 0x00,0x00, 0xE0,0x00, 0x10,0x31, 0x08,0x22, 0x08,0x22, 0x10,0x11, 0xE0,0x0f, 0x00,0x00])

fontdecimal=uarray.array('B',[ 0x00,0x00, 0x00,0x30, 0x00,0x30, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00])

fontspace=uarray.array('B',[ 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00  ])

#############################################################
#shift and OR scratch and data
def store():
    global data, scratch  # Use global variables
    buf=bytearray([0x03])                           	# RDA5807 0x03 register , bit15:6 will accept the desired channel , range 0-210 , 0=87Mhz ,210=108Mhz
    i2c.writeto(randomWaddress,buf,False)      		# write buf to set RDA5807 pointer to 0x0A
    utime.sleep(.1)
    data=i2c.readfrom(randomRaddress,2,True)   		# read 2 bytes from register 0x03 of RDA5807
    data=int.from_bytes(data, 'big')                	# 2 bytes from 0x0A IN DATA, CONVERTED to 16bit word(integer from bytes received)
    data=data & 0x003F                              	# strip the top 10 bits to write new channel data
    data=data | 0x10 					# enable tune bit in register 0x03 , bit4 to 1, resets to 0 after tune is successful
    scratch = scratch | data				# now we have the top 10bits (15:6) set with new channel and lower 6bits(5:0) with what was inherited and tune bit
    return None

###############################################################

def seekup():
    global data, scratch  # Use global variables
    buf=bytearray([0x02])                           	# RDA5807 0x02 register
    i2c.writeto(randomWaddress,buf,False)      		# write buf to set RDA5807 pointer to 0x02
    utime.sleep(.1)
    data=i2c.readfrom(randomRaddress,2,True)   		# read 2 bytes from register 0x02 of RDA5807
    data=int.from_bytes(data, 'big')               	# 2 bytes from 0x02 IN DATA, CONVERTED to 16bit word
    scratch = data                                  	# transfer contents of data to scratch
    scratch = data | 0x300                          	# station seek increase by 1 point,bit 8 and bit9 for seek up
    scratch = scratch.to_bytes(2,'big')             	# convert scratch integer to 2 bytes
    buf.extend(scratch)                             	#2 bytes in scratch tail chained with 0x02 in buffer
    i2c.writeto(randomWaddress,buf,True)       		# write to a register 0x02 msb , lsb appended in buf
    frequency = read_freq()                         	# read current frequency
    ascii_values=frequency_to_ascii(frequency)      	# convert frequency to ascii characters
    display(ascii_values)
    return None

#################################################################

def seekdown():
    global data, scratch  # Use global variables
    buf=bytearray([0x02])                           	# better than buf=bytearray(1),buf[0]=0x02
    i2c.writeto(randomWaddress,buf,False)     		# write buf to set RDA5807 pointer to 0x02
    utime.sleep(.1)
    data=i2c.readfrom(randomRaddress,2,True) 		# read 2 bytes from register 0x02 of RDA5807
    data=int.from_bytes(data, 'big')            	# 2 bytes from 0x02 IN DATA, CONVERTED to 16bit word
    scratch = data
    scratch = data | 0x100                      	# station seek decrease by 1 point
    scratch = scratch.to_bytes(2,'big')         	# convert scratch integer to 2 bytes
    buf.extend(scratch)                             	#2 bytes in scratch tail chained with 0x02 in buffer
    i2c.writeto(randomWaddress,buf,True)       		# write to a register 0x02 msb , lsb appended in buf
    frequency = read_freq()                 		# read current frequency
    ascii_values=frequency_to_ascii(frequency) 		# convert frequency to ascii characters
    display(ascii_values)
    return None
##################################################################
# Tune upward 0.1Mhz
def tune_up():
    global data, scratch  # Use global variables
    buf=bytearray([0x0A])                           	# better than buf=bytearray(1),buf[0]=0x02
    i2c.writeto(randomWaddress,buf,False)      		# write buf to set RDA5807 pointer to 0x0A
    utime.sleep(.1)
    data=i2c.readfrom(randomRaddress,2,True)   		# read 2 bytes from register 0x02 of RDA5807
    data=int.from_bytes(data, 'big')                	# 2 bytes from 0x0A IN DATA, CONVERTED to 16bit word
    scratch = data                                  	# transfer to scratch for manipulation
    scratch=scratch & 0x03ff                        	# strip upper 6 bits of the half word in scratch,lower 0-9 bits is channel
    scratch=scratch+0x01                            	# increase channel value by 1
    if scratch >=(211):     				#211+870 = 108.1Mhz which is above max channel 108mhz allowed in this band.1080-870=210
        scratch=0         				# shifted 6 to lhs,aligns with 0x03 top 10 bits 15:6
        store()
        scratch = scratch.to_bytes(2,'big')         	# convert scratch integer to 2 bytes
        buf=bytearray([0x03])                       	# load RDA5807 register to write
        buf.extend(scratch)                         	# #2 bytes in scratch tail chained with 0x03 in buffer
        i2c.writeto(randomWaddress,buf,True)   		# write buf to set RDA5807 pointer to 0x03
    else:
        scratch = scratch << 6              		# shift integer in scratch 6 poistions left to align with top 10 bits
        store()
        scratch = scratch.to_bytes(2,'big')         	# convert scratch integer to 2 bytes
        buf=bytearray([0x03])                       	# load RDA5807 register to write
        buf.extend(scratch)                         	# #2 bytes in scratch tail chained with 0x03 in buffer
        i2c.writeto(randomWaddress,buf,True)   		# write buf to set RDA5807 pointer to 0x03
    frequency = read_freq()                 		# read current frequency
    ascii_values=frequency_to_ascii(frequency) 		# convert frequency to ascii characters
    display(ascii_values)

####################################################################
# Tune downwards with 0.1Mhz
def tune_down():
    global data, scratch  # Use global variables
    buf=bytearray([0x0A])                           	# better than buf=bytearray(1),buf[0]=0x02
    i2c.writeto(randomWaddress,buf,False)      		# write buf to set RDA5807 pointer to 0x0A
    utime.sleep(.1)
    data=i2c.readfrom(randomRaddress,2,True)   		# read 2 bytes from register 0x02 of RDA5807
    data=int.from_bytes(data, 'big')                	# 2 bytes from 0x0A IN DATA, CONVERTED to 16bit word
    scratch = data                                  	# transfer to scratch for manipulation
    scratch=scratch & 0x03ff                        	# strip upper 6 bits of the half word in scratch,lower 0-9 bits is channel
    scratch=scratch-0x01                            	# decrease channel value by 1
    if scratch <(0):    				#1080-870=210 , 0= 870Khz and 200=1080Khz, if less than 0 channel is less than 87Mhz
        scratch = 210                               	# 210= 108Mhz, load highest vlue
        scratch=scratch<<6         			# shifted 6 to lhs,aligns with 0x03 top 10 bits 15:6
        store()
        scratch = scratch.to_bytes(2,'big')         	# convert scratch integer to 2 bytes
        buf=bytearray([0x03])                       	# load RDA5807 register to write
        buf.extend(scratch)                         	# #2 bytes in scratch tail chained with 0x03 in buffer
        i2c.writeto(randomWaddress,buf,True)   		# write buf to set RDA5807 pointer to 0x03
    else:
        scratch = scratch << 6              		# shift integer in scratch 6 poistions left to align with top 10 bits
        store()
        scratch = scratch.to_bytes(2,'big')         	# convert scratch integer to 2 bytes
        buf=bytearray([0x03])                       	# load RDA5807 register to write
        buf.extend(scratch)                         	# #2 bytes in scratch tail chained with 0x03 in buffer
        i2c.writeto(randomWaddress,buf,True)   		# write buf to set RDA5807 pointer to 0x03
    frequency = read_freq()                 		# read current frequency
    ascii_values=frequency_to_ascii(frequency) 		# convert frequency to ascii characters
    display(ascii_values)

###############################################################
# reads current frequency from RDA5807
def read_freq():
    global data, scratch  # Use global variables
    buf=bytearray(1)
    buf[0]=0x0A
    i2c.writeto(randomWaddress,buf,False)     		# write buf to set RDA5807 pointer to 0x0A
    utime.sleep(.1)
    data=i2c.readfrom(randomRaddress,2,True) 		# read 2 bytes from register 0x0A of RDA5807
    data=int.from_bytes(data, 'big')       		# 2 bytes from 0x0A IN DATA, CONVERTED to 16bit word
    scratch = data                             		# transfer to scratch for manipulation
    scratch=scratch & 0x03ff          			# strip upper 6 bits of the half word in scratch
    frequency = scratch + 870             		# add 870 with scratch to get current frequency in mhz
    return frequency

###############################################################
# converts frequency to ASCII array with decimal at 2nd position
def frequency_to_ascii(frequency):
    if frequency < 1000:
    # Create a string with a leading space for the thousand position
        frequency_str = " " + str(frequency)  # One leading space
    else:
        frequency_str = str(frequency)  # Convert frequency to string

    # Insert a period before the last character (unit place)
    if len(frequency_str) > 1:
        frequency_str = frequency_str[:-1] + '.' + frequency_str[-1]  # Insert '.'

    # Ensure the string has 5 characters for consistent positioning
    if len(frequency_str) < 5:
        frequency_str = " " * (5 - len(frequency_str)) + frequency_str  # Pad with spaces at the start

    ascii_values = []
    for char in frequency_str:
        ascii_values.append(ord(char))  # Convert each character to ASCII value

    return ascii_values

# Example usage
#ascii_values = frequency_to_ascii(500)
# Display the results
#print("ASCII Values:", ascii_values)

#############################################################


def display1(ascii_values):
    set_cursor_00()
    font_map = {
        '0': font0,
        '1': font1,
        '2': font2,
        '3': font3,
        '4': font4,
        '5': font5,
        '6': font6,
        '7': font7,
        '8': font8,
        '9': font9,
        '.': fontdecimal,
        ' ': fontspace,
    }
    
    for ascii_value in ascii_values:
        char = chr(ascii_value)  # Convert ASCII value back to character
        if char in font_map:
            expanded_font_bytearray = expand_font_and_return_bytearray(font_map[char])
            buf=expanded_font_bytearray
            expanded_font_bytearray=bytearray([data_cmd])
            expanded_font_bytearray.extend(buf)
            i2c.writeto(OLEDaddress, expanded_font_bytearray, True)  # Send to OLED
        else:
            print(f"Character '{char}' not in font map.")  # For debugging
################################################################
# here the function receives a list of ascii values from  frequency_to_ascii(frequency)
# display function call cursor setting function to set at coordinates 00. Then each ascii
# value is compared to the font map and appropriate font array is called and input to another function 
# that doubles the 16x16 font to 32x16 font and stores in expanded_font_bytearray. As the OLED needs the lsb
# of each byte 1st then the msb of the expanded array we call a codeblock to seperate all even and odd index bytes.
# After seperation the bytes are rearranged so that even bytes in the old array are alternately placed before the
# odd bytes in the old array. This is then transmitted to i2C.
        
def display(ascii_values):
    set_cursor_00()
    font_map = {
        '0': font0,
        '1': font1,
        '2': font2,
        '3': font3,
        '4': font4,
        '5': font5,
        '6': font6,
        '7': font7,
        '8': font8,
        '9': font9,
        '.': fontdecimal,
        ' ': fontspace,
    }
    
    rearrange_array = bytearray()  # Initialize the rearranged bytearray
    evenbuf = bytearray()
    oddbuf = bytearray()

    for ascii_value in ascii_values:
        char = chr(ascii_value)  						# Convert ASCII value back to character
        if char in font_map:
            expanded_font_bytearray = expand_font_and_return_bytearray(font_map[char])	# 16byte font array is converted to 32byte array, each byte is doubled
            
            # Append to evenbuf or oddbuf based on index of buf
            for i in range(len(expanded_font_bytearray)):
                if (i + 1) % 2 == 0:  # Even index (1-based)			# if index is even (we add 1 with index so that counting starts from 1, loop starts with 0)
                    evenbuf.append(expanded_font_bytearray[i])			# if index+1 is even we store the byte at that position to evenbuf
                else:  # Odd index (1-based)
                    oddbuf.append(expanded_font_bytearray[i])			# if index+1 is odd we store in oddbuf
        else:
            print(f"Character '{char}' not in font map.")  # For debugging

    # Rearrange even and odd buffers
    for item_a, item_b in zip(evenbuf, oddbuf):					# we use zip function as bot odd and even bufs ahve same element count
        rearrange_array.append(item_a)  # Append even item first		# 1 item from evenbuf is appended to rearrange_array
        rearrange_array.append(item_b)  # Then append odd item			# 1 item from oddbuf is appended to rearrange_array


    # If there are leftover items in evenbuf (if the length is odd)
    if len(evenbuf) > len(oddbuf):
        rearrange_array.extend(evenbuf[len(oddbuf):])  				# Add remaining even items

    # Prepare the final bytearray with the command
    final_bytearray = bytearray([data_cmd])					# final_bytearray is initiated with data_cmd which tells all trailing bytes are for screen
    final_bytearray.extend(rearrange_array)					# the rearranged bytes are appended behind the data_cmd

    # Send the final bytearray to the OLED
    i2c.writeto(OLEDaddress, final_bytearray, True)  				# Send to OLED

###############################################################



###############################################################
#Function to clear 128x4 OLED display screen
def clear_display():
    set_cursor_00()                                          			# set cursor to 0,0
    buf=bytearray([data_cmd])                                			# load data_cmd in buffer, tells oled data is being send
    buf1=bytearray([0x00]*(128*4))                   				# create a byte array of 128x4 zeros.
    buf.extend(buf1)
    i2c.writeto(OLEDaddress,buf,True)                  				# transmit data command to OLED
    
   
##############################################################
# function sets the OLED cursor to 0,0
def set_cursor_00():                                           			# positions cursor at 0,0 = x,y
    buf=bytearray([command ,0x22,0x00,0x03,0x21,0x00,0x7f]) 			# register 0x22 for Y start at 0 and end at page 3
    i2c.writeto(OLEDaddress,buf,True)                   			# register 0x21 for X cordinate, start at 0 end at 127


###############################################################

# Function to expand the font array and return a new array of 32 bytes
def expand_font_and_return_bytearray(font_array):
    expanded_array = uarray.array('B', [0] * 32)  				# Initialize a new array with 32 bytes
    index = 0  # Index for the expanded array

    for byte in font_array:
        # Process each byte as per your bit-shifting logic
        x = 0x0000  # Initialize x for each byte
        data_out = [(byte >> (7 - bit)) & 1 for bit in range(8)]  		# Extract bits from the byte

        # Iterate through bits from right to left
        for bit in reversed(data_out):
            x = (x >> 2)  # Always shift x right by 2 bits
            if bit == 1:  # Check if the bit is 1
                x |= 0xC000  # Set the two highest bits to 11

        # Convert x to bytes and fill the expanded array
        buf = x.to_bytes(2, 'big')
        expanded_array[index] = buf[0]  # Store the first byte
        index += 1
        expanded_array[index] = buf[1]  # Store the second byte
        index += 1

    # Convert the expanded array to bytearray for I2C transfer
    return bytearray(expanded_array)
# Expand the font and get the new bytearray for I2C transfer
# USAGE ==== expanded_font_bytearray = expand_font_and_return_bytearray(font0)


#################################################################
# function reads the current frequency and writes to FRAM MB85RC256V
def shutdown():
    frequency = read_freq()                     # read current frequency
    buf=bytearray([0x00,0x00])                  # 16bit register of FRAM
    frequency=frequency.to_bytes(2,'big')       # convert frequency integer to 2 bytes
    buf.extend(frequency)                       # add the frequency to the buffer
    i2c.writeto(FRAM_address,buf,True)     # write buf to set FRAM register 0x0000

#####################################################################

# Switch Initializations
tuneup_sw=machine.Pin(0,mode=Pin.IN,pull=Pin.PULL_UP) # tune up switch
tunedn_sw=machine.Pin(1,mode=Pin.IN,pull=Pin.PULL_UP) # tune down switch
seekup_sw=machine.Pin(2,mode=Pin.IN,pull=Pin.PULL_UP) # seek up switch
seekdn_sw=machine.Pin(3,mode=Pin.IN,pull=Pin.PULL_UP) # seek down switch
pwr_sw=machine.Pin(4,mode=Pin.IN,pull=Pin.PULL_UP)    # shutdown switch , signal used to store channel in FRAM

# I2C Initialization
i2c = I2C(id=0,scl=Pin(9),sda=Pin(8),freq=100_000)

# Initialize OLED
buf=bytearray([command])                                #create a bytearray with i element and assign as buf
buf.extend(bytearray(OLED_INIT_BYTES))
i2c.writeto(OLEDaddress,buf,True)         # write oed command 0x00 , no stop
utime.sleep(.5)                                 # 500ms delay

# Initialize RDA5807 radio
buf=bytearray(init_RDA)                         #create a bytearray from init_RDA and reassign buf
i2c.writeto(seqWaddress,buf,True)          # write RDA5807 init bytes, send stop
utime.sleep(.5)
buf=bytearray([0x02,0xc1,0x01])                 # RDA register 0x02 ,high byte , low byte for enabling radio
i2c.writeto(randomWaddress,buf,True)
buf=bytearray([0x03,0x2b,0x10])                 # RDA register 0x03 ,high byte  channel, low byte for enabling tune
i2c.writeto(randomWaddress,buf,True)
utime.sleep(.5)
clear_display()
tune_up()
tune_down()

while True:
    current_time = utime.ticks_ms()
    if not tuneup_sw.value():           # if tuneup sw is 0
        if(current_time - last_press_time) > debounce_delay:
            tune_up()
            last_press_time = current_time

    if not tunedn_sw.value():           # if tunedn sw is 0
        if(current_time - last_press_time) > debounce_delay:
            tune_down()
            last_press_time = current_time

    if not seekup_sw.value():           # if seekup sw is 0
        if(current_time - last_press_time) > debounce_delay:
            seekup()
            last_press_time = current_time

    if not seekdn_sw.value():           # if seekdn sw is 0
        if(current_time - last_press_time) > debounce_delay:
            seekdown()
            last_press_time = current_time

    if not pwr_sw.value():           # if pwr sw is 0
        if(current_time - last_press_time) > debounce_delay:
            shutdown()
            last_press_time = current_time

    utime.sleep(0.1)
