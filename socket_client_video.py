import socket, videosocket
import errno
from threading import Thread
from videofeed import VideoFeed
import cv2

HEADER_LENGTH = 10
client_socket_video = None
vsock = None
videofeed = None
self_username = ''

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_video
    global vsock
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
        vsock = videosocket.videosocket (client_socket_video)
        videofeed = VideoFeed(1,my_username,1)
        if not (videofeed.capture.isOpened()):
            print('Can not open camera')
            client_socket_video.close()
            return False

    except Exception as e:
        # Connection error
        error_callback('Connection error: {}'.format(str(e)), False)
        return False

    # Prepare username and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    username = my_username.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket_video.send(username_header + username)

    return True

# Sends a message to the server - NOT Used for video. only used to send username
def send(message):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket_video.send(message_header + message)


def start_sending_video(incoming_message_callback, error_callback):
    Thread(target=send_video, args=(incoming_message_callback, error_callback), daemon=True).start()

def send_video(incoming_message_callback, error_callback):
    global vsock
    global videofeed
    while True:
        try:
            ret = cv2.getWindowProperty(self_username, cv2.WND_PROP_VISIBLE)
            if(ret > 0):
                x = cv2.waitKey(1)
                if(x == 27):
                    cv2.destroyAllWindows()
                    vsock = None
                    videofeed = None
                    client_socket_video.close()
                    break

                if( (videofeed != None) and (vsock != None)):
                    frame=videofeed.get_frame()
                    vsock.vsend(frame)
                    videofeed.set_frame(frame)  
                else:
                    break
            else:
                cv2.destroyAllWindows()
                vsock = None
                videofeed = None
                client_socket_video.close()
                break
        except Exception as e:
            # Any other exception - something happened, exit
            print('falied in send_video. Destroying all video windows and closing video communication.')
            cv2.destroyWindow(self_username)
            vsock = None
            videofeed = None
            client_socket_video.close()
            error_callback('Reading error: {}'.format(str(e)), False)
            break


# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
def start_listening(incoming_message_callback, error_callback):
    Thread(target=listen, args=(incoming_message_callback, error_callback), daemon=True).start()

# Listens for incomming messages
def listen(incoming_message_callback, error_callback):
    global vsock
    global videofeed

    # Now we want to loop over received messages (there might be more than one) and print them
    while True:
        try:
            #while True:
            if((vsock != None) and (videofeed != None)):
                #first get the username
                # Receive our "header" containing username length, it's size is defined and constant
                username_header = client_socket_video.recv(HEADER_LENGTH)

                # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                if not len(username_header):
                    error_callback('Connection closed by the server')

                # Convert header to int value
                username_length = int(username_header.decode('utf-8').strip())

                # Receive and decode username
                username = client_socket_video.recv(username_length).decode('utf-8')

                # Now create OpenCV window for this username if not already created
                if(cv2.getWindowProperty(username, 0) < 0):
                    cv2.namedWindow(username)

                frame = vsock.vreceive()
                cv2.imshow(username, frame)
            else:
                break
        except Exception as e:
            # Any other exception - something happened, exit
            print('falied in listen. Destroying all video windows and closing video communication.')
            cv2.destroyWindow(self_username)
            vsock = None
            videofeed = None
            client_socket_video.close()
            error_callback('Reading error: {}'.format(str(e)), False)