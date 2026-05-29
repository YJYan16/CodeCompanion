"""
AST（抽象语法树）指纹提取
"""
import ast
import hashlib

class ASTFingerprint:
    @staticmethod
    def extract(code: str) -> str:
        """
        提取代码的AST结构指纹
        忽略变量名、字符串字面量、注释等，只保留语法结构
        """
        try:
            tree = ast.parse(code)
            # 自定义访问器，将AST节点转换为结构字符串
            fingerprint = ASTFingerprint._node_to_str(tree)
            # 生成哈希缩短指纹
            return hashlib.md5(fingerprint.encode()).hexdigest()[:12]
        except SyntaxError:
            # 语法错误的代码，用原始代码的哈希代替
            return hashlib.md5(code.encode()).hexdigest()[:12]

    @staticmethod
    def _node_to_str(node, level=0) -> str:
        """递归将AST节点转为结构描述字符串"""
        if isinstance(node, ast.AST):
            node_type = type(node).__name__
            parts = [node_type]
            for field, value in ast.iter_fields(node):
                if isinstance(value, str):
                    # 忽略具体的字符串值，用占位符
                    parts.append("STR")
                elif isinstance(value, (int, float)):
                    parts.append("NUM")
                elif isinstance(value, list):
                    parts.append("[" + ",".join(ASTFingerprint._node_to_str(v, level+1) for v in value) + "]")
                elif value is None:
                    parts.append("None")
                else:
                    parts.append(ASTFingerprint._node_to_str(value, level+1))
            return "(" + " ".join(parts) + ")"
        return "LEAF"
