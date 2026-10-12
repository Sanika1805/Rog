import cv2
import numpy as np
from flask import Flask, Response

app = Flask(__name__)

# Initialize Logitech C920 webcam (default camera index 0)
camera = cv2.VideoCapture(0)

# Optional: Request higher capture resolution from webcam hardware
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Convert frame to HSV color space for accurate color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Red spans across two ranges in HSV space
            lower_red1 = np.array([0, 120, 70])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 120, 70])
            upper_red2 = np.array([180, 255, 255])

            # Create masks and combine them
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2

            # Find contours around detected red areas
            contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Ignore tiny noisy pixels
                    x, y, w, h = cv2.boundingRect(contour)
                    # Draw a green bounding box around detected red objects
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, "Red Object Detected", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Stream frame as MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    # CSS added to make image cover full screen with zero margins
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Red Object Detection - Fullscreen</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                background-color: #000;
            }
            body, html {
                width: 100%;
                height: 100%;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            img {
                width: 100vw;
                height: 100vh;
                object-fit: contain; /* Keeps aspect ratio intact without distortion */
            }
        </style>
    </head>
    <body>
        <img src="/video_feed">
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)