import socket
import select
#import videosocket

HEADER_LENGTH = 10
NP_ROW_CHARS_SIZE = 10
NP_COL_CHARS_SIZE = 4

print('Provide IP and port for audio communication server')
#IP = "127.0.0.1"
IP = input(f'IP: {socket.gethostbyname(socket.gethostname())}') or socket.gethostbyname(socket.gethostname())

#PORT = 5678
PORT = int(input(f'PORT: '))

# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
server_socket.bind((IP, PORT))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}

print(f'Audio chat server: Listening for connections on {IP}:{PORT}...')

# Handles message receiving
def receive_message(client_socket, receive_size=HEADER_LENGTH):

    try:
        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(receive_size)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

def send_ack(client_socket, message):
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message)

while True:
    try:
        # Calls Unix select() system call or Windows select() WinSock call with three parameters:
        #   - rlist - sockets to be monitored for incoming data
        #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
        #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
        # Returns lists:
        #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
        #   - writing - sockets ready for data to be send thru them
        #   - errors  - sockets with some exceptions
        # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


        # Iterate over notified sockets
        for notified_socket in read_sockets:

            # If notified socket is a server socket - new connection, accept it
            if notified_socket == server_socket:

                # Accept new connection
                # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                # The other returned object is ip/port set
                client_socket, client_address = server_socket.accept()

                # Client should send his name right away, receive it
                user = receive_message(client_socket, HEADER_LENGTH)

                # If False - client disconnected before he sent his name
                if user is False:
                    continue

                # Add accepted socket to select.select() list
                sockets_list.append(client_socket)

                # Also save username and username header
                clients[client_socket] = user

                print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

            # Else existing socket is sending a message
            else:

                #we must get a message with keyword DATA or CLOSING prior to any other message
                keyword_dict = receive_message(notified_socket, HEADER_LENGTH)
                if( keyword_dict is False):
                    #print('keyword_dict is False')
                    print('During keyword_dict = receive_message, Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                    # Remove from list for socket.socket()
                    sockets_list.remove(notified_socket)

                    # Remove from our list of users
                    del clients[notified_socket]

                    continue
                keyword_message = (keyword_dict['data'].decode('utf-8')).strip()
                if(keyword_message.upper() == 'CLOSING'):
                    #print('keyword = CLOSING')
                    user = clients[notified_socket]
                    for client_socket in clients:
                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            client_socket.send(user['header'] + user['data'])
                            client_socket.send(keyword_dict['header'] + keyword_dict['data'])
                    
                    notified_socket.send(user['header'] + user['data'])
                    send_ack(notified_socket, 'ACK_CLOSED')

                    sockets_list.remove(notified_socket)

                    # Remove from our list of users
                    del clients[notified_socket]

                elif(keyword_message.upper() == 'DATA'):
                    #firsr we need to get the shape of the stream
                    #first we get the rows
                    shape_rows_dict = receive_message(notified_socket, NP_ROW_CHARS_SIZE)
                    shape_cols_dict = receive_message(notified_socket, NP_COL_CHARS_SIZE)

                    if( (shape_rows_dict is False) or (shape_cols_dict is False)):
                        #print('(shape_rows_dict is False) or (shape_cols_dict is False)):')
                        print('Shape is False, Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                        # Remove from list for socket.socket()
                        sockets_list.remove(notified_socket)

                        # Remove from our list of users
                        del clients[notified_socket]

                        continue

                    totrec = 0
                    """message_size = int((shape_rows_dict['data'].decode('utf-8')).strip()) * \
                                int((shape_cols_dict['data'].decode('utf-8')).strip())"""
                    #get the size of byte stream
                    message_size_dict = receive_message(notified_socket, HEADER_LENGTH)
                    if(message_size_dict is False):
                        #print('(message_size_dict is False)')
                        print('message_size_dict is False, Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                        # Remove from list for socket.socket()
                        sockets_list.remove(notified_socket)

                        # Remove from our list of users
                        del clients[notified_socket]

                        continue

                    message_size = int((message_size_dict['data'].decode('utf-8')).strip())
                    #print('after message size decode:' + str(message_size))
                    message = ''.encode('utf-8')
                    while totrec<message_size :
                        chunk = notified_socket.recv(message_size - totrec)
                        #print('after notified_socket.recv(message_size - totrec')
                        if chunk is False:
                            print("Received empty chunk of audio: During receiving frame socket connection broken")
                            #raise RuntimeError("Socket connection broken")
                            break
                        totrec += len(chunk)
                        message = message + chunk


                    # If False, client disconnected, cleanup
                    if message is False:
                        #print('message is False:')
                        print('Audio message is False, Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                        # Remove from list for socket.socket()
                        sockets_list.remove(notified_socket)

                        # Remove from our list of users
                        del clients[notified_socket]

                        continue

                    # Get user by notified socket, so we will know who sent the message
                    user = clients[notified_socket]

                    #print(f'Received message from {user["data"].decode("utf-8")}') #': {message["data"].decode("utf-8")}')

                    # Iterate over connected clients and broadcast message
                    for client_socket in clients:

                        # But don't sent it to sender
                        if client_socket != notified_socket:
                            # Text code - keeping for reference
                            """
                            # Send user and message (both with their headers)
                            # We are reusing here message header sent by sender, and saved username header send by user when he connected
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                            """ 
                            #print('before send user name: + user[data].decode(utf-8)')
                            client_socket.send(user['header'] + user['data'])
                            #print('before send user name: + user[data].decode(utf-8)')

                            client_socket.send(keyword_dict['header'] + keyword_dict['data'])

                            #now send the shape of original stream
                            #print('before : client_socket.send(shape_rows_dict, shape_rows_dict')
                            client_socket.send(shape_rows_dict['header'] + shape_rows_dict['data'])
                            client_socket.send(shape_cols_dict['header'] + shape_cols_dict['data'])
                            #print('after : client_socket.send(shape_cols_dict, shape_cols_dict')

                            #send the size of the message
                            client_socket.send(message_size_dict['header'] + message_size_dict['data'])

                            totalsent = 0
                            while totalsent < message_size :
                                #print('before : sent = client_socket.send(message)')
                                sent = client_socket.send(message)
                                if sent == 0:
                                    print("client_socket.send(message) returned 0 bytes, breaking send to username =  " + user['data'].decode('utf-8'))
                                    #raise RuntimeError("Socket connection broken")
                                    break
                                totalsent += sent
                                #print('after : sent = client_socket.send(message)')
                            #print('after vsocksend.vsend(message)')

        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:

            # Remove from list for socket.socket()
            sockets_list.remove(notified_socket)

            # Remove from our list of users
            del clients[notified_socket]
    except Exception as e:
        print('Exception in audio server - ' + str(e))