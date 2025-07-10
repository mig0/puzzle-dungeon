@echo off
setlocal EnableDelayedExpansion

rem Special --check mode for external use
if "%~1" == "--check" (
	call :check_installed_python >nul || exit /b 1
	call :check_python_modules   >nul || exit /b 1
	echo !PGZRUN_EXE!
	exit /b 0
)

rem Normal mode, install dependencies if needed
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
"!PYTHON_EXE!" -m pip install pygame pgzero bitarray

if !errorlevel! neq 0 (
	echo ERROR: Failed to install required python modules
	exit /b 1
)

call :check_python_modules || exit /b 1

echo Dependent python modules were successfully installed
goto :eof

rem ================================================================
:check_installed_python
set "PYTHON_EXE="

rem Check if python.exe in PATH and is not broken
for /f "delims=" %%P in ('where python 2^>nul') do (
	set "CANDIDATE=%%P"
	if exist "!CANDIDATE!" (
		for %%F in ("!CANDIDATE!") do (
			if %%~zF gtr 0 (
				set "PYTHON_EXE=!CANDIDATE!"
				goto :check_python_version
			) else (
				echo Ignoring broken python.exe stub at !CANDIDATE!
			)
		)
	)
)

echo No Python in PATH, checking it in common locations

rem Check common install locations
for /d %%D in (
	"%ProgramFiles(x86)%\Python*"
	"%LocalAppData%\Programs\Python\Python*"
	"%ProgramFiles%\Python*"
) do (
	if exist "%%D\python.exe" (
		set "PYTHON_EXE=%%D\python.exe"
		goto :check_python_version
	)
)

echo No Python in common locations
exit /b 1

:check_python_version
for /f "tokens=2" %%V in ('"!PYTHON_EXE!" --version 2^>^&1') do (
	for /f "tokens=1,2 delims=." %%a in ("%%V") do (
		set "PY_MAJOR=%%a"
		set "PY_MINOR=%%b"
	)
)

if not defined PY_MAJOR goto :bad_python_version

if !PY_MAJOR! LSS 3 goto :bad_python_version
if !PY_MAJOR! == 3 if !PY_MINOR! LSS 10 goto :bad_python_version

echo Python !PY_MAJOR!.!PY_MINOR! is installed and meets version requirement
goto :eof

:bad_python_version
echo Found python %PYTHON_EXE% is old version (%PY_MAJOR%.%PY_MINOR%). Need to update
set "PYTHON_EXE="
exit /b 1

rem ================================================================
:check_python_modules

"!PYTHON_EXE!" -c "import pygame, pgzero, bitarray" 2>nul
if !errorlevel! NEQ 0 (
	echo Required python modules ^(pygame, pgzero, bitarray^) failed
	exit /b 1
)

echo All required python modules seem to be present

rem Try to find pgzrun.exe
set "PGZRUN_EXE="
for /d %%D in (
	"%UserProfile%\AppData\Roaming\Python\Python!PY_MAJOR!!PY_MINOR!*"
	"%LocalAppData%\Programs\Python\Python!PY_MAJOR!!PY_MINOR!*"
	"%ProgramFiles%\Python!PY_MAJOR!!PY_MINOR!*"
	"%ProgramFiles(x86)%\Python!PY_MAJOR!!PY_MINOR!*"
) do (
	if exist "%%D\Scripts\pgzrun.exe" (
		set PGZRUN_EXE=%%~D\Scripts\pgzrun.exe
		echo Found pgzrun.exe at: !PGZRUN_EXE!
		goto :eof
	)
)

echo Error: pgzrun.exe not found inside python installation
exit /b 1

