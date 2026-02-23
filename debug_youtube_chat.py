import subprocess
import sys
import os

# This script attempts to run src/youtube_chat.py and prints detailed debug info.
def main():
    script_path = os.path.join(os.path.dirname(__file__), 'src', 'youtube_chat.py')
    print(f"Running: {sys.executable} {script_path}")
    result = subprocess.run([
        sys.executable,
        script_path
    ], capture_output=True, text=True)
    print("Return code:", result.returncode)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    if result.returncode != 0:
        print("Error detected. Check STDERR above.")
    else:
        print("Script executed successfully.")

if __name__ == "__main__":
    main()
