@ECHO off
ECHO Only run this once!
ECHO Create venv, add project path to it and install all dependencies?
SET /p continue=[y/n] 
IF %continue%==n EXIT
SET /p path=Input path to Python 3.5+ executable: 
ECHO Is this a PyPy executable?
SET /p pypy=[y/n] 
ECHO ##################################
ECHO Creating Virtual Environment ...
ECHO ##################################
IF %pypy%==n MKDIR %~dp0venv
IF %pypy%==n %path% -m venv %~dp0venv
IF %pypy%==y MKDIR %~dp0pypyvenv
IF %pypy%==y %path% -m venv %~dp0pypyvenv
ECHO Appending Development Directory to PYTHONPATH ...
IF %pypy%==n > %~dp0venv\Lib\site-packages\pygase.pth ECHO %~dp0pygase\
IF %pypy%==y > %~dp0pypyvenv\site-packages\pygase.pth ECHO %~dp0pygase\
ECHO ##################################
ECHO Installing Dependencies ...
ECHO ##################################
IF %pypy%==n %~dp0venv\Scripts\python.exe -m pip install --upgrade pip
IF %pypy%==n %~dp0venv\Scripts\python.exe -m pip install --upgrade setuptools
IF %pypy%==n %~dp0venv\Scripts\python.exe -m pip install -r %~dp0dev-requirements.txt
IF %pypy%==n %~dp0pypyvenv\Scripts\pypy3.exe -m pip install --upgrade pip
IF %pypy%==n %~dp0pypyvenv\Scripts\pypy3.exe -m pip install --upgrade setuptools
IF %pypy%==n %~dp0pypyvenv\Scripts\pypy3.exe -m pip install -r %~dp0dev-requirements.txt
ECHO ##################################
ECHO Dev Setup completed.
ECHO Use .\venv environment for testing
ECHO and development.
ECHO ##################################
PAUSE