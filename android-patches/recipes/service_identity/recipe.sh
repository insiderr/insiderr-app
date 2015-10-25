#!/bin/bash

VERSION_service_identity=14.0.0
DEPS_service_identity=(python)
URL_service_identity=https://pypi.python.org/packages/source/s/service_identity/service_identity-$VERSION_service_identity.tar.gz
DEPS_service_identity=(pyopenssl pyasn1modules pyasn1 characteristic python)
MD5_service_identity=cea0b0156d73b025ecef660fb51f0d9a
BUILD_service_identity=$BUILD_PATH/service_identity/$(get_directory $URL_service_identity)
RECIPE_service_identity=$RECIPES_PATH/service_identity


# function called for preparing source code if needed
# (you can apply patch etc here.)
function prebuild_service_identity() {
	cp $RECIPE_service_identity/setup.py $BUILD_service_identity/
}

function shouldbuild_service_identity() {
    if [ -d "$SITEPACKAGES_PATH/service_identity" ]; then
		DO_BUILD=0
	fi
}

function build_service_identity() {
	cd $BUILD_service_identity
	push_arm
	export EXTRA_CFLAGS="--host linux-armv"
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

# function called after all the compile have been done
function postbuild_service_identity() {
	true
}

