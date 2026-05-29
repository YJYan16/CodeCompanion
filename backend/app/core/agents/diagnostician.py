"""
诊断智能体 - 代码诊断与错误分析
"""
import os
import sys
import hashlib
from cachetools import TTLCache

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if os.path.dirname(backend_dir) not in sys.path:
    sys.path.insert(0, os.path.dirname(backend_dir))

try:
    from config.settings import get_settings
    from app.core.knowledge.graph_builder import KnowledgeGraph
    from app.core.languages import LANGUAGE_PARSERS
except ImportError:
    from config.settings import get_settings
    from backend.app.core.knowledge.graph_builder import KnowledgeGraph
    from backend.app.core.languages import LANGUAGE_PARSERS

settings = get_settings()


class Diagnostician:
    def __init__(self):
        print("诊断智能体初始化...")
        self._embedding_model = None
        self._embedding_model_loaded = False
        self._chroma_client = None
        self._chroma_initialized = False
        self._error_collection = None
        self._example_collection = None

        self.kg = KnowledgeGraph()

        self.knowledge_cache = TTLCache(maxsize=1000, ttl=3600)
        self.kg_cache = TTLCache(maxsize=500, ttl=7200)

        print("诊断智能体就绪（知识图谱已加载）")

    @property
    def embedding_model(self):
        if not self._embedding_model_loaded:
            self._load_embedding_model()
        return self._embedding_model

    @property
    def chroma_client(self):
        if not self._chroma_initialized:
            self._init_chroma()
        return self._chroma_client

    @property
    def error_collection(self):
        if not self._chroma_initialized:
            self._init_chroma()
        return self._error_collection

    @property
    def example_collection(self):
        if not self._chroma_initialized:
            self._init_chroma()
        return self._example_collection

    def _load_embedding_model(self):
        """延迟加载嵌入模型 - 仅在实际使用时加载"""
        if self._embedding_model_loaded:
            return
        self._embedding_model_loaded = True

        try:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
            print("✅ 嵌入模型加载成功")
        except Exception as e:
            print(f"⚠️ 嵌入模型加载失败: {e}")
            print("   将使用知识图谱进行诊断")

    def _init_chroma(self):
        """延迟初始化 Chroma 数据库"""
        if self._chroma_initialized:
            return
        self._chroma_initialized = True

        try:
            import chromadb
            kb_path = os.path.join(backend_dir, settings.chromadb_path)
            self._chroma_client = chromadb.PersistentClient(path=kb_path)
            self._error_collection = self._chroma_client.get_or_create_collection("python_errors")
            self._example_collection = self._chroma_client.get_or_create_collection("python_examples")
            print("✅ Chroma 数据库初始化成功")
        except Exception as e:
            print(f"⚠️ Chroma 数据库初始化失败: {e}")
            print("   将仅使用知识图谱进行诊断")

    def static_analysis(self, code: str) -> dict:
        """静态分析代码"""
        issues = []
        try:
            compile(code, '<student_code>', 'exec')
        except SyntaxError as e:
            issues.append({"type": "语法错误", "line": e.lineno or 0, "reason": str(e.msg)})
        return {"static_issues": issues}

    def knowledge_search(self, query_text: str, n_results: int = 3) -> dict:
        """搜索知识库"""
        cache_key = f"knowledge:{hashlib.md5(query_text.encode('utf-8')).hexdigest()}:{n_results}"

        if cache_key in self.knowledge_cache:
            return self.knowledge_cache[cache_key]

        error_collection = self.error_collection
        example_collection = self.example_collection

        if not error_collection or not example_collection:
            return {"errors": [], "examples": []}

        try:
            error_results = error_collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
        except Exception:
            error_results = {"ids": [[]], "metadatas": [[]]}

        try:
            example_results = example_collection.query(
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
        self.knowledge_cache[cache_key] = result
        return result

    def _extract_error_keywords(self, code: str, static_issues: list) -> list:
        """从代码和静态分析结果中提取错误关键词"""
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
        """完整诊断：错误→知识点→建议资源"""
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

        self.kg_cache[diag_cache_key] = result
        return result