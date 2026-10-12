import cv2
import time
import threading
from flask import Flask, Response
from ultralytics import YOLO

# ==========================================
# 1. Threaded Video Capture (Prevents Lag)
# ==========================================
class VideoStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        # Lower resolution for high FPS performance on robots
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.cap.isOpened():
                break
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()

# ==========================================
# 2. Main Robot Perception Engine
# ==========================================
# Initialize YOLO Nano model
model = YOLO("yolov8n.pt")

# Initialize threaded camera feed
vs = VideoStream(src=0).start()
time.sleep(1.0)  # Allow camera to warm up

# Initialize Flask app for remote live streaming
app = Flask(__name__)

def process_and_stream():
    while True:
        frame = vs.read()
        if frame is None:
            continue

        # Run detection (conf=0.4 filters out weak false positives)
        results = model(frame, conf=0.4, verbose=False)
        annotated_frame = results[0].plot()

        # Parse detected objects for navigation decisions
        detected_objects = []
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            label = model.names[class_id]
            confidence = float(box.conf[0])
            
            # Extract bounding box coordinates: [x_min, y_min, x_max, y_max]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Calculate object center point for obstacle avoidance / tracking
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            detected_objects.append({
                "label": label,
                "confidence": round(confidence, 2),
                "bbox": [x1, y1, x2, y2],
                "center": (center_x, center_y)
            })

        # --- ROBOT ACTION LOGIC GOES HERE ---
        # Example decision logic based on detections:
        for obj in detected_objects:
            if obj["label"] in ["person", "chair", "obstacle"]:
                # Print telemetry to terminal
                print(f"ALERT: Detected {obj['label']} at Center: {obj['center']}")
                # Pass 'obj' coordinates to motor controller (e.g., ROS, Serial, GPIO)
        # -----------------------------------

        # Encode frame to JPEG for live web display
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ==========================================
# 3. Web Interface (View Feed from Any Device)
# ==========================================
@app.route('/')
def video_feed():
    return Response(process_and_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Robot detection system running...")
    print("View live feed on your phone/laptop at: http://<robot_ip_address>:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)