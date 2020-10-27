from tkinter import *
import tkinter.messagebox as MessageBox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
# payload là phần dữ liệu thực sự được truyền đi của một gói tin giữa hai phía
from RtpPacket import RtpPacket


#request: "DATATYPE"+" abc.jpeg\n"+" rtspSeq\n"+" adadds "+" port"

class Client:
    # state
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    # command
    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.filename = filename
        self.serveraddr = serveraddr
        self.rtspSeq = 0
        self.rtpPort = int(rtpport)
        self.serverPort = int(serverport)
        self.requestSent = -1
        self.CreateGUI()
        self.connectToServer()
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def CreateGUI(self):
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

    	# Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        if self.state == self.INIT:
            print("Setup Movie")
            self.sendRTSPRequest(self.SETUP)

    def playMovie(self):
        if self.state == self.READY:
            print("Playing Movie")
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRTSPRequest(self.PLAY)

    def pauseMovie(self):
        if self.state == self.PLAYING:
            print("Pause movie")
            self.sendRTSPRequest(self.PAUSE)

    def exitClient(self):
        self.sendRTSPRequest(self.TEARDOWN)
        self.master.destroy()
        sys.exit(0)

    def sendRTSPRequest(self, requestCode):
        # setup
        if self.SETUP == requestCode and self.state == self.INIT:
            threading.Thread(target=self.recieveRtspReply).start()
            self.rtspSeq = 1
            request= "SETUP "+str(self.filename)+"\n "+str(self.rtspSeq) + "\n"+" RTSP/1.0 RTP/UDP "+str(self.rtpPort)
            self.rtpSocket.send(request.encode())
            self.requestSent = self.SETUP
        # play

        elif self.PLAY == requestCode and self.state == self.READY:
            self.rtspSeq += 1
            request = "PLAY \n" + str(self.rtspSeq)
            self.rtpSocket.send(request.encode())
            self.requestSent=self.PLAY
        # pause

        elif self.pause == requestCode and self.state == self.PAUSE:
            self.rtspSeq+=1
            request="PAUSE \n"+str(self.rtspSeq)
            self.rtpSocket.send(request.encode())
            self.requestSent=self.PAUSE

        elif self.teardown == requestCode and not self.state == self.INIT:
            self.rtspSeq+=1
            request="TEARDOWN \n"+str(self.rtspSeq)
            self.rtpSocket.send(request.encode())
            self.requestSent=self.TEARDOWN
        else:
            return

    def connectToServer(self):
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # AF_INET ipv4
        # sock_stream TCP
        try:
            # client --> server
            self.rtpSocket.connect((self.serveraddr, self.serverPort))
        except:
            MessageBox.showerror(
                'Connection Failed', 'Connection to \'%s\' failed.' % self.serveraddr)

    def recieveRtspReply(self):
        pass

    def listenRtp(self):
        pass

    def FrameVideo(self,image):
        try:
            photo=ImageTk.PhotoImage(Image.open(image))
        except:
            traceback.print_exc(file=sys.stdout)
        self.label.configure(image = photo, height=288)
        self.label.image = photo

a = Tk()
 
w = Client(a,'172.17.2.221',1025,5008,'video.mjpeg')
a.mainloop()
