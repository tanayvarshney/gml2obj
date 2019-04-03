# gml2obj

A Python tool to extract individual buildings from CityGML files

### Usage
python main.py -i INPUT_DIR -o OUTPUT_DIR

`INPUT_DIR` and `OUTPUT_DIR` are input and output directories specified by the user. This tool will find all `.gml` files in the `INPUT_DIR`, extract all buildings from these `.gml` files, and write individual building mesh as `.obj` files to the `OUTPUT_DIR`.

A note on the format of output meshes: this code will not do triangulation on meshes. In CityGML files, building surfaces are stored as a set of polygons, with semantic information attached. This code will extract exactly these polygons.

This tool will also demean on `x` and `y` axis on all vertices in a building.

Every `obj` file will have the following parts of information:
- (comment line) header : include creation date and uid
- (comment line) semantic label of faces: 0 = GroundSurface, 1 = WallSurface, 2 = RoofSurface. Every face label will have its own line!
- vertices
- faces

A sample output `.obj` file:

```
# UUID_0a9d2527-75fa-4114-b015-09a06aa0eabd
# created on 2019-04-03
# mean 2677901.813794118 1249702.0955588236
# 0
# 1
... (many lines of face labels, not in the real obj file!)
# 2
v -7.315794117748737 -4.198558823438361 0.5117352941176136
v -6.295794117730111 -4.041558823548257 -9.062264705882342
... (other vertices, not in the read obj file!)
v 2.22620588215068 0.39544117636978626 3.2227352941176264
v 7.546205881983042 1.6774411764927208 0.5117352941176136
f 20 2 4 6 12 32
f 28 29 24 23
... (other faces, not in the real obj file!)
f 8 25 9 1
f 24 29 31 27
```
