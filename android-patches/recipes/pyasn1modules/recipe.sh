#!/bin/bash

VERSION_pyasn1modules=0.0.5
URL_pyasn1modules=https://pypi.python.org/packages/source/p/pyasn1-modules/pyasn1-modules-$VERSION_pyasn1modules.tar.gz
DEPS_pyasn1modules=(python)
MD5_pyasn1modules=
BUILD_pyasn1modules=$BUILD_PATH/pyasn1modules/$(get_directory $URL_pyasn1modules)
RECIPE_pyasn1modules=$RECIPES_PATH/pyasn1modules

function prebuild_pyasn1modules() {
	true
}

function shouldbuild_pyasn1modules() {
	if [ -d "$SITEPACKAGES_PATH/pyasn1modules" ]; then
		DO_BUILD=0
	fi
}

function build_pyasn1modules() {
	cd $BUILD_pyasn1modules
	push_arm
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

function postbuild_pyasn1modules() {
	true
}
