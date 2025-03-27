# Advanced Webcam Feed Application

## Overview

This Streamlit-based application provides a real-time, multi-view webcam feed with advanced image processing and visualization capabilities. The application offers simultaneous display of BGR, grayscale, and color channel feeds with interactive controls.

## Features

### 🎥 Real-Time Video Processing
- Capture live webcam feed
- Simultaneous display of multiple image representations
- Adaptive frame caching for continuous viewing

### 🖥️ Interactive Controls
- Grayscale intensity adjustment
- Color channel selection (Blue/Green/Red)
- Dynamic frame resizing
- Sidebar information display

### 🔧 Technical Highlights
- Multithreaded video capture [**Work in progress**]
- Thread-safe frame caching
- Error handling for webcam connectivity
- Flexible UI layout

## Prerequisites

### System Requirements
- Python 3.8+
- Webcam-enabled device

### Dependencies
- OpenCV (`opencv-python`)
- NumPy
- Streamlit
- Threading module

## Installation

1. Clone the repository:
```bash
git clone git@github.com:satishsolanki1990/AdvancedWebcamFeedApp.git
cd AdvancedWebcamFeedApp
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install required packages:
```bash
pip install streamlit opencv-python 
```

## Running the Application

```bash
streamlit run main.py
```

## Usage Guide

### Sidebar Controls
- **Grayscale Intensity**: Adjust the brightness/contrast of the grayscale feed
- **Channel Selection**: Choose between Blue, Green, and Red color channels
- **Frame Scale Factor**: Resize the video frames dynamically

### Display Sections
1. **Main BGR Feed**: Full-color webcam view
2. **Grayscale Feed**: Monochrome representation
3. **Channel Feed**: Selected color channel visualization

## Performance Considerations
- Application uses multithreading for smooth performance [**Work in progress**]
- Frame caching supports up to 30 seconds of video
- Adjustable frame rate and scale factor

## Contact

Your Name - satishsolanki1990@gmail.com
