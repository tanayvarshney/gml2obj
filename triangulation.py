#!/usr/bin/env python
### a program to triangularize convex polygon mesh into triangular meshes
import polygon3dmodule
import markup3dmodule
from lxml import etree
import os
import argparse
import glob
import numpy as np
import itertools
import datetime
import sys
import copy
import math
import triangle
from main import face_to_idx
from timeit import default_timer as timer
from datetime import timedelta


def parse_obj(path):
    """
    a function to read and parse obj files
    @ param path: absolute path to obj file
    rvalue:
    - all_v : list of lists, all vertice coordinates
    - all_f: list of lists, all faces. each face consists of vertice ID
    """
    with open(path) as fp:
        lines = fp.readlines()
    lines = [x for x in lines if x[0] != '#']
    # handling all vertices
    all_v = [x.split(' ')[1:] for x in lines if x[0] == 'v'] # all verices
    new_vs = []
    for v in all_v:
        v = [float(x.strip()) for x in v]
        new_vs.append(v)

    # handling all faces
    all_f = [x.split(' ')[1:] for x in lines if x[0] == 'f'] # all verices
    new_fs = []
    for f in all_f:
        f = [int(x.strip()) for x in f]
        new_fs.append(f)
    return new_vs, new_fs


def concrete_faces(v_list, f_list):
    """
    translate face indices to concrete 3D points!!
    :param v_list: a list of vertex coordinates. list of list
    :param f_list: a list of faces each consits of indices. list of list
    :return: a list of faces. list of list of lists. the innermost lists are point coordinates
    """
    faces = []
    for f in f_list:
        ff = [v_list[i-1] for i in f]  # for every index find the point!!!
        faces.append(ff)
    return faces


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=
        """
        Use the command line argument parser in Python.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    p.add_argument("-i", "--in_dir",
                   help="input directory of all polygon mesh files ")
    p.add_argument("-o", "--out_dir",
                   help="output directory of all triangular mesh files ")
    return(p.parse_args())


def find_match(v_list, p):
    """
    During triangulation there is a step we convert 3D points to 2D then convert it back, resulting in numerical errors
    This function compares the calculated point p in the original vertices and match it with closet neighbors
    :param v_list: a list of original vertices
    :param p: point of concern
    :return: matched data point
    """
    eps = 1e-3   # error margin
    for v in v_list:
        distance = np.sqrt((v[0]-p[0])**2 + (v[1]-p[1])**2 + (v[2]-p[2])**2)
        if distance < eps:
            return v
    raise Exception("Calculated point not found in original set!")


def my_triangulation(e):
    """Triangulate the polygon with the exterior and interior list of points. Works only for convex polygons.
    Assumes planarity. Projects to a 2D plane and goes back to 3D."""
    vertices = []
    segments = []
    index_point = 0
    # -- Slope computation points
    a = [[], [], []]
    b = [[], [], []]
    for ip in range(len(e)):
        vertices.append(e[ip])
        if a == [[], [], []] and index_point == 0:
            a = [e[ip][0], e[ip][1], e[ip][2]]
        if index_point > 0 and (e[ip] != e[ip - 1]):
            if b == [[], [], []]:
                b = [e[ip][0], e[ip][1], e[ip][2]]
        if ip == len(e) - 1:
            segments.append([index_point, 0])  # create segments
        else:
            segments.append([index_point, index_point + 1])
        index_point += 1
    # print("Slope code finished!")
    # print(vertices)
    # print(segments)
    # print("Slope results printed!")

    # -- Project to 2D since the triangulation cannot be done in 3D with the library that is used
    npolypoints = len(vertices)
    # -- Check if the polygon is vertical, i.e. a projection cannot be made.
    # -- First copy the list so the originals are not modified
    temppolypoints = copy.deepcopy(vertices)
    newpolypoints = copy.deepcopy(vertices)
    # -- Compute the normal of the polygon for detecting vertical polygons and
    # -- for the correct orientation of the new triangulated faces
    # -- If the polygon is vertical, i.e. parallel to the z axis
    try:
       normal = polygon3dmodule.unit_normal(temppolypoints[0], temppolypoints[1], temppolypoints[2])
    except Exception as e:
        print(e)
        return None

    if math.fabs(normal[2]) < 10e-2:
        vertical = True
    else:
        vertical = False
    # -- We want to project the vertical polygon to the XZ plane
    # -- If a polygon is parallel with the YZ plane that will not be possible
    YZ = True
    for i in range(1, npolypoints):
        if temppolypoints[i][0] != temppolypoints[0][0]:
            YZ = False
            continue
    # -- Project the plane in the special case
    if YZ:
        for i in range(0, npolypoints):
            # the polygon is in YZ plane. We just shift it to the XZ plane by changing coordinates
            newpolypoints[i][0] = temppolypoints[i][1]
            newpolypoints[i][1] = temppolypoints[i][2]
    # -- Project the plane
    elif vertical:
        for i in range(0, npolypoints):
            newpolypoints[i][1] = temppolypoints[i][2]
    else:
        pass  # -- No changes here

    #-- Drop the last point (identical to first)
    for p in newpolypoints:
        p.pop(-1)

    if len(newpolypoints) != len(unique_items(newpolypoints)):
        print("We have duplicated points!!! Check why.")
        return None
    # -- Plane information (assumes planarity)
    a = e[0]
    b = e[1]
    c = e[2]
    # -- Construct the plane
    pl = polygon3dmodule.plane(a, b, c)

    # -- Prepare the polygon to be triangulated
    # poly = {'vertices': np.array(newpolypoints), 'segments': np.array(segments), 'holes': np.array(newholes)}
    poly = {'vertices': np.array(newpolypoints), 'segments': np.array(segments)}
    np.set_printoptions(threshold=sys.maxsize)
    # print(poly)
    # -- Triangulate
    # print("poly vertices")
    # print(poly['vertices'])
    # print("poly segments")
    # print(poly['segments'])
    t = triangle.triangulate(poly, "p")
    # print("t")
    # print(t)
    try:
        tris = t['triangles']
    except:
        return None
    # print("tris")
    # print(tris)
    try:
        vert = t['vertices'].tolist()
    except:
        return None
    # print("vert")
    # print(vert)
    # print(tris)
    # -- Store the vertices of each triangle in a list
    tri_points = []  # store all the traingles. a list of list of list
    for tri in tris:
        # print("now print tri")
        # print(tri)
        tri_points_tmp = []   # a single triangle. list of lists
        for v in tri.tolist():
            try:
                vert_adj = [0] * 3   # initialize a vertex!
                if YZ:
                    vert_adj[0] = temppolypoints[0][0]
                    vert_adj[1] = vert[v][0]
                    vert_adj[2] = vert[v][1]
                elif vertical:
                    vert_adj[0] = vert[v][0]
                    vert_adj[2] = vert[v][1]
                    vert_adj[1] = polygon3dmodule.get_y(pl, vert_adj[0], vert_adj[2])
                else:
                    vert_adj[0] = vert[v][0]
                    vert_adj[1] = vert[v][1]
                    vert_adj[2] = polygon3dmodule.get_height(pl, vert_adj[0], vert_adj[1])
            except Exception as e:
                print(e)
                return None
            try:
                # print("now print vert adj")
                # print(vert_adj)
                match_vert = find_match(vertices, vert_adj)
            except Exception:
                print("Calculated point not found!!")
                return None
            tri_points_tmp.append(match_vert)
        try:
            tri_normal = polygon3dmodule.unit_normal(tri_points_tmp[0], tri_points_tmp[1], tri_points_tmp[2])
        except:
            print("Triangle normal incorrect!!\n")
            return None
        if polygon3dmodule.compare_normals(normal, tri_normal):
            tri_points.append(tri_points_tmp)
        else:
            tri_points_tmp = polygon3dmodule.reverse_vertices(tri_points_tmp)
            tri_points.append(tri_points_tmp)
    return tri_points


def coor2idx(face_list, vertice_list):
    """
    change coordinates in faces to index in vertice lists
    :param face_list: a list of list of list. all the triangles on a building surface
    :param vertice_list: all the vertice list
    :return: new_face_list, still all the triangles but every point is represented as an index
    """
    new_face_list = []
    for f in face_list:
       new_face_list.append(face_to_idx(f, vertice_list))
    return new_face_list


def write_obj(out_path, header, v, f):
    """
    Output Python objects of information to a obj file for each building
    @ param header: header file. containing creation date and building id
    @ param mu: mean of x and y
    @ param v: vertices
    @ param f: faces
    """
    with open(out_path, "w") as obj_file:
        obj_file.write(header)
        obj_file.write("\n")
        for point in v:
            line = "v {0} {1} {2}\n".format(point[0], point[1], point[2])
            obj_file.write(line)
        for face in f:
            line = "f"  # current line to write
            for point in face:
                # loop through every vertice of this face and writes to line
                line += " " + str(point + 1)  # vertex id starts from 1
            obj_file.write("%s\n" % line)
    return


def unique_items(L):
    found = []
    for item in L:
        if item not in found:
            found.append(item)
    return found


def main():
    args = cmdline_args()
    DIRECTORY = args.in_dir
    RESULT = args.out_dir
    files = os.listdir(DIRECTORY)

    error_log = os.path.join(RESULT, "error.txt")
    duplicates_log = os.path.join(RESULT, "dup.txt")   # obj files with duplicated faces
    # f = "/media/yuqiong/DATA/city/zurich/UUID_00024863-0e11-4178-9e6b-83d00e0bd57e.obj"
    counter = 0
    start = timer()
    for f in files:
        # print(f)
        if f.split(".")[1] != "obj":
            continue
        if counter % 1000 == 0:
            end = timer()
            print("Processed: {0}-th file. Time elapsed: {1} s.".format(counter, timedelta(seconds=end-start)))
        success = True   # a flag to check if triangulation is successful
        path = os.path.join(DIRECTORY, f)
        out_path = os.path.join(RESULT, f)

        v_list, f_list = parse_obj(path)
        unique_v = unique_items(v_list)
        unique_f = unique_items(f_list)

        if len(v_list) != len(unique_v) or len(f_list) != len(unique_f):
            if len(v_list) != len(unique_v):
                print("Has duplicated vertices!")
            else:
                print("Has duplicated faces!")
            with open(duplicates_log, "w+") as d:
                d.write(f)


        # a search dictionary for vertices
        face_with_points = concrete_faces(unique_v, unique_f)

        tri_f_list = []  # triangle face lists
        for i, face in enumerate(face_with_points):
            # print(face)
            tris = my_triangulation(face)
            # print(tris)
            if tris:  # triangulation is successful
                tri_f_list.extend(tris)   # tri_f_list and tris both list of list of lists
            else:
                print("Triangulation failure! " + f)
                success = False
                break
        if success:
            new_tri_list = coor2idx(tri_f_list, unique_v)
            write_obj(out_path, f, unique_v, new_tri_list)
        else:
            with open(error_log, "w+") as e:
                e.write(f)
        counter += 1
    return


if __name__ == "__main__":
    main()
