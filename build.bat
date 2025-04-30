@echo off
setlocal enabledelayedexpansion
echo Building Text2SQL Application...

:: Set project root directory
set "PROJECT_ROOT=%~dp0"
cd "%PROJECT_ROOT%"

:: Remove existing venv if exists
if exist venv (
    rmdir /s /q venv
)

:: Create fresh virtual environment
python -m venv venv --clear

:: Activate virtual environment
call venv\Scripts\activate.bat

q:: Install dependencies in specific order
python -m pip install --upgrade pip wheel setuptools

:: Install psycopg2 alternative
pip uninstall -y psycopg2-binary
pip install --no-cache-dir psycopg2-binary==2.8.6

:: Install PyInstaller first
pip install --no-cache-dir PyInstaller==4.5.1

:: Install other requirements
pip install -r requirements.txt

:: Verify PyInstaller installation
python -c "import PyInstaller" || (
    echo PyInstaller installation failed
    exit /b 1
)

:: Build frontend
if exist frontend (
    cd frontend
    call npm install
    call npm run build
    cd ..
)

:: Build executable with explicit Python path
python build_exe.py

echo Build complete! Executable is in dist/Text2SQL
pause

deactivate