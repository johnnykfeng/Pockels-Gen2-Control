# from xenics.xeneth import *
from xenics.xeneth import XGetFrameFlags, XCamera
from xenics.xeneth.errors import XenethAPIException
import numpy as np

class CameraControl:
    def __init__(self, url):
        self.url = url
        self.cam = XCamera()
        try:
            self.cam.open(url)
            self.buffer = self.cam.create_buffer()
        except XenethAPIException as e:
            print(f"Error: {e.message}")
            raise XenethAPIException(e.message)

    def apply_averaging_filter(self):
        if self.cam.is_initialized:
            flt_averaging = self.cam.filter_queue("Averaging")
            self.cam.pri_image_filter = flt_averaging
            print("Averaging filter applied")


    def start_capture(self):
        if self.cam.is_initialized:
            print("Start capturing")
            self.cam.start_capture()
        else:
            print("Camera is not initialized")

    def get_frame(self):
        if self.cam.get_frame(self.buffer, flags=XGetFrameFlags.XGF_Blocking):
            return self.buffer.image_data

    # def get_average_frames(self, num_frames):

    #     if self.cam.is_capturing:
    #         # avg_frame = np.zeros((self.cam.height, self.cam.width))
    #         frames = []
    #         for i in range(num_frames):
    #             frame = self.get_frame()
    #             frames.append(frame)

    #         #     avg_frame += frame
    #         # print(frame[0].shape)
    #         # print(type(frame[0]))
    #         print(avg_frame[0].shape)
    #         print(type(avg_frame[0]))

    #         return avg_frame
        
    #         # return frames
    #     else:
    #         print("Camera is not capturing")

    def stop_capture(self):
        if self.cam.is_capturing:
            print("Stop capturing")
            self.cam.stop_capture()

    def close_camera(self):
        self.cam.close()

    def save_as_bin(self, data, file_path):
        with open(file_path, 'wb') as f:
            f.write(data)


if __name__=="__main__":
    url = "cam://0"
    cam = CameraControl(url)
    # cam.start_capture()
    # frame = cam.get_frame()
    # cam.save_as_bin(frame, r"CAMERA_IMAGES\\test_image3.bin")
    # avg_frame = cam.get_average_frames(5)
    # cam.save_as_bin(avg_frame, r"CAMERA_IMAGES\\test_image_avg.bin")
    
    if cam.cam.is_capturing:
        print("Camera still capturing")
        cam.stop_capture()
    cam.close_camera()
    print("Camera closed")