#v0.8
from tkinter import *
from tkinter import ttk
from tkinter import messagebox as msgbx
import os.path as ospath
import socket_client_text, socket_client_video, socket_client_audio
import cv2
import sounddevice as sd
from threading import Thread

class vConnectApp():
    def __init__(self):
        super().__init__()

        self.root = Tk()
        self.root.wm_state('normal')
        self.root.wm_title("vConnect-Text, Audio and Video")
        #self.root.resizable(width=True, height=False)

        self.root.wm_protocol("WM_DELETE_WINDOW", self.close_app)

        #configure device variables
        self.audioin = None
        self.audioout = None
        self.is_test_audio_clicked = False
        self.is_test_video_clicked = False
        ####

        self.is_self_audio_avlbl = False
        self.is_self_video_avlbl = False
        if(ospath.isfile('prev_details.txt')):
            with open('prev_details.txt', 'r') as f:
                d = f.read().split(',')
                f.close()
            prev_ip = d[0]
            prev_text_port = d[1]
            prev_video_port = d[2]
            prev_audio_port = d[3]
            prev_username = d[4]
        else:
            prev_ip = ''
            prev_text_port = ''
            prev_video_port = ''
            prev_audio_port = ''
            prev_username = ''

        #self.content = ttk.Frame(self.root, padding=(5, 5, 12, 0))
        self.content = ttk.Frame(self.root)

        self.notebook = ttk.Notebook(self.content)
        self.fConfigurePage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")#, padding=5)
        self.fConnectPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")#, padding=5)
        self.fInfoPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")
        self.fChatPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")

        self.notebook.add(self.fConfigurePage, text='Configure Devices')
        self.notebook.add(self.fConnectPage, text='Connect')
        self.notebook.add(self.fChatPage, text = 'Chat')
        self.notebook.add(self.fInfoPage, text='Information')

        #create configure device fields
        self.frame_configure = ttk.Frame(self.fConfigurePage) #, borderwidth=5, relief="sunken")
        self.video_select_label = ttk.Label(self.frame_configure, text='Click the button to test video: ')
        self.btn_video_test = ttk.Button(self.frame_configure, text="Test Video", command=self.test_video)

        #self.frame_audio_config = ttk.Frame(self.fConfigurePage) #, borderwidth=5, relief="sunken")
        self.speaker_select_label = ttk.Label(self.frame_configure, text='Selected speaker: ')
        self.speaker_select_text = StringVar(value='')
        self.speaker_select_entry = ttk.Entry(self.frame_configure, textvariable=self.speaker_select_text, width=60)

        self.mic_select_label = ttk.Label(self.frame_configure, text='Selected Microphone: ')
        self.mic_select_text = StringVar(value='')
        self.mic_select_entry = ttk.Entry(self.frame_configure, textvariable=self.mic_select_text, width=60)
        self.btn_audio_test = ttk.Button(self.frame_configure, text="Test Audio", command=self.test_audio)


        #create Connect Page fields
        self.frame_connect_details = ttk.Frame(self.fConnectPage) #, borderwidth=5, relief="sunken")
     
        self.ip_label = ttk.Label(self.frame_connect_details, text='IP: ')
        self.ip_text = StringVar(value=prev_ip)
        self.ip_entry = ttk.Entry(self.frame_connect_details, textvariable=self.ip_text, width=20)

        self.port_text_label = ttk.Label(self.frame_connect_details, text='Port for text chat: ')
        self.port_text_text = StringVar(value=prev_text_port)
        self.port_text_entry = ttk.Entry(self.frame_connect_details, textvariable=self.port_text_text, width=20)

        self.port_video_label = ttk.Label(self.frame_connect_details, text='Port for video chat: ')
        self.port_video_text = StringVar(value=prev_video_port)
        self.port_video_entry = ttk.Entry(self.frame_connect_details, textvariable=self.port_video_text, width=20)

        self.port_audio_label = ttk.Label(self.frame_connect_details, text='Port for audio chat: ')
        self.port_audio_text = StringVar(value=prev_audio_port)
        self.port_audio_entry = ttk.Entry(self.frame_connect_details, textvariable=self.port_audio_text, width=20)

        self.username_label = ttk.Label(self.frame_connect_details, text='User name: ')
        self.username_text = StringVar(value=prev_username)
        self.username_entry = ttk.Entry(self.frame_connect_details, textvariable=self.username_text, width=20)

        self.btn_join = ttk.Button(self.frame_connect_details, text="Join", command=self.join_button)

        #create Information Page fields
        self.frame_info_label = ttk.Frame(self.fInfoPage)#, borderwidth=5, relief="sunken")
        self.vscroll_info_message = Scrollbar(self.frame_info_label)
        self.info_message_text = Text(self.frame_info_label, yscrollcommand=self.vscroll_info_message.set, state=DISABLED)#, height=30, width=90) #DISABLED
        self.vscroll_info_message.config(command=self.info_message_text.yview)

        #Create Chat Page fields
        self.frame_chat_history = ttk.Frame(self.fChatPage)#, borderwidth=5, relief="sunken")
        self.vscroll_chat_history = Scrollbar(self.frame_chat_history)
        self.chat_history_text = Text(self.frame_chat_history, yscrollcommand=self.vscroll_chat_history.set, state=DISABLED) #height=24, width=80) #DISABLED
        self.vscroll_chat_history.config(command=self.chat_history_text.yview)

        self.chat_history_text.tag_configure("b", foreground='blue')
        self.chat_history_text.tag_configure("r", foreground='red')


        self.frame_new_message = ttk.Frame(self.fChatPage)#, borderwidth=5, relief="sunken")
        self.new_message_text = StringVar(value='')
        self.new_message_entry = ttk.Entry(self.frame_new_message, textvariable=self.new_message_text, width=90)
        self.new_message_entry.bind('<Return>',self.send_text_message_on_enter)
        self.btn_send = ttk.Button(self.frame_new_message, text="Send Text", command=self.send_text_message)

        self.frame_command_btn = ttk.Frame(self.fChatPage)#, borderwidth=5, relief="sunken")
        self.btn_start_video = ttk.Button(self.frame_command_btn, text="Start Video", command=self.start_video_send, state=NORMAL)
        self.btn_stop_video = ttk.Button(self.frame_command_btn, text="Stop Video", command=self.stop_video_send, state=DISABLED)

        self.btn_start_audio = ttk.Button(self.frame_command_btn, text="Start Audio", command=self.start_audio_send, state=NORMAL)
        self.btn_stop_audio = ttk.Button(self.frame_command_btn, text="Stop Audio", command=self.stop_audio_send, state=DISABLED)

        self.btn_close_app = ttk.Button(self.frame_command_btn, text="Close App", command=self.close_app)

        #put everything on grid

        self.content.grid(column=0, row=0, sticky=(N, S, E, W))
        self.notebook.grid(row=0, column=0, sticky=(N, E, S, W), padx=5, pady=5) 
        
        #configure page
        self.frame_configure.grid(column=3, row=1, sticky=(N, S, E, W), padx=5, pady=5)
        self.video_select_label.grid(column=0, row=0, padx=2, pady=2, sticky=(N, E))
        self.btn_video_test.grid(column=1, row=0, padx=2, pady=2, sticky=(N, W))

        #self.frame_audio_config.grid(column=0, row=1, sticky=(N, S, E, W), padx=5, pady=5)
        self.speaker_select_label.grid(column=0, row=1, padx=2, pady=2, sticky=(N, E))
        self.speaker_select_entry.grid(column=1, row=1, padx=2, pady=2, sticky=(N, E, W))
        self.mic_select_label.grid(column=0, row=2, padx=2, pady=2, sticky=(N, E))
        self.mic_select_entry.grid(column=1, row=2, padx=2, pady=2, sticky=(N, E, W))
        self.btn_audio_test.grid(column=1, row=3, padx=2, pady=2, sticky=(N, W))


        #Connect page
        self.frame_connect_details.grid(row=3, column=1, sticky=(N, S, E, W), padx=5, pady=5)
        self.ip_label.grid(row=0, column=2, padx=2, pady=2, sticky=(N, E))
        self.ip_entry.grid(row=0, column=3, padx=2, pady=2, sticky=(N, E, W))
        self.port_text_label.grid(row=1, column=2, padx=2, pady=2, sticky=(N, E))
        self.port_text_entry.grid(row=1, column=3, padx=2, pady=2, sticky=(N, E, W))
        self.port_video_label.grid(row=2, column=2, padx=2, pady=2, sticky=(N, E))
        self.port_video_entry.grid(row=2, column=3, padx=2, pady=2, sticky=(N, E, W))
        self.port_audio_label.grid(row=3, column=2, padx=2, pady=2, sticky=(N, E))
        self.port_audio_entry.grid(row=3, column=3, padx=2, pady=2, sticky=(N, E, W))
        self.username_label.grid(row=4, column=2, padx=2, pady=2, sticky=(N, E))
        self.username_entry.grid(row=4, column=3, padx=2, pady=2, sticky=(N, E, W))

        self.btn_join.grid(row=5, column=3, padx=5, pady=5)

        #info page
        self.frame_info_label.grid(row=0, column=0, sticky=(N, E, S, W), padx=5, pady=5)
        self.info_message_text.grid(row=0, column=0, padx=2, pady=2, sticky=(N, E, W))
        self.vscroll_info_message.grid(row=0, column=1, sticky=(N,S))

        #chat page
        self.frame_chat_history.grid(row=0, column=0, sticky=(N, E, S, W), padx=5, pady=5)
        self.chat_history_text.grid(row=0, column=0, padx=2, pady=2, sticky=(N, E, W))
        self.vscroll_chat_history.grid(row=0, column=1, sticky=(N,S))

        self.frame_new_message.grid(row=1, column=0, padx=5, pady=5, sticky=(N, E, S, W) )
        self.new_message_entry.grid(row=0, column=0, padx=2, pady=2, sticky=(N, E, W))
        self.btn_send.grid(row=0, column=1, padx=2, pady=2)

        self.frame_command_btn.grid(row=2, column=0, sticky=(N, E, S, W), padx=5, pady=5)
        self.btn_start_video.grid(row=0, column=4, padx=20, pady=2)
        self.btn_stop_video.grid(row=0, column=5, padx=2, pady=2)
        self.btn_start_audio.grid(row=0, column=6, padx=20, pady=2)
        self.btn_stop_audio.grid(row=0, column=7, padx=2, pady=2)
        self.btn_close_app.grid(row=0, column=8, padx=20, pady=2)


        #make resize %
        #now set resize
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.content.columnconfigure(0, weight=3)
        self.content.columnconfigure(1, weight=3)
        self.content.columnconfigure(2, weight=3)
        self.content.columnconfigure(3, weight=1)
        self.content.columnconfigure(4, weight=3)

        self.content.rowconfigure(0, weight=3)
        self.content.rowconfigure(1, weight=3)
        self.content.rowconfigure(2, weight=3)
        self.content.rowconfigure(3, weight=3)
        self.content.rowconfigure(4, weight=3)
        self.content.rowconfigure(5, weight=3)

        self.fConfigurePage.columnconfigure(0, weight=3)
        self.fConfigurePage.columnconfigure(1, weight=3)

        self.fConfigurePage.rowconfigure(0, weight=1)
        self.fConfigurePage.rowconfigure(1, weight=1)
        self.fConfigurePage.rowconfigure(2, weight=1)

        self.frame_configure.columnconfigure(0, weight=1)
        self.frame_configure.columnconfigure(1, weight=1)

        self.frame_configure.rowconfigure(0, weight=1)
        self.frame_configure.rowconfigure(1, weight=1)
        self.frame_configure.rowconfigure(2, weight=1)


        self.fConnectPage.columnconfigure(0, weight=3)
        self.fConnectPage.columnconfigure(1, weight=3)
        self.fConnectPage.columnconfigure(2, weight=3)
        self.fConnectPage.columnconfigure(3, weight=1)
        self.fConnectPage.columnconfigure(4, weight=3)

        self.fConnectPage.rowconfigure(0, weight=3)
        self.fConnectPage.rowconfigure(1, weight=3)
        self.fConnectPage.rowconfigure(2, weight=3)
        self.fConnectPage.rowconfigure(3, weight=3)
        self.fConnectPage.rowconfigure(4, weight=3)
        self.fConnectPage.rowconfigure(5, weight=3)

        self.frame_connect_details.columnconfigure(0, weight=3)
        self.frame_connect_details.columnconfigure(1, weight=3)
        self.frame_connect_details.columnconfigure(2, weight=3)
        self.frame_connect_details.columnconfigure(3, weight=1)
        self.frame_connect_details.columnconfigure(4, weight=3)

        self.frame_connect_details.rowconfigure(0, weight=3)
        self.frame_connect_details.rowconfigure(1, weight=3)
        self.frame_connect_details.rowconfigure(2, weight=3)
        self.frame_connect_details.rowconfigure(3, weight=3)
        self.frame_connect_details.rowconfigure(4, weight=3)
        self.frame_connect_details.rowconfigure(5, weight=3)

        self.fInfoPage.columnconfigure(0, weight=10)
        self.fInfoPage.columnconfigure(1, weight=0)
        self.fInfoPage.rowconfigure(0, weight=3)

        self.frame_info_label.columnconfigure(0, weight=10)
        self.frame_info_label.columnconfigure(1, weight=0)
        self.frame_info_label.rowconfigure(0, weight=3)

        self.fChatPage.columnconfigure(0, weight=3)
        self.fChatPage.columnconfigure(1, weight=0)
        self.fChatPage.rowconfigure(0, weight=10)
        self.fChatPage.rowconfigure(1, weight=0)
        self.fChatPage.rowconfigure(2, weight=0)

        self.frame_chat_history.columnconfigure(0, weight=3)
        self.frame_chat_history.columnconfigure(1, weight=0)
        self.frame_chat_history.rowconfigure(0, weight=1)

        self.frame_new_message.columnconfigure(0, weight=3)
        self.frame_new_message.columnconfigure(1, weight=0)
        self.frame_new_message.rowconfigure(0, weight=1)

        self.frame_command_btn.columnconfigure(0, weight=1)
        self.frame_command_btn.columnconfigure(1, weight=1)
        self.frame_command_btn.columnconfigure(2, weight=1)
        self.frame_command_btn.columnconfigure(3, weight=1)
        self.frame_command_btn.columnconfigure(4, weight=1)
        self.frame_command_btn.columnconfigure(5, weight=1)
        self.frame_command_btn.columnconfigure(6, weight=1)
        self.frame_command_btn.columnconfigure(7, weight=1)
        self.frame_command_btn.columnconfigure(8, weight=1)
        self.frame_command_btn.rowconfigure(0, weight=1)


        self.speaker_dict = self.get_speaker_list()
        self.speaker_select_text.set(self.speaker_dict['name'])
        self.mic_dict = self.get_mic_list()
        self.mic_select_text.set(self.mic_dict['name'])

        self.notebook.tab(2, state=DISABLED)

        mainloop()

    #handler methods
    def close_app(self):
        #socket_client_text.client_socket_text.close()
        socket_client_text.close_connection()
        self.stop_audio_send()
        self.stop_video_send()
        self.root.destroy()

    #following is the content of device_dict 
    """'name':'Speakers (Realtek High Definiti'
    'hostapi':0
    'max_input_channels':0
    'max_output_channels':2
    'default_low_input_latency':0.09
    'default_low_output_latency':0.09
    'default_high_input_latency':0.18
    'default_high_output_latency':0.18
    'default_samplerate':44100.0"""

    def get_speaker_list(self):
        device_dict = sd.query_devices(kind='output')
        return device_dict

    def get_mic_list(self):
        device_dict = sd.query_devices(kind='input')
        return device_dict

    def test_video(self):
        if(self.is_test_video_clicked == False):
            self.is_test_video_clicked = True

            self.btn_video_test.configure(text='Stop Video Test')

            thread_start_show_video = Thread(target=self.show_video)
            thread_start_show_video.start()

        else:
            self.is_test_video_clicked = False
            self.btn_video_test.configure(text='Test Video')

    def show_video(self):
        cv2.namedWindow('Test Video', cv2.WINDOW_AUTOSIZE) #.NamedWindow(name, cv2.VideoCapture.CV_WINDOW_AUTOSIZE)
        capture = cv2.VideoCapture(0) #.CaptureFromCAM(self.camera_index)
        if not (capture.isOpened()):
            cv2.destroyWindow('Test Video')
            print('No Camera found')
        else:
            while (self.is_test_video_clicked == True):
                ret, frame =  capture.read() #cv2.QueryFrame(self.capture)
                frame = cv2.resize(frame, (0,0), fx = 0.5, fy = 0.5)
                cv2.imshow('Test Video', frame)
                x = cv2.waitKey(1)

            capture.release()
            cv2.destroyAllWindows()


    def test_audio(self):
        if(self.is_test_audio_clicked == False):
            self.audioin = sd.InputStream(samplerate=int(self.mic_dict['default_samplerate']),dtype='float32')
            self.audioout = sd.OutputStream(samplerate=int(self.speaker_dict['default_samplerate']),dtype='float32')        

            self.is_test_audio_clicked = True

            thread_start_recording = Thread(target=self.record_audio)
            thread_start_recording.start()

            self.btn_audio_test.configure(text='Stop Audio Test')
        else:
            self.is_test_audio_clicked = False
            self.btn_audio_test.configure(text='Test Audio')

    def record_audio(self):
        self.audioin.start()
        self.audioout.start()
        frame = None
        while (self.is_test_audio_clicked == True):
            frame, ret = self.audioin.read(1000)
            #sd.sleep(int(1000))
            self.audioout.write(frame)

        self.audioin.abort()
        self.audioout.abort()

        self.audioin = None
        self.audioout = None

    def join_button(self):
        port_text = self.port_text_text.get()
        port_video = self.port_video_text.get()
        port_audio = self.port_audio_text.get()
        ip = self.ip_text.get()
        username = self.username_text.get()

        self.root.wm_title('vConnect-Text, Audio and Video (User: ' + username +')')

        with open('prev_details.txt', 'w') as f:
            f.write(f'{ip},{port_text},{port_video},{port_audio},{username}')
            f.close()

        self.info_message_text.configure(state=NORMAL)
        self.info_message_text.insert(END, f"Attempting to join {ip}: text port={port_text} videoport={port_video} audioport={port_audio} as {username}" + '\n')
        self.info_message_text.configure(state=DISABLED)
        self.notebook.tab(3, state='normal')
        self.notebook.select(3)
        self.connect()

    def connect(self):
        port_text = int(self.port_text_text.get())
        port_video = int(self.port_video_text.get())
        port_audio = int(self.port_audio_text.get())
        ip = self.ip_text.get()
        username = self.username_text.get()

        if not socket_client_text.connect(ip, port_text, username, self.show_error):
            return

        #start the text communication right away
        socket_client_text.start_listening(self.incoming_message, self.show_error)

        self.notebook.tab(2, state='normal')
        self.notebook.select(2)

        """In the following example, the resulting text is blue on a yellow background.
            text.tag_config("n", background="yellow", foreground="red")
            text.tag_config("a", foreground="blue")
            text.insert(contents, ("n", "a")) """
    
    def update_chat_history(self, username, message):
        self.chat_history_text.configure(state=NORMAL)
        #self.chat_history_text.tag_config("n", foreground=color_code) movng this line to init
        
        self.chat_history_text.insert(END, '\n'+username, ('r', 'b'))

        self.chat_history_text.insert(END, message)

        self.chat_history_text.configure(state=DISABLED)


    def incoming_message(self, username, message):
        self.chat_history_text.tag_raise('r', 'b')
        self.update_chat_history(f'{username} > ', message)
        #self.update_chat_history(f'[color=20dd20]{username}[/color] > {message}')

    def show_error(self, message = '', exit_flag = True):
        self.info_message_text.configure(state=NORMAL)
        self.info_message_text.insert(END, message + '\n')
        self.info_message_text.configure(state=DISABLED)
        self.notebook.tab(3, state='normal')
        self.notebook.select(3)
        if(exit_flag):
            self.close_app()
        else:
            self.notebook.tab(2, state='normal')
            self.notebook.select(2)

    def send_text_message_on_enter(self, evnt):
        self.send_text_message()

    def send_text_message(self):
        message = self.new_message_text.get()
        self.new_message_text.set('')
        
        # If there is any message - add it to chat history and send to the server
        if message:
            self.chat_history_text.tag_raise('b', 'r')
            self.update_chat_history(f'{self.username_text.get()} > ', message)
            #self.update_chat_history(f'[color=dd2020]{self.username_text.get()}[/color] > {message}')
            socket_client_text.send('DATA')
            socket_client_text.send(message)

        # As mentioned above, we have to shedule for refocusing to input field
        self.new_message_entry.focus_set()

    def start_audio_send(self):
        port_audio = int(self.port_audio_text.get())
        ip = self.ip_text.get()
        username = self.username_text.get()

        self.is_self_audio_avlbl = socket_client_audio.connect(ip, port_audio, username, self.speaker_dict, self.mic_dict, self.show_error)
        if self.is_self_audio_avlbl == -1:
            #this means client was not able to connect to server, we will not be able to use video chat at all
            print('socket_client_audio.connect returned -1: Not able to connect to server')
            self.btn_start_audio.configure(state=NORMAL)
            self.btn_stop_audio.configure(state=DISABLED)
        elif self.is_self_audio_avlbl == -2:
            #means error while sending the username, which means we do not have connection 
            # to server or server refused
            print('socket_client_audio.connect returned -2: send of username failed and return <= 0')
            self.btn_start_audio.configure(state=NORMAL)
            self.btn_stop_audio.configure(state=DISABLED)
        else:   #we got connected
            self.btn_start_audio.configure(state=DISABLED)
            self.btn_stop_audio.configure(state=NORMAL)
            socket_client_audio.start_listening(self.callback_listen_audio, self.show_error)
            socket_client_audio.start_sending_audio(self.callback_send_audio, self.show_error)

    def stop_audio_send(self):
        #connection is good, we have the self video window and we were able to send our username
        self.btn_start_audio.configure(state=NORMAL)
        self.btn_stop_audio.configure(state=DISABLED)
        socket_client_audio.close_connection()

    def start_video_send(self):
        port_video = int(self.port_video_text.get())
        ip = self.ip_text.get()
        username = self.username_text.get()

        #connect to server
            
        self.is_self_video_avlbl = socket_client_video.connect(ip, port_video, username, self.show_error)
        if self.is_self_video_avlbl == -1:     #not socket_client_video.connect(ip, port_video, username, show_error):
            #this means client was not able to connect to server, we will not be able to use video chat at all
            print('socket_client_video.connect returned -1: Not able to connect to server')
            self.btn_start_video.configure(state=NORMAL)
            self.btn_stop_video.configure(state=DISABLED)
            #info = f"Can not connect to video device"
            #chatapp.info_page.update_info(info)
        elif self.is_self_video_avlbl == -2:
            #means error while sending the username, which means we do not have connection 
            # to server or server refused
            print('socket_client_video.connect returned -2: send of username failed and return <= 0')
            self.btn_start_video.configure(state=NORMAL)
            self.btn_stop_video.configure(state=DISABLED)
        elif self.is_self_video_avlbl == -3:
            #connection is good, we were able to send self username but error occurred 
            # while creating self video window and we do not have self video window
            print('socket_client_video.connect returned -3: No camera connected so only listen & show')
            self.btn_start_video.configure(state=DISABLED)
            self.btn_stop_video.configure(state=NORMAL)
            socket_client_video.start_listening(self.callback_listen_video, self.show_error)
        else:   # self.is_self_video_avlbl == 1:
            #connection is good, we have the self video window and we were able to send our username
            self.btn_start_video.configure(state=DISABLED)
            self.btn_stop_video.configure(state=NORMAL)
            socket_client_video.start_listening(self.callback_listen_video, self.show_error)
            socket_client_video.start_sending_video(self.callback_send_video, self.show_error)

    def stop_video_send(self):
        #connection is good, we have the self video window and we were able to send our username
        self.btn_start_video.configure(state=NORMAL)
        self.btn_stop_video.configure(state=DISABLED)
        socket_client_video.close_connection()

    def callback_listen_video(self, _=None):
        return

    def callback_listen_audio(self, _=None):
        return

    def callback_send_video(self, _=None):
        return

    def callback_send_audio(self, _=None):
        return

    def show(self):
        self.wm_deiconify()
        self.wait_window()


if __name__ == "__main__":
    obj1 = vConnectApp()
