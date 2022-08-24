import socket
import os
import sys
import struct
import time
import select
from _socket import htons
from tkinter import *
#from Tkinter import * #Python version is 2.x

'''
Student name : Tian Yu      Student ID : 17722024
This is task1-ICMP Ping
@For the basic functions: The ping function can be realized correctly， and can measure delay time and report packet loss.
@For the additional functions:
1. The program can take an IP or host name as an argument.
2. Once the ping stopped, the programe can show minimum, average and maximum delay across all measurements.
3. The program has a configurable timeout, which can be entered by uesers.
4. It can measure and report packet loss.
5. The program has a configurable measurement count
5. The program can handle the icmp error types. 
@NOTE:
This programe has a User interface, which is developed under Python 3.7
The program can output on both GUI and terminal (with print).
The comments are localed in the upper side of each line.
'''

ICMP_ECHO_REQUEST = 8 # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0   # ICMP type code for echo reply messages.

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count+1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    if sys.platform == 'darwin':
        answer = htons(answer) & 0xffff
    else:
        answer = htons(answer)

    return answer

'''
receiveOnePing()
This function is to reecive icmp reply message.
It can also handle some icmp error: Network Unreachable, Host Unreachable and Port Unreachable
It also insert some message to GUI and print out them.
'''
def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    #Loop to receive, once get the reply, break the loop.
    while True:
        receive_select = select.select([icmpSocket], [], [], timeout)
        #If there is a timeout.
        if receive_select[0] == []:
            text_field.insert(INSERT, "No packet! Time out!\n")
            print("No packet! Time out!\n")
            return -1
        # Record the receive time, so as to caculate dalay.
        receive_time = time.time()
        receive_packet, address = icmpSocket.recvfrom(1024)
        # Get icmp header of the packet.
        icmp_header = receive_packet[20:28]
        # Unpack the icmp header and get information.
        icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_sequence = struct.unpack('bbHHh', icmp_header)
        # Get the time of sending the packet.
        time_send = struct.unpack("d", receive_packet[28:36])[0]
        # No icmp errors, return the delay between send and receive time.
        if icmp_type == ICMP_ECHO_REPLY and icmp_id == ID:
            text_field.insert(INSERT, "Success\n")
            print("Success\n")
            return receive_time - time_send
        # Icmp error: network unreachable.
        elif icmp_type == 3 and icmp_code == 0:
            text_field.insert(INSERT, "Network Unreachable\n")
            print("Network Unreachable\n")
            return -1
            break
        # Icmp error: host unreachable.
        elif icmp_type == 3 and icmp_code == 1:
            text_field.insert(INSERT, "Host Unreachable\n")
            print("Host Unreachable\n")
            break
        # Icmp error: port unreachable.
        elif icmp_type == 3 and icmp_code == 3:
            text_field.insert(INSERT, "Port Unreachable\n")
            print("Port Unreachable\n")
            return -1
            break
        # Other icmp errors.
        else:
            return -1
        # Jump out of the loop.
        break
    pass

'''
sendOnePing()
The function is to send one message to target address.
Also, it caculate the checksum of each packet and pack them together.
'''

def sendOnePing(icmpSocket, destinationAddress, ID):
    # Initialize the checksum.
    my_checksum = 0
    # Pack the information such as ID, sequence number and icmp code...
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    # Record the sending time, which is packed into data.
    data = struct.pack("d", time.time())
    # Build the icmp packet.
    packet = header + data
    # Put the packet into checksum()function and caculate the checksum.
    new_checksum = checksum(packet)
    # Use the new checksum to build the new icmp packet header.
    new_header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, new_checksum, ID, 1)
    # Build the final icmp packet.
    new_packet = new_header + data
    # Send the packet to target address, with a port number 80.
    icmpSocket.sendto(new_packet, (destinationAddress, 80))
    pass

'''
doOnePing()
The function initalizes the icmp socket, calls sendOnePing() function and receiveOnePing() function.
Also, it transfers the total delay into milliseconds and return it to ping() function.
'''

def doOnePing(destinationAddress, timeout):
    # Initialize the icmp socket.
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    # Get the ip address of this PC.
    my_ID = os.getpid() & 0xffff
    # Call sendOnePing() function and send packets.
    sendOnePing(icmp_socket, destinationAddress, my_ID)
    # Get the delay between sending and receiving.
    output = receiveOnePing(icmp_socket, destinationAddress, my_ID, timeout)
    # Close the icmp socket.
    icmp_socket.close()
    # Tansfer the total delay into milliseconds with 3 significant figures and return this number.
    return round(output * 1000,3)

'''
ping()
The function gives the final output on both GUI and terminal.
The function defines the measuring times, total timeout of ICMP ping.
Also, the function caculate the maximun, minimun and average delay.
'''

def ping(host, timeout, measure):
    # Get measurement time of ICMP Ping, which can be setted in GUI.
    degree = measure
    # Transfer the target host name into ip address.
    target_adress = socket.gethostbyname(host)
    # Set a list that stores the delay of each measurement.
    times = [0]*measure
    # Set a list that stores th number of timeout.
    total_timeout = [0]*measure
    # The varaible is to record the total time of delay, in order to caculate the average delay.
    total_time = 0
    # A for loop that output every measurement.
    for number in range(0, measure):
        # Call the doOneOing() function and get the delay of the measurement.
        reply = doOnePing(target_adress, timeout)
        # If no time out or other icmp errors.
        if reply != -1000:
            my_ping = str(reply)
            text_field.insert(INSERT, "The reply from " + target_adress + "  Time = " + my_ping + "ms\n")
            print("The reply from " + target_adress + "  Time = " + my_ping + "ms\n")
            times[number] = reply
            time.sleep(0.5)
            text_field.update()
        # If there is a timeout or other icmp errors.
        if reply == -1000: #There is a time out
            text_field.insert(INSERT, "The reply from [" + target_adress + "] has a time out!\n")
            print("The reply from [" + target_adress + "] has a time out!\n")
            total_timeout[number] = 1  # Record the number of time out.
            times[number] = 0
            time.sleep(0.5)
            text_field.update()
    # A for loop that get the total delay.
    for number in range(0,degree):
        total_time = total_time + times[number]
    # Get the average delay.
    average_time = str(round((total_time) / degree, 3))
    # Get the maximun delay.
    max_time = str(max(times))
    # Get the minimun delay.
    shortest = times[0]
    for n in range(1,degree):
        if times[n] < shortest:
            shortest = times[n]
    min_time = str(shortest) #The shortest time.
    lost_packet = 0
    # Get the number of lost packtes.
    for i in range(0,degree):
        lost_packet = lost_packet + total_timeout[i]
    text_field.insert(INSERT, "\nThe summarise of " +  target_adress +": \n")
    text_field.insert(INSERT, "The number of time out: "+ str(lost_packet) + "\n")
    print("\nThe number of time out: "+ str(lost_packet) + "\n")
    text_field.insert(INSERT, "The min = " + min_time + "ms" + "   The max = " + max_time + "ms" + "\nThe average = " + average_time + "ms\n")
    print("The min = " + min_time + "ms" + "   The max = " + max_time + "ms" + "\nThe average = " + average_time + "ms\n")
    pass

'''
get_input_data()
The function is trhe listener of "Start" button of GUI.
It gets the input from enter field and transfer them to ping() function.
Also, it provides a check function of input address, that is, if users enter a wrong host name, the program can tall them an input error.
Once input error occurs, the program cannot run unless users enter a correct host name.
'''

def get_input_data():
    host_name = enter_adress.get()
    time_out_number = enter_timeout.get()
    number_of_measure = enter_number_measure.get()
    time_out_number = float(time_out_number)
    number_of_measure = int(number_of_measure)
    try:
        socket.gethostbyname(host_name)
    except socket.error:
        text_field.insert(INSERT, "WRONG HOST NAME!")
        print("WRONG HOST NAME!")
        return
    text_field.insert(INSERT, "Now Ping " + host_name + " [" + socket.gethostbyname(host_name) + "] :\n")
    print("Now Ping " + host_name + " [" + socket.gethostbyname(host_name) + "] :\n")
    ping(host_name, time_out_number, number_of_measure)
    pass

'''
GUI
The GUI is developed in python 3.7, therfore, the import statements is different from python 2.7
The GUI has 3 enter field, 1 "start" button and 1 output field.
'''

# Define a frame(GUI)
top_frame = Tk()
# Title of GUI
top_frame.title("ICMP Ping Measure Tool")
# Length and width of GUI
top_frame.geometry("500x500")

# Label, which inputs host name or ip address that is going to ping.
input_adress_label = Label(top_frame, text = "IP/Host name:")
# Layout of label.
input_adress_label.grid(row = 0, column = 0, sticky = W)
# Enter field of input ip or host name.
enter_adress = Entry(top_frame, bd = 5, width = 50)
enter_adress.grid(row = 0, column = 1, sticky = W)
# Label of enter timeout.
enter_timeout_label = Label(top_frame, text = "Time out:")
enter_timeout_label.grid(row = 1, column = 0, sticky=W)
enter_timeout = Entry(top_frame, bd = 5, width = 50)
enter_timeout.grid(row = 1, column = 1, sticky = W)
# Label and enter field of measuring times
enter_number_measure_label = Label(top_frame, text = "Measuring times:")
enter_number_measure_label.grid(row = 2, column = 0, sticky = W)
enter_number_measure = Entry(top_frame, bd = 5, width = 50)
enter_number_measure.grid(row = 2, column = 1, sticky = W)

# Button of start to do ping and listener for the button.
start_measure_button = Button(text = "Start", width = 7, height = 15, command =get_input_data)
start_measure_button.grid(row = 3, column = 0)#Button

# Output
text_field = Text(top_frame, width = 51, height = 30)
text_field.grid(row = 3, column = 1)

top_frame = mainloop()
sys.exit(0)