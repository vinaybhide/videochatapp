#v0.8
import socket
import errno
from threading import Thread, Event
thread_listen_text = None
pill_to_kill_listen_thread = None
stop_connection = False
HEADER_LENGTH = 10
client_socket_text = None

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_text
    global pill_to_kill_listen_thread
    global stop_connection

    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    stop_connection = False
    client_socket_text = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to a given ip and port
        client_socket_text.connect((ip, port))
    except Exception as e:
        # Connection error
        error_callback('Connection error: {}'.format(str(e)))
        return False

    # Prepare username and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    username = my_username.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket_text.send(username_header + username)

    pill_to_kill_listen_thread = Event()

    return True

# Sends a message to the server
def send(message):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket_text.send(message_header + message)

def close_connection():
    global client_socket_text
    stop_text_comm()    
    if( client_socket_text != None ):
        client_socket_text.close()
    client_socket_text = None

def stop_text_comm():
    global stop_connection

    stop_connection = True

    #send CLOSING
    if( client_socket_text != None ):
        send('CLOSING')

    try:
        while((thread_listen_text !=None) and (thread_listen_text.is_alive())):
            print('waiting for listen thread to become None')
    except Exception as e:
        print('stopped listen thread')

# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
def start_listening(incoming_message_callback, error_callback):
    global thread_listen_text

    thread_listen_text = Thread(target=listen, args=(incoming_message_callback, error_callback), daemon=True)
    thread_listen_text.start()

# Listens for incomming messages
def listen(incoming_message_callback, error_callback):
    # Now we want to loop over received messages (there might be more than one) and print them
    #while True:
    while not pill_to_kill_listen_thread.wait(0):
        try:
            # Receive our "header" containing username length, it's size is defined and constant
            username_header = client_socket_text.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                error_callback('Connection closed by the server')

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive and decode username
            username = client_socket_text.recv(username_length).decode('utf-8')

            keyword_header = client_socket_text.recv(HEADER_LENGTH)
            if not len(keyword_header):
                #error_callback('Connection closed by the server', False)
                print('Connection closed by server: client_socket_audio.recv(HEADER_LENGTH)')
                continue

            # Convert header to int value
            keyword_length = int(keyword_header.decode('utf-8').strip())
            keyworkd_message = client_socket_text.recv(keyword_length).decode('utf-8')
            if(keyworkd_message.upper() == 'CLOSING'):
                print('received CLOSING message from: '+username)
            elif(keyworkd_message.upper() == 'ACK_CLOSED'):
                #print('Stopping listen thread as received ACK_CLOSED message from: '+username)
                pill_to_kill_listen_thread.set()
                break                
            elif(keyworkd_message.upper() == 'DATA'):
                # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                message_header = client_socket_text.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket_text.recv(message_length).decode('utf-8')

                # Print message
                incoming_message_callback(username, message)
                #if(stop_connection == True):
                #    pill_to_kill_listen_thread.set()

        except Exception as e:
            # Any other exception - something happened, exit
            error_callback('Reading error: {}'.format(str(e)))