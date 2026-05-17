import subprocess
import webbrowser
import time
import sys

from pipeline.run import run_pipeline

URL = "http://127.0.0.1:8000"

if __name__ == "__main__":
    # Run the full ETL pipeline first, then launch the dashboard
    run_pipeline()

    print("\nStarting server...")
    # Start uvicorn as a child process using the same Python interpreter
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--reload"])
    time.sleep(1.5)      # give uvicorn a moment to boot
    webbrowser.open(URL) # opens the default browser, cross-platform
    try:
        server.wait()
    except KeyboardInterrupt:
        server.terminate()
        print("\nServer stopped.")
