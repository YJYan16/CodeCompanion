import os
import sys
from sentence_transformers import SentenceTransformer
import chromadb

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.knowledge.graph_builder import KnowledgeGraph
from src.languages import LANGUAGE_PARSERS

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "kb_data")


class Diagnostician:
    def __init__(self):
        print("🔍 诊断智能体初始化...")
        self.embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
        self.chroma_client = chromadb.PersistentClient(path=KB_PATH)
        self.error_collection = self.chroma_client.get_or_create_collection("python_errors")
        self.example_collection = self.chroma_client.get_or_create_collection("python_examples")
        self.kg = KnowledgeGraph()
        print("✅ 诊断智能体就绪（含知识图谱）")

    def static_analysis(self, code: str) -> dict:
        issues = []
        try:
            compile(code, '<student_code>', 'exec')
        except SyntaxError as e:
            issues.append({"type": "语法错误", "line": e.lineno or 0, "reason": str(e.msg)})
        return {"static_issues": issues}

    def knowledge_search(self, query_text: str) -> dict:
        return {"errors": [], "examples": []}

    def _extract_error_keywords(self, code: str, static_issues: list) -> list:
        return []

    def diagnose(self, code: str, question: str = "", language: str = "python") -> dict:
        parser = LANGUAGE_PARSERS.get(language, LANGUAGE_PARSERS["python"])
        syntax_result = parser.check_syntax(code)

        return {
            "static": {"static_issues": syntax_result["errors"], "structure": {}, "language": language},
            "knowledge": {"errors": [], "examples": []},
            "graph_diagnosis": [],
            "error_types": [],
            "weak_knowledge_points": [],
            "summary": f"静态问题: {len(syntax_result['errors'])} 个"
        }