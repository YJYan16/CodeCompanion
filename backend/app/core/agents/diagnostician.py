import os
import sys
import hashlib
from sentence_transformers import SentenceTransformer
import chromadb
from cachetools import TTLCache

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import get_settings
from src.knowledge.graph_builder import KnowledgeGraph
from src.languages import LANGUAGE_PARSERS

settings = get_settings()

class Diagnostician:
    def __init__(self):
        print("🔍 诊断智能体初始化...")
        self.embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
        kb_path = os.path.join(os.path.dirname(__file__), "..", "..", settings.chromadb_path)
        self.chroma_client = chromadb.PersistentClient(path=kb_path)
        self.error_collection = self.chroma_client.get_or_create_collection("python_errors")
        self.example_collection = self.chroma_client.get_or_create_collection("python_examples")
        self.kg = KnowledgeGraph()
        
        # 内存缓存：向量查询结果缓存
        self.knowledge_cache = TTLCache(maxsize=1000, ttl=3600)
        self.kg_cache = TTLCache(maxsize=500, ttl=7200)
        
        print("✅ 诊断智能体就绪（含知识图谱和缓存）")

    def static_analysis(self, code: str) -> dict:
        issues = []
        try:
            compile(code, '<student_code>', 'exec')
        except SyntaxError as e:
            issues.append({"type": "语法错误", "line": e.lineno or 0, "reason": str(e.msg)})
        return {"static_issues": issues}

    def knowledge_search(self, query_text: str, n_results: int = 3) -> dict:
        """在知识库中搜索相关知识（已缓存）"""
        # 生成缓存键
        cache_key = f"knowledge:{hashlib.md5(query_text.encode('utf-8')).hexdigest()}:{n_results}"
        
        if cache_key in self.knowledge_cache:
            return self.knowledge_cache[cache_key]
        
        try:
            error_results = self.error_collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
        except Exception:
            error_results = {"ids": [[]], "metadatas": [[]]}
        
        try:
            example_results = self.example_collection.query(
                query_texts=[query_text],
                n_results=min(n_results, 2)
            )
        except Exception:
            example_results = {"ids": [[]], "metadatas": [[]]}

        errors = []
        for i in range(len(error_results['ids'][0])):
            meta = error_results['metadatas'][0][i]
            errors.append({
                "type": meta.get('error_type', ''),
                "explanation": meta.get('explanation', ''),
                "fix_example": meta.get('fix_example', '')
            })

        examples = []
        for i in range(len(example_results['ids'][0])):
            meta = example_results['metadatas'][0][i]
            examples.append({
                "topic": meta.get('topic', ''),
                "code": meta.get('code', ''),
                "explanation": meta.get('explanation', '')
            })

        result = {"errors": errors, "examples": examples}
        
        # 缓存结果
        self.knowledge_cache[cache_key] = result
        return result

    def _extract_error_keywords(self, code: str, static_issues: list) -> list:
        """从静态分析结果和代码中提取错误关键词"""
        keywords = []
        
        for issue in static_issues:
            keywords.append(issue.get('type', ''))
            keywords.append(issue.get('reason', ''))
        
        import re
        variable_patterns = [
            (r'max_num\s*=\s*0', '初始化错误'),
            (r'max_val\s*=\s*0', '初始化错误'),
            (r'range\(1,\s*len\(', '索引起始错误'),
            (r'for\s+i\s+in\s+range\(', '循环索引'),
            (r'if\s+not\s+numbers', '空列表检查'),
        ]
        
        for pattern, keyword in variable_patterns:
            if re.search(pattern, code):
                keywords.append(keyword)
        
        return list(set(keywords))

    def diagnose(self, code: str, question: str = "", language: str = "python") -> dict:
        # 先检查是否有缓存的诊断结果
        diag_cache_key = f"diagnose:{hashlib.md5((code + question + language).encode('utf-8')).hexdigest()}"
        if diag_cache_key in self.kg_cache:
            return self.kg_cache[diag_cache_key]
            
        parser = LANGUAGE_PARSERS.get(language, LANGUAGE_PARSERS["python"])
        syntax_result = parser.check_syntax(code)
        
        error_keywords = self._extract_error_keywords(code, syntax_result["errors"])
        
        knowledge_result = self.knowledge_search(code)
        
        graph_diagnosis = self.kg.diagnose(error_keywords)
        
        weak_knowledge_points = []
        for diag in graph_diagnosis:
            for node in diag.get('chain', []):
                if node.get('type') == '知识点':
                    weak_knowledge_points.append(node['node'].get('name', ''))
        
        error_types = [err.get('type', '') for err in syntax_result["errors"]]
        error_types.extend([err.get('type', '') for err in knowledge_result.get('errors', [])])
        
        summary_parts = []
        if syntax_result["errors"]:
            summary_parts.append(f"检测到 {len(syntax_result['errors'])} 个语法错误")
        if knowledge_result["errors"]:
            summary_parts.append(f"匹配到 {len(knowledge_result['errors'])} 个已知错误模式")
        if weak_knowledge_points:
            summary_parts.append(f"识别到薄弱知识点: {', '.join(weak_knowledge_points[:3])}")
        
        if not summary_parts:
            summary = "代码语法正确，未发现明显问题"
        else:
            summary = "; ".join(summary_parts)

        result = {
            "static": {"static_issues": syntax_result["errors"], "structure": {}, "language": language},
            "knowledge": knowledge_result,
            "graph_diagnosis": graph_diagnosis,
            "error_types": list(set(error_types)),
            "weak_knowledge_points": list(set(weak_knowledge_points)),
            "summary": summary
        }
        
        # 缓存诊断结果
        self.kg_cache[diag_cache_key] = result
        return result
