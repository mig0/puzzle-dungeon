@echo off
setlocal EnableDelayedExpansion

rem Special --check mode for external use
if "%~1" == "--check" (
	call :check_symlinks         >nul || exit /b 1
	call :check_installed_python >nul || exit /b 1
	call :check_python_modules   >nul || exit /b 1
	echo !PGZRUN_EXE!
	exit /b 0
)

rem Normal mode, install dependencies if needed
call :check_symlinks                                             || exit /b 1
call :check_installed_python || call :need_python_install        || exit /b 1
call :check_python_modules   || call :need_python_module_install || exit /b 1

echo.
echo All dependencies are present. Run dungeon.bat
exit /b 0

rem ================================================================
:need_python_install

set "PYTHON_VER=3.13.4"
echo No good Python found. Attempting to download and install Python %PYTHON_VER%...

rem Detect architecture
set "ARCH_SUFFIX="
if defined ProgramFiles(x86) (
	rem 64-bit Windows or ARM64
	reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PROCESSOR_ARCHITECTURE | find /i "ARM64" >nul && (
		set "ARCH_SUFFIX=-arm64"
	) || (
		set "ARCH_SUFFIX=-amd64"
	)
) else (
	rem 32-bit Windows
	set "ARCH_SUFFIX="
)

set "PYTHON_INSTALLER=python-!PYTHON_VER!!ARCH_SUFFIX!.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/!PYTHON_VER!/!PYTHON_INSTALLER!"

echo Downloading Python !PYTHON_VER! from this URL:
echo   !PYTHON_URL!
curl -L -A "Mozilla/5.0" -o "!PYTHON_INSTALLER!" "!PYTHON_URL!"

if not exist "!PYTHON_INSTALLER!" (
	echo ERROR: Failed to download Python installer
	exit /b 1
)

for %%F in ("!PYTHON_INSTALLER!") do echo Downloaded file size: %%~zF bytes

echo.
echo Running silent installer...
echo Please confirm the User Account Control (UAC) prompt in a separate window
echo After Pressing Yes button please wait for about a minute
start /wait "" "!PYTHON_INSTALLER!" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

rem Give time to update PATH if running as administrator
timeout /t 3 >nul
del "!PYTHON_INSTALLER!"
echo.

call :check_installed_python && goto :eof
echo ERROR: Python installer failed or Python not found after install
exit /b 1

rem ================================================================
:need_python_module_install

echo Installing required modules...
"!PYTHON_EXE!" -m pip install pygame pgzero bitarray PyYAML

if !errorlevel! neq 0 (
	echo ERROR: Failed to install required python modules
	exit /b 1
)

call :check_python_modules || exit /b 1

echo Dependent python modules were successfully installed
goto :eof

rem ================================================================
:check_symlinks
rem Smoke test for broken symlink (file with small size)
for %%F in ("images\default\char.png") do set "file_size=%%~zF"
if %file_size% GTR 0 if %file_size% LSS 555 (
	echo Seems you miss proper symbolic links.
	echo You may possibly lose them on unzip or on git clone.
	echo Try to unzip as Administrator.
	echo If you use Git Bash, run it as Administrator and execute these commands:
	echo 	export MSYS=winsymlinks:nativestrict
	echo 	git config --local core.symlinks true
	echo 	git checkout .
	exit /b 1
)
goto :eof

rem ================================================================
:check_installed_python
set MIN_PY_MAJOR=3
set MIN_PY_MINOR=10

set "PYTHON_IN_PATH_DIR="

rem Check whether python.exe is in PATH
for /f "delims=" %%P in ('where python.exe 2^>^nul') do (
	set "PYTHON_IN_PATH_DIR=%%~dpP"
	set "PYTHON_IN_PATH_DIR=!PYTHON_IN_PATH_DIR:~0,-1!"
	rem echo Found python.exe in PATH directory !PYTHON_IN_PATH_DIR!
	goto check_python_in_path_and_common_locations
)

echo "No python.exe in PATH"

rem Check python in common install locations
:check_python_in_path_and_common_locations
for /d %%D in (
	!PYTHON_IN_PATH_DIR!
	"%UserProfile%\AppData\Roaming\Python\Python*"
	"%LocalAppData%\Programs\Python\Python*"
	"%ProgramFiles%\Python*"
	"%ProgramFiles(x86)%\Python*"
) do (
	set "PYTHON_DIR=%%D"
	set "PYTHON_EXE=!PYTHON_DIR!\python.exe"
	if exist "!PYTHON_EXE!" (
		rem echo Checking !PYTHON_EXE!
		for %%P in ("!PYTHON_EXE!") do (
			if %%~zP gtr 0 (
				"!PYTHON_EXE!" -c "import sys; exit(not sys.version_info >= (!MIN_PY_MAJOR!, !MIN_PY_MINOR!))" 2>nul && (
					goto :check_python_version
				)
				echo Ignoring python.exe in "!PYTHON_DIR!" failing ^>^=!MIN_PY_MAJOR!.!MIN_PY_MINOR! requirement
			) else (
				echo Ignoring broken python.exe stub in "!PYTHON_DIR!"
			)
		)
	)
)

echo No good Python in PATH and in common locations
set "PYTHON_EXE="
exit /b 1

rem Already checked, but check again for safety and a nice print
:check_python_version
for /f "tokens=2" %%V in ('"!PYTHON_EXE!" --version 2^>^nul') do (
	for /f "tokens=1,2 delims=." %%a in ("%%V") do (
		set "PY_MAJOR=%%a"
		set "PY_MINOR=%%b"
	)
)

if not defined PY_MAJOR goto :bad_python_version
if !PY_MAJOR! LSS !MIN_PY_MAJOR! goto :bad_python_version
if !PY_MAJOR! == !MIN_PY_MAJOR! if !PY_MINOR! LSS !MIN_PY_MINOR! goto :bad_python_version

echo Python !PY_MAJOR!.!PY_MINOR! is installed and meets version requirement
echo Going to use python at !PYTHON_EXE!
goto :eof

:bad_python_version
echo "Found python !PYTHON_EXE! is old version (!PY_MAJOR!.!PY_MINOR!). Need to update"
set "PYTHON_EXE="
exit /b 1

rem ================================================================
:check_python_modules

"!PYTHON_EXE!" -c "import pygame, pgzero, bitarray, yaml" >nul 2>&1
if !errorlevel! NEQ 0 (
	echo Required python modules ^(pygame, pgzero, bitarray, yaml^) failed
	exit /b 1
)

echo All required python modules seem to be present

rem Try to find pgzrun.exe
set "PGZRUN_EXE="
for %%P in (!PYTHON_EXE!) do (
	set "PYTHON_DIR=%%~dpP"
	set "PYTHON_DIR=!PYTHON_DIR:~0,-1!"
	if exist "!PYTHON_DIR!\Scripts\pgzrun.exe" (
		set "PGZRUN_EXE=!PYTHON_DIR!\Scripts\pgzrun.exe"
		echo Going to use pgzrun at !PGZRUN_EXE!
		goto :eof
	)
)

echo Error: pgzrun.exe not found inside python installation
exit /b 1

