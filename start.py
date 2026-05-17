import subprocess
import webbrowser
import time
import sys

URL = "http://127.0.0.1:8000"

if __name__ == "__main__":
    print("Starting Job Market Tracker...")
    # Start uvicorn as a child process using the same Python interpreter that ran this script
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--reload"])
    time.sleep(1.5)      # give uvicorn a moment to boot before opening the browser
    webbrowser.open(URL) # opens the default browser — works on macOS, Windows, and Linux
    try:
        server.wait()    # keep the script alive while the server runs
    except KeyboardInterrupt:
        server.terminate()
        print("\nServer stopped.")
