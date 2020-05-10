import socket
import numpy as np

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

    #input framesring is in bytes
    def vsend(self, framestring, send_size):
        metasent = 0
        totalsent = 0

        #now send the actual data
        while totalsent < send_size :
            sent = self.sock.send(framestring[totalsent:])
            if sent == 0:
                print("vsend: During sending frame Socket connection broken")
                raise RuntimeError("Socket connection broken")
            totalsent += sent

    def vreceive(self, receive_size):
        metarec=0
        totrec=0
        metaArray = []
        streamtoreturn = ''.encode('utf-8')

        # now fetch the data in bytes
        while totrec<receive_size :
            chunk = self.sock.recv(receive_size - totrec)
            if chunk == '':
                print("vreceive: During receiving frame socket connection broken")
                raise RuntimeError("Socket connection broken")
            totrec += len(chunk)
            streamtoreturn = streamtoreturn + chunk

        #we will return only the data in bytes to caller
        return streamtoreturn


    def vsend_notused(self, framestring):
        totalsent = 0
        metasent = 0
        #length =len(framestring)
        #lengthstr=str(length).zfill(8)
        size = framestring.size
        lengthstr=str(size).zfill(8)
        while metasent < 8 :
            lengthbytes = (lengthstr[metasent:]).encode('utf-8')
            sent = self.sock.send(lengthbytes)
            #sent = self.sock.send(lengthstr[metasent:])
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


    def vreceive_notused(self):
        totrec=0
        metarec=0
        msgArray = []
        metaArray = []
        streamtoreturn = ''.encode('utf-8')
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
                
                totrec += len(chunk)
                msgArray.append(chunk)
                streamtoreturn = streamtoreturn + chunk

            #return ''.join(msgArray)
            out_ndarray = np.asarray(msgArray)
            test_stream_ndarray = np.asarray(streamtoreturn)
            #return msgArray
            #return streamtoreturn
            return out_ndarray
        except Exception as e:
            print("exception in vreceive: " + str(e))
            return False
   


        
