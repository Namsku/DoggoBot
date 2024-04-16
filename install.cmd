@echo off

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python is not installed.
        echo Please install Python from https://www.python.org/downloads/ and rerun this script.
        exit /b 1
    ) 
)

:: Check for Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not installed.
    echo Please install Git from https://git-scm.com/downloads and rerun this script.
    exit /b 1
)

:: Install virtualenv
py -m pip install virtualenv
if %errorlevel% neq 0 (
    echo Failed to install virtualenv.
    exit /b 1
)

:: Create a virtual environment
py -m virtualenv venv
if %errorlevel% neq 0 (
    echo Failed to create a virtual environment.
    exit /b 1
)

:: Activate the virtual environment
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate the virtual environment.
    exit /b 1
)

:: Install requirements
py -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    exit /b 1
)

py -m pip install -U git+https://github.com/PythonistaGuild/twitchio.git@fix/routines --force-reinstall 
echo All requirements installed successfully.