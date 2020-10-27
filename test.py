
fileName="adadad"

rtspSeq=123
rtpPort=14
a="SETUP "+str( fileName)+"\n "+str( rtspSeq) + "\n"+" RTSP/1.0 RTP/UDP "+str( rtpPort)
a="SETUP \n"+"13"
line0=a.split('\n')
#print(line0[0].split(' '))
for i in line0:
    print(i.split(' '))