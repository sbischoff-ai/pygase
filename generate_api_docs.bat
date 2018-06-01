@ECHO off
ECHO Make sure CPython venv exists.
ECHO Doc generation doesn't work with PyPy.
PAUSE
ECHO ##################################
ECHO Generating Markdown files ...
ECHO ##################################
.\venv\Scripts\pydocmd.exe simple pygase+ pygase.client++ > .\docs\api\pygase.client.md
.\venv\Scripts\pydocmd.exe simple pygase+ pygase.shared++ > .\docs\api\pygase.shared.md
.\venv\Scripts\pydocmd.exe simple pygase+ pygase.server++ > .\docs\api\pygase.server.md
ECHO ##################################
ECHO Doc generation completed.
ECHO Remember: If you add a new module
ECHO    you must add it to this script!
ECHO ##################################
PAUSE