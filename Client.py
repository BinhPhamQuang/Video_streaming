from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
import tkinter.font as font
from RtpPacket import RtpPacket
from time import time

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    counter = 0
    # Initiation..

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.totalSize = 0
        self.currentTimeStamp = 0
        self.initTimestamp = 0
        self.firstPacket = 0
        self.pauseStart = 0
        self.pauseDuration = 0
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def createWidgets(self):
        """Build GUI."""
        """
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		"""
        # Create Play button
        myFontSize= font.Font(size=10)
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "| |"
        self.start["command"] = self.pauseMovie
        self.start.grid(row=1, column=0, padx=2, pady=2)
        

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "|>"
        self.pause["command"] = self.playMovie
        self.pause.grid(row=1, column=1, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "O"
        self.teardown["command"] = self.stopMovie
        self.teardown.grid(row=1, column=2, padx=2, pady=2)

        self.describe = Button(self.master, width=20, padx=3, pady=3)
        self.describe["text"] = "Describe"
        self.describe["command"] = self.showDescibe
        self.describe.grid(row=1, column=3, padx=2, pady=2)
        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label["text"] = "| |: Pause, |>: Play, O: Stop"
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)
        self.label['font']=myFontSize

        self.stat = Label(self.master, height=3, justify=LEFT)
        self.stat["text"] = "Statistics"
        self.stat.grid(row=2, column=0, sticky=W+N)
        self.stat['font']=myFontSize

    def showDescibe(self):
        myFontSize= font.Font(size=10)
        self.sts = ['Init', 'Ready', 'Playing']

        self.lbnamemov = Label(self.master)
        self.lbnamemov["text"] = "Name: "+self.fileName
        self.lbnamemov.grid(row=5, column=0, sticky=W+N)
        self.lbnamemov['font']=myFontSize

        self.lbstatus = Label(self.master)
        self.lbstatus["text"] = "Status: "+self.sts[self.state]
        self.lbstatus.grid(row=6, column=0, sticky=W+N)
        self.lbstatus['font']=myFontSize

        self.lbencode = Label(self.master)
        self.lbencode["text"] = "Encode: utf8"
        self.lbencode.grid(row=7, column=0, sticky=W+N)
        self.lbencode['font']=myFontSize

        self.lb200 = Label(self.master)
        self.lb200["text"] = "" if self.state <= 1 else "RTSP/1.0 200 OK"
        self.lb200.grid(row=8, column=0, sticky=W+N)
        self.lb200['font']=myFontSize

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            if self.requestSent == self.TEARDOWN:
                self.sessionId = 0
                self.frameNbr = 0
                self.rtspSeq = 0
                self.teardownAcked = 0
                self.totalSize = 0
                self.counter = 0
                self.firstPacket = 0
                self.pauseStart = 0
                self.pauseDuration = 0
                self.rtpSocket = socket.socket(
                    socket.AF_INET, socket.SOCK_DGRAM)
                self.connectToServer()
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        try:
            # Delete the cache image from video
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            pass

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        # Pressing PLAY button at the first time will also SETting up.
        self.setupMovie()
        while True:
            if self.state == self.READY:
                # Create a new thread to listen for RTP packets

                threading.Thread(target=self.listenRtp).start()
                self.playEvent = threading.Event()
                self.playEvent.clear()
                self.sendRtspRequest(self.PLAY)

                break
            elif self.state == self.PLAYING:

                break

    def stopMovie(self):
        if (self.state == self.READY or self.state == self.PLAYING) and self.requestSent is not self.SETUP:
            self.sendRtspRequest(self.TEARDOWN)
            try:
                # Delete the cache image from video
                os.remove(CACHE_FILE_NAME +
                          str(self.sessionId) + CACHE_FILE_EXT)
            except:
                pass

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    print("Current Seq Num: " + str(rtpPacket.seqNum()))

                    try:
                        if self.frameNbr + 1 != rtpPacket.seqNum():
                            self.counter += 1
                            print('!'*60 + '\nPacket Loss\n' + '!'*60)
                        currFrameNbr = rtpPacket.seqNum()
                    except:
                        print("seqNum() ERROR")
                        traceback.print_exc(file=sys.stdout)

                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        payload = rtpPacket.getPayload()
                        self.totalSize += payload.__sizeof__()

                        self.currentTimeStamp = rtpPacket.timestamp()
                        if self.firstPacket == 0:
                            self.initTimestamp = rtpPacket.timestamp()
                            self.firstPacket = 1

                        self.updateMovie(self.writeFrame(
                            rtpPacket.getPayload()))
                        self.updateStat()

            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.state == self.PLAYING:
                    print('Didn\'t receive data')
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)

        file.close()
        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def updateStat(self):
        #print("PAUSE: " + str(self.pauseEnd - self.pauseStart))
        duration = self.currentTimeStamp - self.initTimestamp - self.pauseDuration
        time = "Time: " + str(duration) + " s"
        loss_rate = "Loss rate: " + str(round((self.counter/self.frameNbr)*100, 2))+"%"
        data_rate = "Data rate: "
        try:
            data_rate += str(round(self.totalSize/duration, 2)) + " Bps"
        except:
            data_rate += "inf"
        self.stat.configure(text=time + '\n' + loss_rate +
                            "\n" + data_rate, height=3)
        self.stat["text"] = time + '\n' + loss_rate + "\n" + data_rate

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            messagebox.showwarning(
                'Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:

            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "SETUP " + str(self.fileName) + " RTSP/1.0\n" + \
                "CSeq: " + str(self.rtspSeq) + "\n" + \
                "Transport: RTP/UDP; client_port= " + str(self.rtpPort)
            # Keep track of the sent request.
            self.requestSent = self.SETUP
            self.rtspSocket.send(request.encode())

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:

            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
			
            request = "PLAY " + str(self.fileName) + " RTSP/1.0\n" + \
                "Cseq: " + str(self.rtspSeq) + "\n" + \
                "Session: " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
			 
            self.requestSent = self.PLAY
            self.rtspSocket.send(request.encode())
        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PAUSE " + str(self.fileName) + " RTSP/1.0\n" + \
                "Cseq: " + str(self.rtspSeq) + "\n" + \
                "Session: " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE
            self.rtspSocket.send(request.encode())
        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN " + str(self.fileName) + " RTSP/1.0\n" + \
                "Cseq: " + str(self.rtspSeq) + "\n" + \
                "Session: " + str(self.sessionId)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN
            self.rtspSocket.send(request.encode())
        else:
            return

        # Send the RTSP request using rtspSocket.
        # ...

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        # self.state = ...

                        self.state = self.READY
                        try:
                            self.lbstatus["text"] = "Status: " + \
                                self.sts[self.state]
                        except:
                            pass
                        # update status in GUI
                        try:
                            self.lb200["text"] = "RTSP/1.0 200 OK"
                        except:
                            pass
						#-----
                        # Open RTP port.
                        self.openRtpPort()

                    elif self.requestSent == self.PLAY:
                        if self.pauseStart != 0:
                            pauseEnd = int(time())
                            self.pauseDuration += pauseEnd - self.pauseStart
                        # self.state = ...
                        self.state = self.PLAYING

                        # update state in gui
                        try:
                            self.lbstatus["text"] = "Status: " + \
                                self.sts[self.state]
                        except:
                            pass
                    elif self.requestSent == self.PAUSE:
                        self.pauseStart = int(time())
                        # self.state = ...
                        self.state = self.READY
                        # update state in gui
                        try:
                            self.lbstatus["text"] = "Status: " + \
                                self.sts[self.state]
                        except:
                            pass
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()

                    elif self.requestSent == self.TEARDOWN:
                        # self.state = ...
                        self.state = self.INIT
                        # update state in gui
                        try:
                            self.lbstatus["text"] = "Status: " + \
                                self.sts[self.state]
                        except:
                            pass
                        self.playEvent.set()
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
                    """
					elif self.requestSent == self.STOP:
						if self.state == self.PLAYING:
							self.state = self.INIT
							self.playEvent.set()
						else:
							self.state = self.INIT
					"""

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...
        # self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        # ...
        self.rtpSocket.settimeout(0.5)
        try:
            # Bind the socket to the address using the RTP port given by the client user
            # ...
            self.rtpSocket.bind((self.serverAddr, self.rtpPort))
        except:
            messagebox.showwarning(
                'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
