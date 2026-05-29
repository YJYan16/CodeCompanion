# src/languages/base_parser.py
from abc import ABC, abstractmethod

class BaseLanguageParser(ABC):
    """编程语言解析器抽象基类"""

    @abstractmethod
    def check_syntax(self, code: str) -> dict:
        """检查语法错误，返回 {has_error: bool, errors: list}"""
        pass

    @abstractmethod
    def extract_structure(self, code: str) -> dict:
        """提取代码结构（函数名、类名、关键调用等）"""
        pass

    @abstractmethod
    def get_sandbox_image(self) -> str:
        """返回 Docker 镜像名称"""
        pass

    @abstractmethod
    def get_execution_command(self, filename: str) -> str:
        """返回在沙箱中执行代码的命令"""
        pass