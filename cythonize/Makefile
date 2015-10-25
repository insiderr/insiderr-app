
LINKSTATE=-shared

export CC=gcc
export CXX=g++
export AS=as
export LD=ld

CXXFLAGS=-fPIC -fpermissive -fexceptions -Wall -O2 -I../external-libs/opencv-2.4.8/build/include -I/usr/include/python2.7

# -llibjpeg -llibpng -llibtiff -llibjasper
LDFLAGS_OPENCV=$(LINKSTATE) \
-fPIC -L/usr/lib/x86_64-linux-gnu \
-Wl,-Bdynamic -l:libopencv_highgui.so.2.4 -l:libopencv_imgproc.so.2.4 -l:libopencv_core.so.2.4 \
-Wl,-Bdynamic -l:libjpeg.so.8 -l:libpng12.so.0 -l:libtiff.so.5 -l:libjasper.so.1 \
-Wl,-Bdynamic -lz \
-Wl,-Bdynamic -lc -lgcc -lm -lpython2.7

LDFLAGS=--sysroot=$(LINKSTATE) \
-fPIC -L/usr/lib/x86_64-linux-gnu\
-Wl,-Bstatic -lgnustl_static -lzz \
-Wl,-Bdynamic -lc -lgcc -lm -llog -lpython2.7


SOURCE=../app/modules/image/native_opencv.pyx
CYTHON=native_opencv.cpp
OBJECT=$(addsuffix .o, $(basename $(CYTHON)))
EXECUTABLE=$(addsuffix .so, $(basename $(SOURCE)))

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJECT)
	$(CXX) $(OBJECT) $(LDFLAGS_OPENCV) -o $@
	rm -f $(OBJECT)
	rm -f $(CYTHON)

$(OBJECT): $(CYTHON)
	$(CC) $(CXXFLAGS) -c $< -o $@
	
$(CYTHON): $(SOURCE)
	cython -t --cplus $< -o $@

clean:
	rm -f $(OBJECT)
	rm -f $(EXECUTABLE)
	rm -f $(CYTHON)


 
