"""
抄袭检测引擎：AST指纹 + 序列比对
"""
import ast
import difflib
from .ast_fingerprint import ASTFingerprint
import numpy as np

class PlagiarismDetector:
    def __init__(self):
        self.fingerprinter = ASTFingerprint()

    def tokenize(self, code: str) -> list:
        """将代码转为token序列（简单按空格/换行分词）"""
        import re
        # 分割标识符、数字、运算符等
        tokens = re.findall(r'[a-zA-Z_]\w*|\d+|==|!=|<=|>=|[+\-*/%=<>]', code)
        return tokens

    def sequence_similarity(self, code1: str, code2: str) -> float:
        """计算两段代码的token序列相似度"""
        tokens1 = self.tokenize(code1)
        tokens2 = self.tokenize(code2)
        if not tokens1 or not tokens2:
            return 0.0
        matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
        return matcher.ratio()

    def structural_similarity(self, code1: str, code2: str) -> float:
        """基于AST指纹的相似度（相同为1.0，不同为0.0，可扩展为树编辑距离）"""
        fp1 = self.fingerprinter.extract(code1)
        fp2 = self.fingerprinter.extract(code2)
        # 简化：指纹相同视为高度相似，否则计算Jaccard（可扩展）
        if fp1 == fp2:
            return 1.0
        # 对于不同指纹，我们根据token序列的粗略结构再判断
        # 这里直接返回0，实际可以结合更多特征
        return 0.0

    def combined_similarity(self, code1: str, code2: str) -> float:
        """综合相似度"""
        struct_sim = self.structural_similarity(code1, code2)
        seq_sim = self.sequence_similarity(code1, code2)
        # 如果结构完全相同，相似度至少0.8
        if struct_sim > 0.9:
            return 0.8 + 0.2 * seq_sim
        # 否则以序列相似度为主
        return seq_sim * 0.9

    def detect(self, student_codes: dict) -> dict:
        """
        批量检测抄袭
        student_codes: {学生姓名: 代码字符串}
        返回: {
            "similarity_matrix": 二维列表 (学生名, 相似度),
            "pairs_above_threshold": [(学生A, 学生B, 相似度), ...]
        }
        """
        names = list(student_codes.keys())
        n = len(names)
        similarity_matrix = np.zeros((n, n))
        pairs = []

        for i in range(n):
            for j in range(i+1, n):
                sim = self.combined_similarity(
                    student_codes[names[i]], student_codes[names[j]]
                )
                similarity_matrix[i][j] = sim
                similarity_matrix[j][i] = sim
                if sim > 0.7:  # 阈值
                    pairs.append((names[i], names[j], round(sim, 3)))

        return {
            "names": names,
            "matrix": similarity_matrix.tolist(),
            "suspicious_pairs": sorted(pairs, key=lambda x: x[2], reverse=True)
        }