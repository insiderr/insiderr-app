#!/bin/bash


DEVELOPER="/Applications/Xcode.app/Contents/Developer"

SDK_VERSION="8.1"
MIN_VERSION="4.3"

IPHONEOS_PLATFORM="${DEVELOPER}/Platforms/iPhoneOS.platform"
IPHONEOS_SDK="${IPHONEOS_PLATFORM}/Developer/SDKs/iPhoneOS${SDK_VERSION}.sdk"
IPHONEOS_GCC="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
IPHONEOS_DEPLOYMENT_TARGET=4.0
ARCH="-arch armv7 -arch armv7s -arch arm64"
PATH=${DEVELOPER}/Platforms/iPhoneOS.platform/Developer/usr/bin:/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin


cd crypto
${IPHONEOS_GCC} -v -c -pthread -fwrapv -DMACOSX  -DNDEBUG -Os  -I ~/kivy-ios/dist/hostpython/include/python2.7/ \
-I ~/kivy-ios/dist/include/armv7/ffi/ -I ~/kivy-ios/dist/include/armv7/ -I ~/kivy-ios/tmp/openssl/ios-openssl/openssl/include/ -isysroot ${IPHONEOS_SDK} ${ARCH} -L ~/kivy-ios/dist/lib/  \
-ldl -lpthread -lffi -lpython2.7 -lssl -lcrypto -lz -lsqlite3 \
crl.c crypto.c netscape_spki.c pkcs12.c pkcs7.c pkey.c revoked.c x509.c x509ext.c x509name.c x509req.c x509store.c 
#ar rcs ../libcryptossl.a crl.o crypto.o netscape_spki.o pkcs12.o pkcs7.o pkey.o revoked.o x509.o x509ext.o x509name.o x509req.o x509store.o
cd ..


cd ssl
${IPHONEOS_GCC} -v -c -pthread -fwrapv -DMACOSX  -DNDEBUG -Os  -I ~/kivy-ios/dist/hostpython/include/python2.7/ \
-I ~/kivy-ios/dist/include/armv7/ffi/ -I ~/kivy-ios/dist/include/armv7/ -I ~/kivy-ios/tmp/openssl/ios-openssl/openssl/include/ -isysroot ${IPHONEOS_SDK} ${ARCH} -L ~/kivy-ios/dist/lib/  \
-ldl -lpthread -lffi -lpython2.7 -lssl -lcrypto -lz -lsqlite3 \
connection.c context.c ssl.c 
#ar rcs ../libsslssl.a connection.o context.o ssl.o
cd ..

${IPHONEOS_GCC} -v -c -pthread -fwrapv -DMACOSX  -DNDEBUG -Os  -I ~/kivy-ios/dist/hostpython/include/python2.7/ \
-I ~/kivy-ios/dist/include/armv7/ffi/ -I ~/kivy-ios/dist/include/armv7/ -I ~/kivy-ios/tmp/openssl/ios-openssl/openssl/include/ -isysroot ${IPHONEOS_SDK} ${ARCH} -L ~/kivy-ios/dist/lib/  \
-ldl -lpthread -lffi -lpython2.7 -lssl -lcrypto -lz -lsqlite3 \
util.c \
-o util.o
#ar rcs libutil.a util.o


${IPHONEOS_GCC} -v -c -pthread -fwrapv -DMACOSX  -DNDEBUG -Os  -I ~/kivy-ios/dist/hostpython/include/python2.7/ \
-I ~/kivy-ios/dist/include/armv7/ffi/ -I ~/kivy-ios/dist/include/armv7/ -I ~/kivy-ios/tmp/openssl/ios-openssl/openssl/include/ -isysroot ${IPHONEOS_SDK} ${ARCH} -L ~/kivy-ios/dist/lib/  \
-ldl -lpthread -lffi -lpython2.7 -lssl -lcrypto -lz -lsqlite3 \
rand/rand.c \
-o rand.o
#ar rcs librand.a rand.o

ar rcs libpyopenssl.a crypto/crl.o crypto/crypto.o crypto/netscape_spki.o crypto/pkcs12.o crypto/pkcs7.o crypto/pkey.o crypto/revoked.o \
crypto/x509.o crypto/x509ext.o crypto/x509name.o crypto/x509req.o crypto/x509store.o \
ssl/connection.o ssl/context.o ssl/ssl.o \
util.o rand.o 
