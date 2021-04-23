# context.area: VIEW_3D
import bpy
import bmesh
import mathutils
import random
import sys, os, importlib
if 'damageutils' in sys.modules: importlib.reload(sys.modules['damageutils'])
extra_path = os.environ["BLENDER_UTILITIES"]
if extra_path not in sys.path: sys.path.append(extra_path)
import damageutils

#Constants
OBJECT = bpy.ops.object
MESH = bpy.ops.mesh
TRANS = bpy.ops.transform
TREE = mathutils.bvhtree.BVHTree

def liquid():
    bpy.ops.mesh.primitive_cube_add(size=8, enter_editmode=False, location=(0, 0, -1))
    bpy.ops.transform.resize(value=(-0.25, 1, -0.1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    mat = bpy.data.materials.get("Chocolate")
    ob = bpy.context.active_object
    ob.data.materials.append(mat)

def create(deform, buffer, R, project, seed_in):
    ob = bpy.context.active_object
    bm = damageutils.initialize_bmesh(ob.data) # creates a BMesh object (enables BVHTree and neighbor algo)
    vcount = len(ob.data.vertices) - 200 # limit for sampling random vertices
    used = set([])
    
    used = damageutils.voronoi_crack(bm.verts[random.randint(0, vcount)], used, deform, buffer, seed_in, 10000) # Actual start of the program - initial crack
    used = damageutils.voronoi_crack(bm.verts[random.randint(0, vcount)], used, deform, buffer, seed_in - 1000, 10000)
    used = damageutils.voronoi_crack(bm.verts[random.randint(0, vcount)], used, deform, buffer, seed_in + 1000, 10000)

    bm.to_mesh(ob.data) # Writes changed data to mesh -- if this isn't called nothing is saved
    bpy.ops.object.camera_add(enter_editmode=False, align='CURSOR', location=(0, 4.55, 0), rotation=(-1.57, 3.14, 0))
    bpy.context.object.data.lens = 20
    bpy.context.scene.camera = bpy.data.objects["Camera"]
    if project: # projects the crack onto a 2d plane -- requires post-processing to be useful
        used_final = []
        [used_final.append(bmv) for bmv in used if bmv not in used_final]
        for v in used_final:
            vnorm = vert2unit(v)
            v.co.x -= deform * vnorm.dot(i) # undoing the deformation function to improve mask quality
            v.co.z -= deform * vnorm.dot(k)
        damageutils.project_crack(bpy.data.objects['Camera'], used_final, '../batch_output/' + str(render_id) + '.csv')
    bm.free() # free the bmesh from memory
    mat = bpy.data.materials.get("Concrete") # Choices -- Concrete, Deterioration
    ob.data.materials.append(mat)
    bpy.data.materials.get("Concrete").node_tree.nodes["Noise Texture.002"].inputs[1].default_value = random.randint(0, 100) + random.random()
    bpy.data.materials.get("Concrete").node_tree.nodes["Musgrave Texture.002"].inputs[1].default_value = random.randint(0, 100) + random.random()
    bpy.data.materials.get("Concrete").node_tree.nodes["Musgrave Texture.001"].inputs[1].default_value = random.randint(0, 100) + random.random()
    bpy.ops.object.light_add(type='POINT', radius=1, location=(0, 1, 0))
    bpy.context.object.data.energy = 40

for render_id in range(1, 2):
    seed = random.randint(0, 10000)
    random.seed(seed)
    damageutils.clean()
    damageutils.create_divided_pipe(8, 512, 512) #length, subdivisions, vertices
    create(.1, 3.95, render_id, True, seed)
    #damageutils.write_csv(bpy.data.objects.get('Cylinder'), '../mesh_data/%s.csv' % render_id)
    liquid()
    damageutils.set_resolution(512, 512)
    bpy.context.scene.render.filepath = os.path.dirname(os.getcwd()) + "/batch/" + str(render_id) + ".png"
    #bpy.ops.render.render(write_still=True)
    print("Completed full execution %d" % render_id)
