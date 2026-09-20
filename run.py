import subprocess
import sys

def main():
    print("Starting FastAPI Backend on port 8000...")
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.api:app", "--reload", "--port", "8000"])
    
    print("Starting Streamlit Frontend...")
    frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
    
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("Servers stopped.")

if __name__ == "__main__":
    main()
