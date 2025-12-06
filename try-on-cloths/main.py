# import cv2
# import mediapipe as mp

# # Setup MediaPipe Pose
# mp_pose = mp.solutions.pose

# pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False)

# # Open webcam or video
# cap = cv2.VideoCapture('3.mp4')

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame = cv2.flip(frame, 1)
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     # Detect pose
#     results = pose.process(rgb)

#     if results.pose_landmarks:
#         h, w = frame.shape[:2]
#         landmarks = results.pose_landmarks.landmark

#         def draw_point(index, label, color):
#             x = int(landmarks[index].x * w)
#             y = int(landmarks[index].y * h)
#             cv2.circle(frame, (x, y), 8, color, -1)
#             cv2.putText(frame, label, (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
#             print(f"{label}: ({x}, {y})")

#         print("\n🦶 Feet Keypoints:")
#         draw_point(mp_pose.PoseLandmark.LEFT_HEEL.value, "Left Heel", (0, 255, 0))
#         draw_point(mp_pose.PoseLandmark.RIGHT_HEEL.value, "Right Heel", (0, 0, 255))
#         draw_point(mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value, "Left Toes", (255, 255, 0))
#         draw_point(mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value, "Right Toes", (255, 0, 255))

#     # Show frame
#     cv2.imshow("MediaPipe Pose (Feet Only)", frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# cap.release()
# cv2.destroyAllWindows()







# --------------------------    --------------------------------
# import cv2
# import mediapipe as mp
# import math
# import numpy as np

# def overlay_transparent(background, overlay, x, y):
#     h, w = overlay.shape[0], overlay.shape[1]
#     if x + w > background.shape[1] or y + h > background.shape[0]:
#         return background

#     alpha_overlay = overlay[:, :, 3] / 255.0
#     alpha_background = 1.0 - alpha_overlay

#     for c in range(3):
#         background[y:y+h, x:x+w, c] = (alpha_overlay * overlay[:, :, c] +
#                                        alpha_background * background[y:y+h, x:x+w, c])
#     return background

# def ensure_alpha(img):
#     if img is not None and img.shape[2] == 3:
#         alpha_channel = np.ones(img.shape[:2], dtype=img.dtype) * 255
#         img = np.dstack([img, alpha_channel])
#     return img

# def rotate_image(image, angle):
#     (h, w) = image.shape[:2]
#     center = (w // 2, h // 2)
#     M = cv2.getRotationMatrix2D(center, angle, 1.0)
#     if image.shape[2] == 4:
#         rotated_channels = [
#             cv2.warpAffine(image[:, :, i], M, (w, h), borderValue=0)
#             for i in range(4)
#         ]
#         return np.stack(rotated_channels, axis=-1)
#     else:
#         return cv2.warpAffine(image, M, (w, h), borderValue=0)

# mp_pose = mp.solutions.pose
# pose = mp_pose.Pose()
# cap = cv2.VideoCapture('4.mp4')

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     h, w = frame.shape[:2]
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = pose.process(rgb)

#     if results.pose_landmarks:
#         landmarks = results.pose_landmarks.landmark

#         # Load both shoe overlays and ensure alpha
#         left_shoe_img = cv2.imread("shoe_render_left.png", cv2.IMREAD_UNCHANGED)
#         right_shoe_img = cv2.imread("shoe_render.png", cv2.IMREAD_UNCHANGED)
#         left_shoe_img = ensure_alpha(left_shoe_img)
#         right_shoe_img = ensure_alpha(right_shoe_img)

#         # Get landmarks for both feet
#         left_heel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value]
#         left_toe = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value]
#         right_heel = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]
#         right_toe = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value]

#         # Overlay each foot
#         for heel, toe, shoe_img in [(left_heel, left_toe, left_shoe_img), (right_heel, right_toe, right_shoe_img)]:
#             if shoe_img is None:
#                 continue
#             heel_pt = (int(heel.x * w), int(heel.y * h))
#             toe_pt = (int(toe.x * w), int(toe.y * h))

#             dx = toe_pt[0] - heel_pt[0]
#             dy = toe_pt[1] - heel_pt[1]
#             angle = math.degrees(math.atan2(dy, dx))
#             length = int(math.hypot(dx, dy))

#             resized = cv2.resize(shoe_img, (length, int(length * 0.5)))
#             resized = ensure_alpha(resized)
#             rotated = rotate_image(resized, angle)
#             rotated = ensure_alpha(rotated)

#             x_offset = heel_pt[0] - rotated.shape[1] // 3
#             y_offset = heel_pt[1] - rotated.shape[0] // 2

#             frame = overlay_transparent(frame, rotated, x_offset, y_offset)

#     cv2.imshow("Virtual Shoe Try-On", frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()





################# model working ###############
import cv2
import numpy as np
import mediapipe as mp
from app import render_on_frame

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, 
                   model_complexity=1,
                   min_detection_confidence=0.5,
                   min_tracking_confidence=0.5)

# Camera parameters
fx, fy = 800.0, 800.0  # Focal length
cx, cy = 320.0, 240.0  # Image center

cap = cv2.VideoCapture(0)  # or use 0 for webcam

# 3D foot model points (in meters)
# Now with 4 points: heel, toe, ankle, and another foot point
foot_3d_points = np.array([
    [0, 0, 0],       # Heel
    [0.5, 0, 0],     # Toe (20cm forward)
    [0, 0.1, 0],     # Ankle (10cm up)
    [0.1, 0, 0.05]   # Side of foot (5cm to side)
], dtype=np.float32)

renderer_cache = {}

def get_landmark_px(lm, idx, w, h):
    """Get landmark pixel coordinates if visible."""
    landmark = lm[idx]
    if landmark.visibility > 0.8:
        return [landmark.x * w, landmark.y * h]
    return None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    h, w = frame.shape[:2]
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)
    
    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark
        
        # Process both feet
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
            
            # Get visible 2D points
            pts_2d = []
            pts_3d = []
            for i, idx in enumerate(indices[:4]):  # Use first 4 points
                px = get_landmark_px(lm, idx, w, h)
                if px is not None:
                    pts_2d.append(px)
                    pts_3d.append(foot_3d_points[i])
            
            if len(pts_2d) >= 4:  # Need at least 4 points
                pts_2d = np.array(pts_2d, dtype=np.float32)
                pts_3d = np.array(pts_3d, dtype=np.float32)
                
                # Solve PnP with SQPNP method that works with 3+ points
                success, rvec, tvec = cv2.solvePnP(
                    pts_3d,
                    pts_2d,
                    cameraMatrix=np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]),
                    distCoeffs=None,
                    flags=cv2.SOLVEPNP_SQPNP  # Changed to SQPNP
                )
                
                if success:
                    R, _ = cv2.Rodrigues(rvec)
                    transform = np.eye(4)
                    transform[:3, :3] = R
                    transform[:3, 3] = tvec.flatten()
                    
                    frame = render_on_frame(
                        frame_bgr=frame,
                        foot_transform_cv=transform,
                        fx=fx, fy=fy, cx=cx, cy=cy,
                        renderer_cache=renderer_cache
                    )
                    
                    # Debug points
                    for pt in pts_2d:
                        cv2.circle(frame, tuple(pt.astype(int)), 5, 
                                  (0, 255, 0) if side == 'left' else (0, 0, 255), -1)
                print("2D Points:", pts_2d)
                print("3D Points:", pts_3d)
    cv2.imshow('3D Shoe Try-On', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()





# import cv2
# import numpy as np
# import mediapipe as mp
# from app import render_on_frame

# # Initialize MediaPipe Pose
# mp_pose = mp.solutions.pose
# pose = mp_pose.Pose(static_image_mode=False, 
#                    model_complexity=1,
#                    min_detection_confidence=0.5,
#                    min_tracking_confidence=0.5)

# # Camera parameters
# # Adjust the focal length if the shoe appears too large/small
# # fx, fy = 800.0, 800.0  # Focal length
# fx, fy = 900.0, 900.0  # Try smaller values for larger FOV
# cx, cy = 320.0, 240.0  # Image center

# cap = cv2.VideoCapture('3.mp4')  # or use 0 for webcam

# # 3D foot model points (in meters)
# foot_3d_points = np.array([
#     [0, 0, 0],       # Heel
#     [0.2, 0, 0],     # Toe (20cm forward)
#     [0, 0.1, 0],     # Ankle (10cm up)
#     [0.1, 0, 0.05]   # Side of foot (5cm to side)
# ], dtype=np.float32)

# renderer_cache = {}

# def get_landmark_px(lm, idx, w, h):
#     """Get landmark pixel coordinates if visible."""
#     landmark = lm[idx]
#     if landmark.visibility > 0.9: #Lower the visibility threshold if landmarks aren't being detected
#         return [landmark.x * w, landmark.y * h]
#     return None

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break
    
#     # Create a copy of the original frame for rendering
#     output_frame = frame.copy()
#     h, w = frame.shape[:2]
    
#     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = pose.process(frame_rgb)
    
#     if results.pose_landmarks:
#         lm = results.pose_landmarks.landmark
        
#         # Process both feet
#         for side in ['left', 'right']:
#             if side == 'left':
#                 indices = [
#                     mp_pose.PoseLandmark.LEFT_HEEL.value,
#                     mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value,
#                     mp_pose.PoseLandmark.LEFT_ANKLE.value,
#                     mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value
#                 ]
#             else:
#                 indices = [
#                     mp_pose.PoseLandmark.RIGHT_HEEL.value,
#                     mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value,
#                     mp_pose.PoseLandmark.RIGHT_ANKLE.value,
#                     mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value
#                 ]
            
#             # Get visible 2D points
#             pts_2d = []
#             pts_3d = []
#             for i, idx in enumerate(indices[:4]):
#                 px = get_landmark_px(lm, idx, w, h)
#                 if px is not None:
#                     pts_2d.append(px)
#                     pts_3d.append(foot_3d_points[i])
            
#             if len(pts_2d) >= 3:  # Need at least 3 points for SQPNP
#                 pts_2d = np.array(pts_2d, dtype=np.float32)
#                 pts_3d = np.array(pts_3d, dtype=np.float32)
                
#                 # Solve PnP
#                 success, rvec, tvec = cv2.solvePnP(
#                     pts_3d,
#                     pts_2d,
#                     cameraMatrix=np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]),
#                     distCoeffs=None,
#                     flags=cv2.SOLVEPNP_SQPNP
#                 )
                
#                 if success:
#                     # Create transformation matrix
#                     R, _ = cv2.Rodrigues(rvec)
#                     transform = np.eye(4)
#                     transform[:3, :3] = R
#                     transform[:3, 3] = tvec.flatten()
                    
#                     # Render shoe on a copy of the frame
#                     shoe_frame = render_on_frame(
#                         frame_bgr=output_frame.copy(),  # Important: work on a copy
#                         foot_transform_cv=transform,
#                         fx=fx, fy=fy, cx=cx, cy=cy,
#                         renderer_cache=renderer_cache
#                     )
                    
#                     # Blend the shoe frame with our output
#                     output_frame = cv2.addWeighted(output_frame, 0.7, shoe_frame, 0.3, 0)
                    
#                     # Debug points
#                     for pt in pts_2d:
#                         cv2.circle(output_frame, tuple(pt.astype(int)), 5, 
#                                   (0, 255, 0) if side == 'left' else (0, 0, 255), -1)
    
#     # Show the composite frame
#     cv2.imshow('3D Shoe Try-On', output_frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
# pose.close()