import cv2

from PIL import Image
#import Image

import numpy as np

class VideoFeed:

    def __init__(self,mode=1,name="w1",capture=1):
        print(name)
        if mode == 1:
            cv2.startWindowThread() #.StartWindowThread()
            cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE) #.NamedWindow(name, cv2.VideoCapture.CV_WINDOW_AUTOSIZE)
        self.camera_index = 0
        self.name=name
        if capture == 1:
            self.capture = cv2.VideoCapture(self.camera_index) #.CaptureFromCAM(self.camera_index)
        
        if not (self.capture.isOpened()):
            cv2.destroyWindow(name)

    def get_frame(self):
        ret, self.frame =  self.capture.read() #cv2.QueryFrame(self.capture)
        """self.c = cv2.waitKey(1)
        if(self.c=="n"): #in "n" key is pressed while the popup window is in focus
            self.camera_index += 1 #try the next camera index
            ret, self.capture = cv2.VideoCapture(self.camera_index) #cv2.CaptureFromCAM(self.camera_index)
            #if not self.capture: #if the next camera index didn't work, reset to 0.
            if ret == False:
                self.camera_index = 0
                self.capture = cv2.VideoCapture(self.camera_index) #cv2.VideoCapture.CaptureFromCAM(camera_index)"""
        
        #following code may not be required as now the frame is numpy array
        """dimensions = self.frame.shape
        self.height = self.frame.shape[0]
        self.width = self.frame.shape[1]
        channels = self.frame.shape[2]

        #jpegImg= Image.fromstring("RGB", self.frame.size, self.frame.tostring())
        jpegImg= Image.frombytes("RGB", (self.width, self.height), self.frame.tostring())
        #retStr=jpegImg.tostring("jpeg","RGB")
        retStr=jpegImg.tobytes("jpeg","RGB")
        print(f'Compressed Size = {len(retStr)}')
        #return retStr"""
        return self.frame

#jpeg.compress(self.frame,640,480,8)

    def set_frame(self, frame):
#im image("RGB",(640,480))
        #jpegPIL = Image.fromstring("RGB",(640,480),frame,"jpeg","RGB","raw")
        #jpegPIL = Image.frombytes("RGB",(640,480),frame,"jpeg","RGB","raw")
        #jpegPIL = Image.frombytes("RGB",(self.width, self.height),frame,"jpeg","RGB","raw")

        #create a blank image
        #cv_im = cv2.CreateImage((640,480), cv2.VideoCapture.IPL_DEPTH_8U, 3)
        #cv_im = np.zeros((640,480, 3), np.uint8)
        #Set the string to image object
        #cv2.VideoCapture.SetData(cv_im,jpegPIL.tostring())
        #cv_im = jpegPIL.tostring()
        #cv_im = jpegPIL.tobytes("jpeg","RGB")

        #OpenCV all frames are in numpy array so we will have to conver this
        #img = np.array(jpegPIL)
        #now show
        #cv2.VideoCapture.ShowImage(self.name, cv_im)
        #cv2.imshow(self.name, cv_im)
        #cv2.imshow(self.name, img)
        cv2.imshow(self.name, frame)

if __name__=="__main__":
    vf = VideoFeed(1,"test",1)
    while 1:
        m = vf.get_frame()
        vf.set_frame(m)
       
