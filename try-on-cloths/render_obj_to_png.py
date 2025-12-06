import trimesh
import pyrender
from PIL import Image
import numpy as np

obj_path = "PureCadence_2_Color_HiRskRedNghtlfeSlvrBlckWht_Size_70/meshes/model.obj"
texture_path = "PureCadence_2_Color_HiRskRedNghtlfeSlvrBlckWht_Size_70/materials/textures/texture.png"
output_image = "shoe_render.png"


mesh = trimesh.load(obj_path, force='mesh')
scene = pyrender.Scene()

render_mesh = pyrender.Mesh.from_trimesh(mesh)
scene.add(render_mesh)


camera = pyrender.PerspectiveCamera(yfov=1.0)
scene.add(camera, pose=[[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0.5],
                        [0, 0, 0, 1]])

light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
scene.add(light, pose=[[1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, 1, 4],
                       [0, 0, 0, 1]])

r = pyrender.OffscreenRenderer(512, 512)
color, _ = r.render(scene)
r.delete()

# pyrender.Viewer(scene, use_raymond_lighting=True)

img = Image.fromarray(color)
img.save(output_image)
print(f"Saved rendered shoe to {output_image}")
