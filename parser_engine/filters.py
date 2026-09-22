from typing import List
from .models import Document, Table

class TableClassifier:
    """Classifies tables into specific categories based on content."""
    
    def classify(self, doc: Document) -> None:
        for table in doc.tables:
            title = table.title.lower()
            headers = " ".join(table.headers).lower()
            
            if any(w in title for w in ["procedure", "execution step", "test sequence"]) or \
                 any(w in headers.split() for w in ["step", "action", "procedure"]):
                table.classification = "STEP_TABLE"
            elif "register" in title or "register" in headers:
                table.classification = "REGISTER_TABLE"
            elif "pin configuration" in title or "pin" in headers:
                table.classification = "PIN_CONFIGURATION"
            elif "state" in title and "machine" in title:
                table.classification = "STATE_MACHINE"
            elif "signal" in title:
                table.classification = "SIGNAL_TABLE"
            elif "configuration" in title:
                table.classification = "CONFIGURATION_TABLE"
            elif "lookup" in title:
                table.classification = "LOOKUP_TABLE"
            elif "timing" in title:
                table.classification = "TIMING_TABLE"
            else:
                table.classification = "UNKNOWN"

class ContextFilter:
    """
    Intelligent Context Filtering Layer.
    Filters out tables/figures that are not useful for test generation.
    """
    
    def __init__(self):
        # Words in table titles/headers that indicate it's NOT useful
        self.ignore_keywords = [
            "revision history",
            "document history",
            "abbreviations",
            "acronyms",
            "references",
            "table of contents"
        ]
        
        # Words indicating high value for test generation
        self.keep_keywords = [
            "functional", "step", "signal", "configuration", 
            "state", "transition", "timing", "precondition",
            "postcondition", "operational", "behavior"
        ]

    def filter(self, doc: Document) -> None:
        """
        Applies filtering rules in-place on the document.
        Removes non-useful tables and figures from the document and its entities.
        """
        useful_tables = []
        for table in doc.tables:
            if self._is_table_useful(table):
                useful_tables.append(table)
            else:
                # Remove from map if filtered out
                if table.table_id in doc.table_map:
                    del doc.table_map[table.table_id]
                    
        doc.tables = useful_tables

    def _is_table_useful(self, table: Table) -> bool:
        title_lower = table.title.lower()
        
        # Check against ignore list
        if any(keyword in title_lower for keyword in self.ignore_keywords):
            return False
            
        # Check against keep list or if it has steps
        if any(keyword in title_lower for keyword in self.keep_keywords):
            return True
            
        if len(table.steps) > 0:
            return True
            
        # Default fallback - keep it if it has substantial content
        if len(table.rows) > 1 and len(table.headers) > 1:
            return True
            
        return False
