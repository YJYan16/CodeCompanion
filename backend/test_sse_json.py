import json

def sse_json_dumps(obj):
    """SSE 响应的 JSON 序列化，使用标准 json 库以支持 ensure_ascii=False"""
    return json.dumps(obj, ensure_ascii=False)

# Test the function
result = sse_json_dumps({'type': 'test', 'content': 'Hello 世界'})
print(f"Result: {result}")
assert 'Hello 世界' in result, "Unicode should be preserved"
print("Test passed!")