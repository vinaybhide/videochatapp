#import socket, videosocket
import socket
import errno
from threading import Thread
from videofeed import VideoFeed
import cv2
import logging
import numpy as np
HEADER_LENGTH = 10
NP_ROW_CHARS_SIZE = 4
NP_COL_CHARS_SIZE = 4
NP_DIM_CHARS_SIZE = 4
client_socket_video = None
#vsock = None
videofeed = None
self_username = ''

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_video
    #global vsock
    global videofeed
    global self_username
    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    client_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self_username = my_username

    try:
        # Connect to a given ip and port
        client_socket_video.connect((ip, port))
        #vsock = videosocket.videosocket (client_socket_video)
        videofeed = VideoFeed(1,my_username,1)
    except Exception as e:
        # Connection error
        error_callback('Connection error: {}'.format(str(e)), False)
        return False

    # Prepare username and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    username = my_username.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    print('before client_socket_video.send(username_header + username)')
    client_socket_video.send(username_header + username)
    print('after client_socket_video.send(username_header + username)')

    if not (videofeed.capture.isOpened()):
        print('Can not open self capture camera')
        #client_socket_video.close()
        return False

    return True

# Sends a message to the server - NOT Used for video. 
def send(message):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket_video.send(message_header + message)


def start_sending_video(incoming_message_callback, error_callback):
    if (videofeed.capture.isOpened()):
        print('before Thread send_video')
        Thread(target=send_video, args=(incoming_message_callback, error_callback), daemon=True).start()
        print('after Thread send_video')

def send_video(incoming_message_callback, error_callback):
    #global vsock
    global videofeed
    while True:
        try:
            #ret = cv2.getWindowProperty(self_username, cv2.WND_PROP_VISIBLE)
            #if(ret > 0):
            x = cv2.waitKey(1)
            if(x == 27):
                cv2.destroyAllWindows()
                break

            frame=videofeed.get_frame()
            #get_frame returns np.ndarray, change the np.ndarray to bytes and then send bytes
            #we also need to send the shape of nparray so that it can be reconstructed in reveice

            shape_row_bytes = (str(frame.shape[0])).encode('utf-8')
            message_header = f"{len(shape_row_bytes):<{NP_ROW_CHARS_SIZE}}".encode('utf-8')
            client_socket_video.send(message_header + shape_row_bytes)

            shape_col_bytes = (str(frame.shape[1])).encode('utf-8')
            message_header = f"{len(shape_col_bytes):<{NP_COL_CHARS_SIZE}}".encode('utf-8')
            client_socket_video.send(message_header + shape_col_bytes)

            shape_dim_bytes = (str(frame.shape[2])).encode('utf-8')
            message_header = f"{len(shape_dim_bytes):<{NP_DIM_CHARS_SIZE}}".encode('utf-8')
            client_socket_video.send(message_header + shape_dim_bytes)

            #now send the entire nparray as bytes
            send_bytes = frame.tobytes()
            totalsent = 0
            send_size = (frame.shape[0] * frame.shape[1] * frame.shape[2])
            while totalsent < send_size :
                sent = client_socket_video.send(send_bytes)
                if sent == 0:
                    print("vsend: During sending frame Socket connection broken")
                    raise RuntimeError("Socket connection broken")
                totalsent += sent


            #vsock.vsend(send_bytes, (frame.shape[0] * frame.shape[1] * frame.shape[2]))
            #vsock.vsend(frame)
            videofeed.set_frame(frame)  
            #else:
            #    cv2.destroyAllWindows()
            #    break
        except Exception as e:
            # Any other exception - something happened, exit
            print('falied in send_video. Destroying all video windows and closing video communication.')
            #cv2.destroyWindow(self_username)
            #vsock = None
            #videofeed = None
            #client_socket_video.close()
            #error_callback('Reading error: {}'.format(str(e)), False)
            break


# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
def start_listening(incoming_message_callback, error_callback):
    print('before Thread listen')
    Thread(target=listen, args=(incoming_message_callback, error_callback), daemon=True).start()
    print('after Thread listen')

# Listens for incomming messages
def listen(incoming_message_callback, error_callback):
    #global vsock
    #global videofeed

    # Now we want to loop over received messages (there might be more than one) and print them
    while True:
        try:
            #while True:
            #if((vsock != None) and (videofeed != None)):
            #first get the username
            # Receive our "header" containing username length, it's size is defined and constant
            print('before client_socket_video.recv')
            username_header = client_socket_video.recv(HEADER_LENGTH)
            print('after client_socket_video.recv')

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                error_callback('Connection closed by the server', False)

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())
            print('after username_length: ' + str(username_length))

            # Receive and decode username
            username = client_socket_video.recv(username_length).decode('utf-8')
            print('client_socket_video.recv: username= ' + username)

            #now get the share of nparray. shape is (row, cols, dim) ex. shape: (480, 640, 3)
            print('before client_socket_video.recv to get row')
            shape_row_header = client_socket_video.recv(NP_ROW_CHARS_SIZE)
            shape_row_length = int(shape_row_header.decode('utf-8').strip())
            shape_row_int = int(client_socket_video.recv(shape_row_length).decode('utf-8'))

            print('before client_socket_video.recv to get col')
            shape_col_header = client_socket_video.recv(NP_COL_CHARS_SIZE)
            shape_col_length = int(shape_col_header.decode('utf-8').strip())
            shape_col_int = int(client_socket_video.recv(shape_col_length).decode('utf-8'))

            print('before client_socket_video.recv to get dim')
            shape_dim_header = client_socket_video.recv(NP_DIM_CHARS_SIZE)
            shape_dim_length = int(shape_dim_header.decode('utf-8').strip())
            shape_dim_int = int(client_socket_video.recv(shape_dim_length).decode('utf-8'))
            print('after client_socket_video.recv to get dim')

            print('before frame = vsock.vreceive()')
            #frame = vsock.vreceive(shape_row_int*shape_col_int*shape_dim_int)

            totrec = 0
            frame = ''.encode('utf-8')
            message_size = shape_row_int*shape_col_int*shape_dim_int
            while totrec<message_size :
                chunk = client_socket_video.recv(message_size - totrec)
                if chunk == '':
                    print("vreceive: During receiving frame socket connection broken")
                    raise RuntimeError("Socket connection broken")
                totrec += len(chunk)
                frame = frame + chunk

            print('after frame = vsock.vreceive()')

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
            received_nparray = np.frombuffer(frame, dtype=np.uint8)
            received_nparray = received_nparray.reshape(shape_row_int, shape_col_int, shape_dim_int)
            #cv2.imshow(username + '_receiver', frame)

            # Now create OpenCV window for this username if not already created
            if(cv2.getWindowProperty(username + '_receiver', 0) < 0):
                print('cv2.getWindowProperty < 0')
                cv2.namedWindow(username + '_receiver', cv2.WINDOW_AUTOSIZE)
                print('after cv2.namedWindow(username + \'_receiver\'')

            cv2.imshow(username + '_receiver', received_nparray)
            cv2.waitKey(1)
            print('after cv2.imshow(username + \'_receiver\'')
            #else:
            #    break
        except Exception as e:
            # Any other exception - something happened, exit
            print('falied in listen. Destroying all video windows and closing video communication.')
            #cv2.destroyWindow(self_username)
            #vsock = None
            #videofeed = None
            #client_socket_video.close()
            error_callback('Reading error: {}'.format(str(e)), False)