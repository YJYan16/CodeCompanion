# backend/app/models/database_models.py
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'student' or 'admin'
    class_name = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    grades = relationship("Grade", back_populates="user")

# 班级模型
class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    grades = relationship("Grade", back_populates="class_obj")

# 题目模型
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String, unique=True, nullable=False)  # 题目唯一标识
    title = Column(String, nullable=False)
    description = Column(Text)
    python_template = Column(Text)
    java_template = Column(Text)
    rubrics = Column(Text)
    difficulty = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    
    grades = relationship("Grade", back_populates="question")

# 成绩模型
class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    code = Column(Text)
    language = Column(String)
    overall_score = Column(Float)
    summary = Column(Text)
    deductions = Column(JSON)
    submitted_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="grades")
    question = relationship("Question", back_populates="grades")
    class_obj = relationship("Class", back_populates="grades")


class StudentDraft(Base):
    """学生代码自动保存草稿。"""
    __tablename__ = "student_drafts"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_draft"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(String, nullable=False)
    code = Column(Text, default="")
    language = Column(String, default="python")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User")


class ErrorLog(Base):
    """应用错误监控日志。"""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    error_type = Column(String(128), default="Exception")
    path = Column(String(512))
    method = Column(String(16))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    stack_trace = Column(Text)
    context = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
