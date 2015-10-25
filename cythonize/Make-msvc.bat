@echo off

echo First Time install
echo Install Kivy to c:\kivy-1.8.0\
echo run kivy.bat
echo run "c:\Program Files (x86)\Microsoft Visual Studio 10.0\Common7\Tools\vsvars32.bat"
echo run pip install twisted
echo pip uninstall zope.interface
echo easy_install zope.interface
echo download, extract and go to directory
echo run python setup.py build -c msvc install
echo you are done
echo.

call "c:\Program Files (x86)\Microsoft Visual Studio 10.0\Common7\Tools\vsvars32.bat"
path=%path%;c:\kivy-1.8.0\Python27

:: cleanup
del ..\app\modules\image\*.dll
del ..\app\modules\image\*.pyd
del ..\app\modules\image\*.so

:: build
echo cython:

python.exe -m cython  -t --cplus ..\app\modules\image\native_opencv.pyx
::if %errorlevel% neq 0 goto :badend
move ..\app\modules\image\native_opencv.cpp .

echo compile:

cl.exe /c /nologo /Ox /MD /W3 /GS- /DNDEBUG -I..\external-libs\opencv-2.4.8\build\include -IC:\kivy-1.8.0\Python27\PC -Ic:\kivy-1.8.0\kivy\kivy\graphics -Ic:\kivy-1.8.0-msvc\glew-1.10.0\include -IC:\kivy-1.8.0\Python27\include /Tpnative_opencv.cpp /Fonative_opencv.obj
::if %errorlevel% neq 0 goto :badend


echo linking:

link.exe /DLL /nologo /INCREMENTAL:NO /LIBPATH:..\external-libs\opencv-2.4.8\build\x86\vc10\lib /LIBPATH:C:\kivy-1.8.0\Python27\libs /LIBPATH:C:\kivy-1.8.0\Python27\PCbuild opencv_highgui248.lib opencv_core248.lib opencv_imgproc248.lib /EXPORT:initnative_opencv native_opencv.obj /OUT:native_opencv.pyd /IMPLIB:native_opencv.lib /MANIFEST /MANIFESTFILE:native_opencv.pyd.manifest
::if %errorlevel% neq 0 goto :badend


echo mt:

mt.exe -nologo -manifest native_opencv.pyd.manifest -outputresource:native_opencv.pyd
::if %errorlevel% neq 0 goto :badend

echo put back library
copy native_opencv.pyd ..\app\modules\image\
move native_opencv.pyd ..\app\modules\image\native_opencv.dll
copy /Y ..\external-libs\opencv-2.4.8\build\x86\vc10\dll\*.dll ..\app\modules\image\
del native_opencv.*

:: done
goto :end

:badend
echo Error occurred
set errorlevel=1

:end
