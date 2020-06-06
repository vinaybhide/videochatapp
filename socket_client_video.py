#v0.8
#import socket, videosocket
import socket
import errno
from threading import Thread, Event
from videofeed import VideoFeed
from cv2 import cv2
import logging
import numpy as np
import zlib

HEADER_LENGTH = 10
NP_ROW_CHARS_SIZE = 4
NP_COL_CHARS_SIZE = 4
NP_DIM_CHARS_SIZE = 4
client_socket_video_send = None
client_socket_video_recv = None
#vsock = None
thread_send_video = None
thread_listen_video = None
pill_to_kill_send_thread = None
pill_to_kill_listen_thread = None
stop_connection = False

videofeed = None
self_username = ''
window_list = []

#currently this is getting called from ConnectPage. 
# But i think this needs to get called from 'Start Video' button. Will need to check this logic

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_video_send
    global client_socket_video_recv
    #global vsock
    global videofeed
    global self_username
    global pill_to_kill_send_thread
    global pill_to_kill_listen_thread
    global stop_connection
    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    stop_connection = False
    try:
        client_socket_video_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to a given ip and port
        client_socket_video_send.connect((ip, port))
        #vsock = videosocket.videosocket (client_socket_video_send)
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        close_connection()
        return -1

    # Prepare username and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    try:
        self_username = my_username
        username = my_username.encode('utf-8')
        keyword = 'SEND_SOCKET'.encode('utf-8')
        sep_bytes = ':'.encode('utf-8')
        username_header = f"{len(keyword+sep_bytes+username):<{HEADER_LENGTH}}".encode('utf-8')
        #print('before client_socket_video_send.send(username_header + username)')
        ret = client_socket_video_send.send(username_header + keyword+sep_bytes+username)
        if(ret <= 0):
            close_connection()
            return -2
        #print('after client_socket_video_send.send(username_header + username)')
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        close_connection()
        return -2

    try:
        client_socket_video_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to a given ip and port
        client_socket_video_recv.connect((ip, port))
        #vsock = videosocket.videosocket (client_socket_video_send)
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        close_connection()
        return -1

    # Prepare username and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    try:
        keyword = 'READ_SOCKET'.encode('utf-8')
        username_header = f"{len(keyword+sep_bytes+username):<{HEADER_LENGTH}}".encode('utf-8')
        #print('before client_socket_video_send.send(username_header + username)')
        ret = client_socket_video_recv.send(username_header + keyword+sep_bytes+username)
        if(ret <= 0):
            close_connection()
            return -2
        #print('after client_socket_video_send.send(username_header + username)')
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        close_connection()
        return -2


    try:
        videofeed = VideoFeed(1,my_username,1)
       
        if not (videofeed.capture.isOpened()):
            videofeed = None
            print('Can not open self capture camera')
            pill_to_kill_listen_thread = Event()
            return -3
    except Exception as e:
        # Connection error
        #error_callback('Connection error: {}'.format(str(e)), False)
        return -3

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
        ret = client_socket_video_send.send(to_send[tot_sent:send_size])
        tot_sent += ret
    #client_socket_video_send.send(message_header + message)

def send_frame(message, frame_bytes, header_size=HEADER_LENGTH):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message+frame_bytes):<{header_size}}".encode('utf-8')
    to_send = message_header + message + frame_bytes
    send_size = len(to_send)
    tot_sent = 0
    while tot_sent < send_size:
        ret = client_socket_video_send.send(to_send[tot_sent:send_size])
        tot_sent += ret

def receive_message(receive_size=HEADER_LENGTH):
    try:
        # Receive our "header" containing message length, it's size is defined and constant
        #message_header = client_socket.recv(receive_size)

        message_header = ''.encode('utf-8')
        totrec = 0
        while totrec<receive_size :
            chunk = client_socket_video_recv.recv(receive_size - totrec)
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
            chunk = client_socket_video_recv.recv(message_length - totrec)
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
    global client_socket_video_send
    global client_socket_video_recv
    global videofeed

    stop_video_comm()    

    if( client_socket_video_send != None ):
        client_socket_video_send.close()

    if( client_socket_video_recv != None ):
        client_socket_video_recv.close()

    #videofeed = None
    client_socket_video_send = None
    client_socket_video_recv = None

def stop_video_comm():
    global stop_connection

    stop_connection = True

    #wait for the send thread to close
    try:
        while((thread_send_video !=None) and (thread_send_video.is_alive())):
            print('waiting for send thread to become None')
    except Exception as e:
        print('stopped send thread')

    print('video send thread stopped')

    if((videofeed != None) and (videofeed.capture.isOpened())):
        videofeed.capture.release()
        cv2.destroyWindow(self_username)

    #send CLOSING
    if( client_socket_video_send != None ):
        send('CLOSING')

    try:
        while((thread_listen_video != None) and (thread_listen_video.is_alive())):
            print('waiting for listen thread to become None')
    except Exception as e:
        print('stopped listen thread')

    print('video listen thread stopped')
    #cv2.destroyAllWindows()

def start_sending_video(send_callback, error_callback):
    global thread_send_video
    if (videofeed.capture.isOpened()):
        #print('before Thread send_video')
        thread_send_video = Thread(target=send_video, args=(send_callback, error_callback), daemon=True)
        thread_send_video.start()
        #print('after Thread send_video')

def send_video(send_callback, error_callback):
    #global vsock
    global videofeed
    global pill_to_kill_send_thread

    #while True:
    while not pill_to_kill_send_thread.wait(0):
        try:
            #ret = cv2.getWindowProperty(self_username, cv2.WND_PROP_VISIBLE)
            #if(ret > 0):
            """x = cv2.waitKey(1)
            if(x == 27):
                cv2.destroyAllWindows()
                break"""

            frame=videofeed.get_frame()
            #get_frame returns np.ndarray, change the np.ndarray to bytes and then send bytes
            #we also need to send the shape of nparray so that it can be reconstructed in reveice

            #if(client_socket_video_send != None):
            """shape_row_bytes = (str(frame.shape[0])).encode('utf-8')
            message_header = f"{len(shape_row_bytes):<{NP_ROW_CHARS_SIZE}}".encode('utf-8')
            client_socket_video_send.send(message_header + shape_row_bytes)

            shape_col_bytes = (str(frame.shape[1])).encode('utf-8')
            message_header = f"{len(shape_col_bytes):<{NP_COL_CHARS_SIZE}}".encode('utf-8')
            client_socket_video_send.send(message_header + shape_col_bytes)

            shape_dim_bytes = (str(frame.shape[2])).encode('utf-8')
            message_header = f"{len(shape_dim_bytes):<{NP_DIM_CHARS_SIZE}}".encode('utf-8')
            client_socket_video_send.send(message_header + shape_dim_bytes)"""

            """shape_str = f"{frame.shape[0]},{frame.shape[1]},{frame.shape[2]}"
            send(shape_str, HEADER_LENGTH)"""
            
            #shape_str_bytes = shape_str.encode('utf-8')
            #message_header = f"{len(shape_str_bytes):<{HEADER_LENGTH}}".encode('utf-8')
            #client_socket_video_send.send(message_header + shape_str_bytes)

            #now send the entire nparray as bytes
            send_bytes = frame.tobytes()
            #send_size = (frame.shape[0] * frame.shape[1] * frame.shape[2])

            #compress the video bytes - 9 is max compression amd 1 is lowest compression, -1 is default (6)
            #compressed_send_bytes = zlib.compress(send_bytes, 9)
            #compressed_send_bytes = zlib.compress(send_bytes, -1)
            
            #send_size = len(send_bytes)
            #send_size = len(compressed_send_bytes)
            #send(str(send_size))

            #frame_size = f"{frame.shape[0]},{frame.shape[1]},{frame.shape[2]},{send_size}"
            frame_size = f"{frame.shape[0]},{frame.shape[1]},{frame.shape[2]},"
            #send(frame_size)
            send('DATA')
            send_frame(frame_size, send_bytes)
            """totalsent = 0
            while totalsent < send_size :
                #sent = client_socket_video_send.send(send_bytes)
                sent = client_socket_video_send.send(compressed_send_bytes)
                if sent == 0:
                    print("client_socket_video_send.send(send_bytes): During sending frame Socket connection broken. breaking the current send operation")
                    #raise RuntimeError("Socket connection broken")
                    break #this means we will exit the thread and sending will stop
                totalsent += sent"""


            videofeed.set_frame(frame)
            if(stop_connection == True):
                #print('before pill_to_kill_send_thread.set()')
                pill_to_kill_send_thread.set()
                #print('after pill_to_kill_send_thread.set()')
                break
            #else:
            #    cv2.destroyAllWindows()
            #    break
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in send_video. Stopping the send thread.: ' + str(e))
            #cv2.destroyWindow(self_username)
            #vsock = None
            #videofeed = None
            #client_socket_video_send.close()
            #error_callback('Reading error: {}'.format(str(e)), False)
            #break

    #if we are out of while loop that means we are closing the socket. We need to tell the server and server
    # will inform the other clients
    #we will first send a braodcast message to let server know we are closing connection
    #server in turn will notify all the clients that I am closing connection
    #clients who receive the closing message in listner, will close that users video window
    #and then they will continue to wait for a new message from server
    #send('CLOSING')
    print('Stopped send video thread')
    #pill_to_kill_send_thread = None

# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
#def start_listening(incoming_message_callback, error_callback):
def start_listening(listen_callback, error_callback):
    global thread_listen_video
    #print('before Thread listen')
    thread_listen_video = Thread(target=listen, args=(listen_callback, error_callback), daemon=True)
    thread_listen_video.start()
    #print('after Thread listen')

# Listens for incomming messages
def listen(listen_callback, error_callback):
    #global vsock
    #global videofeed
    global pill_to_kill_listen_thread
    global pill_to_kill_send_thread
    global window_list
    #global thread_listen_video
    #global thread_send_video

    # Now we want to loop over received messages (there might be more than one) and print them
    #while True:
    while not pill_to_kill_listen_thread.wait(0):
        try:
            #while True:
            #if((vsock != None) and (videofeed != None)):
            #first get the username
            # Receive our "header" containing username length, it's size is defined and constant
            """username_header = client_socket_video_send.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                #error_callback('Connection closed by the server', False)
                print('Connection closed by server: if not len(username_header):')
                continue

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())
            #print('after username_length: ' + str(username_length))

            # Receive and decode username
            username = client_socket_video_send.recv(username_length).decode('utf-8')
            #print('client_socket_video_send.recv: username= ' + username)"""

            username_dict = receive_message()
            if(username_dict is False):
                print('username_dict is False. continuing...')
                continue

            keyword_dict = receive_message()
            if(keyword_dict is False):
                print('keyword_dict is False. continuing...')
                continue

            username = (username_dict['data'].decode('utf-8')).strip()

            """keyword_header = client_socket_video_send.recv(HEADER_LENGTH)
            if not len(keyword_header):
                #error_callback('Connection closed by the server', False)
                print('Connection closed by server in keyword_header = client_socket_video_send.recv(HEADER_LENGTH)')
                continue

            # Convert header to int value
            keyword_length = int(keyword_header.decode('utf-8').strip())
            keyworkd_message = client_socket_video_send.recv(keyword_length).decode('utf-8')"""


            keyworkd_message = (keyword_dict['data'].decode('utf-8')).strip()

            if(keyworkd_message.upper() == 'CLOSING'):
                #we need to close the video window of the specific sender
                #if(cv2.getWindowProperty(username + '_receiver', 0) == 0):
                if (username + '_receiver') in window_list:
                    window_list.remove(username + '_receiver')
                    cv2.destroyWindow(username + '_receiver')
            elif(keyworkd_message.upper() == 'ACK_CLOSED'):
                for each_window in window_list:
                    cv2.destroyWindow(each_window)
                window_list.clear()
                pill_to_kill_listen_thread.set()
                break
            elif(keyworkd_message.upper() == 'DATA'):
                #now get the share of nparray. shape is (row, cols, dim) ex. shape: (480, 640, 3)
                #print('before client_socket_video_send.recv to get row')
                """shape_size_header = client_socket_video_send.recv(HEADER_LENGTH)
                shape_size_length = int(shape_size_header.decode('utf-8').strip())

                shape_size_str = client_socket_video_send.recv(shape_size_length).decode('utf-8')"""

                shape_dict = receive_message()
                if(shape_dict is False):
                    print('shape_dict is False. continuing...')
                    continue

                #shape_size_str = (shape_dict['data'].decode('utf-8')).strip()

                #shape_size_split = shape_size_str.split(',')
                shape_size_split = shape_dict['data'].split(','.encode('utf-8'), 3)
                shape_row_int = int(shape_size_split[0].decode('utf-8'))
                shape_col_int = int(shape_size_split[1].decode('utf-8'))
                shape_dim_int = int(shape_size_split[2].decode('utf-8'))
                #message_size = int(shape_size_split[3])
                frame = shape_size_split[3]

                """shape_row_header = client_socket_video_send.recv(NP_ROW_CHARS_SIZE)
                shape_row_length = int(shape_row_header.decode('utf-8').strip())
                shape_row_int = int(client_socket_video_send.recv(shape_row_length).decode('utf-8'))

                #print('before client_socket_video_send.recv to get col')
                shape_col_header = client_socket_video_send.recv(NP_COL_CHARS_SIZE)
                shape_col_length = int(shape_col_header.decode('utf-8').strip())
                shape_col_int = int(client_socket_video_send.recv(shape_col_length).decode('utf-8'))

                #print('before client_socket_video_send.recv to get dim')
                shape_dim_header = client_socket_video_send.recv(NP_DIM_CHARS_SIZE)
                shape_dim_length = int(shape_dim_header.decode('utf-8').strip())
                shape_dim_int = int(client_socket_video_send.recv(shape_dim_length).decode('utf-8'))
                #print('after client_socket_video_send.recv to get dim')"""

                #get the size of the bytes array
                """message_size_header = client_socket_video_send.recv(HEADER_LENGTH)
                message_size_length = int(message_size_header.decode('utf-8').strip())
                message_size = int(client_socket_video_send.recv(message_size_length).decode('utf-8'))"""

                """message_size_dict = receive_message(client_socket_video_send, HEADER_LENGTH)
                if(message_size_dict is False):
                    print('message_size_dict is False. continuing...')
                    continue

                message_size = int((message_size_dict['data'].decode('utf-8')).strip())"""

                """totrec = 0
                frame = ''.encode('utf-8')
                #message_size = shape_row_int*shape_col_int*shape_dim_int
                while totrec<message_size :
                    chunk = client_socket_video_recv.recv(message_size - totrec)
                    if chunk == '':
                        print("client_socket_video_send.recv(message_size - totrec): During receiving frame socket connection broken, Breaking the current receive operation")
                        #raise RuntimeError("Socket connection broken")
                        break
                    totrec += len(chunk)
                    frame = frame + chunk"""

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

                    #decompress the recived frame
                    #frame = zlib.decompress(frame)
                    
                    received_nparray = np.frombuffer(frame, dtype=np.uint8)
                    received_nparray = received_nparray.reshape(shape_row_int, shape_col_int, shape_dim_int)
                    #cv2.imshow(username + '_receiver', frame)

                    # Now create OpenCV window for this username if not already created
                    #if(cv2.getWindowProperty(username + '_receiver', 0) < 0):
                    #if( cv2.getWindowProperty(username + '_receiver',cv2.WND_PROP_VISIBLE) <= 0):
                        #print('cv2.getWindowProperty < 0')
                        #cv2.namedWindow(username + '_receiver', cv2.WINDOW_AUTOSIZE)
                    #print('after cv2.namedWindow(username + \'_receiver\'')

                    if (username + '_receiver') not in window_list:
                        window_list.append(username + '_receiver')
                        cv2.namedWindow(username + '_receiver', cv2.WINDOW_AUTOSIZE)

                    cv2.imshow(username + '_receiver', received_nparray)
                    x = cv2.waitKey(1)
                    #print('after cv2.imshow(username + \'_receiver\'')
        except Exception as e:
            # Any other exception - something happened, exit
            print('Falied in listen :' + str(e))
            #cv2.destroyWindow(self_username)
            #vsock = None
            #videofeed = None
            #client_socket_video_send.close()
            #error_callback('Reading error: {}'.format(str(e)), False)
            #break
    #since we are out of while, that means a 'CLOSING' message was received by a 
    pill_to_kill_listen_thread.set()
    if(pill_to_kill_send_thread != None):
        pill_to_kill_send_thread.set()
    print('Stopped listen video thread')
