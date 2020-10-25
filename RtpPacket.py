import sys
from time import time
import VideoStream
HEADER_SIZE = 12


class RtpPacket:
    def __init__(self):
        self.header = bytearray(HEADER_SIZE)
# V:RTP version P:padding X: extension
# PT: payload_type,CC: contributing sources
# M marker, sq : sequence number

    def encode(self, V, P, X, CC, M, PT, sq, SSRC, payload):
        timestamp = int(time())
        print("timestamp: "+str(int(time())))
        self.header[0] = V << 6  # VV000000
        self.header[0] = self.header[0] | P << 5  # VVP00000
        self.header[0] = self.header[0] | X << 4  # VVPX0000
        self.header[0] = self.header[0] | CC  # VVPXCCCC

        self.header[1] = M << 7  # M0000000
        self.header[1] = self.header[1] | PT  # MPT

        self.header[2] = sq >> 8
        self.header[3] = sq & 0x00FF  # delete 8 first bit

        self.header[4] = timestamp >> 24
        self.header[5] = (timestamp & 0x00FFFFFF) >> 16
        self.header[6] = (timestamp & 0x0000FFFF) >> 8
        self.header[7] = (timestamp & 0x000000FF)

        self.header[8] = SSRC >> 24
        self.header[9] = (SSRC & 0x00FFFFFF) >> 16
        self.header[10] = (SSRC & 0x0000FFFF) >> 8
        self.header[11] = (SSRC & 0x000000FF)

        self.payload = payload

    def decode(self, byteStream):
        self.header = bytearray(byteStream[:HEADER_SIZE])
        self.payload = byteStream[HEADER_SIZE:]

    def version(self):
        return int(self.header[0] >> 6)

    def padding(self):
        return int((self.header[0] >> 5 & 0x1))

    def seqNum(self):
        return int(self.header[2] << 8 | self.header[3])

    def timestamp(self):
        return int(self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7])

    def payload_type(self):
        return int(self.header[1] & 127)  # 01111111

    def getPayload(self):

        return self.payload

    def getPacket(self):

        return self.header + self.payload



print(time())