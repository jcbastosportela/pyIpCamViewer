import cv2
import threading
import time
import numpy as np
import vlc
import keyboard

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


class VlcStream(object):
    def __init__(self, link):
        self.link = link
        self.stream = None

    def open(self):
        try:
            self.stream = vlc.MediaPlayer(self.link)
        except Exception as ex:
            print(f'Error in VlcStream object {ex}')
            pass


mouseX=None
mouseY=None
SELECTED_CAM_VLC=None
WIDTH=320
LENGTH=240
ALL_CAMS = np.zeros((LENGTH*2,WIDTH*3,3), dtype=np.uint8)
IMG_MASK = ALL_CAMS
USER='user'
PASS='pass'
QUALITY='Standard' # Standard / Motion
TYPE='nphMotionJpeg' # nphMotionJpeg / SnapShotJPEG

CAMS_MAP = {
    'cima_cimo'     : (0,0),
    'cima_fundo'    : (1,0),
    'cima_tulha'    : (2,0),
    'baixo_cimo'    : (0,1),
    'baixo_fundo'   : (1,1),
    'baixo_tulha'   : (2,1),
}
CAMS_MAP_inv = {v: k for k, v in CAMS_MAP.items()}

STREAMS = {
    'cima_cimo'     : Stream(f'http://{USER}:{PASS}@192.168.1.251/{TYPE}?Resolution={WIDTH}x{LENGTH}&Quality={QUALITY}'),
    'cima_fundo'    : Stream(f'http://{USER}:{PASS}@192.168.1.250/{TYPE}?Resolution={WIDTH}x{LENGTH}&Quality={QUALITY}'),
    'cima_tulha'    : Stream(f'http://{USER}:{PASS}@192.168.1.246/{TYPE}?Resolution={WIDTH}x{LENGTH}&Quality={QUALITY}'),
    'baixo_cimo'    : Stream(f'http://{USER}:{PASS}@192.168.1.249/{TYPE}?Resolution={WIDTH}x{LENGTH}&Quality={QUALITY}'),
    'baixo_fundo'   : Stream(f'http://{USER}:{PASS}@192.168.1.248/{TYPE}?Resolution={WIDTH}x{LENGTH}&Quality={QUALITY}'),
    'baixo_tulha'   : Stream(f'http://{USER}:{PASS}@192.168.1.247/{TYPE}?Resolution={WIDTH}x{LENGTH}&Quality={QUALITY}')
}
VLC_STREAMS = {
    'cima_cimo'     : VlcStream(f'rtsp://{USER}:{PASS}@192.168.1.251/MediaInput/mpeg4'),
    'cima_fundo'    : VlcStream(f'rtsp://{USER}:{PASS}@192.168.1.250/MediaInput/mpeg4'),
    'cima_tulha'    : VlcStream(f'rtsp://{USER}:{PASS}@192.168.1.246/MediaInput/mpeg4'),
    'baixo_cimo'    : VlcStream(f'rtsp://{USER}:{PASS}@192.168.1.249/MediaInput/mpeg4'),
    'baixo_fundo'   : VlcStream(f'rtsp://{USER}:{PASS}@192.168.1.248/MediaInput/mpeg4'),
    'baixo_tulha'   : VlcStream(f'rtsp://{USER}:{PASS}@192.168.1.242/MediaInput/mpeg4')
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
    try:
        STREAMS[cam_name].stream.release()
        STREAMS[cam_name].stream = None
    except Exception as ex:
        print(f'Display worker error releasing: {ex}')
        pass
    print(f'{cam_name} thread stopped!')


def stream_connector(stop_lamb):
    ths = {}

    while(not stop_lamb()):
        for cam in STREAMS:
            column, line = CAMS_MAP[cam]
            if STREAMS[cam].stream is None:
                print(f'Trying to connect to {cam}...')
                STREAMS[cam].start()
                if STREAMS[cam].stream is not None:
                    ths[cam] = threading.Thread(target=display_worker, kwargs=dict(cam_name=cam, video_cap= STREAMS[cam].stream, vertical_pos=line, horizontal_pos=column, stop_lamb=stop_lamb))
                    ths[cam].start()
        time.sleep(1)
    
    for cam in STREAMS:
        ths[cam].join()


def select_camera(event,x,y,flags,param):
    global mouseX,mouseY
    global SELECTED_CAM_VLC
    if event == cv2.EVENT_MOUSEMOVE:
        mouseX,mouseY = x,y
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        selected_cam=CAMS_MAP_inv[(int(x / WIDTH),int(y / LENGTH))]
        print(f'Clicked on {selected_cam}')
        VLC_STREAMS[selected_cam].open()
        if VLC_STREAMS[selected_cam].stream is not None:
            SELECTED_CAM_VLC=VLC_STREAMS[selected_cam]


def run():
    global ALL_CAMS
    global SELECTED_CAM_VLC
    drawing=False
    playing_vlc=False
    vlc_not_playing_counter=0

    while(True):
        if SELECTED_CAM_VLC is None and not drawing:
            print('drawing...')
            stop = False
            drawing=True
            playing_vlc=False
            th = threading.Thread(target=stream_connector, kwargs=dict(stop_lamb= lambda:stop))
            th.start()
            cv2.namedWindow('Aviario',cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty('Aviario',cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.setMouseCallback('Aviario',select_camera)
        elif SELECTED_CAM_VLC is not None and not playing_vlc:
            print(f'Vlc Selected {SELECTED_CAM_VLC.link}')
            #th.join()  
            playing_vlc=True
            drawing=False
            stop=True
            vlc_not_playing_counter=0
            SELECTED_CAM_VLC.stream.play()          
            SELECTED_CAM_VLC.stream.toggle_fullscreen()
            cv2.destroyAllWindows()
        
        key_pressed = cv2.waitKey(5) & 0xFF
        if playing_vlc:
            time.sleep(0.1)
            if not SELECTED_CAM_VLC.stream.is_playing():
                vlc_not_playing_counter += 1
            else:
                vlc_not_playing_counter = 0
            if keyboard.is_pressed(' ') or SELECTED_CAM_VLC is None or vlc_not_playing_counter > 10:
                SELECTED_CAM_VLC.stream.stop()
                SELECTED_CAM_VLC=None
                playing_vlc=False
        elif drawing: 
            if mouseX is not None and mouseY is not None:
                rec_x0 = int(mouseX / WIDTH)*WIDTH
                rec_x1 = rec_x0 + WIDTH
                rec_y0 = int(mouseY / LENGTH)*LENGTH
                rec_y1 = rec_y0 + LENGTH
                cv2.rectangle(ALL_CAMS, (rec_x0,rec_y0), (rec_x1,rec_y1), (0,255,0), 3)
            cv2.imshow('Aviario', ALL_CAMS)
            time.sleep(0.05)
            if key_pressed == ord('q'):
                stop = True
                print('Stopping all')
                break
            elif key_pressed == ord('a'):
                print(f'{mouseX},{mouseY}')

    #th.join()
    cv2.destroyAllWindows()
    exit()


if __name__ == '__main__':
    run()
