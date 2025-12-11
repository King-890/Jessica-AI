import os
import sys

def main():
    print("🛑 Stopping all Jessica AI processes...")
    # Force kill all python.exe instances
    # /T = Tree (child processes)
    # /F = Force
    os.system("taskkill /F /IM python.exe /T")

if __name__ == "__main__":
    main()
