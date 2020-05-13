#import socket, videosocket
import socket
import errno
from threading import Thread
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

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_audio
    global self_username
    global audio_in
    global audio_out
    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    client_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self_username = my_username

    try:
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
    set_output_device_options()
    """audio_in = sd.InputStream(samplerate=44100, dtype='float32')
    audio_out = sd.OutputStream(samplerate=44100, dtype='float32')
    if not (audio_in):
        print('Can not open microphone')
        #client_socket_video.close()
        return False"""

    return 1

# Sends a message to the server - NOT Used for video. 
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

def stop_audio_comm():
    stop_send_thread()
    stop_listen_thread()

def stop_send_thread():
    global thread_send_audio

    if( (thread_send_audio != None) and (thread_send_audio.is_alive() == True)):
        thread_send_audio._stop()
    thread_send_audio = None

def stop_listen_thread():
    global thread_listen_audio

    if( (thread_listen_audio != None) and (thread_listen_audio.is_alive() == True)):
        thread_listen_audio._stop()

    thread_listen_audio = None

def start_sending_audio(send_callback, error_callback):
    global thread_send_audio
    if (audio_in != None):
        #print('before Thread send_video')
        thread_send_audio = Thread(target=send_audio, args=(send_callback, error_callback), daemon=True)
        thread_send_audio.start()
        #print('after Thread send_video')

def send_audio(send_callback, error_callback):
    #global vsock
    global audio_in
    audio_in = sd.InputStream(samplerate=44100, dtype='float32')
    audio_in.start()
    while True:
        try:
            frame, ret = audio_in.read(READ_SIZE)

            shape_row_bytes = (str(frame.shape[0])).encode('utf-8')
            message_header = f"{len(shape_row_bytes):<{NP_ROW_CHARS_SIZE}}".encode('utf-8')
            client_socket_audio.send(message_header + shape_row_bytes)

            shape_col_bytes = (str(frame.shape[1])).encode('utf-8')
            message_header = f"{len(shape_col_bytes):<{NP_COL_CHARS_SIZE}}".encode('utf-8')
            client_socket_audio.send(message_header + shape_col_bytes)

            #now send the entire nparray as bytes
            send_bytes = frame.tobytes()
            totalsent = 0
            send_size = (frame.shape[0] * frame.shape[1])
            while totalsent < send_size :
                sent = client_socket_audio.send(send_bytes)
                if sent == 0:
                    print("send_audio: During sending frame Socket connection broken. breaking the current send operation")
                    #raise RuntimeError("Socket connection broken")
                    break #this means we will exit the current send and sending will stop to server
                totalsent += sent
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in send_audio. Stopping the send thread. :' + str(e))
            #if we get exception in sending, that means server has stopped and we need to stop sending
            #break #breaking out of while loop


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
    global audio_out

    audio_out = sd.OutputStream(samplerate=44100, dtype='float32')
    audio_out.start()
    while True:
        try:
            username_header = client_socket_audio.recv(HEADER_LENGTH)
            #print('after client_socket_video.recv')

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                print('Connection closed by server')
                error_callback('Connection closed by the server', False)

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())
            #print('after username_length: ' + str(username_length))

            # Receive and decode username
            username = client_socket_audio.recv(username_length).decode('utf-8')
            #print('client_socket_video.recv: username= ' + username)

            #now get the share of nparray. shape is (row, cols, dim) ex. shape: (480, 640, 3)
            #print('before client_socket_video.recv to get row')
            shape_row_header = client_socket_audio.recv(NP_ROW_CHARS_SIZE)
            shape_row_length = int(shape_row_header.decode('utf-8').strip())
            shape_row_int = int(client_socket_audio.recv(shape_row_length).decode('utf-8'))

            #print('before client_socket_video.recv to get col')
            shape_col_header = client_socket_audio.recv(NP_COL_CHARS_SIZE)
            shape_col_length = int(shape_col_header.decode('utf-8').strip())
            shape_col_int = int(client_socket_audio.recv(shape_col_length).decode('utf-8'))

            totrec = 0
            frame = ''.encode('utf-8')
            message_size = shape_row_int*shape_col_int
            while totrec<message_size :
                chunk = client_socket_audio.recv(message_size - totrec)
                if chunk == '':
                    print("receive audion error: During receiving frame socket connection broken, Breaking the current receive operation")
                    #raise RuntimeError("Socket connection broken")
                    break
                totrec += len(chunk)
                frame = frame + chunk

            #print('after frame = vsock.vreceive()')

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
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in listen. Stopping the listen thread.')
