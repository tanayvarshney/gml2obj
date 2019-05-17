from lxml import etree
import os
import argparse
import glob
import numpy as np
import itertools
import datetime
import sys
import pandas as pd

def getText(b, path):
    """
    input building and relative xpath from the building, get the text from the path 
    """
    return b.findall(path)[0].text

DIRECTORY = "/media/yuqiong/DATA/city/nyc/test"  # input dir
RESULT =  "/media/yuqiong/DATA/city/nyc"  # input dir
# args = cmdline_args()
# DIRECTORY = args.in_dir
# RESULT = args.out_dir

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

    FILENAME = f[:f.rfind('.')]
    FULLPATH = os.path.join(DIRECTORY, f)

    #-- Reading and parsing the CityGML file(s)
    citygml = etree.parse(FULLPATH)
    #-- Getting the root of the XML tree
    root = citygml.getroot()

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
    b_info_total = []

    #-- Do each building separately
    for b in buildings:
        try:
            # store all information and tags
            dic = {}

            #-- Increment the building counter
            b_counter += 1

            ob = b.xpath("@g:id", namespaces={'g' : ns_gml})
            if not ob:
                ob = b_counter
            else:
                ob = ob[0]

            dic["bid"] = ob

            # https://stackoverflow.com/questions/5466451/how-can-i-print-literal-curly-brace-characters-in-python-string-and-also-use-fo
            value_tag = "{{{0}}}value".format(ns_gen)

            elevation_tag = "{{{0}}}stringAttribute[@name='ground_elevation']".format(ns_gen)
            elevation_path = os.path.join(elevation_tag, value_tag)
            dic["elevation"] = float(getText(b, elevation_path))

            volume_tag = "{{{0}}}stringAttribute[@name='building_volume']".format(ns_gen)
            volume_path = os.path.join(volume_tag, value_tag)
            dic["volume"] = float(getText(b, volume_path))

            base_tag = "{{{0}}}stringAttribute[@name='building_base_area']".format(ns_gen)
            base_path = os.path.join(base_tag, value_tag)
            dic["area"] = float(getText(b, base_path))

            block_tag = "{{{0}}}stringAttribute[@name='borough_block_lot_number']".format(ns_gen)
            block_path = os.path.join(block_tag, value_tag)
            dic["block"] = int(getText(b, block_path))

            height_path = "{{{0}}}measuredHeight".format(ns_bldg)
            dic["height"] = float(getText(b, height_path))

            b_info_total.append(dic)

        except:
            pass

    df = pd.DataFrame(b_info_total)

    with open("test.csv", 'a') as f:
        df.to_csv(f, header=True)