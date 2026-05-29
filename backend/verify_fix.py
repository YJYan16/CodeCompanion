import sys
import os

sys.path.insert(0, '.')
os.chdir(r'E:\CodeCompanion\backend')

try:
    print("Testing imports...")
    from app.api import endpoints
    print("endpoints imported successfully")

    # Test the sse_json_dumps function
    result = endpoints.sse_json_dumps({'type': 'test', 'content': 'Hello 世界'})
    print(f"sse_json_dumps result: {result}")

    print("\nAll tests passed!")
except Exception as e:
    import traceback
    print(f"\nError: {e}")
    traceback.print_exc()