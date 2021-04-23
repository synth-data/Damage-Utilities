import bpy
import mathutils
import random
import sys, os, importlib
if 'damageutils' in sys.modules: importlib.reload(sys.modules['damageutils'])
extra_path = os.environ["BLENDER_UTILITIES"]
if extra_path not in sys.path: sys.path.append(extra_path)
import damageutils

OBJECT = bpy.ops.object
MESH = bpy.ops.mesh
TRANS = bpy.ops.transform

def create(pipelength, seed_in: int, bend: bool):
    # Deformation
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    ob = bpy.context.active_object
    damageutils.noise_deform(ob, mathutils.Vector((seed_in, seed_in, seed_in)), 0.5, 0.25)
    if bend:
        damageutils.bend(ob, 0.2, pipelength)

    #Performance Optimization
    OBJECT.editmode_toggle()
    MESH.dissolve_limited(angle_limit=0.0523599, delimit={'NORMAL'})
    MESH.face_make_planar()
    MESH.fill_holes()
    OBJECT.editmode_toggle()
    
    #Rendering stuff
    mat = bpy.data.materials.get("Deterioration")
    ob.data.materials.append(mat)
    OBJECT.light_add(type='POINT', radius=1, location=(0, 1, .25))
    bpy.context.object.data.energy = 20
    OBJECT.camera_add(enter_editmode=False, align='CURSOR', location=(.33, -pipelength/2, .388), rotation=(1.62, 0, 0.087))
    bpy.context.object.data.lens = 20
    bpy.context.scene.camera = bpy.data.objects["Camera"]
    
    #Blue Ball
    ball_x = random.uniform(-.6, .6)
    ball_y = random.uniform(-.6, .6)
    ball_z = random.uniform(-.6, -.2)
    MESH.primitive_uv_sphere_add(segments=32, ring_count=32, radius=.3, enter_editmode=False, location=(ball_x, ball_y, ball_z))
    mat2 = bpy.data.materials.get("Ball")
    ob = bpy.context.active_object
    ob.data.materials.append(mat2)
    OBJECT.shade_smooth()

for render_id in range(1, 2):
    seed = random.randint(0, 10000)
    random.seed(seed)
    damageutils.clean()
    damageutils.create_divided_pipe(8, 64, 64)
    create(8, seed, True)
    damageutils.set_resolution(512, 512)
    bpy.context.scene.render.filepath = os.path.dirname(os.getcwd()) + "/batch/" + str(render_id) + ".png"
    #bpy.ops.render.render(write_still = True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.join()
    #damageutils.write_csv(bpy.data.objects.get('Cylinder'), '../mesh_data/%s.csv' % render_id)
    print("Completed full execution %d" % render_id)
