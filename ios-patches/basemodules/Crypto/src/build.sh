#!/bin/bash


DEVELOPER="/Applications/Xcode.app/Contents/Developer"

SDK_VERSION="8.1"
MIN_VERSION="4.3"

IPHONEOS_PLATFORM="${DEVELOPER}/Platforms/iPhoneOS.platform"
IPHONEOS_SDK="${IPHONEOS_PLATFORM}/Developer/SDKs/iPhoneOS${SDK_VERSION}.sdk"
IPHONEOS_GCC="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
IPHONEOS_DEPLOYMENT_TARGET=4.0
PATH=${DEVELOPER}/Platforms/iPhoneOS.platform/Developer/usr/bin:/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin
ARCH="-arch armv7 -arch armv7s -arch arm64"


${IPHONEOS_GCC} -v -c -pthread -fwrapv -DMACOSX  -DNDEBUG -Os  -I ~/kivy-ios/dist/hostpython/include/python2.7/ \
-I ~/kivy-ios/dist/include/armv7/ffi/ -I ~/kivy-ios/dist/include/armv7/  -isysroot ${IPHONEOS_SDK} ${ARCH} -L ~/kivy-ios/dist/lib/  \
-ldl -lpthread -lffi -lpython2.7 -lssl -lcrypto -lz -lsqlite3 \
AES.c \
ARC2.c \
ARC4.c \
Blowfish.c \
CAST.c \
cast5.c \
DES.c \
DES3.c \
MD2.c \
MD4.c \
RIPEMD160.c \
SHA224.c \
SHA256.c \
SHA384.c \
SHA512.c \
strxor.c \
winrand.c \
XOR.c \
_counter.c \
#_fastmath.c 
#stream_template.c \
#hash_SHA2_template.c \
#hash_template.c \
#block_template.c \

ar rcs libpycrypto.a \
AES.o \
ARC2.o \
ARC4.o \
Blowfish.o \
CAST.o \
cast5.o \
DES.o \
DES3.o \
MD2.o \
MD4.o \
RIPEMD160.o \
SHA224.o \
SHA256.o \
SHA384.o \
SHA512.o \
strxor.o \
winrand.o \
XOR.o \
_counter.o \
#_fastmath.o 

#block_template.o \
#stream_template.o \
#hash_SHA2_template.o \
#hash_template.o \
