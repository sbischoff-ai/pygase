@ECHO off
SET /p pypy=Update pypyvenv instead of venv? [y/n]
ECHO ##################################
ECHO Updating Dependencies ...
ECHO ##################################
IF %pypy%==n %~dp0venv\Scripts\python.exe -m pip install --upgrade pip
IF %pypy%==n %~dp0venv\Scripts\python.exe -m pip install --upgrade setuptools
IF %pypy%==n %~dp0venv\Scripts\python.exe -m pip install --upgrade -r %~dp0dev-requirements.txt
IF %pypy%==y %~dp0pypyvenv\Scripts\pypy3.exe -m pip install --upgrade pip
IF %pypy%==y %~dp0pypyvenv\Scripts\pypy3.exe -m pip install --upgrade setuptools
IF %pypy%==y %~dp0pypyvenv\Scripts\pypy3.exe -m pip install --upgrade -r %~dp0dev-requirements.txt
ECHO ##################################
ECHO Dev Update completed.
ECHO ##################################
PAUSE