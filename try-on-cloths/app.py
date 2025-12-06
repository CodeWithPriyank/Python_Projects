# from ultralytics import YOLO
# import cv2

# # Load YOLOv8-pose model
# model = YOLO("yolov8n-pose.pt")  # Use yolov8m or l for higher accuracy

# # Open webcam
# file = '3.mp4'
# cap = cv2.VideoCapture(file)

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     # Predict
#     results = model.predict(frame, conf=0.5)

#     # Get keypoints
#     keypoints_list = results[0].keypoints  # keypoints for all detected persons

#     frame = results[0].plot()

#     if keypoints_list is not None:
#         for person_id, keypoints in enumerate(keypoints_list.xy):
#             print(f"\n🧍 Person {person_id + 1}")
#             for idx, (x, y) in enumerate(keypoints):
#                 print(f"Keypoint {idx}: ({int(x)}, {int(y)})")

#     # Show the annotated frame
#     cv2.imshow("YOLOv8 Full Body Keypoints", frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# cap.release()
# cv2.destroyAllWindows()





# app.py
import numpy as np
import trimesh
import pyrender

# ----- load mesh once -----
MESH_PATH = "PureCadence_2_Color_HiRskRedNghtlfeSlvrBlckWht_Size_70/meshes/model.obj"
shoe_trimesh = trimesh.load(MESH_PATH, force='mesh')

# Optional scale (mm->m)
# shoe_trimesh.apply_scale(0.001)

shoe_mesh = pyrender.Mesh.from_trimesh(shoe_trimesh, smooth=False)
light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)

def make_base_scene(fx, fy, cx, cy):
    scene = pyrender.Scene(ambient_light=[0.2,0.2,0.2])
    cam = pyrender.IntrinsicsCamera(fx, fy, cx, cy)
    cam_node = scene.add(cam, pose=np.eye(4))
    light_node = scene.add(light, pose=np.array([[1,0,0,0],
                                                 [0,1,0,0],
                                                 [0,0,1,4],
                                                 [0,0,0,1]], dtype=np.float32))
    shoe_node = scene.add(shoe_mesh, pose=np.eye(4))
    return scene, shoe_node

def alpha_composite(background_bgr, render_rgba):
    rgb = render_rgba[..., :3]
    a   = render_rgba[..., 3:4] / 255.0
    rgb_bgr = rgb[..., ::-1]
    out = background_bgr.astype(np.float32) * (1 - a) + rgb_bgr.astype(np.float32) * a
    return out.astype(np.uint8)

# OpenCV -> GL transform
T_CV2GL = np.array([[1,0, 0,0],
                    [0,-1,0,0],
                    [0,0,-1,0],
                    [0,0, 0,1]], dtype=np.float32)

def render_on_frame(frame_bgr, foot_transform_cv, fx, fy, cx, cy, renderer_cache={}):
    H, W = frame_bgr.shape[:2]
    key = (W, H, fx, fy, cx, cy)
    if key not in renderer_cache:
        scene, shoe_node = make_base_scene(fx, fy, cx, cy)
        renderer = pyrender.OffscreenRenderer(viewport_width=W, viewport_height=H)
        renderer_cache[key] = (scene, shoe_node, renderer)
    else:
        scene, shoe_node, renderer = renderer_cache[key]

    pose_gl = T_CV2GL @ foot_transform_cv
    scene.set_pose(shoe_node, pose=pose_gl)

    color_rgba, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
    return alpha_composite(frame_bgr, color_rgba)
