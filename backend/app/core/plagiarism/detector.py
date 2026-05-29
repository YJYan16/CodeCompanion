import ast
import difflib
from .ast_fingerprint import ASTFingerprint
import numpy as np
from collections import Counter

class PlagiarismDetector:
    def __init__(self):
        self.fingerprinter = ASTFingerprint()

    def tokenize(self, code: str) -> list:
        import re
        tokens = re.findall(r'[a-zA-Z_]\w*|\d+|==|!=|<=|>=|[+\-*/%=<>]|[\{\}\[\]\(\),.:]', code)
        return tokens

    def sequence_similarity(self, code1: str, code2: str) -> float:
        tokens1 = self.tokenize(code1)
        tokens2 = self.tokenize(code2)
        if not tokens1 or not tokens2:
            return 0.0
        matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
        return matcher.ratio()

    def _ast_to_structure(self, tree: ast.AST) -> list:
        """将AST转换为结构化表示"""
        structure = []
        for node in ast.walk(tree):
            node_type = type(node).__name__
            if node_type in ['FunctionDef', 'ClassDef']:
                structure.append(f"{node_type}:{node.name}")
            elif node_type in ['If', 'For', 'While', 'Return', 'Assign']:
                structure.append(node_type)
        return structure

    def structural_similarity(self, code1: str, code2: str) -> float:
        """基于AST结构的相似度"""
        try:
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)
        except SyntaxError:
            return 0.0
        
        struct1 = self._ast_to_structure(tree1)
        struct2 = self._ast_to_structure(tree2)
        
        if not struct1 or not struct2:
            return 0.0
        
        set1, set2 = set(struct1), set(struct2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        matcher = difflib.SequenceMatcher(None, struct1, struct2)
        seq_sim = matcher.ratio()
        
        return (jaccard + seq_sim) / 2.0

    def _extract_features(self, code: str) -> dict:
        """提取代码特征"""
        features = {
            'line_count': code.count('\n') + 1,
            'func_count': 0,
            'class_count': 0,
            'if_count': 0,
            'loop_count': 0,
            'var_names': [],
            'func_names': [],
        }
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    features['func_count'] += 1
                    features['func_names'].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    features['class_count'] += 1
                elif isinstance(node, ast.If):
                    features['if_count'] += 1
                elif isinstance(node, (ast.For, ast.While)):
                    features['loop_count'] += 1
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    features['var_names'].append(node.id)
        except SyntaxError:
            pass
        
        return features

    def feature_similarity(self, code1: str, code2: str) -> float:
        """基于代码特征的相似度"""
        features1 = self._extract_features(code1)
        features2 = self._extract_features(code2)
        
        score = 0.0
        total = 0
        
        numeric_features = ['line_count', 'func_count', 'class_count', 'if_count', 'loop_count']
        for feat in numeric_features:
            v1, v2 = features1[feat], features2[feat]
            if v1 + v2 > 0:
                score += 1.0 - abs(v1 - v2) / max(v1, v2)
                total += 1
        
        var_sim = self._jaccard_similarity(features1['var_names'], features2['var_names'])
        score += var_sim
        total += 1
        
        func_sim = self._jaccard_similarity(features1['func_names'], features2['func_names'])
        score += func_sim
        total += 1
        
        return score / total if total > 0 else 0.0

    def _jaccard_similarity(self, list1: list, list2: list) -> float:
        """计算Jaccard相似度"""
        set1, set2 = set(list1), set(list2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def combined_similarity(self, code1: str, code2: str) -> float:
        """综合相似度：结构相似度(40%) + 序列相似度(35%) + 特征相似度(25%)"""
        struct_sim = self.structural_similarity(code1, code2)
        seq_sim = self.sequence_similarity(code1, code2)
        feat_sim = self.feature_similarity(code1, code2)
        
        return 0.4 * struct_sim + 0.35 * seq_sim + 0.25 * feat_sim

    def detect(self, student_codes: dict, threshold: float = 0.7) -> dict:
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
                if sim > threshold:
                    pairs.append((names[i], names[j], round(sim, 3)))

        return {
            "names": names,
            "matrix": similarity_matrix.tolist(),
            "suspicious_pairs": sorted(pairs, key=lambda x: x[2], reverse=True),
            "threshold": threshold
        }
