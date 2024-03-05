import configparser
import gc
import os
import platform
import time
#import locale
import tkinter
from   tkinter import ttk
from   tkinter import messagebox
from   tkinter import simpledialog
import traceback

import uuid
#import socket
import gspread
import paho.mqtt.client as paho
from   paho import mqtt
#from table import TableCanvas
import tksheet
from   tksheet import Sheet
#from   bCNC.lib.log import null

# Google Spreadsheet ID for publishing times
# Elzwelle        SPREADSHEET_ID = '1obtfHymwPSGoGoROUialryeGiMJ1vkEUWL_Gze_hyfk'
# FilouWelle      SPREADSHEET_ID = '1M05W0igR6stS4UBPfbe7-MFx0qoe5w6ktWAcLVCDZTE'
SPREADSHEET_ID = '1M05W0igR6stS4UBPfbe7-MFx0qoe5w6ktWAcLVCDZTE'

#startSheet = null

#---------------------- Fix local.DE -------------------
class locale:
    
    @staticmethod
    def atof(s):
        return float(s.strip().replace(',','.'))

    @staticmethod
    def format_string(fmt, *args):
        return  (fmt % args).replace('.',',')
    
#-------------------------------------------------------------------
# Define the GUI
#-------------------------------------------------------------------
class sheetapp_tk(tkinter.Tk):
    def __init__(self,parent):
        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        self.run   = 0

    def showError(self, *args):
        err = traceback.format_exception(*args)
        messagebox.showerror('Exception',err)
        
        # but this works too
        tkinter.Tk.report_callback_exception = self.showError

    def noop(self):
        return

    def setRun(self,run):
        self.run = run
        #print(run)
        if run == 1:
            self.training.set(True)
            self.run_1.set(False)
            self.run_2.set(False)
            self.inputSheet = self.inputSheet_T
        elif run == 2:
            self.training.set(False)
            self.run_1.set(True)
            self.run_2.set(False)
            self.inputSheet = self.inputSheet_1
        elif run == 3:
            self.training.set(False)
            self.run_1.set(False)
            self.run_2.set(True)
            self.inputSheet = self.inputSheet_2
        else:
            self.run = 0
        self.runText.set(self.headerText[self.run])

    def initialize(self):
        rows = config.getint('competition','rows')
        noteStyle = ttk.Style()
        noteStyle.theme_use('default')
        noteStyle.configure("TNotebook", background='lightgray')
        noteStyle.configure("TNotebook.Tab", background='#eeeeee')
        noteStyle.map("TNotebook.Tab", background=[("selected", '#005fd7')],foreground=[("selected", 'white')])
        
        self.geometry("1000x400")
        
        self.run = 1
        self.headerText = ['','Training','Lauf 1','Lauf 2']
        self.runText    = tkinter.StringVar(value='')
        
        self.training   = tkinter.BooleanVar(value=False)
        self.run_1      = tkinter.BooleanVar(value=False)
        self.run_2      = tkinter.BooleanVar(value=False)
        
        self.menuBar = tkinter.Menu(self)
        self.config(menu = self.menuBar)
        self.menuCompetition = tkinter.Menu(self.menuBar, tearoff=False) 
        
        self.menuCompetition.add_checkbutton(command=lambda: self.setRun(1),label="Training",variable=self.training,onvalue=1, offvalue=0)
        self.menuCompetition.add_checkbutton(command=lambda: self.setRun(2),label="Lauf 1",variable=self.run_1,onvalue=1, offvalue=0)
        self.menuCompetition.add_checkbutton(command=lambda: self.setRun(3),label="Lauf 2",variable=self.run_2,onvalue=1, offvalue=0)
        
        self.menuBar.add_cascade(label="Wettbewerb",menu=self.menuCompetition)
        
        self.pageHeader = tkinter.Label(self,textvariable=self.runText,
                                        font=("Arial", 18),
                                        bg='#D3E3FD')
        self.pageHeader.pack(expand = 0, fill ="x") 
        
        self.tabControl = ttk.Notebook(self) 
        self.tabControl
          
        self.startTab   = ttk.Frame(self.tabControl) 
        self.finishTab  = ttk.Frame(self.tabControl)
        self.courseTab  = ttk.Frame(self.tabControl)
        self.inputTab_T = ttk.Frame(self.tabControl) 
        self.inputTab_1 = ttk.Frame(self.tabControl) 
        self.inputTab_2 = ttk.Frame(self.tabControl)
        
        self.tabControl.add(self.startTab, text ='Start') 
        self.tabControl.add(self.finishTab, text ='Ziel') 
        self.tabControl.add(self.courseTab, text ='Strecke') 
        self.tabControl.add(self.inputTab_T, text ='Training')
        self.tabControl.add(self.inputTab_1, text ='Lauf 1') 
        self.tabControl.add(self.inputTab_2, text ='Lauf 2')
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
        self.startSheet.enable_bindings("edit_cell","single_select","row_select","copy")
        
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
        self.finishSheet.enable_bindings("edit_cell","single_select","row_select","copy")
        
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
        self.courseSheet.enable_bindings("edit_cell","single_select","row_select","copy")
        
        #----- Input Page Training -------
        
        self.inputTab_T.grid_columnconfigure(0, weight = 1)
        self.inputTab_T.grid_rowconfigure(0, weight = 1)
        self.inputSheet_T = Sheet(self.inputTab_T,
                           data = [[f"{r+1}",'0,00','0,00','0,00','0,00','0,00']+
        #                         [f"0" for c in range(25)] for r in range(200)],
                                  (["0"]*26) for r in range(rows)],
                           header = ['Startnummer','ZS Start','ZS Ziel','Fahrzeit','Strafzeit','Wertung']+
                                    [f"{c+1}" for c in range(25)]+["Ziel"])
        self.inputSheet_T.enable_bindings()
        self.inputSheet_T.grid(column = 0, row = 0)
        self.inputSheet_T.grid(row = 0, column = 0, sticky = "nswe")
        for i in range(25):
            self.inputSheet_T.column_width(i+6, 40, False, True) 
        self.inputSheet_T.column_width(31, 50, False, True)
        
        inputSpan = self.inputSheet_T[:]
        inputSpan.align('right')
        
        self.inputSheet_T.disable_bindings("All")
        self.inputSheet_T.enable_bindings("edit_cell","single_select","right_click_popup_menu","row_select","copy")
        
        #----- Input Page 1-------
        
        self.inputTab_1.grid_columnconfigure(0, weight = 1)
        self.inputTab_1.grid_rowconfigure(0, weight = 1)
        self.inputSheet_1 = Sheet(self.inputTab_1,
                           data = [[f"{r+1}",'0,00','0,00','0,00','0,00','0,00']+
        #                         [f"0" for c in range(25)] for r in range(200)],
                                  (["0"]*26) for r in range(rows)],
                           header = ['Startnummer','ZS Start','ZS Ziel','Fahrzeit','Strafzeit','Wertung']+
                                    [f"{c+1}" for c in range(25)]+["Ziel"])
        self.inputSheet_1.enable_bindings()
        self.inputSheet_1.grid(column = 0, row = 0)
        self.inputSheet_1.grid(row = 0, column = 0, sticky = "nswe")
        for i in range(25):
            self.inputSheet_1.column_width(i+6, 40, False, True)
        self.inputSheet_1.column_width(31, 50, False, True) 
        
        inputSpan = self.inputSheet_1[:]
        inputSpan.align('right')
        
        self.inputSheet_1.disable_bindings("All")
        self.inputSheet_1.enable_bindings("edit_cell","single_select","right_click_popup_menu","row_select","copy")
        
        #----- Input Page 2-------
        
        self.inputTab_2.grid_columnconfigure(0, weight = 1)
        self.inputTab_2.grid_rowconfigure(0, weight = 1)
        self.inputSheet_2 = Sheet(self.inputTab_2,
                           data = [[f"{r+1}",'0,00','0,00','0,00','0,00','0,00']+
        #                         [f"0" for c in range(25)] for r in range(200)],
                                  (["0"]*26) for r in range(rows)],
                           header = ['Startnummer','ZS Start','ZS Ziel','Fahrzeit','Strafzeit','Wertung']+
                                    [f"{c+1}" for c in range(25)]+["Ziel"])
        self.inputSheet_2.enable_bindings()
        self.inputSheet_2.grid(column = 0, row = 0)
        self.inputSheet_2.grid(row = 0, column = 0, sticky = "nswe")
        for i in range(25):
            self.inputSheet_2.column_width(i+6, 40, False, True) 
        self.inputSheet_2.column_width(31, 50, False, True)
        
        inputSpan = self.inputSheet_2[:]
        inputSpan.align('right')
        
        self.inputSheet_2.disable_bindings("All")
        self.inputSheet_2.enable_bindings("edit_cell","single_select","right_click_popup_menu","row_select","copy")
        
        self.setRun(1)
        self.tabControl.select(3)
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
    print("Publish mid: " + str(mid))


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
    # global time_stamps_start_dirty 
    # global time_stamps_finish_dirty
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )

        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    
    payload = msg.payload.decode('ISO8859-1')        # ('utf-8')
    
    if msg.topic == 'elzwelle/stopwatch/login':
        if config.getboolean("auth","app_pin_enabled"):
            print("PIN enabled")
            pin = int(payload[:4], 16)-4096
            print(pin)
            print(pins.count(pin))
            if pins.count(pin) > 0:
                mqtt_client.publish("elzwelle/stopwatch/login/akn", payload="4f4b"+payload[4:], qos=1)
            else:
                mqtt_client.publish("elzwelle/stopwatch/login/akn", payload="4e4f"+payload[4:], qos=1)
        else:
            print("PIN disabled")
            print("PIN OK")
            mqtt_client.publish("elzwelle/stopwatch/login/akn", payload="4f4b"+payload[4:], qos=1)
            
    
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
            
            if locale.atof(app.inputSheet.get_cell_data(row,2)) > 0.0:  # TsFinish > 0
                calculateTimes(row)
        
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
        time   = '00:00:00'
        stamp  = '0,00'
        number = '0'       
        try:
            data   = payload.split(' ')
            time   = data[0].strip()
            stamp  = data[1].strip()
            number = data[2].strip()
            if int(number) > 0:
                row    = app.startSheet.span("B").data.index(stamp)+1
                app.startSheet.span("C{:}".format(row)).data = number
                if len(data) > 3:
                    app.startSheet.span("D{:}".format(row)).data = data[3].strip()
                
                row = app.inputSheet.span("A").data.index(data[2].strip())
                #print(row)
                app.inputSheet.set_cell_data(row,1,value = data[1])
                mqtt_client.publish("elzwelle/stopwatch/start/number/akn",
                                    payload='{:} {:} {:}'.format(time,stamp,number), 
                                    qos=1)
            else:
                mqtt_client.publish("elzwelle/stopwatch/start/number/error", 
                                    payload='{:} {:} {:}'.format(time,stamp,number), 
                                    qos=1)
            
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
            print(e.args[0])
            mqtt_client.publish("elzwelle/stopwatch/start/number/error", 
                                payload='{:} {:} {:}'.format(time,stamp,number), 
                                qos=1)
    
    if msg.topic == 'elzwelle/stopwatch/finish/number':   
        time   = '00:00:00'
        stamp  = '0,00'
        number = '0'       
        try:
            data   = payload.split(' ')
            time   = data[0].strip()
            stamp  = data[1].strip()
            number = data[2].strip()
            if int(number) > 0:
                row    = app.finishSheet.span("B").data.index(stamp)+1
                app.finishSheet.span("C{:}".format(row)).data = number
                if len(data) > 3:
                    app.finishSheet.span("D{:}".format(row)).data = data[3].strip()
                    
                row = app.inputSheet.span("A").data.index(data[2].strip())
                #print(row)
                app.inputSheet.set_cell_data(row,2,value = data[1])
                # ------------ Calculate ----------
                calculateTimes(row)
                # tsStart  = locale.atof(app.inputSheet.get_cell_data(row,1))
                # tsFinish = locale.atof(app.inputSheet.get_cell_data(row,2))
                # tripTime = tsFinish - tsStart
                # app.inputSheet.set_cell_data(row,3,value = locale.format_string('%0.2f',tripTime))
                # penaltyTime = locale.atof(app.inputSheet.get_cell_data(row,4))
                # finalTime = tripTime + penaltyTime
                # app.inputSheet.set_cell_data(row,5,value = locale.format_string('%0.2f',finalTime))
                # ----------------------------------
                mqtt_client.publish("elzwelle/stopwatch/finish/number/akn",
                                    payload='{:} {:} {:}'.format(time,stamp,number), 
                                    qos=1)
            else:
                mqtt_client.publish("elzwelle/stopwatch/finish/number/error", 
                                    payload='{:} {:} {:}'.format(time,stamp,number), 
                                    qos=1)
    
        except Exception as e:
            print("MQTT Decode exception: ",e,payload)
            print(e.args[0])
            mqtt_client.publish("elzwelle/stopwatch/start/number/error", 
                                payload='{:} {:} {:}'.format(time,stamp,number), 
                                qos=1)

def calculateTimes(row):
    tsStart  = locale.atof(app.inputSheet.get_cell_data(row,1))
    tsFinish = locale.atof(app.inputSheet.get_cell_data(row,2))
    tripTime = tsFinish - tsStart
    app.inputSheet.set_cell_data(row,3,value = locale.format_string('%0.2f',tripTime))
    penaltyTime = locale.atof(app.inputSheet.get_cell_data(row,4))
    finalTime = tripTime + penaltyTime
    app.inputSheet.set_cell_data(row,5,value = locale.format_string('%0.2f',finalTime))

GATE_CELLS        = 25
GATE_CELLS_OFFSET = 6

def copyToGoogleSheet():
    print("Copy to GOOGLE Sheet")
    tab = app.tabControl.index(app.tabControl.select())
    gates = config.getint('competition','gates')
    print("GAT: ",gates)
    
    if (app.inputSheet == app.inputSheet_1 and tab == 4) or (app.inputSheet == app.inputSheet_2 and tab == 5):
        # Index asugewälte Zeile
        currently_selected = app.inputSheet.get_currently_selected()
        print("SEL: ",currently_selected.row)
        
        data = app.inputSheet[currently_selected].data[0]
        print("TAB: ",data)
        
        try:
            # Startnummer Spalte aus Google holen
            startNums = wks_input.col_values(4)
            print("NUM: ",startNums)
            
            # Startnummer Position suchen
            row = startNums.index(data[0])+1
            print("ROW: ",row)
        
            # Zeile aus Google holen
            gData = wks_input.row_values(row)
            print("GOD: ",gData)
            
            if tab == 4:
                print("COM: Lauf 1")
                gTzStartIdx     = tksheet.alpha2num("M")-1
                gTzFinishIdx    = tksheet.alpha2num("N")-1
                gTor_1_Idx      = tksheet.alpha2num("O")-1
                gRange          = "M"+str(row)+":"+"AN"+str(row)
            if tab == 5:
                print("COM: Lauf 2")
                gTzStartIdx     = tksheet.alpha2num("AR")-1
                gTzFinishIdx    = tksheet.alpha2num("AS")-1
                gTor_1_Idx      = tksheet.alpha2num("AT")-1
                gRange          = "AR"+str(row)+":"+"BS"+str(row)
            
            gData[gTzStartIdx]  = data[1]
            gData[gTzFinishIdx] = data[2]
            gData[gTor_1_Idx:gTor_1_Idx+gates] = data[GATE_CELLS_OFFSET : GATE_CELLS_OFFSET+gates]
            gData[gTor_1_Idx+GATE_CELLS] = data[GATE_CELLS + GATE_CELLS_OFFSET] 
            
            print("UPD: ",[gData[gTzStartIdx:gTor_1_Idx+GATE_CELLS+1]])
            
            wks_input.update([gData[gTzStartIdx:gTor_1_Idx+GATE_CELLS+1]],gRange,
                              value_input_option='USER_ENTERED')
            
            colSpan = "A"+str(currently_selected.row+1)+":F"+str(currently_selected.row+1)
            app.inputSheet.span(colSpan).highlight(bg = "aquamarine")
        except Exception as e:
            colSpan = "A"+str(currently_selected.row+1)+":F"+str(currently_selected.row+1)
            app.inputSheet.span(colSpan).highlight(bg = "pink")
            messagebox.showerror(title="Fehler", message=e)
    else:
        messagebox.showerror(title="Fehler", message="Falscher Wettbewerb aktiv!")

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
    
    config['competition']   = {
        'gates':25,
        'rows':300,
    }
    
    config['auth']   = {
        'pin_enabled':"no",
        'app_pin_enabled':'no',
    }
        
    # Platform specific
    if myPlatform == 'Windows':
        # Platform defaults
        config.read('windows.ini') 
    if myPlatform == 'Linux':
        config.read('linux.ini')

    pins = [int(x) for x in config.get('auth','pins').split(',')]   #string list to int list
    
    #locale.setlocale(locale.LC_ALL, 'de_DE')
    try:
        google_client = gspread.service_account(filename=config.get('google','client_secret_json'))
        google_client.http_client.set_timeout(5)
        # Open a sheet from a spreadsheet in one go
        wks_input = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(0)
        
        # # Open a sheet from a spreadsheet in one go
        # wks_start = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(0)
        # #print("Ranges: ",gc.open("timestamp").list_protected_ranges(0))
        # # Open a sheet from a spreadsheet in one go
        # wks_finish = google_client.open(config.get('google','spreadsheet_name')).get_worksheet(1)
    except Exception as e:
        messagebox.showerror(title="Fehler", message="Keine Verbindung zu Google Sheets!")
        print("Error: ",e)
        exit(1)

    #--------------------------------- MQTT --------------------------

    # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
    # userdata is user defined data of any type, updated by user_data_set()
    # client_id is the given name of the client
    try:
        mqtt_client = paho.Client(client_id="elzwelle_"+str(uuid.uuid4()), userdata=None, protocol=paho.MQTTv311)
    
        # enable TLS for secure connection
        if config.getboolean('mqtt','tls_enabled'):
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
    except Exception as e:
        messagebox.showerror(title="Fehler", message="Keine Verbindung zum MQTT Server!")
        print("Error: ",e)
        exit(1)   
        
    # ---------- setup and start GUI --------------
    app = sheetapp_tk(None)
    
    print(pins)
    
    if config.getboolean("auth", "pin_enabled"): 
        login = False
        while not login:
            login = pins.count(simpledialog.askinteger("Login","Pin" )) > 0
        
    app.title("MQTT Tabelle Elz-Zeit")
    app.refresh()
    
    app.inputSheet_1.popup_menu_add_command(
        "Copy to GOOGLE Sheet 1. Lauf",
        copyToGoogleSheet,
        table_menu=False,
        header_menu=False,
        empty_space_menu=False,
    )
    
    app.inputSheet_2.popup_menu_add_command(
        "Copy to GOOGLE Sheet 2. Lauf",
        copyToGoogleSheet,
        table_menu=False,
        header_menu=False,
        empty_space_menu=False,
    )
    
    # run
    app.mainloop()
    print(time.asctime(), "GUI done")
          
    # Stop all dangling threads
    os.abort()