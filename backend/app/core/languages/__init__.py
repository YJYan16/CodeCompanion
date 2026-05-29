# src/languages/__init__.py
from .python_parser import PythonParser
from .java_parser import JavaParser

LANGUAGE_PARSERS = {
    "python": PythonParser(),
    "java": JavaParser()
}