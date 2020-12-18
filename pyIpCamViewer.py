import cv2
import threading
import time
import keyboard
import numpy as np

class Stream(object):
    def __init__(self, link):
        self.link = link
        self.stream = None

    def start(self):
        try:
            self.stream = cv2.VideoCapture(self.link)
        except Exception as ex:
            print(f'Error in Stream object {ex}')
            pass


WIDTH=320
LENGTH=240
ALL_CAMS = np.zeros((LENGTH*2,WIDTH*3,3), dtype=np.uint8)
USER='user'
PASS='pass'

STREAMS = {
    'cima_cimo'     : Stream(f'http://{USER}:{PASS}@192.168.1.251/nphMotionJpeg?Resolution={WIDTH}x{LENGTH}&Quality=Standard'),
    'cima_fundo'    : Stream(f'http://{USER}:{PASS}@192.168.1.250/nphMotionJpeg?Resolution={WIDTH}x{LENGTH}&Quality=Standard'),
    'cima_tulha'    : Stream(f'http://{USER}:{PASS}@192.168.1.246/nphMotionJpeg?Resolution={WIDTH}x{LENGTH}&Quality=Standard'),
    'baixo_cimo'    : Stream(f'http://{USER}:{PASS}@192.168.1.249/nphMotionJpeg?Resolution={WIDTH}x{LENGTH}&Quality=Standard'),
    'baixo_fundo'   : Stream(f'http://{USER}:{PASS}@192.168.1.248/nphMotionJpeg?Resolution={WIDTH}x{LENGTH}&Quality=Standard'),
    'baixo_tulha'   : Stream(f'http://{USER}:{PASS}@192.168.1.247/nphMotionJpeg?Resolution={WIDTH}x{LENGTH}&Quality=Standard'),
}


def display_worker(cam_name, video_cap, vertical_pos, horizontal_pos, stop_lamb):
    print(f'Started {cam_name} display_worker')
    while(not stop_lamb()):
        try:
            ret, ALL_CAMS[LENGTH*vertical_pos:LENGTH*(vertical_pos+1), WIDTH*horizontal_pos:WIDTH*(horizontal_pos+1), 0:3] = video_cap.read()
        except Exception as ex:
            print(f'Display worker error: {ex}')
            ALL_CAMS[LENGTH*vertical_pos:LENGTH*(vertical_pos+1), WIDTH*horizontal_pos:WIDTH*(horizontal_pos+1), 0:3] = np.zeros((LENGTH, WIDTH, 3), np.uint8)
            try:
                video_cap.release()
            except Exception as ex:
                print(f'Display worker error releasing: {ex}')
                pass
            STREAMS[cam_name].stream = None
            break
        cv2.waitKey(1)
        time.sleep(0.06)

    print(f'{cam_name} thread stopped!')


def stream_connector(stop_lamb):
    ths = {}

    while(not stop_lamb()):
        counter = 0
        vertical_line = 0
        for cam in STREAMS:
            if cam.startswith('baixo') and vertical_line == 0:
                vertical_line = 1
                counter = 0
            if STREAMS[cam].stream is None:
                print(f'Trying to connect to {cam}...')
                STREAMS[cam].start()
                if STREAMS[cam].stream is not None:
                    ths[cam] = threading.Thread(target=display_worker, kwargs=dict(cam_name=cam, video_cap= STREAMS[cam].stream, vertical_pos=vertical_line, horizontal_pos=counter, stop_lamb=stop_lamb))
                    ths[cam].start()
            counter += 1
        time.sleep(1)
    
    for cam in STREAMS:
        ths[cam].join()
        STREAMS[cam].stream.release()


def run():
    global ALL_CAMS
    stop = False
    th = threading.Thread(target=stream_connector, kwargs=dict(stop_lamb= lambda:stop))
    th.start()
    cv2.namedWindow('Aviario',cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Aviario",cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while(True):
        cv2.imshow('Aviario', ALL_CAMS)
        cv2.waitKey(5)
        time.sleep(0.05)
        if keyboard.is_pressed('q'):
            stop = True
            print('Stopping all')
            break
    
    th.join()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    run()