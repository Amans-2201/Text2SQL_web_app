import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def clean_dist():
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

def build_exe():
    # Clean previous builds
    clean_dist()
    
    # Build frontend first
    os.system("cd frontend && npm run build")
    
    PyInstaller.__main__.run([
        'launcher.py',
        '--name=Text2SQL',
        '--onedir',
        '--windowed',
        '--icon=frontend/public/favicon.ico',
        '--add-data=frontend/build;frontend/build',
        '--add-data=backend;backend',
        '--add-data=app_config.json;.',
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--hidden-import=google.generativeai',
        '--collect-all=fastapi',
        '--collect-all=starlette',
        '--collect-all=google.generativeai',
    ])

if __name__ == "__main__":
    build_exe()