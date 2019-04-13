### A code to lookup a particular building from cityGML files to check its topology
### 20190412
### Yuqiong Li
import argparse
from lxml import etree
import markup3dmodule
import polygon3dmodule

def main():
    parser = ArgumentParser()
    parser.add_argument("-f", "--file",
                        help="the gml file path")
    parser.add_argument("-b", "--bid",
                        help="building id")
    args = parser.parse_args()

    gmlpath = args.file
    bid = args.bid

    CITYGML = etree.parse(gmlpath)
    #-- Getting the root of the XML tree
    root = CITYGML.getroot()
    #-- Determine CityGML version
    if root.tag == "{http://www.opengis.net/citygml/1.0}CityModel":
        ns_bldg = "http://www.opengis.net/citygml/building/1.0"
    else:
        ns_bldg = "http://www.opengis.net/citygml/building/2.0"

    #-- Find all instances of cityObjectMember and put them in a list
    for b in root.getiterator('{%s}Building'% ns_blbg):
        if b.tag == '{%s}Building' %ns_bldg:
            ob = b.xpath("@g:id", namespaces={'g' : ns_gml})
            if ob == bid:
                print(b.text)
    return


if __name__ == "__main__":
    main()
