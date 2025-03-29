import cv2
import threading
import time
import streamlit as st
from queue import Queue, Empty

class StreamlitUI_manager:
    """Manage Streamlit UI and its features"""
    def __init__(self):
        # UI components
        st.title("Advanced Webcam Feed Application")
        self.info_placeholder = st.empty()
        self.error_placeholder = st.empty()

        self.gray_slider = st.sidebar.slider("Grayscale Intensity", 0, 255, 128) # gray intensity
        self.channel = st.sidebar.selectbox("Select Channel", ["Blue", "Green", "Red"], index=0) # select channel
        self.user_width = st.sidebar.slider("Frame width", 320, 1920, 640)
        self.user_height = st.sidebar.slider("Frame height", 240, 1080, 480)

        # Add mirror option
        self.mirror_mode = st.sidebar.checkbox("Mirror Mode", value=True)


        self.col1, self.col2, self.col3 = st.columns([1,1,1])
        self.channel_map = {"Blue": 0, "Green": 1, "Red": 2}

        with self.col1:
            st.subheader("BGR Feed")
            self.frame_placeholder = st.empty()
        with self.col2:
            st.subheader("Gray Feed")
            self.gray_placeholder = st.empty() 
        with self.col3:
            st.subheader("B/G/R Feed")
            self.bgr_placeholder = st.empty()

    def display_info(self, message):
        self.info_placeholder.write(message)

    def display_error(self, message):
        self.error_placeholder.write(message)

    def display_feed(self, frames, live_or_cache):
        if frames:
            frame = frames['raw']
            grayframe = cv2.convertScaleAbs(frames['gray'], alpha=1, beta=self.gray_slider)

             # Apply mirror effect if enabled
            if self.mirror_mode:
                frame = cv2.flip(frame, 1)  # 1 = horizontal flip
                grayframe = cv2.flip(grayframe, 1) 
                
            self.frame_placeholder.image(frame, channels="BGR", caption=f"BGR {live_or_cache} Feed", use_container_width=True)
            self.gray_placeholder.image(grayframe, channels="Gray", caption=f"Gray {live_or_cache} Feed", use_container_width=True)
            self.bgr_placeholder.image(frame[:, :, self.channel_map[self.channel]], channels="Gray", caption=f"{live_or_cache} {self.channel} Feed", use_container_width=True)
        else:
            self.error_placeholder.write("No frames available")

class WebcamFeedApp:
    def __init__(self):
        # UI
        self.ui_manager = StreamlitUI_manager()

        # Queues and threading
        self.frame_queue = Queue(maxsize=30)  # Store 1 sec (30 frames) for live feed
        self.frame_cache = Queue(maxsize=900) # Store 30 sec (30x30 frames) for cache feed
        self.message_queue = Queue() # Logging
        self.stop_event = threading.Event()
        
        # Camera parameters
        self.fps = 30
        self.camera_error = False

    def capture_video(self):
        """ Frame capture and processing """
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.message_queue.put({"error": "Unable to open webcam"})
                self.camera_error = True
                return
            
            # Get webcam parameters
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.message_queue.put({'info': f"Camera: Frame {frame_width}x{frame_height}, FPS: {fps}"})

            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    self.message_queue.put({"error": "Lost webcam connection"})
                    self.camera_error = True
                    break
                
                # Resize and convert frame
                resized_frame = cv2.resize(frame, (self.ui_manager.user_width, self.ui_manager.user_height))
                gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

                frame_data = {
                    'raw': resized_frame,
                    'gray': gray_frame,
                }

                try:
                    # Try to put frame in queue, with a timeout to prevent blocking
                    self.frame_queue.put(frame_data, timeout=0.1)
                    self.frame_cache.put(frame_data, timeout=0.1)
                except Exception as e:
                    # If queue is full, remove oldest frame
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(frame_data)
                        self.frame_cache.get_nowait()
                        self.frame_cache.put(frame_data)
                    except Empty:
                        pass
                    except Exception as inner_e:
                        self.message_queue.put({"error": f"Queue error: {inner_e}"})

                # Control frame rate
                time.sleep(1/self.fps)
            
            cap.release()
        except Exception as e:
            self.message_queue.put({"error": f"Capture error: {e}"})
            self.camera_error = True

    def display_feed(self):
        """ Display video feed and handle messages """
        while not self.stop_event.is_set():
            # Process messages
            try:
                while True:
                    msg = self.message_queue.get_nowait()
                    if 'info' in msg:
                        self.ui_manager.display_info(msg['info'])
                    elif 'error' in msg:
                        self.ui_manager.display_error(msg['error'])
            except Empty:
                pass

            try:
                # Prioritize live feed, fallback to cache
                live_or_cache = "Live"
                try:
                    frames = self.frame_queue.get(timeout=0.1)
                except Empty:
                    if self.camera_error and not self.frame_cache.empty():
                        live_or_cache = "Cache"
                        frames = self.frame_cache.get(timeout=0.1)
                    else:
                        # No frames available
                        time.sleep(0.1)
                        continue

                # Display frames
                self.ui_manager.display_feed(frames, live_or_cache)

            except Empty:
                self.ui_manager.display_info("Waiting for video feed...")
                time.sleep(0.1)
            except Exception as e:
                self.message_queue.put({"error": f"Display error: {e}"})
                time.sleep(0.1)

def main():
    # Create app instance
    app = WebcamFeedApp()
    
    # Start video capture in a separate thread
    capture_thread = threading.Thread(target=app.capture_video, daemon=True)
    capture_thread.start()

    try:
        # Run display feed in the main thread
        app.display_feed()
    except KeyboardInterrupt:
        st.write("Application stopped by user")
    finally:
        # Ensure threads are stopped cleanly
        app.stop_event.set()
        capture_thread.join(timeout=2)

if __name__ == "__main__":
    main()