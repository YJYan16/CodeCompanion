from pydantic import BaseModel, field_validator, ValidationInfo
from typing import List, Optional

SUPPORTED_LANGUAGES = ['python', 'java']
MAX_CODE_LENGTH = 10000
MAX_QUESTION_LENGTH = 2000
MAX_RUBRICS_LENGTH = 2000

class GradeRequest(BaseModel):
    code: str
    question: str = ""
    rubrics: str = ""
    language: str = "python"
    
    @field_validator('code')
    @classmethod
    def code_must_be_reasonable_length(cls, v: str) -> str:
        if len(v) > MAX_CODE_LENGTH:
            raise ValueError(f'代码长度不能超过{MAX_CODE_LENGTH}字符')
        if not v.strip():
            raise ValueError('代码不能为空')
        return v
    
    @field_validator('language')
    @classmethod
    def language_must_be_supported(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f'不支持的语言，支持: {SUPPORTED_LANGUAGES}')
        return v
    
    @field_validator('question')
    @classmethod
    def question_length_check(cls, v: str) -> str:
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(f'题目描述不能超过{MAX_QUESTION_LENGTH}字符')
        return v
    
    @field_validator('rubrics')
    @classmethod
    def rubrics_length_check(cls, v: str) -> str:
        if len(v) > MAX_RUBRICS_LENGTH:
            raise ValueError(f'评分标准不能超过{MAX_RUBRICS_LENGTH}字符')
        return v

class TutorRequest(BaseModel):
    question: str
    chat_history: List[dict] = []
    report_json: str = "{}"
    student_code: str = ""
    
    @field_validator('question')
    @classmethod
    def question_cannot_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('问题不能为空')
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(f'问题长度不能超过{MAX_QUESTION_LENGTH}字符')
        return v
    
    @field_validator('chat_history')
    @classmethod
    def chat_history_limit(cls, v: List[dict]) -> List[dict]:
        if len(v) > 50:
            raise ValueError('聊天历史不能超过50条')
        return v

class Deduction(BaseModel):
    line: int
    type: str
    points_deducted: int
    reason: str
    suggestion: str
    ai_generated: bool = True

class GradeResponse(BaseModel):
    overall_score: int
    summary: str
    deductions: List[Deduction]
    diagnosis_summary: str = ""
    weak_knowledge_points: List[str] = []
    ai_generated: bool = True

class TutorResponse(BaseModel):
    answer: str
    ai_generated: bool = True

class HealthResponse(BaseModel):
    status: str
    version: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str
    user: dict


class SaveGradeRequest(BaseModel):
    user_id: int
    user_name: str = ""
    question_id: str
    code: str
    language: str = "python"
    overall_score: float
    summary: str = ""
    deductions: list | str = []
    class_name: str = ""


class DraftRequest(BaseModel):
    question_id: str
    code: str
    language: str = "python"


class ClientErrorReport(BaseModel):
    message: str
    stack: str = ""
    url: str = ""
    component: str = ""