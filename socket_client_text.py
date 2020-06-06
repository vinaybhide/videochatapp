#v0.8
import socket
import errno
from threading import Thread, Event
thread_listen_text = None
pill_to_kill_listen_thread = None
stop_connection = False
HEADER_LENGTH = 10
client_socket_text_send = None
client_socket_text_recv = None

# Connects to the server
def connect(ip, port, my_username, error_callback):
    global client_socket_text_send
    global client_socket_text_recv
    global pill_to_kill_listen_thread
    global stop_connection

    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    stop_connection = False
    client_socket_text_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket_text_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #connect send client socket
    try:
        # Connect to a given ip and port
        client_socket_text_send.connect((ip, port))

        # Prepare username and header and send them
        # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
        username = my_username.encode('utf-8')
        keyword = 'SEND_SOCKET'.encode('utf-8')
        sep_bytes = ':'.encode('utf-8')
        username_header = f"{len(keyword+sep_bytes+username):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket_text_send.send(username_header + keyword+sep_bytes+username)

        client_socket_text_recv.connect((ip, port))

        # Prepare username and header and send them
        # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
        keyword = 'READ_SOCKET'.encode('utf-8')
        username_header = f"{len(keyword+sep_bytes+username):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket_text_recv.send(username_header + keyword+sep_bytes+username)

    except Exception as e:
        # Connection error
        error_callback('Connection error: {}'.format(str(e)))
        return False

    pill_to_kill_listen_thread = Event()

    return True

def send(message, header_size=HEADER_LENGTH):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{header_size}}".encode('utf-8')
    to_send = message_header + message
    send_size = len(to_send)
    tot_sent = 0
    while tot_sent < send_size:
        ret = client_socket_text_send.send(to_send[tot_sent:send_size])
        tot_sent += ret

def receive_message(receive_size=HEADER_LENGTH):

    try:
        # Receive our "header" containing message length, it's size is defined and constant
        #message_header = client_socket.recv(receive_size)

        message_header = ''.encode('utf-8')
        totrec = 0
        while totrec<receive_size :
            chunk = client_socket_text_recv.recv(receive_size - totrec)
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
            chunk = client_socket_text_recv.recv(message_length - totrec)
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
    global client_socket_text_send
    global client_socket_text_recv

    stop_text_comm()    
    if( client_socket_text_send != None ):
        client_socket_text_send.close()
    if( client_socket_text_recv != None ):
        client_socket_text_recv.close()

    client_socket_text_send = None
    client_socket_text_recv = None

def stop_text_comm():
    global stop_connection

    stop_connection = True

    #send CLOSING
    if( client_socket_text_send != None ):
        send('CLOSING')
    
    try:
        while((thread_listen_text !=None) and (thread_listen_text.is_alive())):
            print('waiting for listen thread to become None')
    except Exception as e:
        print('stopped listen thread')

    print('Text listen thread stopped')

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
            """username_header = client_socket_text_send.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                error_callback('Connection closed by the server')

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive and decode username
            username = client_socket_text_send.recv(username_length).decode('utf-8')"""

            username_dict = receive_message()
            if(username_dict is False):
                print('username_dict is False. continuing...')
                continue

            keyword_dict = receive_message()
            if(keyword_dict is False):
                print('keyword_dict is False. continuing...')
                continue

            username = (username_dict['data'].decode('utf-8')).strip()

            """keyword_header = client_socket_text_send.recv(HEADER_LENGTH)
            if not len(keyword_header):
                #error_callback('Connection closed by the server', False)
                print('Connection closed by server: client_socket_audio.recv(HEADER_LENGTH)')
                continue

            # Convert header to int value
            keyword_length = int(keyword_header.decode('utf-8').strip())
            keyworkd_message = client_socket_text_send.recv(keyword_length).decode('utf-8')"""


            keyworkd_message = (keyword_dict['data'].decode('utf-8')).strip()

            if(keyworkd_message.upper() == 'CLOSING'):
                print(f'Received CLOSING message from: {username}')
                incoming_message_callback(username, f'Closing text chat message : {username}')
                continue
            elif(keyworkd_message.upper() == 'ACK_CLOSED'):
                #print('Stopping listen thread as received ACK_CLOSED message from: '+username)
                pill_to_kill_listen_thread.set()
                break                
            elif(keyworkd_message.upper() == 'DATA'):
                # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                message_dict = receive_message()
                message = (message_dict['data'].decode('utf-8')).strip()
                """message_header = client_socket_text_send.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket_text_send.recv(message_length).decode('utf-8')"""

                # Print message
                incoming_message_callback(username, message)
                #if(stop_connection == True):
                #    pill_to_kill_listen_thread.set()

        except Exception as e:
            # Any other exception - something happened, exit
            #error_callback('Reading error: {}'.format(str(e)))
            print('Falied in listen :' + str(e))

    pill_to_kill_listen_thread.set()
    print('Stopped listen text thread')


