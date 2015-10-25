#!/bin/bash

#if we don't have imagemagick and librsvg2-bin install it
dpkg -s imagemagick 2>/dev/null > /dev/null
if [ $? -ne 0 ]; then
    sudo apt-get install librsvg2-bin
fi

# folders
BASE=./post_themes/images
THUMBS=../app/data/post_themes/thumbs
MASKED=../app/data/post_themes/images

# clear previous
rm -R $THUMBS/
rm -R $MASKED/
mkdir $MASKED
mkdir $THUMBS

echo create folders
for f in $BASE/*/;
do
    echo "Processing $f :"
    fixed_out="${f/$BASE/$THUMBS}"
    mkdir $fixed_out
    fixed_out="${f/$BASE/$MASKED}"
    mkdir $fixed_out
    
    # copy files 
    i=0
    for p in $(find $f -name "*.jpg" -o -name "*.png" | sort);
    do
        i=$[$i +1]
        echo copying: $p to $fixed_out$i.jpg
        cp $p $fixed_out$i.jpg
    done
done

echo overlay masks $MASKED
for f in $(find $MASKED -name '*.jpg' -o -name '*.png');
do
    echo "Processing $f :"
    #fixed_out="${f/$BASE/$MASKED}"
    fixed_out=$f

    convert $f -gravity center maskcorners.png -composite $fixed_out
done

echo mogrify thumbs from originals
for f in $MASKED/*/;
do
    echo "Processing $f :"
    fixed_out="${f/$MASKED/$THUMBS}"

    mogrify -resize 265x265 -quality 85% -strip -interlace Plane -sampling-factor 4:2:0 -path $fixed_out $f/*.jpg
done

echo mogrify overlayed images optimize jpegs
for f in $MASKED/*/;
do
    echo "Processing $f :"
    #fixed_out="${f/$BASE/$MASKED}"
    fixed_out=$f

    mogrify -quality 85% -strip -interlace Plane -sampling-factor 4:2:0 $fixed_out/*.jpg
done

