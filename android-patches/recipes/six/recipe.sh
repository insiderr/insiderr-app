#!/bin/bash

VERSION_six=1.9.0
URL_six=https://pypi.python.org/packages/source/s/six/six-$VERSION_six.tar.gz
DEPS_six=(python)
MD5_six=
BUILD_six=$BUILD_PATH/six/$(get_directory $URL_six)
RECIPE_six=$RECIPES_PATH/six

function prebuild_six() {
	true
}

function shouldbuild_six() {
	if [ -d "$SITEPACKAGES_PATH/six" ]; then
		DO_BUILD=0
	fi
}

function build_six() {
	cd $BUILD_six
	push_arm
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

function postbuild_six() {
	true
}
