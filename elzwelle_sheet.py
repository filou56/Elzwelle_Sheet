import configparser
import gc
import os
import platform
import time
import locale
import tkinter
from   tkinter import ttk
import uuid
#import socket
#import gspread
import paho.mqtt.client as paho
from paho import mqtt
#from table import TableCanvas
from tksheet import Sheet
from bCNC.lib.log import null

# Google Spreadsheet ID for publishing times
# Elzwelle        SPREADSHEET_ID = '1obtfHymwPSGoGoROUialryeGiMJ1vkEUWL_Gze_hyfk'
# FilouWelle      SPREADSHEET_ID = '1M05W0igR6stS4UBPfbe7-MFx0qoe5w6ktWAcLVCDZTE'
SPREADSHEET_ID = '1M05W0igR6stS4UBPfbe7-MFx0qoe5w6ktWAcLVCDZTE'

startSheet = null

#-------------------------------------------------------------------
# Define the GUI
#-------------------------------------------------------------------
class sheetapp_tk(tkinter.Tk):
    def __init__(self,parent):
        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def noop(self):
        return

    def initialize(self):
        noteStyle = ttk.Style()
        noteStyle.theme_use('default')
        noteStyle.configure("TNotebook", background='lightgray')
        noteStyle.configure("TNotebook.Tab", background='#eeeeee')
        noteStyle.map("TNotebook.Tab", background=[("selected", '#005fd7')],foreground=[("selected", 'white')])
        
        self.geometry("1000x400")
        self.tabControl = ttk.Notebook(self) 
        self.tabControl
          
        self.startTab = ttk.Frame(self.tabControl) 
        self.finishTab = ttk.Frame(self.tabControl)
        self.courseTab = ttk.Frame(self.tabControl)
        self.inputTab = ttk.Frame(self.tabControl) 
        
        self.tabControl.add(self.startTab, text ='Start') 
        self.tabControl.add(self.finishTab, text ='Ziel') 
        self.tabControl.add(self.courseTab, text ='Strecke') 
        self.tabControl.add(self.inputTab, text ='Eingabe') 
        self.tabControl.pack(expand = 1, fill ="both") 
         
        #----- Start Page -------
                 
        self.startTab.grid_columnconfigure(0, weight = 1)
        self.startTab.grid_rowconfigure(0, weight = 1)
        self.startSheet = Sheet(self.startTab,
                           #data = [['00:00:00','0,00','',''] for r in range(2)],
                           header = ['Uhrzeit','Zeitstempel','Startnummer','Kommentar'])
        self.startSheet.enable_bindings()
        self.startSheet.grid(column = 0, row = 0)
        self.startSheet.grid(row = 0, column = 0, sticky = "nswe")
        self.startSheet.span('A:').align('right')
        
        self.startSheet.disable_bindings("All")
        self.startSheet.enable_bindings("edit_cell","single_select")
        
        #----- Finish Page -------
                 
        self.finishTab.grid_columnconfigure(0, weight = 1)
        self.finishTab.grid_rowconfigure(0, weight = 1)
        self.finishSheet = Sheet(self.finishTab,
                           #data = [['00:00:00','0,00','',''] for r in range(200)],
                           header = ['Uhrzeit','Zeitstempel','Startnummer','Kommentar'])
        self.finishSheet.enable_bindings()
        self.finishSheet.grid(column = 0, row = 0)
        self.finishSheet.grid(row = 0, column = 0, sticky = "nswe")
        self.finishSheet.span('A:').align('right')
        
        self.finishSheet.disable_bindings("All")
        self.finishSheet.enable_bindings("edit_cell","single_select")
        
        #----- Course Page -------
        
        self.courseTab.grid_columnconfigure(0, weight = 1)
        self.courseTab.grid_rowconfigure(0, weight = 1)
        self.courseSheet = Sheet(self.courseTab,
                           #data = [['0','0','0',''] for r in range(200)],
                           header = ['Startnummer','Tornummer','Strafzeit','Kommentar'])
        self.courseSheet.enable_bindings()
        self.courseSheet.grid(column = 0, row = 0)
        self.courseSheet.grid(row = 0, column = 0, sticky = "nswe")
        
        self.courseSheet.disable_bindings("All")
        self.courseSheet.enable_bindings("edit_cell","single_select")
        
        #----- Input Page -------
        
        self.inputTab.grid_columnconfigure(0, weight = 1)
        self.inputTab.grid_rowconfigure(0, weight = 1)
        self.inputSheet = Sheet(self.inputTab,
                           data = [[f"{r+1}",'0,00','0,00','0,00','0,00','0,00']+
                                  [f"0" for c in range(25)] for r in range(200)],
                           header = ['Startnummer','ZS Start','ZS Ziel','Fahrzeit','Strafzeit','Wertung']+
                                    [f"{c+1}" for c in range(25)])
        self.inputSheet.enable_bindings()
        self.inputSheet.grid(column = 0, row = 0)
        self.inputSheet.grid(row = 0, column = 0, sticky = "nswe")
        for i in range(25):
            self.inputSheet.column_width(i+6, 40, False, True) 
        
        inputSpan = self.inputSheet[:]
        inputSpan.align('right')
        
        self.inputSheet.disable_bindings("All")
        self.inputSheet.enable_bindings("edit_cell","single_select","right_click_popup_menu","row_select")
        
        self.inputSheet.popup_menu_add_command(
            "Copy to GOOGLE Sheet",
            None,
            table_menu=False,
            header_menu=False,
            empty_space_menu=False,
        )
        
        self.resizable(True,True)
        
    def penaltySum(self,row):
        sumSeconds = 0
        rowData = self.inputSheet[row].data
        for penalty in rowData[6::]:
            sumSeconds = sumSeconds + locale.atof(penalty)
        return sumSeconds   
    
    def refresh(self):
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
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    
    payload = msg.payload.decode('utf-8')
    
    if msg.topic == 'elzwelle/stopwatch/course/data':
        try:
            data = payload.split(',') 
            app.courseSheet.insert_row(data)
            row = app.inputSheet.span("A").data.index(data[0].strip()) 
            col = int(data[1].strip())
            app.inputSheet.set_cell_data(row,col+5,value = data[2])
            if int(data[2]) == 50:
                app.inputSheet[row,col+5].highlight(bg = "pink")
            elif int(data[2]) == 2:
                app.inputSheet[row,col+5].highlight(bg = "khaki")
            
            penaltyTime = app.penaltySum(row)    
            app.inputSheet.set_cell_data(row,4,value = locale.format_string('%0.2f', penaltyTime) )
            #print(sumSeconds,cellValue)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
            
    if msg.topic == 'elzwelle/stopwatch/start':
        try:
            data = payload.split(' ')
            app.startSheet.insert_row([ data[0].strip(),
                                        data[1].strip(),
                                        data[2].strip(),
                                            ''])         
        except:
            print("MQTT Decode exception: ",msg.payload)
        

    if msg.topic == 'elzwelle/stopwatch/finish':
        try:
            data = payload.split(' ')
            app.finishSheet.insert_row([data[0].strip(),
                                        data[1].strip(),
                                        data[2].strip(),
                                        ''])
        except:
            print("MQTT Decode exception: ",msg.payload)
            
    if msg.topic == 'elzwelle/stopwatch/start/number':       
        try:
            data   = payload.split(' ')
            time   = data[0].strip()
            stamp  = data[1].strip()
            number = data[2].strip()
            row    = app.startSheet.span("B").data.index(stamp)+1
            app.startSheet.span("C{:}".format(row)).data = number
            if len(data) > 3:
                app.startSheet.span("D{:}".format(row)).data = data[3].strip()
            
            row = app.inputSheet.span("A").data.index(data[2].strip())
            print(row)
            app.inputSheet.set_cell_data(row,1,value = data[1])
            mqtt_client.publish("elzwelle/stopwatch/start/number/akn",
                                payload='{:} {:} {:}'.format(time,stamp,number), 
                                qos=1)
            
            # message = '{:} | {:>10} | {:>2}'.format(time,stamp,number)
            # cell = wks_start.find(stamp)
            # if cell != None:
            #     print("ROW: ",cell.row)     
            #     wks_start.update_cell(cell.row,3,number)
                # start_update_number(stamp, number)
            #     mqtt_client.publish("elzwelle/stopwatch/start/number/akn", 
            #                 payload='{:} {:} {:}'.format(time,stamp,number), 
            #                 qos=1)
            # else:
            #     print("Stamp not found: ",payload)
            #     mqtt_client.publish("elzwelle/stopwatch/start/number/error", 
            #                 payload='{:} {:} {:}'.format(time,stamp,number), 
            #                 qos=1)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
    
    if msg.topic == 'elzwelle/stopwatch/finish/number':       
        try:
            data   = payload.split(' ')
            time   = data[0].strip()
            stamp  = data[1].strip()
            number = data[2].strip()
            row    = app.finishSheet.span("B").data.index(stamp)+1
            app.finishSheet.span("C{:}".format(row)).data = number
            if len(data) > 3:
                app.finishSheet.span("D{:}".format(row)).data = data[3].strip()
                
            row = app.inputSheet.span("A").data.index(data[2].strip())
            #print(row)
            app.inputSheet.set_cell_data(row,2,value = data[1])
            tsStart  = locale.atof(app.inputSheet.get_cell_data(row,1))
            tsFinish = locale.atof(app.inputSheet.get_cell_data(row,2))
            tripTime = tsFinish - tsStart
            app.inputSheet.set_cell_data(row,3,value = locale.format_string('%0.2f',tripTime))
            penaltyTime = locale.atof(app.inputSheet.get_cell_data(row,4))
            finalTime = tripTime + penaltyTime
            app.inputSheet.set_cell_data(row,5,value = locale.format_string('%0.2f',finalTime))
            
            mqtt_client.publish("elzwelle/stopwatch/finish/number/akn",
                                payload='{:} {:} {:}'.format(time,stamp,number), 
                                qos=1)
            
            # message = '{:} | {:>10} | {:>2}'.format(time,stamp,number)
            # cell = wks_finish.find(stamp)
            # if cell != None:
            #     print("ROW: ",cell.row)     
            #     wks_finish.update_cell(cell.row,3,number)    
            #     # finish_update_number(stamp, number)
            #     mqtt_client.publish("elzwelle/stopwatch/finish/number/akn", 
            #                 payload='{:} {:} {:}'.format(time,stamp,number), 
            #                 qos=1)
            # else:
            #     print("Stamp not found: ",payload)
            #     mqtt_client.publish("elzwelle/stopwatch/finish/number/error", 
            #                 payload='{:} {:} {:}'.format(time,stamp,number), 
            #                 qos=1)
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
    
#     if msg.topic == 'elzwelle/stopwatch/start/get':       
#         try:
#             data = payload.split(' ')
#             message = '{:} | {:10.2f} | {:>2}'.format(data[0].strip(),
#                                                     float(data[1]),
#                                                     data[2].strip())
# #            cell = wks_start.find(data[2].strip())
#             # if cell != None:
#             #     print("ROW: ",cell.row,"COL: ",cell.col)     
#             # else:
#             #     print("Entry not found: ",payload)
#         except Exception as e:
#             print("MQTT Decode exception: ",e,payload)
#
#     if msg.topic == 'elzwelle/stopwatch/finish/get':       
#         try:
#             data = payload.split(' ')
#             message = '{:} | {:10.2f} | {:>2}'.format(data[0].strip(),
#                                                     float(data[1]),
#                                                     data[2].strip())
# #            cell = wks_finish.find(data[2].strip())
#             # if cell != None:
#             #     print("ROW: ",cell.row,"COL: ",cell.col)     
#             # else:
#             #     print("Entry not found: ",payload)
#         except Exception as e:
#             print("MQTT Decode exception: ",e,payload)

#-------------------------------------------------------------------
# Main program
#-------------------------------------------------------------------
if __name__ == '__main__':    
   
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

    locale.setlocale(locale.LC_ALL, 'de_DE')
    
    # google_client = gspread.service_account(filename=config.get('google','client_secret_json'))
    #
    # # Open a sheet from a spreadsheet in one go
    # wks_start = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(0)
    # #print("Ranges: ",gc.open("timestamp").list_protected_ranges(0))
    # # Open a sheet from a spreadsheet in one go
    # wks_finish = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(1)

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
    app = sheetapp_tk(None)
    app.title("MQTT Tabelle Elz-Zeit")
    app.refresh()
    app.mainloop()
    print(time.asctime(), "GUI done")
          
    # Stop all dangling threads
    os.abort()