#!/bin/bash

#if we don't have imagemagick and librsvg2-bin install it
dpkg -s librsvg2-bin 2>/dev/null > /dev/null
if [ $? -ne 0 ]; then
    sudo apt-get install librsvg2-bin
fi

# now let's continue
rm -R ../app/data/themes
mkdir ../app/data/themes
rm -R atlases
mkdir atlases
cd atlases

BASE=../svgs/
FOLDERS=$BASE/*
export w720=90

RES="1080
768
720
640
576
540
480
400
320"
for r in $RES
do
    resdir=$r'px'
    mkdir $resdir
    for directory in $( find $BASE -type d ); do
        res=$r'px/'
        target=${directory/$BASE/$res}
        #echo mkdir $target
        mkdir -p $target
    done
done

#for f in $(find ../svgs/ -name '*.svg' -or -name '*.png');
for f in $(find $BASE -name '*.svg');
do
    echo "Processing $f ..."
    for r in $RES
    do
        res=$r'px/'
        target=${f/$BASE/$res}
        target=${target/.svg/.png}
        #dpi=$(($r*($w720)/720))
        #echo "target $target dpi $dpi
        #echo convert -density $dpi  +antialias -background transparent $f png32:$target
        zoom=`echo "$r 720" | awk '{printf "%.3f \n", $1/$2}'`
        echo "target $target zoom $zoom ..."
        rsvg-convert -x $zoom -z $zoom -f png -o $target $f
    done
done
   
# Try to create atlases
for r in $RES
do
    echo "Atlasing $r px ..."
    res=$r'px/'
    cd $res
    python ../../make_theme.py
    mkdir ../../../app/data/themes/$res
    cp *.png ../../../app/data/themes/$res/
    cp *.atlas ../../../app/data/themes/$res/
    cd ..
done

cd .. 

