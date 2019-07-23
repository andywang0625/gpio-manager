try:
    import tkinter as tk
    import tkinter.messagebox
    from tkinter import *
    import time
    import datetime
    import RPi.GPIO as GPIO
    import io,shutil
    import urllib
    import threading
    import queue
    import os
    from http.server import HTTPServer,BaseHTTPRequestHandler
except ImportError:
    print("Importing Package(s) Failed")
    
messageQueue = queue.Queue(10)
GPIOStatusG = [0]*40

class httpServer(threading.Thread):
    def __init__(self, Manager, port=8080):
        threading.Thread.__init__(self)
        self.Manager = Manager
        self.port = port
    def run(self):
        class GPIOHttpHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if '?' in self.path:
                    #command,targetPort=urllib.Request.splitquery(self.path)
                    
                    rawRequests = self.path[2:]
                    cookedRequests = rawRequests.split("&")
                    #print(type(cookedRequests))
                    isAPI = False
                    for req in cookedRequests:
                        attr = req.split("=")
                        if isAPI:
                            messageQueue.put((attr[0],attr[1]))
                            self.send_response(200)
                            return
                        if attr[0]=="httpapi":
                            if attr[1]=="true":
                                isAPI = True
                                continue
                        #implement needed
                        #print(attr[0]+"\n"+attr[1])
                        #print(type(messageQueue))
                        messageQueue.put((attr[0],attr[1]))
                    pass
                self.send_response(200)
                self.send_header("Content-type","text/html")
                self.send_header("test","This is test!")
                self.end_headers()
                statusTable = ""
                statusTable = statusTable+"<div style='width:95vw;text-align:center;'><table border='2' style='margin:auto;width:95%;text-align:center;'>"
                i = 0
                statusTable = statusTable+"<tr>"
                time.sleep(0.2)
                for theGPIO in GPIOStatusG:
                    if i%5 == 0:
                        statusTable = statusTable+"</tr><tr>"
                    statusTable = statusTable+"<td>GPIO"+str(i)+"<br/>"+ ("0V" if (theGPIO==0 or theGPIO==False) else "3.3V")  +"</td>"
                    i = i + 1
                statusTable = statusTable+"</tr></table></div>"
                self.page= '''
                    <html>
                    <haed>
                    <title>GPIO Web Manager</title>
                    <meta name="viewport" content="width=device-width,initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
                    </haed>
                    <body>
                    <div style="text-align:center;width:97vw;height:100vh;">
                    <h1>GPIO Manager</h1>
                    <hr/>
                    <form method="get">
                    <h3>Switch A Port</h3>
                        <input style="width:60vw;hieght:20vh;" type="text" name="port"/>
                        <input style="width:60vw;hieght:20vh;" type="submit" value="Submit"/>
                '''+ statusTable +'''
                </form>
                    </div>
                    </body>
                    </html>
                    '''
                self.page = self.page.encode()
                self.wfile.write(self.page)
        self.httpServer = HTTPServer(('',
                                int(self.port)),
                                GPIOHttpHandler)
        self.httpServer.serve_forever()
        
class timmerAlarm(threading.Thread):
    def __init__(self, day=0, hour=0, mins=0, sec=3):
        threading.Thread.__init__(self)
        self.day = day
        self.hour = hour
        self.mins = mins
        self.sec = sec
        #print(self.sec)
        #print(sec)
    def run(self):
        self.current = datetime.datetime.now()
        #print(self.sec)
        print(datetime.timedelta(days=self.day, hours=self.hour, minutes=self.mins, seconds=int(self.sec)))
        timeLeft = self.current+datetime.timedelta(days=self.day, hours=self.hour, minutes=self.mins, seconds=int(self.sec))
        #print(self.current)
        print(timeLeft)
        
        while(1):
            self.current = datetime.datetime.now()
            if self.current > timeLeft:
                #print("done")
                for i in range(10):
                    messageQueue.put(("port", 1))
                    time.sleep(1)
                    messageQueue.put(("port", 1))
                    time.sleep(0.5)
                return

class GPIOManager:
    def __init__(self):
        self.GPIOStatus = [0]*40
        self.GPIO2Board = {0:11, 1:12, 2:13, 3:15, 4:16, 5:18, 6:22, 7:7, 21:29, 22:31, 23:33, 24:35, 25:37, 26:32, 27:36, 28:38, 29:40}
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for TheGPIO in self.GPIO2Board.items():
            #print(TheGPIO)
            GPIO.setup(TheGPIO[1], 0)
            GPIO.output(TheGPIO[1], 0)
        self.drawWindow()
    
    def updatePorts(self):
        i = 0
        for TheGPIO in self.GPIO2Board.items():
            GPIO.output(TheGPIO[1], self.GPIOStatus[i])
            i = i+1
        self.GPIOSwitch()
    
    def setTimer(self, day=0, hour=0, mins=0, sec=0):
        NewTimer = timmerAlarm(day=day, hour=hour, mins=mins, sec=sec)
        NewTimer.start()
        
    def drawWindow(self):
        self.window = tk.Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.title('GPIO Manager')
        self.window.geometry('600x800')
        self.board = tk.Text(self.window,
                        width=25,
                        height=17)
        self.board.pack()
        self.GPIOSwitch()
        dayEntry = Entry(self.window,textvariable="0")
        dayEntry.insert(END, '0')
        dayEntry.pack(side=tk.TOP)
        hourEntry = Entry(self.window)
        hourEntry.insert(END, '0')
        hourEntry.pack(side=tk.TOP)
        minEntry = Entry(self.window)
        minEntry.insert(END, '0')
        minEntry.pack(side=tk.TOP)
        secEntry = Entry(self.window)
        secEntry.insert(END, '0')
        secEntry.pack(side=tk.TOP)
        setTimer = tk.Button(self.window,
                          text="Set Timer",
                          width=15,
                          height=1,
                          command=lambda :self.setTimer(day=int(dayEntry.get()), hour=int(hourEntry.get()), mins=int(minEntry.get()), sec=int(secEntry.get())))
        setTimer.pack(side=tk.TOP)
        AllOff = tk.Button(self.window,
                          text="All Off",
                          width=15,
                          height=1,
                          command=self.GPIOsOFF)

        AllOff.pack(side=tk.LEFT)
        AllON = tk.Button(self.window,
                          text="All ON",
                          width=15,
                          height=1,
                          command=self.GPIOsON)

        AllON.pack(side=tk.RIGHT)

        gpio0 = tk.Button(self.window,
                          text="GPIO0 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=0))

        gpio0.pack()


        gpio1 = tk.Button(self.window,
                          text="GPIO1 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=1))

        gpio1.pack()

        gpio2 = tk.Button(self.window,
                          text="GPIO2 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=2))

        gpio2.pack()

        gpio3 = tk.Button(self.window,
                          text="GPIO3 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=3))

        gpio3.pack()

        gpio4 = tk.Button(self.window,
                          text="GPIO4 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=4))

        gpio4.pack()

        gpio5 = tk.Button(self.window,
                          text="GPIO5 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=5))

        gpio5.pack()

        gpio6 = tk.Button(self.window,
                          text="GPIO6 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=6))

        gpio6.pack()

        gpio7 = tk.Button(self.window,
                          text="GPIO7 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=7))

        gpio7.pack()

        gpio21 = tk.Button(self.window,
                          text="GPIO21 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=21))

        gpio21.pack()

        gpio22 = tk.Button(self.window,
                          text="GPIO22 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=22))

        gpio22.pack()

        gpio23 = tk.Button(self.window,
                          text="GPIO23 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=23))

        gpio23.pack()

        gpio24 = tk.Button(self.window,
                          text="GPIO24 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=24))

        gpio24.pack()

        gpio25 = tk.Button(self.window,
                          text="GPIO25 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=25))

        gpio25.pack()

        gpio26 = tk.Button(self.window,
                          text="GPIO26 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=26))

        gpio26.pack()

        gpio27= tk.Button(self.window,
                          text="GPIO27 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=27))

        gpio27.pack()

        gpio28 = tk.Button(self.window,
                          text="GPIO28 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=28))

        gpio28.pack()

        gpio29 = tk.Button(self.window,
                          text="GPIO29 On/Off",
                          width=15,
                          height=1,
                          command=lambda :self.GPIOSwitch(GPIOPort=29))

        gpio29.pack()

    def on_closing(self):
        self.window.destroy()
        os._exit(0)
        
    def GPIOsON(self):
        """
        Turn Every Ports On
        """
        for TheGPIO in self.GPIO2Board.items():
            GPIO.output(TheGPIO[1], 1)
        self.GPIOSwitch()
    def GPIOsOFF(self):
        """
        Vice versa
        """
        for TheGPIO in self.GPIO2Board.items():
            GPIO.output(TheGPIO[1], 0)
        self.GPIOSwitch()

    def GPIOSwitch(self, GPIOPort=999):
        '''
        If there is no attr posted in, the method will update the status board.
        '''
        global GPIOStatusG
        self.board.delete(1.0,tkinter.END)
        if GPIOPort != 999:
            self.GPIOStatus[GPIOPort] = not self.GPIOStatus[GPIOPort]
            GPIO.output(self.GPIO2Board[GPIOPort], self.GPIOStatus[GPIOPort])
        for TheGPIO in self.GPIO2Board.items():
            self.board.insert(TheGPIO[0]+1.0, "GPIO"+str(TheGPIO[0])+"\t\t"+("3.3V" if(GPIO.input(TheGPIO[1])==1) else "0V")+"\n")
        GPIOStatusG = self.GPIOStatus[:]
    def mainLoop(self, window):
        while 1:
            try:
                window.update()
            except:
                exit()
            if not messageQueue.empty():
                message = messageQueue.get(block=False)
                if(message[0]=="port"):
                    try:
                        self.GPIOStatus[int(message[1])] = not self.GPIOStatus[int(message[1])]
                        self.updatePorts()
                    except:
                        print("Failed to Update Info")
                else:
                    if message[1] == "1" or message[1].lower() == "true" or message[1].lower() == "3.3v":
                        self.GPIOStatus[int(message[0])] = True
                    else:
                        self.GPIOStatus[int(message[0])] = False
                    self.updatePorts()




def main():
    Manager = GPIOManager()
    HTTPServer = httpServer(Manager)
    HTTPServer.start()
    Manager.mainLoop(Manager.window)


    
if __name__ == '__main__':
    main()
