@echo off

set PGZRUN_EXE=
for /f "usebackq delims=" %%P in (`install-deps.bat --check`) do (
	set "PGZRUN_EXE=%%P"
)

if not defined PGZRUN_EXE (
	echo Missing dependencies. Please run script install-deps.bat
	exit /b 1
)

set PYGAME_HIDE_SUPPORT_PROMPT=1
set PYTHONDONTWRITEBYTECODE=1

set CMD_ARGS=
:build_args
if "%~1" == "" goto after_args
set "ARG=%~1"
set "ARG=%ARG:"=""%"
set "CMD_ARGS=%CMD_ARGS% "%ARG%""
shift
goto build_args
:after_args

"%PGZRUN_EXE%" main.py
