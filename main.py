import cv2
import threading
import time
import streamlit as st
from queue import deque
from threading import Lock

class WebcamFeedApp:
    def __init__(self):
        # Initialize thread-safe queues and locks
        self.frame_cache_bgr = deque(maxlen=900)
        self.frame_cache_gray = deque(maxlen=900)
        self.frame_lock = Lock()
        
        # Webcam parameters
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.capture_running = True
        self.camera_source = 0
        
        
        
    
    def capture_video(self):
        try:
            cap = cv2.VideoCapture(0)
            
            # Validate webcam capture
            if not cap.isOpened():
                st.error("Error: Unable to open webcam")
                return
            
            # Get webcam parameters
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.camera_source = cap.get(cv2.CAP_PROP_POS_FRAMES) 
            
            while self.capture_running:
                ret, frame = cap.read()
                if not ret:
                    st.warning("Lost webcam connection")
                    break
                
                # Thread-safe frame cache update
                with self.frame_lock:
                    self.frame_cache_bgr.append(frame)
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    self.frame_cache_gray.append(gray_frame)
                
                time.sleep(1 / self.fps)
            
            cap.release()
        except Exception as e:
            st.error(f"Capture error: {e}")
    
    def resize_frame(self, frame, scale_factor):
        new_width = int(frame.shape[1] * scale_factor)
        new_height = int(frame.shape[0] * scale_factor)
        return cv2.resize(frame, (new_width, new_height))
    
    def display_feed(self):
        channel_map = {"Blue": 0, "Green": 1, "Red": 2}
        # Create columns for parallel display
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            st.subheader("BGR Feed")
            frame_placeholder = st.empty() # place holder for video feed

        with col2:
            st.subheader("Gray Feed")
            gray_placeholder = st.empty()

        with col3:
            st.subheader("B/G/R Feed")
            blue_placeholder = st.empty()

        while True:
            with self.frame_lock:
                if not self.frame_cache_bgr:
                    time.sleep(0.1)
                    continue
                
                frame = self.frame_cache_bgr[-1]

            resized_frame = self.resize_frame(frame, st.session_state.scale_factor)

            # BGR display
            frame_placeholder.image(resized_frame, channels="BGR", caption="Live BGR Feed", use_container_width=True)

            # Gray display
            gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.convertScaleAbs(gray_frame, alpha=1, beta=st.session_state.gray_slider)
            caption = f"Live Grayscale Feed (Intensity: {st.session_state.gray_slider})"
            gray_placeholder.image(gray_frame, channels="Gray", caption=caption, use_container_width=True)

            # B/G/R display
            bgr_frame = resized_frame[:, :, channel_map[st.session_state.channel]]
            caption = f"Live {st.session_state.channel} Channel Feed"
            blue_placeholder.image(bgr_frame, channels=st.session_state.channel, caption=caption, use_container_width=True)
            
            time.sleep(1 / self.fps)
    
    def run(self):
        st.title("Advanced Webcam Feed Application")
        
        # Sidebar controls
        st.session_state.gray_slider = st.sidebar.slider("Grayscale Intensity", 0, 255, 128)
        st.session_state.channel = st.sidebar.selectbox("Select Channel", ["Blue", "Green", "Red"], index=0)
        st.session_state.scale_factor = st.sidebar.slider("Frame Scale Factor", 0.1, 2.0, 1.0)

        # Display webcam info
        st.sidebar.write(f"Video Source: Camera {self.camera_source}")
        st.sidebar.write(f"FPS: {self.fps}")
        st.sidebar.write(f"Frame Dimensions: {self.frame_width}x{self.frame_height}")
        
        self.display_feed()

def main():
    app = WebcamFeedApp()
    
    # Start video capture in a separate thread
    threading.Thread(target=app.capture_video, daemon=True).start()
    
    # Run the application
    app.run()

if __name__ == "__main__":
    main()