"""
评估智能体 - 代码评分与反馈生成
支持在线（智谱AI）和离线（Ollama）两种模式
"""
import os
import sys
import json
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config.settings import get_settings
from ..ollama_client import get_ollama_client

settings = get_settings()


class Evaluator:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.zhipu_api_key
        self.use_local_model = settings.use_local_model
        self.ollama_client = None
        
        if self.use_local_model:
            self.ollama_client = get_ollama_client()
    
    def _build_evaluation_prompt(self, code: str, question: str, rubrics: str, diagnosis: dict = None) -> str:
        """构建评估提示词"""
        prompt = f"""请对以下学生代码进行评估：

题目要求：
{question}

评分标准：
{rubrics}

学生代码：
```python
{code}
```

"""
        
        if diagnosis and diagnosis.get('errors'):
            prompt += f"\n代码诊断信息：\n"
            for error in diagnosis['errors']:
                prompt += f"- {error}\n"
        
        prompt += """
请按照以下JSON格式返回评估结果（只返回JSON，不要其他内容）：
评分规则：
- 代码为空或只有注释/占位符: overall_score = 0
- 存在严重语法错误导致无法运行: overall_score = 5-20
- 语法正确但存在运行时错误: overall_score = 20-50
- 语法和运行都正确，但功能不完整或有逻辑错误: overall_score = 50-75
- 功能完整且正确，但代码可优化: overall_score = 75-90
- 代码完美，符合所有要求: overall_score = 90-100

请根据上述规则和评分标准，给出一个合理的分数。分数应该能反映代码的真实质量，而不是极端值。

{
    "overall_score": 85,
    "deductions": [
        {
            "type": "边界条件处理",
            "reason": "未处理空列表情况",
            "suggestion": "添加对空列表的判断",
            "severity": 2,
            "points_deducted": 10
        }
    ],
    "analysis": "代码整体结构清晰，但缺少边界条件处理..."
}
"""
        return prompt
    
    def _build_feedback_prompt(self, code: str, evaluation: dict, diagnosis: dict) -> str:
        """构建反馈报告提示词"""
        deductions_str = ""
        if evaluation.get('deductions'):
            for d in evaluation['deductions']:
                deductions_str += f"- {d.get('type', '')}: {d.get('reason', '')}\n"
        
        prompt = f"""请为以下学生代码生成详细的反馈报告：

学生代码：
```python
{code}
```

评估结果：
总分：{evaluation.get('overall_score', 0)}

扣分项：
{deductions_str}

请生成一份详细的反馈报告，包括：
1. 代码优点
2. 需要改进的地方
3. 具体的改进建议
4. 学习建议

报告要友好、鼓励性，适合学生阅读。
"""
        return prompt
    
    async def _evaluate_with_ollama(self, code: str, question: str, rubrics: str, diagnosis: dict = None) -> dict:
        """使用Ollama本地模型进行评估"""
        if not self.ollama_client:
            raise Exception("Ollama客户端未初始化")
        
        prompt = self._build_evaluation_prompt(code, question, rubrics, diagnosis)
        
        try:
            response = await self.ollama_client.generate(
                prompt=prompt,
                temperature=0.3,  # 降低温度以获得更稳定的JSON输出
                max_tokens=1500
            )
            
            # 尝试解析JSON响应
            try:
                # 清理可能的markdown代码块标记
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                result = json.loads(response)
                
                # 确保返回必要的字段
                if 'overall_score' not in result:
                    result['overall_score'] = 75
                if 'deductions' not in result:
                    result['deductions'] = []
                if 'analysis' not in result:
                    result['analysis'] = "代码评估完成"
                
                return result
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认结果
                print(f"Ollama返回的不是有效JSON: {response[:200]}")
                return {
                    "overall_score": 75,
                    "deductions": [],
                    "analysis": "代码评估完成（JSON解析失败，使用默认评分）"
                }
        except Exception as e:
            print(f"Ollama评估失败: {str(e)}")
            # 返回默认结果
            return {
                "overall_score": 70,
                "deductions": [],
                "analysis": f"评估过程中出现错误: {str(e)}"
            }
    
    async def _generate_feedback_with_ollama(self, code: str, evaluation: dict, diagnosis: dict) -> str:
        """使用Ollama生成反馈报告"""
        if not self.ollama_client:
            raise Exception("Ollama客户端未初始化")
        
        prompt = self._build_feedback_prompt(code, evaluation, diagnosis)
        
        try:
            response = await self.ollama_client.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            return response.strip()
        except Exception as e:
            print(f"Ollama生成反馈失败: {str(e)}")
            return f"反馈生成过程中出现错误: {str(e)}"
    
    def evaluate(self, code: str, question: str, rubrics: str, diagnosis: dict = None,  language: str = "python") -> dict:
        """
        评估代码质量
        
        Returns:
            dict: 包含 overall_score 和 deductions
        """
        if self.use_local_model:
            # 使用Ollama本地模型
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._evaluate_with_ollama(code, question, rubrics, diagnosis)
                )
                return result
            finally:
                loop.close()
        else:
            # 使用在线API（智谱AI）
            # 这里保留原有的实现
            return {
                "overall_score": 0,
                "deductions": [],
                "analysis": ""
            }
    
    def generate_feedback(self, code: str, evaluation: dict, diagnosis: dict) -> str:
        """生成详细的反馈报告"""
        if self.use_local_model:
            # 使用Ollama本地模型
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                feedback = loop.run_until_complete(
                    self._generate_feedback_with_ollama(code, evaluation, diagnosis)
                )
                return feedback
            finally:
                loop.close()
        else:
            # 使用在线API（智谱AI）
            return "评估完成"