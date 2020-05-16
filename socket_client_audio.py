#import socket, videosocket
import socket
import errno
from threading import Thread, Event
from videofeed import VideoFeed
import sounddevice as sd
import logging
import numpy as np

HEADER_LENGTH = 10
NP_ROW_CHARS_SIZE = 10
NP_COL_CHARS_SIZE = 4
READ_SIZE = 1000
client_socket_audio = None
audio_in = None
audio_out = None
self_username = ''
thread_send_audio = None
thread_listen_audio = None
pill_to_kill_send_thread = None
pill_to_kill_listen_thread = None
stop_connection = False

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_audio
    global self_username
    global audio_in
    global audio_out
    global pill_to_kill_send_thread
    global pill_to_kill_listen_thread
    global stop_connection
    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    stop_connection = False
    try:
        client_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to a given ip and port
        client_socket_audio.connect((ip, port))
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
        username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
        #print('before client_socket_video.send(username_header + username)')
        ret = client_socket_audio.send(username_header + username)
        #print('after client_socket_video.send(username_header + username)')
        if(ret <= 0):
            close_connection()
            return -2
    except Exception as e:
        close_connection()
        return -2

    set_input_device_options()
    audio_in = sd.InputStream(samplerate=44100, dtype='float32')
    audio_in.start()

    set_output_device_options()
    audio_out = sd.OutputStream(samplerate=44100, dtype='float32')
    audio_out.start()

    """audio_in = sd.InputStream(samplerate=44100, dtype='float32')
    audio_out = sd.OutputStream(samplerate=44100, dtype='float32')
    if not (audio_in):
        print('Can not open microphone')
        #client_socket_video.close()
        return False"""

    pill_to_kill_listen_thread = Event()
    pill_to_kill_send_thread = Event()

    return 1

# Sends a message to the server - used to send DATA or CLOSING message
def send(message):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket_audio.send(message_header + message)

def set_input_device_options():
    return

def set_output_device_options():
    return

def close_connection():
    global client_socket_audio
    stop_audio_comm()    
    if( client_socket_audio != None ):
        client_socket_audio.close()
    client_socket_audio = None

    #sd.InputStream().close()
    #sd.OutputStream().close()

def stop_audio_comm():
    global stop_connection

    stop_connection = True

    #wait for the send thread to close
    try:
        while((thread_send_audio != None) and (thread_send_audio.is_alive())):
            print('waiting for send thread to become None')
    except Exception as e:
        print('stopped send thread')

    if(audio_in != None):
        audio_in.close()

    #send CLOSING
    if( client_socket_audio != None ):
        send('CLOSING')

    try:
        while((thread_listen_audio != None) and (thread_listen_audio.is_alive())):
            print('waiting for listen thread to become None')
    except Exception as e:
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
            send('DATA')

            frame, ret = audio_in.read(READ_SIZE)

            shape_row_bytes = (str(frame.shape[0])).encode('utf-8')
            message_header = f"{len(shape_row_bytes):<{NP_ROW_CHARS_SIZE}}".encode('utf-8')
            client_socket_audio.send(message_header + shape_row_bytes)
            #print('after : client_socket_audio.send(message_header + shape_row_bytes)')
            
            shape_col_bytes = (str(frame.shape[1])).encode('utf-8')
            message_header = f"{len(shape_col_bytes):<{NP_COL_CHARS_SIZE}}".encode('utf-8')
            client_socket_audio.send(message_header + shape_col_bytes)
            #print('after : client_socket_audio.send(message_header + shape_col_bytes)')

            #now send the entire nparray as bytes
            send_bytes = frame.tobytes()
            totalsent = 0
            #send_size = (frame.shape[0] * frame.shape[1])
            send_size = len(send_bytes)
            send(str(send_size))
            while totalsent < send_size :
                sent = client_socket_audio.send(send_bytes)
                if sent == 0:
                    print("client_socket_audio.send(send_bytes): During sending frame Socket connection broken. breaking the current send operation")
                    #raise RuntimeError("Socket connection broken")
                    break #this means we will exit the current send and sending will stop to server
                totalsent += sent
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
    # Now we want to loop over received messages (there might be more than one) and print them
    #while True:
    while not pill_to_kill_listen_thread.wait(0):
        try:
            username_header = client_socket_audio.recv(HEADER_LENGTH)
            #print('after :username_header = client_socket_audio.recv(HEADER_LENGTH)')

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                print('Connection closed by server: if not len(username_header)')
                error_callback('Connection closed by the server', False)

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())
            #print('after username_length: ' + str(username_length))

            # Receive and decode username
            username = client_socket_audio.recv(username_length).decode('utf-8')
            #print('client_socket_audio.recv: username= ' + username)

            keyword_header = client_socket_audio.recv(HEADER_LENGTH)
            if not len(keyword_header):
                #error_callback('Connection closed by the server', False)
                print('Connection closed by server: client_socket_audio.recv(HEADER_LENGTH)')
                continue

            # Convert header to int value
            keyword_length = int(keyword_header.decode('utf-8').strip())
            keyworkd_message = client_socket_audio.recv(keyword_length).decode('utf-8')

            if(keyworkd_message.upper() == 'CLOSING'):
                print('received CLOSING message from: '+username)
                """if(audio_out.closed == False):
                    audio_out.close()
                audio_out = None"""
            elif(keyworkd_message.upper() == 'ACK_CLOSED'):
                #print('Stopping listen thread as received ACK_CLOSED message from: '+username)
                pill_to_kill_listen_thread.set()
                break                
            elif(keyworkd_message.upper() == 'DATA'):
                #now get the share of nparray. shape is (row, cols, dim) ex. shape: (480, 640, 3)
                #print('before :client_socket_audio.recv(NP_ROW_CHARS_SIZE)')
                shape_row_header = client_socket_audio.recv(NP_ROW_CHARS_SIZE)
                shape_row_length = int(shape_row_header.decode('utf-8').strip())
                shape_row_int = int(client_socket_audio.recv(shape_row_length).decode('utf-8'))

                #print('before :client_socket_audio.recv(NP_COL_CHARS_SIZE)')
                shape_col_header = client_socket_audio.recv(NP_COL_CHARS_SIZE)
                shape_col_length = int(shape_col_header.decode('utf-8').strip())
                shape_col_int = int(client_socket_audio.recv(shape_col_length).decode('utf-8'))

                #get the size of the bytes array
                message_size_header = client_socket_audio.recv(HEADER_LENGTH)
                message_size_length = int(message_size_header.decode('utf-8').strip())
                message_size = int(client_socket_audio.recv(message_size_length).decode('utf-8'))

                totrec = 0
                frame = ''.encode('utf-8')
                #message_size = shape_row_int*shape_col_int
                while totrec<message_size :
                    chunk = client_socket_audio.recv(message_size - totrec)
                    if chunk is False:
                        print("client_socket_audio.recv(message_size - totrec): During receiving frame socket connection broken, Breaking the current receive operation")
                        #raise RuntimeError("Socket connection broken")
                        break
                    totrec += len(chunk)
                    frame = frame + chunk

                #print('after frame = client_socket_audio.recv')

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
                    received_nparray = np.frombuffer(frame, dtype=np.float32)
                    received_nparray = received_nparray.reshape(shape_row_int, shape_col_int)
                    audio_out.write(received_nparray)
                    #print('after : audio_out.write(received_nparray)')
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in listen :' + str(e))
    
    #since we are out of while, that means a 'CLOSING' message was received by a 
    print('Stopped listen audio thread')
    #pill_to_kill_listen_thread = None