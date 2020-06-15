#v0.9 - Alpha 1
#v0.8
import cv2
import zlib

#from PIL import Image
#import Image

#import numpy as np

class VideoFeed:

    def __init__(self,mode=1,name="w1",capture=1, reduce_size=True):
        #print(name)
        self.reduce_size = reduce_size
        #if mode == 1:
        #    cv2.startWindowThread() #.StartWindowThread()
        self.camera_index = 0
        self.name=name
        if capture == 1:
            self.capture = cv2.VideoCapture(self.camera_index) #.CaptureFromCAM(self.camera_index)
            if not (self.capture.isOpened()):
                self.capture.release()
                #cv2.destroyWindow(name)
            else:
                cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE) #.NamedWindow(name, cv2.VideoCapture.CV_WINDOW_AUTOSIZE)


    def get_frame(self):
        ret, frame =  self.capture.read() #cv2.QueryFrame(self.capture)
        #frame1 = cv2.flip(frame, 1)

        if(self.reduce_size == True):
            frame = cv2.resize(frame, (0,0), fx = 0.5, fy = 0.5, interpolation=cv2.INTER_AREA)

        return frame

#jpeg.compress(self.frame,640,480,8)

    def set_frame(self, frame):
        cv2.imshow(self.name, frame)
        x = cv2.waitKey(1)

if __name__=="__main__":
    vf = VideoFeed(1,"test",1)
    while 1:
        m = vf.get_frame()
        vf.set_frame(m)
       
