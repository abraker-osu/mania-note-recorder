:: Description
::   Builds the project
::
:: Usage
::   > scripts\build.bat
@echo off

if NOT EXIST "venv_win" (
    echo No venv found
    EXIT /B 1
)

call "venv_win\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment
    EXIT /B 1
)

if "%VIRTUAL_ENV%" == "" (
    echo Virtual environment not active
    EXIT /B 1
)

call "$~dp0\clean.bat"

:: Build exe
del /s "dist\osu-note-recorder.exe" >nul 2>&1
pyinstaller -y "build.spec"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to build exe
    EXIT /B 1
)

:: Generate version file to set exe version
del /s "data\version.txt" >nul 2>&1
python "scripts\helper\gen_ver.py"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to generate version file
    EXIT /B 1
)

:: Set exe version (shown in file properties metadata)
pyi-set_version "data\version.txt" "dist\osu-note-recorder.exe"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to set version to exe
    EXIT /B 1
)

echo [ DONE ]
EXIT /B 0
