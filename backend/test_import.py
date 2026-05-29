import sys
import os

sys.path.insert(0, '.')

try:
    print("Step 1: Importing from app.main...")
    from app.main import app
    print("Step 1: Success")
    
    print("\nStep 2: Testing API endpoints...")
    from app.api.endpoints import router
    print("Step 2: Success")
    
    print("\nStep 3: Testing Coordinator import...")
    from backend.app.core.agents import Coordinator
    print("Step 3: Success")
    
    print("\nAll imports successful!")
    
except Exception as e:
    import traceback
    print("\nError occurred:", str(e))
    traceback.print_exc()