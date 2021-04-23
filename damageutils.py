import csv
import bpy
import bmesh
from bpy_extras.object_utils import world_to_camera_view
import mathutils
import random
import os

# Constants
i = mathutils.Vector((1, 0, 0))
j = mathutils.Vector((0, 1, 0))
k = mathutils.Vector((0, 0, 1))
OBJECT = bpy.ops.object
MESH = bpy.ops.mesh
TRANS = bpy.ops.transform
TREE = mathutils.bvhtree.BVHTree

def write_csv(ob, filepath):
    """ Writes vertex data to a CSV. Use with MATLAB to make pretty 3d graphs! """
    verts = [ob.matrix_world @ v.co for v in ob.data.vertices]
    csv_lines = [";".join([str(v) for v in co]) + "\n" for co in verts]
    f = open(filepath, 'w')
    f.writelines(csv_lines)
    f.close()

def get_neighbor_verts(vertex):
    """ Return the neighbor vertices of a vertex! """
    edges = vertex.link_edges[:]
    relevant_neighbour_verts = {v for e in edges for v in e.verts[:] if v != vertex}
    return relevant_neighbour_verts

def vert2unit(v):
    """ Converts a blender vertex into a blender math vector that's normalized. """
    return mathutils.Vector((v.co.x, v.co.y, v.co.z)).normalized()

def initialize_bmesh(dat):
    """ Create a new BMesh from the given data """
    newbm = bmesh.new()
    newbm.from_mesh(dat)
    newbm.verts.ensure_lookup_table() # lets us index into the data
    return newbm

def project_crack(camera, used, filepath: str):
    """ Project a set of points onto the plane of the rendered image """

    scene = bpy.context.scene
    render = scene.render
    coords_2d = [world_to_camera_view(scene, camera, coord.co) for coord in used]
    vertsx = []
    vertsy = []
    for x, y, distance_to_lens in coords_2d:
        vertsx.append(round(render.resolution_x*x))
        vertsy.append(round(render.resolution_y*y))
    f = open(filepath, 'w', newline='')
    with f:
        header = ['X', 'Y']
        writer = csv.DictWriter(f, fieldnames=header)
        for index in range(1, len(vertsx)):
            writer.writerow({'X': str(vertsx[index]), 'Y': str(vertsy[index])})
    f.close()

def set_resolution(x: int, y: int):
    bpy.context.scene.render.resolution_x = x
    bpy.context.scene.render.resolution_y = y

def clean():
    """ Delete all objects. Don't call this if you don't want all your objects to be deleted. """
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)

def deselect_all():
    """ Deselect every object. """
    for obj in bpy.data.objects:
        obj.select_set(False)

def optimize():
    """ Greatly reduces the number of vertices in the mesh. Does not work with sharp edges. """
    OBJECT.editmode_toggle()
    MESH.dissolve_limited(angle_limit=0.02)
    OBJECT.editmode_toggle()

def view3d_find(areas, return_area=False):
    """ Discovers a viewport manually for operations that require it (such as loopcutting) """
    for area in areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    if return_area: return region, rv3d, v3d, area
                    return region, rv3d, v3d
    return None, None

def create_divided_pipe(pipelength, subdivisions, verts):
    """ Creates a pipe that is thinly subdivided. My regards to the Blender Foundation for making it this complex. """
    MESH.primitive_cylinder_add(vertices=verts, radius=1, depth=pipelength, enter_editmode=False, location=(0, 0, 0))
    TRANS.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    OBJECT.editmode_toggle()
    #Subdiv work
    region, rv3d, v3d, area = view3d_find(bpy.context.window.screen.areas, True)
    override = {'scene'  : bpy.context.scene,'region' : region, 'area'   : area, 'space'  : v3d}
    MESH.loopcut_slide(override, 
        MESH_OT_loopcut={"number_cuts": subdivisions, "smoothness": 0, "falloff": 'SMOOTH', "object_index": 0, "edge_index": 2, "mesh_select_mode_init" : (True, False, False)},
        TRANSFORM_OT_edge_slide={"value": 0, "mirror": False, "snap": False,"snap_target": 'CLOSEST',"snap_point": (0, 0, 0),"snap_align": False,"snap_normal": (0, 0, 0),"correct_uv": False,"release_confirm": False})    
    
    # Delete front and back of the cylinder
    deselect_all()
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    MESH.select_face_by_sides(number=8, type='GREATER')
    MESH.delete(type='FACE')
    # Invert Normals
    deselect_all()
    MESH.select_face_by_sides(number=4, type='EQUAL')
    MESH.flip_normals()
    OBJECT.editmode_toggle()
    OBJECT.shade_smooth()
    OBJECT.transform_apply(location=True, rotation=True, scale=True)

def plane(size: int, subdivisions: int):
    """ Creates a plane rotated vertically """
    MESH.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=(0, 0, 0), rotation=(1.5708, 0, 0))
    OBJECT.editmode_toggle()
    for number in range(0, subdivisions + 1):
        MESH.subdivide()
    OBJECT.editmode_toggle()
    OBJECT.shade_smooth()
    OBJECT.transform_apply(location=True, rotation=True, scale=True)

def voronoi_crack(vertex, used: set, deform: float, max_y: float, seed_in: int, size: int, use_x: bool = True, use_y: bool = False, use_z: bool = True, project: bool = True) -> set:
    """ Generates a crack following a noise pattern. Used is a set containing vertices that should not be deformed """
    offset_vector = mathutils.Vector((seed_in, seed_in, seed_in))
    for iteration in range(0, size): # Deform an arbitrary amount of vertices
        neighbor_verts = get_neighbor_verts(vertex) # gets neighbor vertices
        neighbors = list(neighbor_verts)
        if random.randint(0, 5) != 0: # Follows the 'path of least resistance'
            neighbor_distances = [mathutils.noise.multi_fractal(0.2 * n.co + offset_vector, 1.0, 5, 2, noise_basis="VORONOI_CRACKLE") if n not in used else 100 for n in neighbors]
            vertex = neighbors[neighbor_distances.index(min(neighbor_distances))]
        else: # Chance to pick a vertex randomly instead of following the algorithm
            vertex = neighbors[random.randint(0, len(neighbors)-1)]
        v_normalized = vert2unit(vertex) if project else mathutils.Vector((1, 1, 1))
        if vertex not in used: # deforms, as long as it hasn't been deformed before
            if use_x:
                vertex.co.x += deform * v_normalized.dot(i) # projects the deformation a static value away from the cylinder
            if use_y:
                vertex.co.y += deform * v_normalized.dot(j)
            if use_z:
                vertex.co.z += deform * v_normalized.dot(k)
            used.add(vertex)
        if abs(vertex.co.y) > max_y:
            return used # Break if we reach the edge
    return used

def bend(ob, amount: float, pipelength: int):
    """ Bends an object in the Z direction in a roughly quadratic shape """
    for vertex in ob.data.vertices:
        vertex.co.z = vertex.co.z + vertex.co.y**2 * amount / (pipelength / 2)

def noise_deform(ob, offset, limit, factor):
    """ Deforms an entire object based on a 3D noise function """
    for vertex in ob.data.vertices:
        noise_value = mathutils.noise.multi_fractal(vertex.co + offset, 1.0, 5.0, 2, noise_basis="BLENDER")
        diff = vertex.co.length # based on the distance from the center of the object, we will deform less
        if diff < limit:
            diff = limit
        vertex.co.x = vertex.co.x + noise_value*factor/diff # in your own implementation, you can deform Y as well if you wish
        vertex.co.z = vertex.co.z + noise_value*factor/diff
