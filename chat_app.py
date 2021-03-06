#v0.8
import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.base import EventLoop
import cv2

import os.path as ospath
import socket_client_text, socket_client_video, socket_client_audio
import sys


class ConnectPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 2

        self.is_self_text_avlbl = True

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

        self.add_widget(Label(text='IP:'))
        self.ip = TextInput(text=prev_ip, multiline=False)
        self.add_widget(self.ip)

        self.add_widget(Label(text='Port for text message:'))
        self.port_text = TextInput(text=prev_text_port, multiline=False)
        self.add_widget(self.port_text)

        self.add_widget(Label(text='Port for video:'))
        self.port_video = TextInput(text=prev_video_port, multiline=False)
        self.add_widget(self.port_video)

        self.add_widget(Label(text='Port for audio:'))
        self.port_audio = TextInput(text=prev_audio_port, multiline=False)
        self.add_widget(self.port_audio)

        self.add_widget(Label(text='Username:'))
        self.username = TextInput(text=prev_username, multiline=False)
        self.add_widget(self.username)
        #self.username.bind(text=self.on_username_changed)
        #self.username.bind(on_text_validate = self.on_username_changed)
        #self.username.bind(focus = self.on_username_changed)

        self.add_widget(Label(text=''))
        self.join = Button(text='Join')
        self.join.bind(on_press=self.join_button)
        self.add_widget(self.join)

    #def on_set_app_title(self, _=None):
    #    chatapp.title = 'Indie Chat-' + self.username.text
    
    """def on_username_changed(self, instance, text):
        chatapp.title = 'Indie Chat-' + instance.text    
        EventLoop.window.title = chatapp.title

        #Clock.schedule_once(self.on_set_app_title, 0.01)"""

    def join_button(self, instance):
        port_text = self.port_text.text
        port_video = self.port_video.text
        port_audio = self.port_audio.text
        ip = self.ip.text
        username = self.username.text

        with open('prev_details.txt', 'w') as f:
            f.write(f'{ip},{port_text},{port_video},{port_audio},{username}')
            f.close()

        info = f"Attempting to join {ip}: text port={port_text} videoport={port_video} audioport={port_audio} as {username}"
        chatapp.info_page.update_info(info)
        chatapp.screen_manager.current = "Info"
        Clock.schedule_once(self.connect, 1)

    # Connects to the server
    # (second parameter is the time after which this function had been called,
    #  we don't care about it, but kivy sends it, so we have to receive it)
    def connect(self, _):
        port_text = int(self.port_text.text)
        port_video = int(self.port_video.text)
        port_audio = int(self.port_audio.text)
        ip = self.ip.text
        username = self.username.text

        if not socket_client_text.connect(ip, port_text, username, show_error):
            return

        ###Commenting and moving the video on audio code for connection to chat page respective buttons
        """
        #if video is not availale continue with text only
        if not socket_client_video.connect(ip, port_video, username, show_error):
            self.is_self_video_avlbl = False
            print('socket_client_video.connect returned False')
            #info = f"Can not connect to video device"
            #chatapp.info_page.update_info(info)
        else:
            self.is_self_video_avlbl = True

        if not socket_client_audio.connect(ip, port_video, username, show_error):
            self.is_self_audio_avlbl = False
            print('socket_client_video.connect returned False')
            #info = f"Can not connect to video device"
            #chatapp.info_page.update_info(info)
        else:
            self.is_self_audio_avlbl = True"""

        
        chatapp.create_chat_page()
        chatapp.screen_manager.current = 'Chat'

   
class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        
        self.message = Label(halign='center', valign='middle', font_size=30)
        self.message.bind(width=self.update_text_width)
        self.add_widget(self.message)

    def update_info(self, message):
        self.message.text = message
    
    def update_text_width(self, *_):
        self.message.text_size = (self.message.width *0.9, None)

class ScrollableView(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScrollView does not allow us to add more than one widget, so we need to trick it
        # by creating a layout and placing two widgets inside it
        # Layout is going to have one collumn and and size_hint_y set to None,
        # so height wo't default to any size (we are going to set it on our own)
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        # Now we need two widgets - Label for chat history and 'artificial' widget below
        # so we can scroll to it every new message and keep new messages visible
        # We want to enable markup, so we can set colors for example
        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()
    
         # We add them to our layout
        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    # Method called externally to add new message to the chat history
    def update_chat_history(self, message):
         # First add new line and message itself
        self.chat_history.text += '\n' + message

        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at teh bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        # As we are updating above, text height, so also label and layout height are going to be bigger
        # than the area we have for this widget. ScrollView is going to add a scroll, but won't
        # scroll to the botton, nor is there a method that can do that.
        # That's why we want additional, empty widget below whole text - just to be able to scroll to it,
        # so scroll to the bottom of the layout
        self.scroll_to(self.scroll_to_point)

    def update_chat_history_layout(self, _=None):
        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at the bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.rows = 4

        self.is_self_video_avlbl = 1
        self.is_self_audio_avlbl = 1

        self.title = Label(text='Welcome: ' + chatapp.connect_page.username.text)
        self.add_widget(self.title)

        # First row is going to be occupied by our scrollable label
        # We want it be take 90% of app height
        self.history = ScrollableView(height=Window.size[1]*0.9, size_hint_y=None)
        self.add_widget(self.history)

        # In the second row, we want to have input fields and Send button
        # Input field should take 80% of window width
        # We also want to bind button click to send_message method
        self.new_message = TextInput(width=Window.size[0]*0.8, size_hint_x=None, multiline=False)
        self.send = Button(text='Send Text')
        self.send.bind(on_press=self.send_text_message)
        """self.start_video = Button(text='Start Video')
        self.start_video.bind(on_press=self.start_video_send)
        if not (chatapp.connect_page.is_self_video_avlbl):
            self.start_video.set_disabled(True)
        self.close = Button(text='Close App')
        self.close.bind(on_press=self.close_app)"""

        # To be able to add 2 widgets into a layout with just one collumn, we use additional layout,
        # add widgets there, then add this layout to main layout as second row
        bottom_line1 = GridLayout(cols=2)
        #bottom_line1 = GridLayout(cols=4)
        bottom_line1.add_widget(self.new_message)
        bottom_line1.add_widget(self.send)
        """bottom_line1.add_widget(self.start_video)
        bottom_line1.add_widget(self.close)"""
        self.add_widget(bottom_line1)

        #add the video start/stop audio start/stop buttons
        self.start_video = Button(text='Start Video')
        self.start_video.bind(on_press=self.start_video_send)
        
        self.stop_video = Button(text='Stop Video')
        self.stop_video.bind(on_press=self.stop_video_send)
        self.stop_video.set_disabled(True)
        
        self.start_audio = Button(text='Start Audio')
        self.start_audio.bind(on_press=self.start_audio_send)

        self.stop_audio = Button(text='Stop Audio')
        self.stop_audio.bind(on_press=self.stop_audio_send)
        self.stop_audio.set_disabled(True)

        self.close = Button(text='Close App')
        self.close.bind(on_press=self.close_app)

        bottom_line2 = GridLayout(cols=5)
        bottom_line2.add_widget(self.start_video)
        bottom_line2.add_widget(self.stop_video)
        bottom_line2.add_widget(self.start_audio)
        bottom_line2.add_widget(self.stop_audio)
        bottom_line2.add_widget(self.close)
        self.add_widget(bottom_line2)

        Window.bind(on_key_down=self.on_key_down)
        Clock.schedule_once(self.focus_text_input, 1)

        socket_client_text.start_listening(self.incoming_message, show_error)

        """if(chatapp.connect_page.is_self_video_avlbl):
            print('before socket_client_video.start_sending_video')
            socket_client_video.start_sending_video(self.show_video, show_error)
            print('after socket_client_video.start_sending_video')"""

        ###commenting code below and moving it in respective button code
        #Even if self camera is not available, one should be able to see other people's video's
        """socket_client_video.start_listening(self.incoming_message, show_error)

        socket_client_audio.start_listening(self.incoming_message, show_error)"""

        self.bind(size=self.adjust_fields)

    def callback_listen_video(self, _=None):
        return

    def callback_listen_audio(self, _=None):
        return

    def callback_send_video(self, _=None):
        return

    def callback_send_audio(self, _=None):
        return

    # Updates page layout
    def adjust_fields(self, *_):

        # Chat history height - 90%, but at least 50px for bottom new message/send button part
        #if Window.size[1] * 0.1 < 50:
        if Window.size[1] * 0.2 < 120:
            #new_height = Window.size[1] - 50
            new_height = Window.size[1] - 120
        else:
            #new_height = Window.size[1] * 0.9
            new_height = Window.size[1] * 0.8
        self.history.height = new_height

        # New message input width - 80%, but at least 160px for send button
        if Window.size[0] * 0.2 < 160:
        #if Window.size[0] * 0.4 < 320:
            new_width = Window.size[0] - 160
            #new_width = Window.size[0] - 320
        else:
            new_width = Window.size[0] * 0.8
            #new_width = Window.size[0] * 0.6
        self.new_message.width = new_width

        # Update chat history layout
        #self.history.update_chat_history_layout()
        Clock.schedule_once(self.history.update_chat_history_layout, 0.01)

    def start_audio_send(self, _):
        port_audio = int(chatapp.connect_page.port_audio.text)
        ip = chatapp.connect_page.ip.text
        username = chatapp.connect_page.username.text

        self.is_self_audio_avlbl = socket_client_audio.connect(ip, port_audio, username, show_error)
        if self.is_self_audio_avlbl == -1:
            #this means client was not able to connect to server, we will not be able to use video chat at all
            print('socket_client_audio.connect returned -1: Not able to connect to server')
            self.start_audio.set_disabled(False)
            self.stop_audio.set_disabled(True)
        elif self.is_self_audio_avlbl == -2:
            #means error while sending the username, which means we do not have connection 
            # to server or server refused
            print('socket_client_audio.connect returned -2: send of username failed and return <= 0')
            self.start_audio.set_disabled(False)
            self.stop_audio.set_disabled(True)
        else:   #we got connected
            self.start_audio.set_disabled(True)
            self.stop_audio.set_disabled(False)
            socket_client_audio.start_listening(self.callback_listen_audio, show_error)
            socket_client_audio.start_sending_audio(self.callback_send_audio, show_error)

    def stop_audio_send(self, _):
        #connection is good, we have the self video window and we were able to send our username
        self.start_audio.set_disabled(False)
        self.stop_audio.set_disabled(True)
        socket_client_audio.close_connection()
    
    def start_video_send(self, _):
        port_video = int(chatapp.connect_page.port_video.text)
        ip = chatapp.connect_page.ip.text
        username = chatapp.connect_page.username.text

        #connect to server
            
        self.is_self_video_avlbl = socket_client_video.connect(ip, port_video, username, show_error)
        if self.is_self_video_avlbl == -1:     #not socket_client_video.connect(ip, port_video, username, show_error):
            #this means client was not able to connect to server, we will not be able to use video chat at all
            print('socket_client_video.connect returned -1: Not able to connect to server')
            self.start_video.set_disabled(False)
            self.stop_video.set_disabled(True)
            #info = f"Can not connect to video device"
            #chatapp.info_page.update_info(info)
        elif self.is_self_video_avlbl == -2:
            #means error while sending the username, which means we do not have connection 
            # to server or server refused
            print('socket_client_video.connect returned -2: send of username failed and return <= 0')
            self.start_video.set_disabled(False)
            self.stop_video.set_disabled(True)
        elif self.is_self_video_avlbl == -3:
            #connection is good, we were able to send self username but error occurred 
            # while creating self video window and we do not have self video window
            print('socket_client_video.connect returned -3: No camera connected so only listen & show')
            self.start_video.set_disabled(True)
            self.stop_video.set_disabled(False)
            socket_client_video.start_listening(self.callback_listen_video, show_error)
        else:   # self.is_self_video_avlbl == 1:
            #connection is good, we have the self video window and we were able to send our username
            self.start_video.set_disabled(True)
            self.stop_video.set_disabled(False)
            socket_client_video.start_listening(self.callback_listen_video, show_error)
            socket_client_video.start_sending_video(self.callback_send_video, show_error)

    def stop_video_send(self, _):
        #connection is good, we have the self video window and we were able to send our username
        self.start_video.set_disabled(False)
        self.stop_video.set_disabled(True)
        socket_client_video.close_connection()


    # Gets called when either Send button or Enter key is being pressed
    # (kivy passes button object here as well, but we don;t care about it)
    def send_text_message(self, _):
        message = self.new_message.text
        self.new_message.text = ''
        
        # If there is any message - add it to chat history and send to the server
        if message:
            self.history.update_chat_history(f'[color=dd2020]{chatapp.connect_page.username.text}[/color] > {message}')
            socket_client_text.send('DATA')
            socket_client_text.send(message)

        # As mentioned above, we have to shedule for refocusing to input field
        Clock.schedule_once(self.focus_text_input, 0.1)

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if(keycode == 40):
            self.send_text_message(None)
    def focus_text_input(self, _):
        self.new_message.focus = True
     
     # Passed to sockets client, get's called on new message
    def incoming_message(self, username, message):
        self.history.update_chat_history(f'[color=20dd20]{username}[/color] > {message}')

    def close_app(self, _):
        #socket_client_text.client_socket_text.close()
        socket_client_text.close_connection()
        self.stop_audio_send(_=None)
        self.stop_video_send(_=None)
        #show_error('Exiting App', True)

        App.get_running_app().stop()
        #Clock.schedule_once(sys.exit, 10)

class EpicApp(App):
    title = 'Indie Chat'
    def build(self):
        self.screen_manager = ScreenManager()

        self.connect_page = ConnectPage()
        screen = Screen(name='Connect')
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        self.info_page = InfoPage()
        screen = Screen(name='Info')
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    # We cannot create chat screen with other but screens, as it;s init method will start listening
    # for incoming connections, but at this stage connection is not being made yet, so we
    # call this method later
    def create_chat_page(self):
        self.chat_page = ChatPage()
        screen = Screen(name='Chat')
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)        

# Error callback function, used by sockets client
# Updates info page with an error message, shows message and schedules exit in 10 seconds
# time.sleep() won't work here - will block Kivy and page with error message won't show up
def show_error(message = '', exit_flag = True):
    chatapp.info_page.update_info(message)
    chatapp.screen_manager.current = 'Info'
    if(exit_flag):
        Clock.schedule_once(sys.exit, 10)
    else:
        chatapp.screen_manager.current = 'Chat'



if __name__ == "__main__":
    chatapp = EpicApp()
    chatapp.run()
  