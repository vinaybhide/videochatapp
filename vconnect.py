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
            #prev_user_mgmt_port = ''
        else:
            prev_ip = ''
            prev_text_port = ''
            prev_video_port = ''
            prev_audio_port = ''
            prev_username = ''
            #prev_user_mgmt_port = ''

        #self.content = ttk.Frame(self.root, padding=(5, 5, 12, 0))
        self.content = ttk.Frame(self.root)

        self.notebook = ttk.Notebook(self.content)
        #self.fUserMgmtPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")#, padding=5)
        self.fConfigurePage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")#, padding=5)
        self.fConnectPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")#, padding=5)
        self.fInfoPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")
        self.fChatPage = ttk.Frame(master=self.notebook, borderwidth=5, relief="sunken")

        #self.notebook.add(self.fUserMgmtPage, text='Login/New User')
        self.notebook.add(self.fConfigurePage, text='Configure Devices')
        self.notebook.add(self.fConnectPage, text='Connect')
        self.notebook.add(self.fChatPage, text = 'Chat')
        self.notebook.add(self.fInfoPage, text='Information')

        #create user mgmt fields
        """self.frame_usermgmt = ttk.Frame(self.fUserMgmtPage) #, borderwidth=5, relief="sunken")
        self.email_label = ttk.Label(self.frame_usermgmt, text='Email id: ')
        self.email_text = StringVar()
        self.email_entry = ttk.Entry(self.frame_usermgmt, textvariable=self.email_text, width=50)

        self.password_label = ttk.Label(self.frame_usermgmt, text='Password: ')
        self.password_text = StringVar()
        self.password_entry = ttk.Entry(self.frame_usermgmt, textvariable=self.password_text, width=50, show="*")

        self.btn_login = ttk.Button(self.frame_usermgmt, text="Login")#, command=self.login)
        self.btn_new_user = ttk.Button(self.frame_usermgmt, text="Create New User")#, command=self.new_user)"""

        #create configure device fields
        self.frame_configure = ttk.Frame(self.fConfigurePage) #, borderwidth=5, relief="sunken")
        self.video_select_label = ttk.Label(self.frame_configure, text='Click the button to test video: ')
        self.btn_video_test = ttk.Button(self.frame_configure, text="Test Video", command=self.test_video)

        #self.frame_audio_config = ttk.Frame(self.fConfigurePage) #, borderwidth=5, relief="sunken")
        self.speaker_select_label = ttk.Label(self.frame_configure, text='Select Output(Speaker) Device: ')
        self.output_device_combo_text = StringVar()
        self.output_device_combo = ttk.Combobox(self.frame_configure, width=60, 
                textvariable=self.output_device_combo_text, state='readonly')
        #self.speaker_select_text = StringVar(value='')
        #self.speaker_select_entry = ttk.Entry(self.frame_configure, textvariable=self.speaker_select_text, width=60, state='readonly')
        self.speaker_info_label = ttk.Label(self.frame_configure, text='Item that starts with <, indicates default output device' )

        self.mic_select_label = ttk.Label(self.frame_configure, text='Select Input(Mic) device: ')
        self.input_device_combo_text = StringVar()
        self.input_device_combo = ttk.Combobox(self.frame_configure, width=60, 
                textvariable=self.input_device_combo_text, state='readonly')
        #self.mic_select_text = StringVar(value='')
        #self.mic_select_entry = ttk.Entry(self.frame_configure, textvariable=self.mic_select_text, width=60, state='readonly')
        self.mic_info_label = ttk.Label(self.frame_configure, text='Item that starts with >, indicates default input device' )

        self.btn_audio_test = ttk.Button(self.frame_configure, text="Test Audio", command=self.test_audio)

        self.output_device_combo.bind('<<ComboboxSelected>>', self.OnOutputDeviceChanged)
        self.input_device_combo.bind('<<ComboboxSelected>>', self.OnInputDeviceChanged)

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

        #User Mgmt Page
        """self.frame_usermgmt.grid(row=1, column=1, sticky=(N, S, E, W), padx=5, pady=5)
        self.email_label.grid(row=0, column=2, padx=2, pady=2, sticky=(N, E))
        self.email_entry.grid(row=0, column=3, padx=2, pady=2, sticky=(N, E, W))

        self.password_label.grid(row=1, column=2, padx=2, pady=2, sticky=(N, E))
        self.password_entry.grid(row=1, column=3, padx=2, pady=2, sticky=(N, E, W))

        self.btn_login.grid(row=2, column=3, padx=5, pady=5)
        self.btn_new_user.grid(row=2, column=4, padx=10, pady=10)"""


        #configure page
        self.frame_configure.grid(column=0, row=1, sticky=(N, S, E, W), padx=5, pady=5)
        self.video_select_label.grid(column=0, row=0, padx=2, pady=2, sticky=(N, E))
        self.btn_video_test.grid(column=1, row=0, padx=2, pady=2, sticky=(N, W))

        #self.frame_audio_config.grid(column=0, row=1, sticky=(N, S, E, W), padx=5, pady=5)
        self.speaker_select_label.grid(column=0, row=1, padx=2, pady=2, sticky=(N, E))
        self.output_device_combo.grid(column=1, row=1, padx=2, pady=2, sticky=(N, W))
        #self.speaker_select_entry.grid(column=2, row=1, padx=2, pady=2, sticky=(N, E, W))
        self.speaker_info_label.grid(column=1, row=2, padx=10, pady=2, sticky=(N, W))        

        self.mic_select_label.grid(column=0, row=3, padx=2, pady=2, sticky=(N, E))
        self.input_device_combo.grid(column=1, row=3, padx=2, pady=2, sticky=(N, W))
        #self.mic_select_entry.grid(column=2, row=3, padx=2, pady=2, sticky=(N, E))
        self.mic_info_label.grid(column=1, row=4, padx=2, pady=2, sticky=(N, W))
        self.btn_audio_test.grid(column=1, row=5, padx=10, pady=2, sticky=(N, W))


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

        """self.fUserMgmtPage.columnconfigure(0, weight=3)
        self.fUserMgmtPage.columnconfigure(1, weight=3)
        self.fUserMgmtPage.columnconfigure(2, weight=1)
        self.fUserMgmtPage.columnconfigure(3, weight=3)
        self.fUserMgmtPage.columnconfigure(4, weight=1)

        self.fUserMgmtPage.rowconfigure(0, weight=3)
        self.fUserMgmtPage.rowconfigure(1, weight=3)
        self.fUserMgmtPage.rowconfigure(2, weight=3)

        self.frame_usermgmt.columnconfigure(0, weight=3)
        self.frame_usermgmt.columnconfigure(1, weight=3)
        self.frame_usermgmt.columnconfigure(2, weight=1)
        self.frame_usermgmt.columnconfigure(3, weight=3)
        self.frame_usermgmt.columnconfigure(4, weight=1)

        self.frame_usermgmt.rowconfigure(0, weight=3)
        self.frame_usermgmt.rowconfigure(1, weight=3)
        self.frame_usermgmt.rowconfigure(2, weight=3)"""

        self.fConfigurePage.columnconfigure(0, weight=1)
        self.fConfigurePage.columnconfigure(1, weight=3)

        self.fConfigurePage.rowconfigure(0, weight=1)
        self.fConfigurePage.rowconfigure(1, weight=1)
        self.fConfigurePage.rowconfigure(2, weight=1)
        self.fConfigurePage.rowconfigure(3, weight=1)
        self.fConfigurePage.rowconfigure(4, weight=1)
        self.fConfigurePage.rowconfigure(5, weight=1)

        self.frame_configure.columnconfigure(0, weight=1)
        self.frame_configure.columnconfigure(1, weight=3)

        self.frame_configure.rowconfigure(0, weight=1)
        self.frame_configure.rowconfigure(1, weight=1)
        self.frame_configure.rowconfigure(2, weight=1)
        self.frame_configure.rowconfigure(3, weight=1)
        self.frame_configure.rowconfigure(4, weight=1)
        self.frame_configure.rowconfigure(5, weight=1)

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


        self.speaker_dict = None
        self.mic_dict = None
        self.input_device_id = -1
        self.output_device_id = -1
        self.devices_list = None
        self.sdlist = None

        self.all_devices()

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

    def update_info(self, message):
        self.info_message_text.configure(state=NORMAL)
        self.info_message_text.insert(END, message + '\n')
        self.info_message_text.configure(state=DISABLED)

    def all_devices(self):
        self.devices_list = sd.query_devices()
        #print(devices_list)
        sdstring = self.devices_list.__repr__()
        #print(sdstring)
        self.sdlist = sdstring.split('\n')
        #print(sdlist)        
        self.output_device_combo['values'] = self.sdlist
        self.input_device_combo['values'] = self.sdlist

        self.input_device_id = -1
        self.output_device_id = -1
        for i in range(len(self.sdlist)):
            item = self.sdlist[i]
            if(self.output_device_id == -1):
                index = item.find('<', 0, 1)
                if(index >= 0):
                    self.output_device_id = i
            if(self.input_device_id == -1):
                index = item.find('>', 0, 1)
                if(index >= 0):
                    self.input_device_id = i

        if(self.output_device_id >= 0):
            self.output_device_combo.current(self.output_device_id)
            self.output_device_combo.event_generate('<<ComboboxSelected>>')

        if(self.input_device_id >= 0):
            self.input_device_combo.current(self.input_device_id)
            self.input_device_combo.event_generate('<<ComboboxSelected>>')
            

    def OnOutputDeviceChanged(self, event):
        self.output_device_id = self.output_device_combo.current()
        #self.speaker_select_text.set(self.output_device_combo_text.get())
        self.speaker_dict = self.devices_list[self.output_device_id]
        self.update_info(f"Output Device Properties:" + '\n' +f'{self.speaker_dict}')

    def OnInputDeviceChanged(self, event):
        self.input_device_id = self.input_device_combo.current()
        #self.mic_select_text.set(self.input_device_combo_text.get())
        self.mic_dict = self.devices_list[self.input_device_id]
        self.update_info(f"Input Device Properties:" + '\n' +f'{self.mic_dict}')

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
            try:
                self.audioin = sd.RawInputStream(samplerate=int(self.mic_dict['default_samplerate']), 
                    blocksize=2048, device=self.input_device_id, 
                    channels=self.mic_dict['max_input_channels'],  
                    dtype='float32', latency=self.mic_dict['default_high_input_latency'] )
                audioin_flag = True
            except Exception as e:
                msgbx.showerror("Audio-in creation error", f'{e}')
                audioin_flag = False
            try:    
                self.audioout = sd.RawOutputStream(samplerate=int(self.speaker_dict['default_samplerate']), 
                    blocksize=2048, device=self.output_device_id, 
                    channels=self.speaker_dict['max_output_channels'],  
                    dtype='float32', latency=self.mic_dict['default_high_output_latency'] )
                audioout_flag = True
            except Exception as e:
                msgbx.showerror("Audio-out creation error", f'{e}')
                audioout_flag = False

            if(audioin_flag and audioout_flag):
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
            frame, ret = self.audioin.read(2048)
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

        self.update_info(f"Attempting to join {ip}: text port={port_text} videoport={port_video} audioport={port_audio} as {username}")
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
            self.update_info(f"Error while connecting to server at {ip}: text port={port_text} videoport={port_video} audioport={port_audio} as {username}")
            return

        self.update_info(f"Connected to server at {ip}: text port={port_text} videoport={port_video} audioport={port_audio} as {username}")

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
        
        self.chat_history_text.see('end')
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

        self.is_self_audio_avlbl = socket_client_audio.connect(ip, port_audio, username, 
                self.speaker_dict, self.mic_dict, self.input_device_id, self.output_device_id, 
                self.show_error)
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
        elif self.is_self_audio_avlbl == -3:
            #means error while creating input stream, 
            print('socket_client_audio.connect returned -3: Error while creating Input stream. Please select correct input device in "Configure Device" tab')
            self.btn_start_audio.configure(state=NORMAL)
            self.btn_stop_audio.configure(state=DISABLED)
        elif self.is_self_audio_avlbl == -4:
            #means error while creating output stream
            print('socket_client_audio.connect returned -4: Error while creating Output stream. Please select correct output device in "Configure Device" tab')
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
