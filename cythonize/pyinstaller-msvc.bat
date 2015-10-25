@echo off

pushd .

call "c:\Program Files (x86)\Microsoft Visual Studio 10.0\Common7\Tools\vsvars32.bat"
call c:\kivy-1.8.0\kivy.bat ignore_me_please.py 2> nul
call pip install twisted==13.2
call pip install pyopenssl
call pip uninstall zope.interface
call easy_install zope.interface
call easy_install http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe
call easy_install pyinstaller

echo Compiling Cython for Windows
call Make-msvc.bat

cd ../app
::call pyinstaller -w main.py --hidden-import=OpenSSL
call pyinstaller -w main.py 
mkdir dist\test
mkdir dist\main\kivy
xcopy /Y /S  c:\kivy-1.8.0\kivy\kivy\*.* dist\main\kivy\ > nul
xcopy /Y *.kv dist\main\kivy > nul
for /F %%v IN ('dir *. /b') DO (
	if not "%%v"=="dist" (
		if not "%%v"=="build" (
			echo copying %%v
			mkdir dist\main\%%v
			xcopy /Y /S %%v\*.* dist\main\%%v\ > nul
		)
	)
)


echo @echo off > dist\insiderr.bat
echo for %%%%* in (.) do set CurrDirName=%%%%~n* >> dist\insiderr.bat
echo cd main  >> dist\insiderr.bat
echo title %%CurrDirName%% >> dist\insiderr.bat
echo main.exe %%CurrDirName%% >> dist\insiderr.bat
echo cd .. >> dist\insiderr.bat

cd dist
pushd .
echo running for the first time - compiling into pyc
echo please exit once you have the app running
call insiderr.bat
popd

if exist main ( 
cd main
del /S *.py > nul
cd ..
)

popd
pause
