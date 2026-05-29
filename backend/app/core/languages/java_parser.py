# src/languages/java_parser.py
from .base_parser import BaseLanguageParser
import subprocess
import tempfile
import os
import re

class JavaParser(BaseLanguageParser):
    def check_syntax(self, code: str) -> dict:
        errors = []
        # 确保类名与文件名一致（临时文件使用 Main.java）
        tmpdir = tempfile.mkdtemp()
        filepath = os.path.join(tmpdir, "Main.java")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            result = subprocess.run(
                ["javac", filepath],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                # 解析 javac 错误输出
                for line in result.stderr.split('\n'):
                    match = re.search(r'Main\.java:(\d+):', line)
                    if match:
                        errors.append({
                            "line": int(match.group(1)),
                            "type": "编译错误",
                            "reason": line.strip()
                        })
        except FileNotFoundError:
            errors.append({
                "line": 0,
                "type": "环境错误",
                "reason": "未安装 JDK，无法编译 Java 代码"
            })
        except Exception as e:
            errors.append({"line": 0, "type": "未知错误", "reason": str(e)})
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        return {"has_error": len(errors) > 0, "errors": errors}

    def extract_structure(self, code: str) -> dict:
        class_pattern = re.findall(r'class\s+(\w+)', code)
        method_pattern = re.findall(r'(public|private|protected)?\s+\w+\s+(\w+)\s*\(', code)
        return {
            "classes": class_pattern,
            "methods": [m[1] for m in method_pattern]
        }

    def get_sandbox_image(self) -> str:
        return "openjdk:11-jdk-slim"

    def get_execution_command(self, filename: str) -> str:
        classname = filename.replace(".java", "")
        return f"cd /code && javac {filename} && java {classname}"