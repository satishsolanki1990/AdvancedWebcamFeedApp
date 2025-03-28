import cv2
import threading
import time
import streamlit as st
from queue import Queue


class WebcamFeedApp:
    def __init__(self):
        # UI components
        st.title("Advanced Webcam Feed Application")
        self.info_placeholder = st.empty()
        self.error_placeholder = st.empty()

        self.gray_slider = st.sidebar.slider("Grayscale Intensity", 0, 255, 128)
        self.channel = st.sidebar.selectbox("Select Channel", ["Blue", "Green", "Red"], index=0)
        self.scale_factor = st.sidebar.slider("Frame Scale Factor", 0.1, 2.0, 1.0)

        self.col1, self.col2, self.col3 = st.columns([1,1,1])
        with self.col1:
            st.subheader("BGR Feed")
            self.frame_placeholder = st.empty()
        with self.col2:
            st.subheader("Gray Feed")
            self.gray_placeholder = st.empty() 
        with self.col3:
            st.subheader("B/G/R Feed")
            self.bgr_placeholder = st.empty() 

        # frame capture and processing
        self.err = False
        self.frame_queue = Queue(maxsize=5)  # Limit queue size to prevent memory buildup
        self.frame_cache = Queue(maxsize=900)
        self.info = Queue() 
        self.stop_event = threading.Event()
        self.fps = 30

        
        # Channel mapping for BGR extraction
        self.channel_map = {"Blue": 0, "Green": 1, "Red": 2}
        self.err = False


    def capture_video(self):
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.info.put({"error":{"message": "Unable to open webcam"}})
                self.err = True
                return
            
            # Get webcam parameters
            self.info.put(
                        {'frame_info': {'fps':cap.get(cv2.CAP_PROP_FPS),
                            'frame_width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                            'frame_height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                            'camera':cap.get(cv2.CAP_PROP_POS_FRAMES)
                        }})

            
            # capture and process
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    self.info.put({"error":{"message": "Lost webcam connection"}})
                    self.err = True
                    break
                
                # capture, process and store in cache
                resized_frame = self.resize_frame(frame, self.scale_factor)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                try:
                    # If queue is full, clear older frames 
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            break
                    
                    # Put new frame
                    self.frame_queue.put({
                        'raw': resized_frame,
                        'gray': gray_frame,
                    }, block=False)
                
                except Exception as e:
                    self.info.put({"error":{"message": e}})
                    self.err = True
                # cache
                try:
                    # If queue is full, clear older frame
                    if self.frame_cache.full():
                        try:
                            self.frame_cache.get_nowait()
                        except:
                            break
                    
                    # Put new frame
                    self.frame_cache.put({
                        'raw': resized_frame,
                        'gray': gray_frame,
                    }, block=False)
                except Exception as e:
                    self.info.put({"error":{"message": e }})
                    self.err = True
 
                time.sleep(1/self.fps)
            
            cap.release()
        except Exception as er:
            self.info.put({"error":{"message": er }})
            self.err = True

    
    def resize_frame(self, frame, scale_factor):
        new_width = int(frame.shape[1] * scale_factor)
        new_height = int(frame.shape[0] * scale_factor)
        return cv2.resize(frame, (new_width, new_height))
    
    def display_feed(self):
        info = self.info.get()
        if 'frame_info' in info:
            frame_info = info['frame_info']
            self.info_placeholder.write(f"Camera: {frame_info['camera']},  Frame:{frame_info['frame_width']}x{frame_info['frame_height']}, FPS:{frame_info['fps']}")
        isLive = "Live"        
        while not self.stop_event.is_set():
            if self.err:
                isLive = "Cache"
                if not self.info.empty():
                    err = self.info.get()['error']
                    self.error_placeholder.write(err)
                frames = self.frame_cache.get()
            else:
                frames = self.frame_queue.get()

            self.frame_placeholder.image(frames['raw'], channels="BGR", caption=f"BGR {isLive} Feed", use_container_width=True)
            self.gray_placeholder.image(frames['gray'], channels="Gray", caption=f"Gray {isLive} Feed", use_container_width=True)
            self.bgr_placeholder.image(frames['raw'][:, : , self.channel_map[self.channel]], channels="Gray", caption=f"{isLive} {self.channel} Feed", use_container_width=True)

def main():
    # Create app instance
    app = WebcamFeedApp()
    
    # Start video capture and process in thread
    capture_thread = threading.Thread(target=app.capture_video, daemon=True)
    capture_thread.start()

    app.display_feed()
    
    # Continuously process UI updates
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()