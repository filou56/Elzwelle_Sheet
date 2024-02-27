import configparser
import gc
import os
import platform
import time
import tkinter
import uuid
import socket
import gspread
import paho.mqtt.client as paho
from paho import mqtt

# Google Spreadsheet ID for publishing times
# Elzwelle        SPREADSHEET_ID = '1obtfHymwPSGoGoROUialryeGiMJ1vkEUWL_Gze_hyfk'
# FilouWelle      SPREADSHEET_ID = '1M05W0igR6stS4UBPfbe7-MFx0qoe5w6ktWAcLVCDZTE'
SPREADSHEET_ID = '1M05W0igR6stS4UBPfbe7-MFx0qoe5w6ktWAcLVCDZTE'

# How many time stamps should be stored and shown on the web page
KEEP_NUM_TIME_STAMPS = 20

# host name (or IP address) for the web server
# copy-paste from the internet
# TODO: do not crash when network is unreachable.
HOST_NAME = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

# some global variables

time_stamps_start  = ['00:00:00 | {:10.2f} |  0'.format(0.0).replace(".",",")] * KEEP_NUM_TIME_STAMPS
time_stamps_finish = ['00:00:00 | {:10.2f} |  0'.format(0.0).replace(".",",")] * KEEP_NUM_TIME_STAMPS

# 12.01.2024 WF
time_stamps_start_dirty  = True
time_stamps_finish_dirty = True

update_time_stamp        = False
serial_time_stamp        = 0

serial_time_stamp_start  = 0
serial_time_stamp_finish = 0

#-------------------------- table utils ----------------------------

def start_update_number(stamp, number):
    global time_stamps_start
    global time_stamps_start_dirty
    
    #for line in time_stamps_start:
    for i in range(len(time_stamps_start)):
        data = time_stamps_start[i].split('|')
        start_stamp = data[1].strip()
        
        if start_stamp == stamp.strip():
            time_stamps_start[i] = '{:} | {:>10} | {:>2}'.format(data[0].strip(),
                                                               start_stamp,
                                                               number.strip())  
            time_stamps_start_dirty = True
            print("Update: ",time_stamps_start[i])
    
def finish_update_number(stamp, number):
    global time_stamps_finish
    global time_stamps_finish_dirty
    
    #for line in time_stamps_start:
    for i in range(len(time_stamps_finish)):
        data = time_stamps_finish[i].split('|')
        finish_stamp = data[1].strip()
        
        if finish_stamp == stamp.strip():
            time_stamps_finish[i] = '{:} | {:>10} | {:>2}'.format(data[0].strip(),
                                                                finish_stamp,
                                                                number.strip())  
            time_stamps_finish_dirty = True
            print("Update: ",time_stamps_finish[i])
        
#-------------------------------------------------------------------
# Define the GUI
#-------------------------------------------------------------------
class simpleapp_tk(tkinter.Tk):
    def __init__(self,parent):
        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.grid()

        #Add a label with the text leftbound black font(fg) on white background(bg) at (0,0) over 2 columns,
        #sticking to the left and to the right of the cell
        self.labelVariable = tkinter.StringVar()
        label = tkinter.Label(self,textvariable=self.labelVariable,anchor="w",fg="black",bg="white")
        label.grid(row=0,column=0,columnspan=2,sticky="EW")

        #Add a label that says 'Start' at (1,0)
        label1 = tkinter.Label(self,text="Start",relief=tkinter.SUNKEN)
        label1.grid(row=1,column=0,sticky="EW")

        #Add a label that says 'Ziel' at (1,1)
        label2 = tkinter.Label(self,text="Ziel",relief=tkinter.SUNKEN)
        label2.grid(row=1,column=1,sticky="EW")
        
        self.startTimeStampsMessage = tkinter.Message(self,text="",
                                                      relief=tkinter.SUNKEN,
                                                      font='TkFixedFont')
        self.startTimeStampsMessage.grid(row=2,column=0,sticky="EW")
        
        self.finishTimeStampsMessage = tkinter.Message(self,text="",
                                                       relief=tkinter.SUNKEN,
                                                       font='TkFixedFont')
        self.finishTimeStampsMessage.grid(row=2,column=1,sticky="EW")

        #Make the first column (0) resize when window is resized horizontally
        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=1)

        #Make the user only being able to resize the window horrizontally
        self.resizable(True,True)

    def refresh(self):
        global time_stamps_start_dirty 
        global time_stamps_finish_dirty
        global update_time_stamp
        global serial_time_stamp
        
        self.labelVariable.set("{} | {}".format(HOST_NAME, time.strftime("%H:%M:%S")))
                      
        if time_stamps_start_dirty:
            message = ""
            for t in time_stamps_start:
                message += t + "\n"
            self.startTimeStampsMessage.config(text=message)
            time_stamps_start_dirty = False

        if time_stamps_finish_dirty:
            message = ""
            for t in time_stamps_finish:
                message += t + "\n"
            self.finishTimeStampsMessage.config(text=message)
            time_stamps_finish_dirty = False
              
        gc.collect()
        self.after(500, self.refresh)

#-------------------------------------------------------------------

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )

        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)
    
    # subscribe to all topics of encyclopedia by using the wildcard "#"
    client.subscribe("elzwelle/stopwatch/#", qos=1)
    
    # a single publish, this can also be done in loops, etc.
    client.publish("elzwelle/monitor", payload="running", qos=1)
    

FIRST_RECONNECT_DELAY   = 1
RECONNECT_RATE          = 2
MAX_RECONNECT_COUNT     = 12
MAX_RECONNECT_DELAY     = 60

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        print("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            print("Reconnected successfully!")
            return
        except Exception as err:
            print("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    print("Reconnect failed after %s attempts. Exiting...", reconnect_count)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )

        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing

        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    global time_stamps_start_dirty 
    global time_stamps_finish_dirty
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )

        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    #print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    
    payload = msg.payload.decode('utf-8')
    
    if msg.topic == 'elzwelle/stopwatch/start':
        try:
            data = payload.split(' ')
            message = '{:} | {:>10} | {:>2}'.format(data[0].strip(),
                                                  data[1].strip(),
                                                  data[2].strip())
            time_stamps_start.insert(0,message)
            while( len(time_stamps_start) > KEEP_NUM_TIME_STAMPS):
                time_stamps_start.pop()
            time_stamps_start_dirty = True
        except:
            print("MQTT Decode exception: ",msg.payload)
        

    if msg.topic == 'elzwelle/stopwatch/finish':
        try:
            data = payload.split(' ')
            message = '{:} | {:>10} | {:>2}'.format(data[0].strip(),
                                                  data[1].strip(),
                                                  data[2].strip())
            time_stamps_finish.insert(0,message)
            while( len(time_stamps_finish) > KEEP_NUM_TIME_STAMPS):
                time_stamps_finish.pop()
            time_stamps_finish_dirty = True
        except:
            print("MQTT Decode exception: ",msg.payload)
            
    if msg.topic == 'elzwelle/stopwatch/start/number':       
        try:
            data   = payload.split(' ')
            time   = data[0].strip()
            stamp  = data[1].strip()
            number = data[2].strip()
            message = '{:} | {:>10} | {:>2}'.format(time,stamp,number)
            cell = wks_start.find(stamp)
            if cell != None:
                print("ROW: ",cell.row)     
                wks_start.update_cell(cell.row,3,number)
                start_update_number(stamp, number)
                mqtt_client.publish("elzwelle/stopwatch/start/number/akn", 
                            payload='{:} {:} {:}'.format(time,stamp,number), 
                            qos=1)
            else:
                print("Stamp not found: ",payload)
                mqtt_client.publish("elzwelle/stopwatch/start/number/error", 
                            payload='{:} {:} {:}'.format(time,stamp,number), 
                            qos=1)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
    
    if msg.topic == 'elzwelle/stopwatch/finish/number':       
        try:
            data   = payload.split(' ')
            time   = data[0].strip()
            stamp  = data[1].strip()
            number = data[2].strip()
            message = '{:} | {:>10} | {:>2}'.format(time,stamp,number)
            cell = wks_finish.find(stamp)
            if cell != None:
                print("ROW: ",cell.row)     
                wks_finish.update_cell(cell.row,3,number)    
                finish_update_number(stamp, number)
                mqtt_client.publish("elzwelle/stopwatch/finish/number/akn", 
                            payload='{:} {:} {:}'.format(time,stamp,number), 
                            qos=1)
            else:
                print("Stamp not found: ",payload)
                mqtt_client.publish("elzwelle/stopwatch/finish/number/error", 
                            payload='{:} {:} {:}'.format(time,stamp,number), 
                            qos=1)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
    
    if msg.topic == 'elzwelle/stopwatch/start/get':       
        try:
            data = payload.split(' ')
            message = '{:} | {:10.2f} | {:>2}'.format(data[0].strip(),
                                                    float(data[1]),
                                                    data[2].strip())
            cell = wks_start.find(data[2].strip())
            if cell != None:
                print("ROW: ",cell.row,"COL: ",cell.col)     
            else:
                print("Entry not found: ",payload)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
                    
    if msg.topic == 'elzwelle/stopwatch/finish/get':       
        try:
            data = payload.split(' ')
            message = '{:} | {:10.2f} | {:>2}'.format(data[0].strip(),
                                                    float(data[1]),
                                                    data[2].strip())
            cell = wks_finish.find(data[2].strip())
            if cell != None:
                print("ROW: ",cell.row,"COL: ",cell.col)     
            else:
                print("Entry not found: ",payload)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
#-------------------------------------------------------------------
# Main program
#-------------------------------------------------------------------
if __name__ == '__main__':    
    GPIO = None
   
    myPlatform = platform.system()
    print("OS in my system : ", myPlatform)
    myArch = platform.machine()
    print("ARCH in my system : ", myArch)

    config = configparser.ConfigParser()
   
    config['google'] = {
        'spreadsheet_id':SPREADSHEET_ID,
        'client_secret_json':'./client_secret.json',
    }
    
    config['mqtt']   = { 
        'url':'144db7091e4a45cbb0e14506aeed779a.s2.eu.hivemq.cloud',
        'port':8883,
        'tls_enabled':'yes',
        'user':'welle',
        'password':'elzwelle', 
    }
    
    # Platform specific
    if myPlatform == 'Windows':
        # Platform defaults
        config.read('windows.ini') 
    if myPlatform == 'Linux':
        config.read('linux.ini')

    google_client = gspread.service_account(filename=config.get('google','client_secret_json'))
    
    # Open a sheet from a spreadsheet in one go
    wks_start = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(0)
    #print("Ranges: ",gc.open("timestamp").list_protected_ranges(0))
    # Open a sheet from a spreadsheet in one go
    wks_finish = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(1)

    # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
    # userdata is user defined data of any type, updated by user_data_set()
    # client_id is the given name of the client
    mqtt_client = paho.Client(client_id="elzwelle_"+str(uuid.uuid4()), userdata=None, protocol=paho.MQTTv311)

    # enable TLS for secure connection
    if config.get('mqtt','tls_enabled'):
        mqtt_client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    mqtt_client.username_pw_set(config.get('mqtt','user'),
                                config.get('mqtt','password'))
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    mqtt_client.connect(config.get('mqtt','url'), config.getint('mqtt','port'))

    # setting callbacks, use separate functions like above for better visibility
    mqtt_client.on_connect      = on_connect
    mqtt_client.on_subscribe    = on_subscribe
    mqtt_client.on_message      = on_message
    mqtt_client.on_publish      = on_publish
    
    mqtt_client.loop_start()
       
    # setup and start GUI
    app = simpleapp_tk(None)
    app.title("MQTT Tabelle Elz-Zeit")
    app.refresh()
    app.mainloop()
    print(time.asctime(), "GUI done")
          
    # Stop all dangling threads
    os.abort()