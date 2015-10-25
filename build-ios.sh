#!/bin/bash


echo -e " Building for Ios "
BASEFOLDER=$(pwd)

# check if we have kivy-ios compiled
echo -e " Check for kivy ios "
if [ ! -d $HOME/kivy-ios ];
then
	echo -e " Building kivy-ios "
	#pushd $HOME
	#git clone git://github.com/kivy/kivy-ios	
	#popd
	mkdir $HOME/kivy-ios
	tar xzf ios-patches/kivy-ios.newtools.tgz -C $HOME/kivy-ios/
	
	find $HOME/kivy-ios/dist/root/python/lib/python2.7 -name "test" -type d -exec rm -Rrf {} \;
	find $HOME/kivy-ios/dist/root/python/lib/python2.7 -name "tests" -type d -exec rm -Rrf {} \;
	find $HOME/kivy-ios/dist/root/python/lib/python2.7 -name "unittest" -type d -exec rm -Rrf {} \;
	find $HOME/kivy-ios/dist/root/python/lib/python2.7 -iname '*.py' -exec rm {} \;
	find $HOME/kivy-ios/dist/root/python/lib/python2.7 -iname '*.pyc' -exec rm {} \;
	find $HOME/kivy-ios/dist/root/python/lib/python2.7 -iname '*.o' -exec rm {} \;
fi

# check we managed to build the kivy-ios
if [ ! -d $HOME/kivy-ios/build ];
then
	pushd $HOME/kivy-ios
	tools/build-all.sh
	popd
	if [ ! -d $HOME/kivy-ios/build ] ; then
		echo -e " Build failed - exiting "
		exit 1
	fi	
fi


# check if we created an xcode project
echo -e " Checking if xcode project "
if [ ! -d $HOME/kivy-ios/app-insiderr ];
then
	pushd $HOME/kivy-ios
	#./toolchain.py create insiderr $BASEFOLDER/app
	mkdir app-insiderr
	cp -R $BASEFOLDER/ios-patches/xcode-project/* app-insiderr/
	popd
	
	mkdir $BASEFOLDER/app/basemodules
	cp -R $BASEFOLDER/ios-patches/basemodules/* $BASEFOLDER/app/basemodules/

	find $BASEFOLDER/app/basemodules -name "test" -type d -exec rm -Rrf {} \;
	find $BASEFOLDER/app/basemodules -name "tests" -type d -exec rm -Rrf {} \;
	find $BASEFOLDER/app/basemodules -name "SelfTest" -type d -exec rm -Rrf {} \;
fi

# Done
echo -e " Project installed successfully "

pushd $HOME/kivy-ios
open  app-insiderr/insiderr.xcodeproj
popd
