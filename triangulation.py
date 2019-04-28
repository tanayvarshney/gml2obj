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
    - mu : mu
    - s : semantics
    """
    with open(path) as fp:
        lines = fp.readlines()
    # then parse mu, throws headers away
    mu_line = lines[2]

    # then parse sematic information
    semantics = [int(x[2]) for x in lines[3:] if x[0] == '#']

    # then parse vertices and faces
    other_lines = [x for x in lines if x[0] != '#']
    # handling all vertices
    all_v = [x.split(' ')[1:] for x in other_lines if x[0] == 'v'] # all verices
    new_vs = []
    for v in all_v:
        v = [float(x.strip()) for x in v]
        new_vs.append(v)

    # handling all faces
    all_f = [x.split(' ')[1:] for x in other_lines if x[0] == 'f'] # all verices
    new_fs = []
    for f in all_f:
        f = [int(x.strip()) for x in f]
        new_fs.append(f)
    return mu_line, semantics, new_vs, new_fs


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


def project3t2(face3d):
    """
    project 3D points to 2D points
    :param face3d: a face with points in 3d coordinates. list of lists of 3D points.
           note we assume all faces are valid. Elsewhile they should be removed in previous steps
    :return:
    """
    # -- Compute the normal of the polygon for detecting vertical polygons and
    # -- for the correct orientation of the new triangulated faces
    # -- If the polygon is vertical, i.e. parallel to the z axis
    try:
       normal = polygon3dmodule.unit_normal(face3d[0], face3d[1], face3d[2])
    except Exception as e:
        print(e)
        return None
    if math.fabs(normal[2]) < 10e-2:
        vertical = True
    else:
        vertical = False

    # -- We want to project the vertical polygon to the XZ plane
    # -- If a polygon is parallel with the YZ plane that will not be possible
    # -- Handles the special case of YZ
    npolypoints = len(face3d)
    YZ = True
    # if parallel with YZ, then all X values are the same
    for i in range(1, npolypoints):
        if face3d[i][0] != face3d[0][0]:
            YZ = False
            break

    # -- Projection code starts
    face2d = copy.deepcopy(face3d)   # easier to modify
    if YZ:  # special case 1
        for i in range(0, npolypoints):
            # the polygon is in YZ plane. We just shift it to the XZ plane by changing coordinates
            face2d[i][0] = face3d[i][1]
            face2d[i][1] = face3d[i][2]
    # -- Project the plane
    elif vertical:
        for i in range(0, npolypoints):
            face2d[i][1] = face3d[i][2]
    else:
        pass  # -- No changes here

    #-- Drop the last coordinate
    for p in face2d:
        p.pop(-1)

    if has_duplicates(face2d):
        print("We have duplicated points after projecting to 2D!!! Check why.")
        return None
    return face2d


def make_segments(n_points):
    """
    make segmenets according to number of points. just connect every points to its adjancent points
    :param n_points: number of points, int
    :return: list of pairs
    """
    a = list(range(n_points))
    b = a[1:] + [a[0]]
    return list(zip(a, b))


def my_triangulation(face2d, segments):
    """
    Triangulate the polygon with the exterior and interior list of points. Works only for convex polygons.
    Assumes planarity. Projects to a 2D plane and goes back to 3D.
    :param face2d: the 2D face vertices. list of list
    :param segments: line segments
    :return:
    """
    # -- Prepare the polygon to be triangulated
    poly = {'vertices': np.array(face2d), 'segments': np.array(segments)}
    np.set_printoptions(threshold=sys.maxsize)
    # -- Triangulate
    t = triangle.triangulate(poly, "p")
    # add error checking code here!!
    return t


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


def write_tri_obj(out_path, header, mu_line, v, f):
    """
    Output Python objects of information to a obj file for each building
    @ param header: header file. containing creation date and building id
    @ param mu_line: a line containing mu information. did not parse this line from poly obj so use directly
    @ param v: vertices
    @ param f: faces
    """
    with open(out_path, "w+") as obj_file:
        obj_file.write(header[0])
        obj_file.write(header[1])
        obj_file.write(mu_line)
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


def write_poly_obj(out_path, header, mu, s, v, f):
    """
    Output Python objects of information to a obj file for each building
    @ param header: header file. containing creation date and building id
    @ param mu: mean of x and y
    @ param v: vertices
    @ param f: faces
    """
    with open(out_path, "w") as obj_file:
        obj_file.write(header)
        obj_file.write("# mean {0} {1}\n".format(mu[0], mu[1]))
        for semantic in s:
            obj_file.write("# %s\n" % semantic)
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


def has_duplicates(L):
    """
    check if a list contains duplicates
    :param L: the list
    :return: True if has duplicates, or else False
    """
    found = []
    for item in enumerate(L):
        if item not in found:
            found.append(item)
    if len(found) == len(L):
        return False
    else:
        return True


def dedup(seq):
    #https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def validate_faces(faces):
    """
    check if faces containing invalid faces and make amendaments
    :param f_list: list of list of lists. each sublist is a face. list of vertex indices
    :return: True if all faces are planar and valid. assumes no duplicates as this has been checked before
    """
    ### !!! Note f_list here is passed by value so must reassign it after the function
    for i, f in enumerate(faces):
        if len(f) < 3:
            print("Fewer than three points. Invalid face!!!")
            return False
        elif not all(len(x) == 3 for x in f):
            print("Some vertices are not 3D. Invalid face!!!")
            return False
        elif not polygon3dmodule.isPolyPlanar(f):
            print("Polygon not planar! Invalid face!!!")
            return False
    return True


def log_error(error_log, f):
    """
    log error to a file
    :param error_log: path to error log. ends with ".txt"
    :param f: obj file name
    :return:
    """
    with open(error_log, "a+") as e:
        e.write(f)
    return


def read_obj(path, error_log, duplicate_log, f):
    """
    read an obj and check validity. if invalid, return None
    :param path: input path of obj
    :param error_log: path to error log. str ends with ".txt"
    :param duplicate_log: path to log file containing all mesh with duplicated points
    :param f: file name to be written to the error_log and dupilcate_log
    :return: None if mesh too wrong. Otherwise vertice_list and f_list
    """

    mu_line, semantics, v_list, f_list = parse_obj(path)

    # check if vertice list and face list have duplicates
    if has_duplicates(v_list):
        print("Has duplicated vertices! Will log down.")
        with open(duplicate_log, "a+") as d:
            d.write(f)
        return None
    if has_duplicates(f_list):
        print("Has duplicated faces! Will log down.")
        with open(duplicate_log, "a+") as d:
            d.write(f)
        return None

    # check if any of the (unique) faces has duplicated vertices
    for i, face_with_id in enumerate(f_list):
        # f is a list of integers so we do it faster!
        if has_duplicates(face_with_id):
            print("Has duplicated vertices in at least one faces! Will clean and rewrite.")
            with open(duplicate_log, "a+") as d:
                d.write(f)
            return None

    face_with_points_3d = concrete_faces(v_list, f_list)
    if not validate_faces(face_with_points_3d):
        # not all faces are planar or have more than 3 points
        log_error(error_log, f)
        return None

    return mu_line, v_list, f_list, face_with_points_3d


def main():
    args = cmdline_args()
    DIRECTORY = args.in_dir
    RESULT = args.out_dir
    files = os.listdir(DIRECTORY)

    error_log = os.path.join(RESULT, "error.txt")
    try:
        os.remove(error_log)
    except OSError:
        pass
        
    duplicate_log = os.path.join(RESULT, "dup.txt")   # obj files with duplicated faces
    try:
        os.remove(duplicate_log)
    except OSError:
        pass
    
    counter = 0
    start = timer()
    for f in files:   # object level for loop
        # binvox files
        if f.split(".")[1] != "obj":
            continue

        if counter % 1000 == 0:
            end = timer()
            print("Processed: {0}-th file. Time elapsed: {1} s.".format(counter, timedelta(seconds=end-start)))

        path = os.path.join(DIRECTORY, f)
        out_path = os.path.join(RESULT, f)

        res = read_obj(path, error_log, duplicate_log, f)
        if not res:
            # file read has error!
            print("File has error: {0}\tSkipping...".format(f))
            continue
        else:
            # file successfully read!
            mu_line, v_list, f_list, face_with_points_3d = res

        success = True   # a flag to check if triangulation is successful. if not , early stop

        tris_global_list = []  # all triangle face lists
        for i, face3d in enumerate(face_with_points_3d):  # face level for loop
            # print("Now handling face {0}".format(i))
            # print(len(face3d))
            # print("Now print all points!!!")
            # for v in face3d:
            #     print(v)
            face2d = project3t2(face3d)  # 2d faces from polygon
            segments = make_segments(len(face2d))
            # print("segments")
            # print(segments)
            t = my_triangulation(face2d, segments)
            try:
                tris = t['triangles']
                vert2d = t['vertices'].tolist()
            except Exception as e:
                print(e)
                success = False
                break

            # transform back to 3D
            vert3d = []
            for v in vert2d:   # vertex level for loop
                try:
                    idx = face2d.index(v)  # index of this point in the original 2D face
                    vert3d.append(face3d[idx])  # map this point to 3d as indices are the same for 3d and 2d face
                except Exception as e:
                    # most likely found new vertices not in the original list
                    # usually from self-intersecting polygons
                    print(e)
                    success = False
                    break

            if not success:
                break   # early exit face level for loop

            # now map the triangle into 3D points !
            tris_with_points_3d = []   # not really necessary, just for clarification
            for tri in tris:
                tri_with_points_3d = [vert3d[x] for x in tri]   # replace index with 3D points
                tris_with_points_3d.append(tri_with_points_3d)   # add this triangle to the list of triangleSS

            # add all triangles in this face to the global list
            tris_global_list.extend(tris_with_points_3d)

        # exit face level for loop
        if not success:   # early exit object level for loop
            log_error(error_log, f)
            continue
        else:
            # print(tris_global_list[0])
            new_tri_list = coor2idx(tris_global_list, v_list)
            header = "# " + f.split(".")[0] + "\n# created on " + datetime.datetime.today().strftime('%Y-%m-%d') + "\n"
            write_tri_obj(out_path, header, mu_line, v_list, new_tri_list)

        counter += 1
    return


if __name__ == "__main__":
    main()
