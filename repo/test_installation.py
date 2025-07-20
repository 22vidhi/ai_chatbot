import sys
import os
from pathlib import Path

def test_basic():
    print("Testing basic Python functionality...")
    
    # Test imports
    try:
        import json
        import sqlite3
        import re
        print("Basic imports: OK")
    except ImportError as e:
        print(f"Basic imports failed: {e}")
        return False
    
    # Test file structure
    required_files = ["app.py", "requirements.txt", "README.md"]
    for file in required_files:
        if not Path(file).exists():
            print(f"Missing file: {file}")
            return False
    
    print("File structure: OK")
    
    # Test directories
    required_dirs = ["src", "models", "data", "database"]
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"Missing directory: {dir_name}")
            return False
    
    print("Directory structure: OK")
    return True

if __name__ == "__main__":
    print("Smart Invoice AI System - Basic Test")
    print("=" * 40)
    
    if test_basic():
        print("All basic tests passed!")
        print("Run: streamlit run app.py")
    else:
        print("Some tests failed.")

