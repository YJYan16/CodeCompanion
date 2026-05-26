"""
知识图谱构建与诊断推理
"""
from .graph_data import KNOWLEDGE_NODES, ERROR_NODES

class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}          # 所有节点 {id: node}
        self.edges = []          # 关系列表 [{from, to, relation}]
        self._build()

    def _build(self):
        """根据定义构建图谱"""
        # 加载知识点
        for kn in KNOWLEDGE_NODES:
            self.nodes[kn["id"]] = kn
            if "prerequisites" in kn:
                for pre_id in kn["prerequisites"]:
                    self.edges.append({
                        "from": kn["id"],
                        "to": pre_id,
                        "relation": "prerequisite"
                    })
            # 资源边
            if "resources" in kn:
                for res in kn["resources"]:
                    res_id = f"RES_{kn['id']}_{res[:4]}"
                    self.nodes[res_id] = {"id": res_id, "name": res, "type": "资源"}
                    self.edges.append({
                        "from": kn["id"],
                        "to": res_id,
                        "relation": "has_resource"
                    })
        # 加载错误模式
        for err in ERROR_NODES:
            self.nodes[err["id"]] = err
            if "caused_by" in err:
                for k_id in err["caused_by"]:
                    self.edges.append({
                        "from": err["id"],
                        "to": k_id,
                        "relation": "caused_by"
                    })

    def find_error(self, error_keywords: list) -> list:
        """根据关键词查找匹配的错误模式节点"""
        matched = []
        for eid, node in self.nodes.items():
            if node.get("type") == "错误模式":
                name = node.get("name", "")
                pattern = node.get("pattern", "")
                text = name + " " + pattern
                for kw in error_keywords:
                    if kw.lower() in text.lower():
                        matched.append(node)
                        break
        return matched

    def trace_causes(self, error_id: str, depth=2) -> list:
        """追溯错误原因链：错误→薄弱知识点→前置知识点"""
        chain = []
        queue = [(error_id, 0)]
        visited = set()
        while queue:
            current, level = queue.pop(0)
            if current in visited or level > depth:
                continue
            visited.add(current)
            node = self.nodes.get(current)
            if node:
                chain.append({
                    "node": node,
                    "level": level,
                    "type": node.get("type")
                })
                # 查找相关边
                for edge in self.edges:
                    if edge["from"] == current and edge["relation"] in ("caused_by", "prerequisite"):
                        queue.append((edge["to"], level + 1))
        return chain

    def diagnose(self, error_keywords: list) -> list:  # 始终返回列表
        """完整诊断：错误→知识点→建议资源"""
        errors = self.find_error(error_keywords)
        if not errors:
            return []  # 改为空列表，不再返回字典
        
        result = []
        for err in errors:
            chain = self.trace_causes(err["id"])
            resources = [node for node in chain if node["type"] == "资源"]
            result.append({
                "error": err,
                "chain": chain,
                "resources": resources
            })
        return result