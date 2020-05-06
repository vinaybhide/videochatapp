import socket

class videosocket:
    '''A special type of socket to handle the sending and receiveing of fixed
       size frame strings over ususal sockets
       Size of a packet or whatever is assumed to be less than 100MB
    '''

    def __init__(self , sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock= sock

    def connect(self,host,port):
        self.sock.connect((host,port))

    def vsend(self, framestring):
        totalsent = 0
        metasent = 0
        #length =len(framestring)
        size = framestring.size
        #lengthstr=str(length).zfill(8)
        lengthstr=str(size).zfill(8)
        while metasent < 8 :
            lengthbytes = (lengthstr[metasent:]).encode('utf-8')
            #sent = self.sock.send(lengthstr[metasent:])
            sent = self.sock.send(lengthbytes)
            if sent == 0:
                print("vsend: During sending size Socket connection broken")
                raise RuntimeError("Socket connection broken")
            metasent += sent
        
        
        #while totalsent < length :
        while totalsent < size :
            sent = self.sock.send(framestring[totalsent:])
            if sent == 0:
                print("vsend: During sending frame Socket connection broken")
                raise RuntimeError("Socket connection broken")
            totalsent += sent

    def vreceive(self):
        totrec=0
        metarec=0
        msgArray = []
        metaArray = []
        try:
            while metarec < 8:
                #chunk = self.sock.recv(8 - metarec)
                chunk_bytes = self.sock.recv(8 - metarec)
                chunk = chunk_bytes.decode('utf-8')
                if chunk == '':
                    print("vreceive: while receiving size socket connection broken")
                    raise RuntimeError("Socket connection broken")
                metaArray.append(chunk)
                metarec += len(chunk)
            lengthstr= ''.join(metaArray)
            length=int(lengthstr)
            while totrec<length :
                chunk = self.sock.recv(length - totrec)
                if chunk == '':
                    print("vreceive: During receiving frame socket connection broken")
                    raise RuntimeError("Socket connection broken")
                msgArray.append(chunk)
                totrec += len(chunk)
            #return ''.join(msgArray)
            return msgArray
        except Exception as e:
            print("exception in vreceive: " + str(e))
            return False
   


        
