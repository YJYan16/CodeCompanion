# backend/app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class GradeRequest(BaseModel):
    code: str
    question: str = ""
    rubrics: str = ""
    language: str = "python"  # 新增

class TutorRequest(BaseModel):
    question: str
    chat_history: List[dict] = []
    report_json: str = "{}"
    student_code: str = ""  # 新增

class Deduction(BaseModel):
    line: int
    type: str
    points_deducted: int
    reason: str
    suggestion: str
    ai_generated: bool = True  # 标记是否由AI生成

class GradeResponse(BaseModel):
    overall_score: int
    summary: str
    deductions: List[Deduction]
    diagnosis_summary: str = ""
    weak_knowledge_points: List[str] = []
    ai_generated: bool = True  # 整体标记

class TutorResponse(BaseModel):
    answer: str
    ai_generated: bool = True

class HealthResponse(BaseModel):
    status: str
    version: str