import sys
import os

# Add parent directory to path so we can import from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_imports():
    print("Checking imports...")
    try:
        import flask
        print("✓ flask")
        import flask_cors
        print("✓ flask_cors")
        import pandas
        print("✓ pandas")
        import numpy
        print("✓ numpy")
        import nflreadpy
        print("✓ nflreadpy")
        import requests
        print("✓ requests")
        import plotly
        print("✓ plotly")
        print("\n✓ All imports successful!")
        return True
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False

def check_local_modules():
    print("\nChecking local modules...")
    try:
        from src.data_fetcher import get_available_seasons
        print("✓ src.data_fetcher imported")
        from src.config import FANTASY_SCORING
        print("✓ src.config imported")
        print("\n✓ All local modules imported successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Local module import failed: {e}")
        return False

def check_nflreadpy():
    print("\nChecking nflreadpy connection (smoke test)...")
    try:
        from src.data_fetcher import get_available_seasons
        seasons = get_available_seasons()
        if seasons and len(seasons) > 0:
            print(f"✓ Successfully fetched {len(seasons)} seasons")
            return True
        else:
            print("❌ Fetched seasons list is empty")
            return False
    except Exception as e:
        print(f"\n❌ nflreadpy check failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting setup verification...\n")
    
    if check_imports() and check_local_modules() and check_nflreadpy():
        print("\n✓ All core tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Setup verification failed!")
        sys.exit(1)
