copy ..\elzwelle_sheet.py .
mkdir dist
mkdir dist\elzwelle_sheet
\opt\miniconda3\Scripts\pyinstaller.exe elzwelle_sheet.py
copy \opt\miniconda3\Library\bin\libcrypto-3-x64.dll 	dist\elzwelle_sheet\_internal
copy \opt\miniconda3\Library\bin\libssh2.dll 			dist\elzwelle_sheet\_internal
copy \opt\miniconda3\Library\bin\libssl-3-x64.dll		dist\elzwelle_sheet\_internal
