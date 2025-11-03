@echo off

set PYTHON_EXE=
for /f "usebackq delims=" %%P in (`install-deps.bat --check-nogui`) do (
	set "PYTHON_EXE=%%P"
)

if not defined PYTHON_EXE (
	echo Missing dependencies. Please run script install-deps.bat
	exit /b 1
)

set PYTHONDONTWRITEBYTECODE=1

"%PYTHON_EXE%" sokodun %*
