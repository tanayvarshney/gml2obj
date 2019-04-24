#!/usr/bin/env python
# python main.py -i /media/yuqiong/DATA/city/Vienna -o /media/yuqiong/DATA/city/Vienna/res
# python main.py -i /media/yuqiong/DATA/city/hague/data -o /media/yuqiong/DATA/city/hague/hague_poly_objs

for d in $(find /media/yuqiong/DATA/city/rotterdam/data -maxdepth 1 -type d)
do
  res=$( echo $d | cut -d'/' -f 8 )  # get the subfolder name only
  src="/media/yuqiong/DATA/city/rotterdam/data/"$res  # source of citygml subfolders 
  dst="/media/yuqiong/DATA/city/rotterdam/rotterdam_poly_objs/"$res  # destination of obj outputs
#  echo $src
#  echo $dst
  mkdir $dst
  python main.py -i $src -o $dst 
done

