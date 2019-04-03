import markup3dmodule
import polygon3dmodule
from lxml import etree
import os
import argparse
import glob
import numpy as np
import itertools
import datetime
import sys


def remove_reccuring(list_vertices):
    """Removes recurring vertices, which messes up the triangulation.
    Inspired by http://stackoverflow.com/a/1143432"""
    # last_point = list_vertices[-1]
    list_vertices_without_last = list_vertices[:-1]
    found = set()
    for item in list_vertices_without_last:
        if str(item) not in found:
            yield item
            found.add(str(item))

def deduplicate_list_of_list(k):
    """
    deduplicate a list of list. Used to remove recurrent vertices
    credit to https://stackoverflow.com/questions/2213923/removing-duplicates-from-a-list-of-lists
    """
    k.sort()
    return list(k for k,_ in itertools.groupby(k))

def extract_polys(polys, label, vertices_all, faces_all):
    """
    extract polygons and their semantic information from GML and output to dictionaries
    @ param polys: list of Element. Returned by markup3dmodule.polygonFinder() function.
    @ param label: which label should we give to the polygon? e.g. "All", "WallSurface", etc
    @ param vertices_all: place to store vertices
    @ paramfaces_all : place to store faces
    """
    for poly in polys:
        #-- Decompose the polygon into exterior and interior
        e, i = markup3dmodule.polydecomposer(poly)

        #-- Points forming the exterior LinearRing
        epoints = markup3dmodule.GMLpoints(e[0])

        #-- Clean recurring points, including the last one
        # last_ep = epoints[-1]
        epoints_clean = list(remove_reccuring(epoints))
        # epoints_clean.append(last_ep)

        #-- Check the exterior polygon
        # valid = polygon3dmodule.isPolyValid(epoints_clean, True)
        valid = True
        if valid:
            vertices_all.extend(epoints_clean)  # do not add the final points to obj
            faces_all[label].append(epoints_clean)
        else:
            pass

    return vertices_all, faces_all

def face_to_idx(face, vertices_list):
    """
    input a single face : list of list, and a vertices dictionary
    map every vertice to its index in the vertices dictionary
    return a face : list of list
    """
    new_face = []
    for point in face:
        new_face.append(vertices_list.index(point))
    return new_face

def vertices_demean(vertices_list):
    """
    input a vertice list, demean on x and y axis
    return
    - a 2D list mu of mean_x and mean_y
    - demeaned vertices_list
    """
    d = np.array(vertices_list)
    mu = np.mean(d, axis=0)
    v = (d - mu).tolist()
    return mu[:2].tolist(), v

def make_faces(faces_all, vertices_all):
    """
    Translate points in faces from absolute coordinates to their ids in vertices_all
    @ param faces_all: original face dictionary. All faces of all kinds of semantic informations
    @ param vertices_all: original vertices dictionary. Not demeanded!
    return:
    - f: list of list. face information
    - s: list of integers, semantic information
    """

    f = []  # face information. list of list
    s = []  # semantic information. list of integers

    for label in faces_all.keys():
        for item in faces_all[label]:
            f.append(face_to_idx(item, vertices_all))

            if label == 'GroundSurface':
                local_s = 0
            elif label == 'WallSurface':
                local_s = 1
            else :
                local_s = 2  # roof surface
            s.append(local_s)  # add this semantic information to global list of semantic info
    return f, s

def write_obj(out_path, header, mu, s, v, f):
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



def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=
        """
        Use the command line argument parser in Python.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    p.add_argument("-i", "--in_dir",
                   help="input directory of all GML files ")
    p.add_argument("-o", "--out_dir",
                   help="output directory of all obj files ")
    return(p.parse_args())

def main():

    # DIRECTORY = os.path.join("/media/yuqiong/DATA", "city")  # input dir
    # RESULT = os.path.join("/media/yuqiong/DATA", "city", "res")  # output dir
    args = cmdline_args()
    DIRECTORY = args.in_dir
    RESULT = args.out_dir

    print(DIRECTORY)
    print(RESULT)
    #-- Start of the program
    print("CityGML2OBJ. Searching for CityGML files...")

    #-- Find all CityGML files in the directory
    os.chdir(DIRECTORY)
    #-- Supported extensions
    types = ('*.gml', '*.GML', '*.xml', '*.XML')
    files_found = []
    for files in types:
        files_found.extend(glob.glob(files))

    for f in files_found:
    # f = files_found[0]
        FILENAME = f[:f.rfind('.')]
        FULLPATH = os.path.join(DIRECTORY, f)

        #-- Reading and parsing the CityGML file(s)
        CITYGML = etree.parse(FULLPATH)
        #-- Getting the root of the XML tree
        root = CITYGML.getroot()
        #-- Determine CityGML version
        # If 1.0
        if root.tag == "{http://www.opengis.net/citygml/1.0}CityModel":
            #-- Name spaces
            ns_citygml="http://www.opengis.net/citygml/1.0"

            ns_gml = "http://www.opengis.net/gml"
            ns_bldg = "http://www.opengis.net/citygml/building/1.0"
            ns_tran = "http://www.opengis.net/citygml/transportation/1.0"
            ns_veg = "http://www.opengis.net/citygml/vegetation/1.0"
            ns_gen = "http://www.opengis.net/citygml/generics/1.0"
            ns_xsi="http://www.w3.org/2001/XMLSchema-instance"
            ns_xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:1.0"
            ns_xlink="http://www.w3.org/1999/xlink"
            ns_dem="http://www.opengis.net/citygml/relief/1.0"
            ns_frn="http://www.opengis.net/citygml/cityfurniture/1.0"
            ns_tun="http://www.opengis.net/citygml/tunnel/1.0"
            ns_wtr="http://www.opengis.net/citygml/waterbody/1.0"
            ns_brid="http://www.opengis.net/citygml/bridge/1.0"
            ns_app="http://www.opengis.net/citygml/appearance/1.0"
        #-- Else probably means 2.0
        else:
            #-- Name spaces
            ns_citygml="http://www.opengis.net/citygml/2.0"

            ns_gml = "http://www.opengis.net/gml"
            ns_bldg = "http://www.opengis.net/citygml/building/2.0"
            ns_tran = "http://www.opengis.net/citygml/transportation/2.0"
            ns_veg = "http://www.opengis.net/citygml/vegetation/2.0"
            ns_gen = "http://www.opengis.net/citygml/generics/2.0"
            ns_xsi="http://www.w3.org/2001/XMLSchema-instance"
            ns_xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
            ns_xlink="http://www.w3.org/1999/xlink"
            ns_dem="http://www.opengis.net/citygml/relief/2.0"
            ns_frn="http://www.opengis.net/citygml/cityfurniture/2.0"
            ns_tun="http://www.opengis.net/citygml/tunnel/2.0"
            ns_wtr="http://www.opengis.net/citygml/waterbody/2.0"
            ns_brid="http://www.opengis.net/citygml/bridge/2.0"
            ns_app="http://www.opengis.net/citygml/appearance/2.0"

        nsmap = {
            None : ns_citygml,
            'gml': ns_gml,
            'bldg': ns_bldg,
            'tran': ns_tran,
            'veg': ns_veg,
            'gen' : ns_gen,
            'xsi' : ns_xsi,
            'xAL' : ns_xAL,
            'xlink' : ns_xlink,
            'dem' : ns_dem,
            'frn' : ns_frn,
            'tun' : ns_tun,
            'brid': ns_brid,
            'app' : ns_app
        }
        #-- Empty lists for cityobjects and buildings
        cityObjects = []
        buildings = []
        other = []

        #-- Find all instances of cityObjectMember and put them in a list
        for obj in root.getiterator('{%s}cityObjectMember'% ns_citygml):
            cityObjects.append(obj)

        print(FILENAME)

        #-- Report the progress and contents of the CityGML file
        print("\tThere are", len(cityObjects), "cityObject(s) in this CityGML file.")
        #-- Store each building separately
        for cityObject in cityObjects:
            for child in cityObject.getchildren():
                if child.tag == '{%s}Building' %ns_bldg:
                    buildings.append(child)
                elif child.tag == '{%s}Road' %ns_tran or child.tag == '{%s}PlantCover' %ns_veg or \
                child.tag == '{%s}GenericCityObject' %ns_gen or child.tag == '{%s}CityFurniture' %ns_frn or \
                child.tag == '{%s}Relief' %ns_dem or child.tag == '{%s}Tunnel' %ns_tun or \
                child.tag == '{%s}WaterBody' %ns_wtr or child.tag == '{%s}Bridge' %ns_brid:
                    other.append(child)

        print("\tAnalysing objects and extracting the geometry...")

        #-- Count the buildings
        b_counter = 0
        b_total = len(buildings)

        #-- Do each building separately
        for b in buildings:
            vertices_all = []
            faces_all = {}

            semanticSurfaces = ['GroundSurface', 'WallSurface', 'RoofSurface']
            for semanticSurface in semanticSurfaces:
                faces_all[semanticSurface] = []

            #-- Increment the building counter
            b_counter += 1

            ob = b.xpath("@g:id", namespaces={'g' : ns_gml})
            if not ob:
                ob = b_counter
            else:
                ob = ob[0]

            #-- Print progress for large files every 1000 buildings.
            if b_counter == 1000:
                print("\t1000... ", end=' ')
            elif b_counter % 1000 == 0 and b_counter == (b_total - b_total % 1000):
                print(str(b_counter) + "...")
            elif b_counter > 0 and b_counter % 1000 == 0:
                print(str(b_counter) + "... ", end=' ')

            header = "# " + ob + "\n# created on " + datetime.datetime.today().strftime('%Y-%m-%d') + "\n"


            for label in faces_all.keys():
                # need to iterate over building to find surfaces
                polys = []
                for child in b.getiterator():
                    if child.tag == '{%s}%s' % (ns_bldg, label):
                        polys.append(child)
                # write polygons to obj
                extract_polys(polys, label, vertices_all, faces_all)

            # remove duplicates from vertices_output
            vertices_all = deduplicate_list_of_list(vertices_all)

            mu, v = vertices_demean(vertices_all)
            f, s = make_faces(faces_all, vertices_all)

            out_path = os.path.join(RESULT, ob + ".obj")
            write_obj(out_path, header, mu, s, v, f)
    print("\tOBJ file(s) written.")

if __name__ == '__main__':
    main()
