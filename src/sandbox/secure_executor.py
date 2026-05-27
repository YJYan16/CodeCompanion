from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Eval import default_guarded_getitem
from RestrictedPython.Guards import full_write_guard
import ast
import sys

class SecureExecutor:
    def __init__(self):
        self.max_execution_time = 5
        self.max_output_length = 10000
        
    def _build_globals(self):
        restricted_globals = {
            '__builtins__': {
                **safe_builtins,
                'print': self._safe_print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'round': round,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'sorted': sorted,
                'reversed': reversed,
                'True': True,
                'False': False,
                'None': None,
            },
            '_getitem_': default_guarded_getitem,
            '_write_': full_write_guard,
        }
        return restricted_globals
    
    def _safe_print(self, *args, **kwargs):
        if hasattr(self, '_output_buffer'):
            self._output_buffer.append(' '.join(str(arg) for arg in args))
    
    def execute_python(self, code: str) -> dict:
        """安全执行Python代码"""
        try:
            byte_code = compile_restricted(
                code,
                filename='<restricted>',
                mode='exec'
            )
        except SyntaxError as e:
            return {"success": False, "error": f"语法错误: {e.msg} (行 {e.lineno})", "output": ""}
        except Exception as e:
            return {"success": False, "error": f"编译错误: {str(e)}", "output": ""}
        
        self._output_buffer = []
        
        try:
            exec(byte_code, self._build_globals(), {})
            
            output = '\n'.join(self._output_buffer)
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + '...'
            
            return {"success": True, "output": output, "error": ""}
            
        except TimeoutError:
            return {"success": False, "error": "执行超时", "output": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": '\n'.join(self._output_buffer)}