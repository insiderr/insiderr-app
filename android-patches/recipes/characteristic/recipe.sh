#!/bin/bash

VERSION_characteristic=14.3.0
URL_characteristic=https://pypi.python.org/packages/source/c/characteristic/characteristic-$VERSION_characteristic.tar.gz
DEPS_characteristic=(python)
MD5_characteristic=
BUILD_characteristic=$BUILD_PATH/characteristic/$(get_directory $URL_characteristic)
RECIPE_characteristic=$RECIPES_PATH/characteristic


# function called for preparing source code if needed
# (you can apply patch etc here.)
function prebuild_characteristic() {
	cp $RECIPE_characteristic/setup.py $BUILD_characteristic/
}

function shouldbuild_characteristic() {
    if [ -d "$SITEPACKAGES_PATH/characteristic" ]; then
		DO_BUILD=0
	fi
}

function build_characteristic() {
	cd $BUILD_characteristic
	push_arm
	export EXTRA_CFLAGS="--host linux-armv"
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

# function called after all the compile have been done
function postbuild_characteristic() {
	true
}

