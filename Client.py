from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
#payload là phần dữ liệu thực sự được truyền đi của một gói tin giữa hai phía
from RtpPacket import RtpPacket
class Client:
    SETUP=0
    PLAY=1
    PAUSE=2
    TEARDOWN=3
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
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        print('hi')

    def playMovie(self):
        pass

    def pauseMovie(self):
        pass

    def exitClient(self):
        pass

 


