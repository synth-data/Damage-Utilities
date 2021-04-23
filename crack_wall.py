# context.area: VIEW_3D
import bpy
import random
import sys, os, importlib
if 'damageutils' in sys.modules: importlib.reload(sys.modules['damageutils'])
extra_path = os.environ["BLENDER_UTILITIES"]
if extra_path not in sys.path: sys.path.append(extra_path)
import damageutils

def create(seed_in: int, project=True):
    ob = bpy.context.active_object
    bm = damageutils.initialize_bmesh(ob.data) # creates a BMesh object (enables BVHTree and neighbor algo)
    vcount = len(ob.data.vertices) - 200 # limit for sampling random vertices

    used = damageutils.voronoi_crack(bm.verts[random.randint(0, vcount)], set([]), -0.15, 2, seed_in, 3000, use_x=False, use_y=True, use_z=False, project=False)

    bm.to_mesh(ob.data) # Writes changed data to mesh -- if this isn't called nothing is saved

    # Scene setup
    mat = bpy.data.materials.get("Concrete") # Choices -- Concrete, Deterioration, Bricks
    ob.data.materials.append(mat)
    bpy.ops.object.light_add(type='SUN', radius=1, location=(-4, 4, 4), rotation=(-1, 0, 0.7))
    bpy.context.object.data.energy = 5
    bpy.ops.object.camera_add(enter_editmode=False, align='CURSOR', location=(0, 4.88, 0), rotation=(1.57, 0, 3.14))
    bpy.context.object.data.lens = 23
    bpy.context.scene.camera = bpy.data.objects["Camera"]

    if project: # projects the crack onto a 2d plane -- requires post-processing to be useful
        used_final = []
        [used_final.append(bmv) for bmv in used if bmv not in used_final]
        for v in used_final:
            v.co.y += 0.15
        damageutils.project_crack(bpy.data.objects['Camera'], used_final, '../batch_output/' + str(render_id) + '.csv')

for render_id in range(1, 2):
    damageutils.set_resolution(128, 128)
    seed = random.randint(0, 10000)
    random.seed(seed)
    damageutils.clean()
    damageutils.plane(8, 7)
    create(seed)
    #damageutils.write_csv(bpy.data.objects.get('Cylinder'), '../mesh_data/%s.csv' % render_id)
    bpy.context.scene.render.filepath = os.path.dirname(os.getcwd()) + "/batch/" + str(render_id) + ".png"
    bpy.ops.render.render(write_still=True)
    print("Completed full execution %d" % render_id)
