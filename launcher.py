import os
import sys
import time
import logging
import threading
import webbrowser
from pathlib import Path
import multiprocessing

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )

def run_backend():
    try:
        from uvicorn.main import run
        from backend.main import app
        run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        logging.error(f"Backend Error: {e}")
        sys.exit(1)

def run_frontend():
    try:
        # Use the bundled frontend build
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        os.chdir(os.path.join(os.path.dirname(__file__), 'frontend', 'build'))
        httpd = HTTPServer(('127.0.0.1', 3000), SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"Frontend Error: {e}")
        sys.exit(1)

def open_browser():
    # Wait for servers to start
    time.sleep(3)
    # Only open one browser window
    webbrowser.open('http://localhost:3000', new=2, autoraise=True)

def main():
    setup_logging()
    logging.info("Starting Text2SQL Application...")

    # Start backend in a separate process
    backend_process = multiprocessing.Process(target=run_backend)
    backend_process.start()

    # Start frontend in a separate process
    frontend_process = multiprocessing.Process(target=run_frontend)
    frontend_process.start()

    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        backend_process.join()
        frontend_process.join()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()