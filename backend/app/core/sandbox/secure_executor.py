from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Eval import default_guarded_getitem
from RestrictedPython.Guards import full_write_guard, safer_getattr
from RestrictedPython.PrintCollector import PrintCollector


class SecureExecutor:
    def __init__(self):
        self.max_execution_time = 5
        self.max_output_length = 10000

    def _build_globals(self):
        return {
            "__builtins__": safe_builtins,
            "_getitem_": default_guarded_getitem,
            "_getattr_": safer_getattr,
            "_write_": full_write_guard,
            "_print_": PrintCollector,
            "_getiter_": iter,
            "__name__": "__main__",
        }

    def execute_python(self, code: str) -> dict:
        try:
            byte_code = compile_restricted(code, filename="<restricted>", mode="exec")
        except SyntaxError as e:
            return {"success": False, "error": f"语法错误: {e.msg} (行 {e.lineno})", "output": ""}
        except Exception as e:
            return {"success": False, "error": f"编译错误: {str(e)}", "output": ""}

        restricted_globals = self._build_globals()

        try:
            exec(byte_code, restricted_globals)

            printed = restricted_globals.get("_print", None)
            if printed is not None:
                output = str(printed()) if callable(printed) else str(printed)
            else:
                output = ""

            if len(output) > self.max_output_length:
                output = output[: self.max_output_length] + "..."

            return {"success": True, "output": output, "error": ""}
        except TimeoutError:
            return {"success": False, "error": "执行超时", "output": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}
