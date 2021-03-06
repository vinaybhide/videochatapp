#v0.9 - Alpha 1
# #v0.8
#import socket, videosocket
import socket
from threading import Thread, Event
#from videofeed import VideoFeed
import sounddevice as sd
import logging
import numpy as np
import zlib
import time

HEADER_LENGTH = 10
NP_ROW_CHARS_SIZE = 10
NP_COL_CHARS_SIZE = 4
READ_SIZE = 4096
client_socket_audio_send = None
client_socket_audio_recv = None
audio_in = None
audio_out = None
self_username = ''
thread_send_audio = None
thread_listen_audio = None
pill_to_kill_send_thread = None
pill_to_kill_listen_thread = None
stop_connection = False
logger = None

# Connects to the server
def connect(ip, port, my_username, input_device_dict, output_device_dict, input_device_id, output_device_id, error_callback):
    global client_socket_audio_send
    global client_socket_audio_recv
    global self_username
    global audio_in
    global audio_out
    global pill_to_kill_send_thread
    global pill_to_kill_listen_thread
    global stop_connection
    #global logger

    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    """logging.basicConfig(filename=my_username+"_audio_client.log", 
                    format='%(asctime)s %(message)s',
                    filemode='a') 

    logger=logging.getLogger()
    logger.setLevel(logging.DEBUG) """

    stop_connection = False
    try:
        client_socket_audio_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to a given ip and port
        client_socket_audio_send.connect((ip, port))
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        close_connection()
        return -1

    try:
        # Prepare username and header and send them
        # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
        self_username = my_username
        username = my_username.encode('utf-8')
        keyword = 'SEND_SOCKET'.encode('utf-8')
        sep_bytes = ':'.encode('utf-8')
        username_header = f"{len(keyword+sep_bytes+username):<{HEADER_LENGTH}}".encode('utf-8')
        ret = client_socket_audio_send.send(username_header + keyword+sep_bytes+username)
        if(ret <= 0):
            close_connection()
            return -2
    except Exception as e:
        close_connection()
        return -2

    try:
        client_socket_audio_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to a given ip and port
        client_socket_audio_recv.connect((ip, port))
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        close_connection()
        return -1

    try:
        # Prepare username and header and send them
        # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
        keyword = 'READ_SOCKET'.encode('utf-8')
        username_header = f"{len(keyword+sep_bytes+username):<{HEADER_LENGTH}}".encode('utf-8')
        ret = client_socket_audio_recv.send(username_header + keyword+sep_bytes+username)
        if(ret <= 0):
            close_connection()
            return -2
    except Exception as e:
        close_connection()
        return -2

    #audio_in = sd.InputStream(samplerate=44100, dtype='float32')
    sd.default.samplerate = 44100
    sd.default.latency = ['high', 'high']
    sd.default.dtype = ['int24', 'int24']
    sd.default.blocksize = READ_SIZE
    sd.default.channels = [input_device_dict['max_input_channels'], output_device_dict['max_output_channels']]
    sd.default.device = [input_device_id, output_device_id]

    try:
        audio_in = sd.RawInputStream(
            #samplerate=int(input_device_dict['default_samplerate']), 
            #samplerate=44100,
            #blocksize=READ_SIZE, 
            #blocksize=0, 
            #device=input_device_id, 
            #channels=input_device_dict['max_input_channels'],  
            #channels=1,
            #dtype=np.float32, 
            #dtype='float32',
            #latency=input_device_dict['default_low_input_latency'] 
             )
        #audio_in = sd.RawInputStream()
        audio_in.start()
    except Exception as e:
        close_connection()
        return -3
    try:
        audio_out = sd.RawOutputStream(
            #samplerate=int(output_device_dict['default_samplerate']), 
            #samplerate=44100,
            #blocksize=READ_SIZE, 
            #blocksize=0, 
            #device=output_device_id, 
            #channels=output_device_dict['max_output_channels'],  
            #channels=1,
            #dtype=np.float32, 
            #dtype='float32',
            #dtype=np.int24, 
            #latency=output_device_dict['default_high_output_latency'] 
             )
        #audio_out = sd.RawOutputStream()

        audio_out.start()
    except Exception as e:
        close_connection()
        return -4

    pill_to_kill_listen_thread = Event()
    pill_to_kill_send_thread = Event()

    return 1

# Sends a message to the server - used to send DATA or CLOSING message
def send(message, header_size=HEADER_LENGTH):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{header_size}}".encode('utf-8')
    to_send = message_header + message
    send_size = len(to_send)
    tot_sent = 0
    while tot_sent < send_size:
        ret = client_socket_audio_send.send(to_send[tot_sent:send_size])
        tot_sent += ret

def send_bytes(bytes_to_send, header_size=HEADER_LENGTH):
    message_header = f"{len(bytes_to_send):<{header_size}}".encode('utf-8')
    to_send = message_header + bytes_to_send
    send_size = len(to_send)
    tot_sent = 0
    while tot_sent < send_size:
        ret = client_socket_audio_send.send(to_send[tot_sent:send_size])
        tot_sent += ret

def receive_message(receive_size=HEADER_LENGTH):

    try:
        # Receive our "header" containing message length, it's size is defined and constant
        #message_header = client_socket.recv(receive_size)

        message_header = ''.encode('utf-8')
        totrec = 0
        while totrec<receive_size :
            chunk = client_socket_audio_recv.recv(receive_size - totrec)
            #if chunk == '':
            if chunk is False:
                print("In receive_message: received 0 bytes during receive of data size.")
                #raise RuntimeError("Socket connection broken")
                #break
                return False
            totrec += len(chunk)
            message_header = message_header + chunk


        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        message_data = ''.encode('utf-8')
        totrec = 0
        while totrec<message_length :
            chunk = client_socket_audio_recv.recv(message_length - totrec)
            #if chunk == '':
            if chunk is False:
                print("In receive_message: received 0 bytes during receive of data.")
                #raise RuntimeError("Socket connection broken")
                #break
                return False
            totrec += len(chunk)
            message_data = message_data + chunk

        if not len(message_data):
            return False

        # Return an object of message header and message data
        #return {'header': message_header, 'data': client_socket.recv(message_length)}
        return {'header': message_header, 'data': message_data}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

def close_connection():
    global client_socket_audio_send
    global client_socket_audio_recv
    stop_audio_comm()    
    if( client_socket_audio_send != None ):
        client_socket_audio_send.close()
    if( client_socket_audio_recv != None ):
        client_socket_audio_recv.close()

    client_socket_audio_send = None
    client_socket_audio_recv = None


def stop_audio_comm():
    global stop_connection

    stop_connection = True

    #wait for the send thread to close
    try:
        while((thread_send_audio != None) and (thread_send_audio.is_alive())):
            print('waiting for send thread to become None')
    except Exception as e:
        print('stopped send thread')

    print('stopped send thread')

    if(audio_in != None):
        audio_in.close()

    #send CLOSING
    if( client_socket_audio_send != None ):
        send('CLOSING')

    try:
        while((thread_listen_audio != None) and (thread_listen_audio.is_alive())):
            print('waiting for listen thread to become None')
    except Exception as e:
        print('stopped listen thread')

    print('stopped listen thread')

    if(audio_out != None):
        audio_out.close()


def start_sending_audio(send_callback, error_callback):
    global thread_send_audio
    if (audio_in != None):
        #print('before Thread send_video')
        thread_send_audio = Thread(target=send_audio, args=(send_callback, error_callback), daemon=True)
        thread_send_audio.start()
        #print('after Thread send_video')

def send_audio(send_callback, error_callback):
    #global vsock
    #while True:
    while not pill_to_kill_send_thread.wait(0):
        try:
            frame, ret = audio_in.read(READ_SIZE)
            #frame, ret = audio_in.read(audio_in.read_available)
            
            frame_bytes = zlib.compress(frame[:], -1)
            """shape_str = f"{frame.shape[0]},{frame.shape[1]}"
            send(shape_str, HEADER_LENGTH)

            #now send the entire nparray as bytes
            send_bytes = frame.tobytes()"""
    
            #compressed_frame_bytes = zlib.compress(frame_bytes, -1)
            #send_bytes(compressed_frame_bytes, HEADER_LENGTH)
            send('DATA')
            send_bytes(frame_bytes)
            #logger.info(f'after send bytes : {int(round(time.time() * 1000))}')
            #send_size = len(send_bytes)
            """send_size = len(compressed_send_bytes)

            send(str(send_size))
            
            totalsent = 0
            while totalsent < send_size :
                #sent = client_socket_audio_send.send(send_bytes)
                sent = client_socket_audio_send.send(compressed_send_bytes)
                if sent == 0:
                    print("client_socket_audio_send.send(send_bytes): During sending frame Socket connection broken. breaking the current send operation")
                    #raise RuntimeError("Socket connection broken")
                    break #this means we will exit the current send and sending will stop to server
                totalsent += sent"""
            if(stop_connection == True):
                #print('before pill_to_kill_send_thread.set()')
                pill_to_kill_send_thread.set()
                #print('after pill_to_kill_send_thread.set()')
                break
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in send_audio :' + str(e))
            #if we get exception in sending, that means server has stopped and we need to stop sending
            #break #breaking out of while loop
    #if we are out of while loop that means we are closing the socket. We need to tell the server and server
    # will inform the other clients
    #we will first send a braodcast message to let server know we are closing connection
    #server in turn will notify all the clients that I am closing connection
    #clients who receive the closing message in listner, will close that users video window
    #and then they will continue to wait for a new message from server
    #send('CLOSING')
    print('Stopped send audio thread')
    #pill_to_kill_send_thread = None


# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
def start_listening(listen_callback, error_callback):
    global thread_listen_audio
    #print('before Thread listen')
    thread_listen_audio = Thread(target=listen, args=(listen_callback, error_callback), daemon=True)
    thread_listen_audio.start()
    #print('after Thread listen')

# Listens for incomming messages
def listen(listen_callback, error_callback):
    global pill_to_kill_listen_thread
    global pill_to_kill_send_thread
    # Now we want to loop over received messages (there might be more than one) and print them
    #while True:
    while not pill_to_kill_listen_thread.wait(0):
        try:
            username_dict = receive_message()
            if(username_dict is False):
                print('username_dict is False. continuing...')
                continue
            keyword_dict = receive_message()
            if(keyword_dict is False):
                print('keyword_dict is False. continuing...')
                continue

            username = (username_dict['data'].decode('utf-8')).strip()


            keyworkd_message = (keyword_dict['data'].decode('utf-8')).strip()

            if(keyworkd_message.upper() == 'CLOSING'):
                print('received CLOSING message from: '+username)
            elif(keyworkd_message.upper() == 'ACK_CLOSED'):
                #print('Stopping listen thread as received ACK_CLOSED message from: '+username)
                pill_to_kill_listen_thread.set()
                break                
            elif(keyworkd_message.upper() == 'DATA'):
                #now get the share of nparray. shape is (row, cols, dim) ex. shape: (480, 640, 3)
                #print('before :client_socket_audio_send.recv(NP_ROW_CHARS_SIZE)')

                """shape_dict = receive_message(client_socket_audio_send, HEADER_LENGTH)
                if(shape_dict is False):
                    print('shape_dict is False. continuing...')
                    continue

                shape_size_str = (shape_dict['data'].decode('utf-8')).strip()

                shape_size_split = shape_size_str.split(',')
                shape_row_int = int(shape_size_split[0])
                shape_col_int = int(shape_size_split[1])"""


                #get the size of the bytes array

                """message_size_dict = receive_message(client_socket_audio_send, HEADER_LENGTH)
                if(message_size_dict is False):
                    print('message_size_dict is False. continuing...')
                    continue

                message_size = int((message_size_dict['data'].decode('utf-8')).strip())

                totrec = 0
                frame = ''.encode('utf-8')
                #message_size = shape_row_int*shape_col_int
                while totrec<message_size :
                    chunk = client_socket_audio_send.recv(message_size - totrec)
                    if chunk is False:
                        print("client_socket_audio_send.recv(message_size - totrec): During receiving frame socket connection broken, Breaking the current receive operation")
                        #raise RuntimeError("Socket connection broken")
                        break
                    totrec += len(chunk)
                    frame = frame + chunk"""
                
                message_dict = receive_message()
                if(message_dict is False):
                    print('message_dict is False. continuing...')
                    continue
                frame = message_dict['data']
                #print('after frame = client_socket_audio_send.recv')

                # we received bytes which we need to convert to np.ndarray
                """ sample to convert nparray to bytes and bytes to nparray
                    In [3]: i = np.arange(28*28).reshape(28, 28)
                    In [4]: k = i.tobytes()
                    In [5]: y = np.frombuffer(k, dtype=i.dtype)
                    In [6]: y.shape
                    Out[6]: (784,)
                    In [7]: np.array_equal(y.reshape(28, 28), i)
                    Out[7]: True            
                    dtype('uint8')
                """
                if(len(frame) > 0):
                    frame = zlib.decompress(frame)
                    """received_nparray = np.frombuffer(frame, dtype=np.float32)
                    received_nparray = received_nparray.reshape(shape_row_int, shape_col_int)
                    audio_out.write(received_nparray)"""
                    ret = audio_out.write(frame)

                    #logger.info(f'after audio_out.write : {int(round(time.time() * 1000))}')

                    #print('after : audio_out.write(received_nparray)')
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in listen :' + str(e))
    #since we are out of while, that means a 'CLOSING' message was received by a 
    pill_to_kill_listen_thread.set()
    if(pill_to_kill_send_thread != None):
        pill_to_kill_send_thread.set()
    print('Stopped listen audio thread')
    #pill_to_kill_listen_thread = None