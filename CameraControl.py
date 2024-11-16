# from xenics.xeneth import *
from xenics.xeneth import XGetFrameFlags, XCamera
from xenics.xeneth.errors import XenethAPIException

class CameraControl:
    def __init__(self, url):
        self.url = url
        self.cam = XCamera()
        try:
            self.cam.open(url)
            self.buffer = self.cam.create_buffer()
        except XenethAPIException as e:
            print(f"Error: {e.message}")


    def start_capture(self):
        if self.cam.is_initialized:
            print("Start capturing")
            self.cam.start_capture()
        else:
            print("Camera is not initialized")

    def get_frame(self):
        if self.cam.get_frame(self.buffer, flags=XGetFrameFlags.XGF_Blocking):
            return self.buffer.image_data

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
    cam.start_capture()
    frame = cam.get_frame()
    cam.save_as_bin(frame, r"CAMERA_IMAGES\\test_image3.bin")
    cam.stop_capture()
    cam.close_camera()
    print("Camera closed")