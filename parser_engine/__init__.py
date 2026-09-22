"""
Requirement Parsing and Context Mapping Engine

This package provides a generic, modular, scalable, and extensible pipeline for
converting engineering requirements documents into a single consolidated JSON
format designed for downstream AI agents (Test Case Generation).
"""

from .pipeline import ParsingPipeline
from .models import Document, Requirement, Table, Figure, Step, ContextItem, FinalRequirementJSON
from .extractors import RequirementExtractor, TableExtractor, FigureExtractor, StepExtractor
from .mappers import RequirementMapper, TableMapper, FigureMapper, NestedReferenceResolver
from .filters import ContextFilter
from .builder import ContextBuilder

__all__ = [
    "ParsingPipeline",
    "Document",
    "Requirement",
    "Table",
    "Figure",
    "Step",
    "ContextItem",
    "FinalRequirementJSON",
    "RequirementExtractor",
    "TableExtractor",
    "FigureExtractor",
    "StepExtractor",
    "RequirementMapper",
    "TableMapper",
    "FigureMapper",
    "NestedReferenceResolver",
    "ContextFilter",
    "ContextBuilder",
]
