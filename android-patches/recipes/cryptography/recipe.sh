#!/bin/bash

VERSION_cryptography=0.7.2
URL_cryptography=https://pypi.python.org/packages/source/c/cryptography/cryptography-$VERSION_cryptography.tar.gz
DEPS_cryptography=(python)
MD5_cryptography=
BUILD_cryptography=$BUILD_PATH/cryptography/$(get_directory $URL_cryptography)
RECIPE_cryptography=$RECIPES_PATH/cryptography

function prebuild_cryptography() {
	cp $RECIPE_cryptography/setup.py $BUILD_cryptography/
}

function shouldbuild_cryptography() {
	if [ -d "$SITEPACKAGES_PATH/cryptography" ]; then
		DO_BUILD=0
	fi
}

function build_cryptography() {
	cd $BUILD_cryptography
	push_arm
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

function postbuild_cryptography() {
	true
}
