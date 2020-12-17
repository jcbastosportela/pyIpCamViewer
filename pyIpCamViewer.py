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

ALL_CAMS = np.zeros((LENGTH*2,WIDTH*3,3), dtype=np.uint8)
# GLOBAL_STOP = False

def display_worker(cam_name, video_cap, draw, stop_lamb):
    print(f'Started {cam_name} display_worker')
    while(not stop_lamb()):
        ret, frame = video_cap.read()
        if frame is None:
            try:
                video_cap.release()
            except Exception as ex:
                print(f'Display worker error: {ex}')
                pass
            STREAMS[cam_name].stream = None
            break
        draw(cam_name, frame)
        cv2.waitKey(100)
        time.sleep(0.05)

    print(f'{cam_name} thread stopped!')


def draw_frame(cam_name, frame):
    global ALL_CAMS
    if frame is not None:
        if cam_name == 'cima_cimo':
            ALL_CAMS[0:LENGTH, 0:WIDTH, 0:3] = frame
        elif cam_name == 'cima_fundo':
            ALL_CAMS[0:LENGTH, WIDTH:WIDTH*2, 0:3] = frame
        elif cam_name == 'cima_tulha':
            ALL_CAMS[0:LENGTH, WIDTH*2:WIDTH*3, 0:3] = frame
        elif cam_name == 'baixo_cimo':
            ALL_CAMS[LENGTH:LENGTH*2, 0:WIDTH, 0:3] = frame
        elif cam_name == 'baixo_fundo':
            ALL_CAMS[LENGTH:LENGTH*2, WIDTH:WIDTH*2, 0:3] = frame
        elif cam_name == 'baixo_tulha':
            ALL_CAMS[LENGTH:LENGTH*2, WIDTH*2:WIDTH*3, 0:3] = frame
    else:
        try:
            STREAMS[cam_name].stream.release()
        except Exception as ex:
            print(f'blaa {ex}')
            pass
        STREAMS[cam_name].stream = None
        return


def stream_connector(stop_lamb):
    ths = {}

    while(not stop_lamb()):
        for cam in STREAMS:
            if STREAMS[cam].stream is None:
                print(f'Trying to connect to {cam}...')
                STREAMS[cam].start()
                if STREAMS[cam].stream is not None:
                    ths[cam] = threading.Thread(target=display_worker, kwargs=dict(cam_name=cam, video_cap= STREAMS[cam].stream, draw=lambda cam_name, frame: 
        draw_frame(cam_name, frame), stop_lamb=stop_lamb))
                    ths[cam].start()
        time.sleep(5)
    
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

        if ALL_CAMS is not None:
            cv2.imshow('Aviario', ALL_CAMS)
        cv2.waitKey(100)
        time.sleep(0.05)
        if keyboard.is_pressed('q'):
            stop = True
            print('Stopping all')
            break
    
    th.join()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    run()