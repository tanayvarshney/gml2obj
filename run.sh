#!/usr/bin/env python
# python main.py -i /media/yuqiong/DATA/city/Vienna -o /media/yuqiong/DATA/city/Vienna/res
python main.py -i /media/yuqiong/DATA/city/hague/data -o /media/yuqiong/DATA/city/hague/hague_poly_objs

#for d in $(find /media/yuqiong/DATA/city/berlin -maxdepth 1 -type d)
#do
#  res=$( echo $d | cut -d'/' -f 7 )  # get the subfolder name only
#  src="/media/yuqiong/DATA/city/berlin/"$res  # source of citygml subfolders 
#  dst="/media/yuqiong/DATA/city/berlin_poly_objs/"$res  # destination of obj outputs
#  # echo $src
#  # echo $dst
#  echo $res
#  python main.py -i $src -o $dst 
#done
#
