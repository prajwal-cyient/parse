import json
import logging
from typing import Any, Dict, List

from .models import Document, FinalRequirementJSON
from .extractors import RequirementExtractor, TableExtractor, FigureExtractor, StepExtractor
from .mappers import RequirementMapper, TableMapper, FigureMapper, NestedReferenceResolver
from .filters import ContextFilter, TableClassifier
from .builder import ContextBuilder

logger = logging.getLogger(__name__)

class ParsingPipeline:
    """Orchestrates the Requirement Parsing and Context Mapping Engine."""
    
    def __init__(self):
        # Stage 1
        self.req_extractor = RequirementExtractor()
        # Stage 2
        self.table_extractor = TableExtractor()
        self.figure_extractor = FigureExtractor()
        
        # Stages 3, 4, 5
        self.req_mapper = RequirementMapper()
        self.table_mapper = TableMapper()
        self.figure_mapper = FigureMapper()
        
        # Stage 6
        self.table_classifier = TableClassifier()
        self.context_filter = ContextFilter()
        
        # Stage 7
        self.step_extractor = StepExtractor()
        
        # Stage 8
        self.nested_resolver = NestedReferenceResolver(max_depth=3)
        
        # Stage 9
        self.context_builder = ContextBuilder()

    def process(self, raw_data: Any) -> Dict[str, Any]:
        """
        Runs the full pipeline on raw document data.
        Returns the final normalized JSON object containing:
        - requirements
        - tables
        - figures
        - cross_reference
        - entity_index
        """
        logger.info("Starting Parsing Pipeline")
        
        if isinstance(raw_data, str) and raw_data.endswith('.docx'):
            import os
            import sys
            p1 = r'c:\Users\pm89542\Downloads\test_parker\test_parker'
            if p1 not in sys.path:
                sys.path.append(p1)
            import docx_to_requirements
            raw_data = docx_to_requirements.extract(raw_data)

        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict) and 'requirement_text' in item and 'text' not in item:
                    item['text'] = item['requirement_text']

        doc = Document()
        
        # 1. Extraction (Stages 1, 2)
        logger.info("Extracting Requirements...")
        doc.requirements = self.req_extractor.extract(raw_data)
        logger.info(f"Extracted {len(doc.requirements)} requirements.")
        
        logger.info("Extracting Tables...")
        doc.tables = self.table_extractor.extract(raw_data)
        logger.info(f"Extracted {len(doc.tables)} tables.")
        
        logger.info("Extracting Figures...")
        doc.figures = self.figure_extractor.extract(raw_data)
        logger.info(f"Extracted {len(doc.figures)} figures.")
        
        # Register entities to maps for quick lookups
        doc.register()
        
        # Classify tables (Stage 4 equivalent)
        logger.info("Classifying tables...")
        self.table_classifier.classify(doc)
        
        # 2. Step Extraction (Stage 7)
        logger.info("Extracting Table Steps...")
        for table in doc.tables:
            self.step_extractor.extract(table)
            
        # 3. Context Filtering (Stage 6)
        logger.info("Filtering irrelevant context...")
        self.context_filter.filter(doc)
        logger.info(f"Tables remaining after filtering: {len(doc.tables)}")
        
        # Re-register maps in case filter modified them
        doc.register()
        
        # 4. Reference Mapping (Stages 3, 4, 5)
        logger.info("Mapping references...")
        self.req_mapper.map_references(doc)
        self.table_mapper.map_references(doc)
        self.figure_mapper.map_references(doc)
        
        # 5. Nested Reference Resolution (Stage 8)
        logger.info("Resolving nested references safely...")
        self.nested_resolver.resolve(doc)
        
        # 6. Context Builder (Stage 9)
        logger.info("Building final context JSON...")
        final_objects = self.context_builder.build(doc)
        
        return self.context_builder.to_dicts(final_objects)

