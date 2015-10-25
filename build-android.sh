#!/bin/bash

BUILDOZERPARAM=release
if [ $# -gt 0 ]; then
    BUILDOZERPARAM="$@"
fi

trap "read -p \"----> Press [Enter] to quit <----\"" INT TERM EXIT

echo -e "\e[104m Building for Android \e[0m"


# check if we compiled at least once so we have python-for-android and NDK
echo -e "\e[104m Check if we compiled at least once so we have python-for-android and NDK \e[0m"
if [ ! -d ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install ] || [ ! -d $HOME/.buildozer/android/platform/android-ndk-r9c ];
then
	echo -e "\e[104m Building once to get NDK and python for android \e[0m"
	buildozer android update $BUILDOZERPARAM
	if [ $? -ne 0 ] || [ ! -d ./.buildozer/android/platform/python-for-android/ ] || [ ! -d $HOME/.buildozer/android/platform/android-ndk-r9c ]; then
		echo -e "\e[101m Build failed - exiting \e[0m"
		exit 1
	fi
fi


# insert build patch to recipe build system
BASEFOLDER=$(pwd)
echo -e "\e[104m Checking if android needs patching \e[0m"
patch --dry-run -s -f -d ./.buildozer/android/platform/python-for-android/ -p0 -i $BASEFOLDER/android-patches/recipe.patch
if [ $? -eq 0 ]; then
	echo -e "\e[104m Patching android build \e[0m"
	patch -d ./.buildozer/android/platform/python-for-android/ -p0 -i $BASEFOLDER/android-patches/recipe.patch
	if [ $? -ne 0 ]; then
		echo -e "\e[101m Patching android (recipe) build - failed \e[0m"
	else
		# build so that we could continue patching.
		buildozer android $BUILDOZERPARAM
	fi
fi

# insert build patch to android java build system
patch --dry-run -s -f -d ./.buildozer/android/platform/python-for-android/ -p0 -i $BASEFOLDER/android-patches/java.patch
if [ $? -eq 0 ]; then
	echo -e "\e[104m Patching android build \e[0m"
	patch -d ./.buildozer/android/platform/python-for-android/ -p0 -i $BASEFOLDER/android-patches/java.patch
	if [ $? -ne 0 ]; then
		echo -e "\e[101m Patching android (kivy) build - failed \e[0m"
	else
		echo -e "\e[104m Rebuild platform after patching \e[0m"	
		buildozer android $BUILDOZERPARAM
	fi
fi

# patch and compile kivy
patch --dry-run -s -f -d ./.buildozer/android/platform/python-for-android/ -p0 -i $BASEFOLDER/android-patches/kivy.patch
if [ $? -eq 0 ]; then
	echo -e "\e[104m Patching android build \e[0m"
	patch -d ./.buildozer/android/platform/python-for-android/ -p0 -i $BASEFOLDER/android-patches/kivy.patch
	if [ $? -ne 0 ]; then
		echo -e "\e[101m Patching android (kivy) build - failed \e[0m"
	else
		echo -e "\e[104m Compile kivy platform after patching \e[0m"	
		# compiling and copying the patched compiled files
		python -O -m py_compile ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/base.py
		python -O -m py_compile ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/core/audio/__init__.py
		python -O -m py_compile ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/core/window/__init__.py
		python -O -m py_compile ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/core/image/__init__.py

		cp ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/base.pyo ./.buildozer/android/platform/python-for-android/dist/insiderr/private/lib/python2.7/site-packages/kivy/
		cp ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/core/audio/__init__.pyo ./.buildozer/android/platform/python-for-android/dist/insiderr/private/lib/python2.7/site-packages/kivy/core/audio/
		cp ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/core/window/__init__.pyo ./.buildozer/android/platform/python-for-android/dist/insiderr/private/lib/python2.7/site-packages/kivy/core/window/
		cp ./.buildozer/android/platform/python-for-android/dist/insiderr/python-install/lib/python2.7/site-packages/kivy/core/image/__init__.pyo ./.buildozer/android/platform/python-for-android/dist/insiderr/private/lib/python2.7/site-packages/kivy/core/image/
	fi
fi

# Cythonize and build for android
echo -e "\e[104m Cythonize and build for android \e[0m"
pushd cythonize
make -f Makefile-android
if [ $? -ne 0 ]; then
	echo -e "\e[101m Cythonize android failed - exiting \e[0m"
	popd
	exit 1
fi
popd


# Build
echo -e "\e[104m Building final \e[0m"
rm bin/*.apk
buildozer android $BUILDOZERPARAM
if [ ! -f bin/*.apk ]; then
	echo -e "\e[101m Build android failed - exiting \e[0m"
	exit 1
fi

if [ -f bin/*release-unsigned.apk ]; then
    # Signing
    echo -e "\e[104m Signing \e[0m"
    # creating a new certificate:
    # keytool -genkey -v -keystore insiderrkey.keystore -alias CERT -keyalg RSA -keysize 2048 -validity 10000
    # use certificate
    # jarsigner -sigalg MD5withRSA  -digestalg SHA1 -verbose -keystore file.keystore -storepass password -keypass password ./bin/Insiderr-*-release-unsigned.apk CERT
    jarsigner -verbose -verify ./bin/Insiderr-*-release-unsigned.apk

    # Zip aligning - make sure path is correct
    echo -e "\e[104m Zip aligning \e[0m"
    # $HOME/.buildozer/android/platform/android-sdk-*/build-tools/*/zipalign -v 4 bin/*.apk bin/insiderr.apk
    # pick the latest version
    ZIPALIGN=`ls $HOME/.buildozer/android/platform/android-sdk-*/build-tools/*/zipalign | tail -1`
    $ZIPALIGN -v 4 bin/*.apk bin/insiderr.apk
fi

# Cythonize back to host os
echo -e "\e[104m Cythonize back to host os \e[0m"
pushd cythonize
make -f Makefile &> /dev/null
if [ $? -ne 0 ]; then
	echo -e "\e[101m Cythonize host OS failed - exiting \e[0m"
	popd
	exit 1
fi
popd


# Done
echo -e "\e[104m Compiled successfully \e[0m"


