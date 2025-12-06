from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
# import eventlet  # Removed eventlet import
import cv2
import numpy as np
import mediapipe as mp
import base64
import threading
import time

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Camera parameters
fx, fy = 800.0, 800.0  # Focal length
cx, cy = 320.0, 240.0  # Image center

# 3D foot model points (in meters)
foot_3d_points = np.array([
    [0, 0, 0],       # Heel
    [0.5, 0, 0],     # Toe (20cm forward)
    [0, 0.1, 0],     # Ankle (10cm up)
    [0.1, 0, 0.05]   # Side of foot (5cm to side)
], dtype=np.float32)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, 
                   model_complexity=1,
                   min_detection_confidence=0.5,
                   min_tracking_confidence=0.5)

# Use webcam (0) or video file
cap = cv2.VideoCapture('5.mp4')

# Helper to get landmark pixel coordinates

def get_landmark_px(lm, idx, w, h):
    landmark = lm[idx]
    if landmark.visibility > 0.8:
        return [landmark.x * w, landmark.y * h]
    return None

# Streaming thread
streaming = False

def video_stream_thread():
    global streaming
    print("[Backend] Video stream thread started")
    while streaming:
        ret, frame = cap.read()
        if not ret:
            print("[Backend] Failed to read frame from camera")
            break
        # print("[Backend] Frame read from camera")
        h, w = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        foot_data = []
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            for side in ['left', 'right']:
                if side == 'left':
                    indices = [
                        mp_pose.PoseLandmark.LEFT_HEEL.value,
                        mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value,
                        mp_pose.PoseLandmark.LEFT_ANKLE.value,
                        mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value
                    ]
                else:
                    indices = [
                        mp_pose.PoseLandmark.RIGHT_HEEL.value,
                        mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value,
                        mp_pose.PoseLandmark.RIGHT_ANKLE.value,
                        mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value
                    ]
                pts_2d = []
                pts_3d = []
                for i, idx in enumerate(indices[:4]):
                    px = get_landmark_px(lm, idx, w, h)
                    if px is not None:
                        pts_2d.append(px)
                        pts_3d.append(foot_3d_points[i])
                if len(pts_2d) >= 4:
                    pts_2d = np.array(pts_2d, dtype=np.float32)
                    pts_3d = np.array(pts_3d, dtype=np.float32)
                    success, rvec, tvec = cv2.solvePnP(
                        pts_3d,
                        pts_2d,
                        cameraMatrix=np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]),
                        distCoeffs=None,
                        flags=cv2.SOLVEPNP_SQPNP
                    )
                    if success:
                        R, _ = cv2.Rodrigues(rvec)
                        transform = np.eye(4)
                        transform[:3, :3] = R
                        transform[:3, 3] = tvec.flatten()
                        foot_data.append({
                            'side': side,
                            'transform': transform.tolist(),
                            'pts_2d': pts_2d.tolist(),
                            'pts_3d': pts_3d.tolist()
                        })
        # Encode frame as JPEG and then base64
        _, buffer = cv2.imencode('.jpg', frame)
        # print("[Backend] Frame encoded to JPEG")
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        # Log foot data
        if foot_data:
            for i, foot in enumerate(foot_data):
                # print(f"[Backend] Foot {i} ({foot['side']}):")
                # print(f"  3D transform: {foot['transform']}")
                # print(f"  2D points: {foot['pts_2d']}")
                
                pass               # print(f"  3D points: {foot['pts_3d']}")
        else:
            print("[Backend] No foot detected in this frame")
        # Send via WebSocket
        # print("[Backend] Emitting frame to clients")
        socketio.emit('frame', {
            'frame': frame_b64,
            'foot_data': foot_data
        })
        time.sleep(0.03)  # ~30 FPS

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('static', path)

@socketio.on('start_stream')
def handle_start_stream():
    global streaming
    # print("[Backend] start_stream received from client")
    if not streaming:
        streaming = True
        thread = threading.Thread(target=video_stream_thread)
        thread.daemon = True
        thread.start()
    emit('stream_started', {'status': 'ok'})

@socketio.on('stop_stream')
def handle_stop_stream():
    global streaming
    print("[Backend] stop_stream received from client")
    streaming = False
    emit('stream_stopped', {'status': 'ok'})

if __name__ == '__main__':
    print("[Backend] Starting Flask-SocketIO server on http://localhost:5000/")
    socketio.run(app, host='0.0.0.0', port=5000) 