# src/languages/python_parser.py
from .base_parser import BaseLanguageParser
import ast

class PythonParser(BaseLanguageParser):
    def check_syntax(self, code: str) -> dict:
        errors = []
        try:
            compile(code, '<student_code>', 'exec')
        except SyntaxError as e:
            errors.append({
                "line": e.lineno or 0,
                "type": "语法错误",
                "reason": str(e.msg)
            })
        return {"has_error": len(errors) > 0, "errors": errors}

    def extract_structure(self, code: str) -> dict:
        try:
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            return {"functions": functions, "classes": classes}
        except:
            return {"functions": [], "classes": []}

    def get_sandbox_image(self) -> str:
        return "python:3.10-slim"

    def get_execution_command(self, filename: str) -> str:
        return f"python /code/{filename}"