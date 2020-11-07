# asd
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

    COUNTER = 0

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.filename = filename
        self.serveraddr = serveraddr
        self.rtspSeq = 0
        self.rtpPort = int(rtpport)
        self.serverPort = int(serverport)
        self.requestSent = -1
        self.sessionId = 0
        self.CreateGUI()
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
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
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)
# event

    def setupMovie(self):
        if self.state == self.INIT:
            print('+------------------------------+')
            print("|Request sent: SET UP !        |")
            print('+------------------------------+')
            self.sendRTSPRequest(self.SETUP)

    def playMovie(self):
        if self.state == self.READY:
            threading.Thread(target=self.listenRtp).start()
            print('+------------------------------+')
            print("|Request sent: PLAY !          |")
            print('+------------------------------+')
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRTSPRequest(self.PLAY)

    def pauseMovie(self):
        if self.state == self.PLAYING:
            print('+------------------------------+')
            print("|Request sent: PAUSE !         |")
            print('+------------------------------+')
            self.sendRTSPRequest(self.PAUSE)

    def exitClient(self):
        print('+------------------------------+')
        print("|Request sent: TEARDOWN !      |")
        print('+------------------------------+')
         
        MessageBox.showinfo('',"Packet Loss Rate: "+str(float(self.COUNTER/self.frameNbr)))
        self.sendRTSPRequest(self.TEARDOWN)
        self.master.destroy()
         # Delete cache jpeg file
        os.remove( "cache-" + str(self.sessionId) + ".jpg")
        
        sys.exit(0)
# end event

# RTSP
    def sendRTSPRequest(self, requestCode):
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.receiveRtspReply).start()
            self.rtspSeq = 1
            request = "SETUP "+str(self.filename)+"\n"+"Seq: "+str(self.rtspSeq) + \
                "\n" + " RTSP/1.0 RTP/UDP "+str(self.rtpPort)
            self.rtspSocket.send(request.encode())
            self.requestSent = self.SETUP

        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtspSeq += 1
            request = "PLAY "+"\n"+"Seq: " + str(self.rtspSeq)
            self.rtspSocket.send(request.encode())
            self.requestSent = self.PLAY

        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = "PAUSE "+"\n"+"Seq: " + str(self.rtspSeq)
            self.rtspSocket.send(request.encode())
            self.requestSent = self.PAUSE

        elif requestCode == self.TEARDOWN:
            self.rtspSeq += 1
            request = "TEARDOWN "+"\n"+"Seq: " + str(self.rtspSeq)
            self.rtspSocket.send(request.encode())
            self.requestSent = self.TEARDOWN

    def receiveRtspReply(self):
        while True:
            # TCP
            reply = self.rtspSocket.recv(1024)
            if reply:
                self.parseRtspReply(reply)

            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        reply = data.decode("utf8").split('\n')
        # reply by server: 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
        seq = int(reply[1].split(' ')[1])
        session = int(reply[2].split(' ')[1])
        if seq == self.rtspSeq:
            if self.sessionId == 0:
                self.sessionId = session  # get session

            if self.sessionId == session and int(reply[0].split(' ')[1]) == 200:
                if self.requestSent == self.SETUP:
                    self.state = self.READY
                    self.OpenRTPport()

                elif self.requestSent == self.PLAY:
                    self.state = self.PLAYING

                elif self.requestSent == self.PAUSE:
                    self.state = self.READY
                    # The play thread exits. A new thread is created on resume.
                    self.playEvent.set()

                elif self.requestSent == self.TEARDOWN:
                    self.teardownAcked = 1

    def OpenRTPport(self):
        self.rtpSocket.settimeout(0.5)
        try:

            self.rtpSocket.bind((self.serveraddr, self.rtpPort))
            print("Bind RtpPort Success")
        except:
            MessageBox.showerror('Connection Failed',
                                 'Connection to rtpServer failed...')

    def connectToServer(self):
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serveraddr, self.serverPort))
        except:
            MessageBox.showerror(
                'Connection Failed', 'Connection to \'%s\' failed.' % self.serveraddr)
        # AF_INET ipv4
        # sock_stream TCP

    def listenRtp(self):

        while True:
            try:
                data, addr = self.rtpSocket.recvfrom(20000)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    print("Received Rtp Packet #" +str(rtpPacket.seqNum()))
                    try:
                        if self.frameNbr+1 != rtpPacket.seqNum():
                            self.counter+=1
                            print ( "PACKET LOSS !")
                        currFrameNbr = rtpPacket.seqNum()
                    except:
                        traceback.print_exc(file=sys.stdout)
                    currFrameNbr = rtpPacket.seqNum()
                    if currFrameNbr > self.frameNbr:
                        
                        self.frameNbr = currFrameNbr
                        self.FrameVideo(self.writeFrame(rtpPacket.getPayload()))
                        
                else:
                    print('----Can not recieve data !----')
            except:
                # Stop when PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def FrameVideo(self, image):
        try:
            photo = ImageTk.PhotoImage(Image.open(image))
        except:
            traceback.print_exc(file=sys.stdout)
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def writeFrame(self, data):
         
        cachename = "cache-" + str(self.sessionId) + ".jpg"
        try:
            file = open(cachename, "wb")
        except:
            print("file open error")
        try:
            file.write(data)
        except:
            print("file write error")
        file.close()
        return cachename


# a = Tk()

# w = Client(a, '172.17.2.221', 1025, 5008, 'video.mjpeg')
# a.mainloop()
