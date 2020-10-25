from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
# payload là phần dữ liệu thực sự được truyền đi của một gói tin giữa hai phía
from RtpPacket import RtpPacket


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

    def __init__(self, root):
        self.root = root
        self.CreateGUI()

    def CreateGUI(self):
        # Create Setup button
        self.setup = Button(self.root, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.root, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.root, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.root, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        self.label = Label(self.root, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        if self.state == self.INIT:
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
        self.root.destroy()
        sys.exit(0)

    def sendRTSPRequest(self, requestCode):
        # setup
        if self.SETUP == requestCode and self.state == self.INIT:
            pass
        # play
        elif self.PLAY == requestCode and self.state == self.READY:
            pass
        # pause
        elif self.pause == requestCode and self.state == self.PAUSE:
            pass
        elif self.teardown == requestCode and not self.state == self.INIT:
            pass


a = Tk()
w = Client(a)
a.mainloop()
