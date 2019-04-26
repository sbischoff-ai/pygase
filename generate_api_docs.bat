@ECHO off
ECHO Make sure CPython .venv exists.
ECHO Doc generation doesn't work with PyPy.
PAUSE
ECHO ##################################
ECHO Generating Markdown files ...
ECHO ##################################
.\.venv\Scripts\pydocmd.exe simple pygase+ pygase.client++ > .\docs\api\pygase.client.md
.\.venv\Scripts\pydocmd.exe simple pygase+ pygase.connection++ > .\docs\api\pygase.connection.md
.\.venv\Scripts\pydocmd.exe simple pygase+ pygase.server++ > .\docs\api\pygase.server.md
.\.venv\Scripts\pydocmd.exe simple pygase+ pygase.event++ > .\docs\api\pygase.event.md
.\.venv\Scripts\pydocmd.exe simple pygase+ pygase.gamestate++ > .\docs\api\pygase.gamestate.md
.\.venv\Scripts\pydocmd.exe simple pygase+ pygase.utils++ > .\docs\api\pygase.utils.md
ECHO ##################################
ECHO Doc generation completed.
ECHO Remember: If you add a new module
ECHO    you must add it to this script!
ECHO ##################################
PAUSE