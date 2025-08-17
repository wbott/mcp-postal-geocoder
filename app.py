# This is the entry point for HuggingFace Spaces
# It simply imports and runs the main Streamlit app
import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true", "--server.port", "7860"])