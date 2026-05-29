import sys
import os

sys.path.insert(0, '.')

print("Testing basic imports...")

try:
    from app.main import app
    print("✓ app.main imported successfully")
except Exception as e:
    print(f"✗ Failed to import app.main: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed")