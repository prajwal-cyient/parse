import re
from typing import List, Set, Dict, Any

from .models import Document, Requirement, Table, Figure

class BaseMapper:
    """Base class for reference mapping."""
    
    def __init__(self, req_pattern: str = r"([A-Z]+-\d+)",
                 table_pattern: str = r"(Table\s+\w+)",
                 figure_pattern: str = r"(Figure\s+\w+)"):
        self.req_pattern = re.compile(req_pattern, re.IGNORECASE)
        self.table_pattern = re.compile(table_pattern, re.IGNORECASE)
        self.figure_pattern = re.compile(figure_pattern, re.IGNORECASE)

    def extract_references(self, text: str) -> dict:
        """Extracts linked IDs from text."""
        return {
            "reqs": list(set(self.req_pattern.findall(text))),
            "tables": list(set(self.table_pattern.findall(text))),
            "figures": list(set(self.figure_pattern.findall(text))),
        }

class RequirementMapper(BaseMapper):
    """Maps references for Requirements from text and notes."""
    
    def map_references(self, doc: Document):
        for req in doc.requirements:
            text_to_search = req.req_text + " " + " ".join(
                note.text if hasattr(note, "text") else getattr(note, "content", "")
                for note in req.notes
            )
            refs = self.extract_references(text_to_search)
            
            # Avoid self-references
            req.linked_requirements = [r for r in refs["reqs"] if r != req.req_id]
            req.linked_tables = refs["tables"]
            req.linked_figures = refs["figures"]


class TableMapper(BaseMapper):
    """Maps references for Tables."""
    
    def map_references(self, doc: Document):
        for table in doc.tables:
            text_to_search = table.title + " " + " ".join(
                " ".join(row) for row in table.rows
            )
            refs = self.extract_references(text_to_search)
            
            table.linked_requirements = refs["reqs"]
            table.linked_tables = [t for t in refs["tables"] if t != table.table_id]
            table.linked_figures = refs["figures"]


class FigureMapper(BaseMapper):
    """Maps references for Figures."""
    
    def map_references(self, doc: Document):
        for fig in doc.figures:
            text_to_search = fig.title + " " + fig.caption
            refs = self.extract_references(text_to_search)
            
            fig.linked_requirements = refs["reqs"]
            fig.linked_tables = refs["tables"]
            fig.linked_figures = [f for f in refs["figures"] if f != fig.figure_id]


class NestedReferenceResolver:
    """Resolves nested references up to a maximum depth to prevent infinite loops."""
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def resolve(self, doc: Document):
        for req in doc.requirements:
            self._resolve_for_entity(req, doc, depth=0, visited=set())

    def _resolve_for_entity(self, entity, doc: Document, depth: int, visited: Set[str]):
        if depth >= self.max_depth:
            return

        entity_id = getattr(entity, 'req_id', getattr(entity, 'table_id', getattr(entity, 'figure_id', None)))
        if not entity_id or entity_id in visited:
            return
            
        visited.add(entity_id)

        entity.linked_requirements = [r for r in entity.linked_requirements if r in doc.req_map]
        entity.linked_tables = [t for t in entity.linked_tables if t in doc.table_map]
        entity.linked_figures = [f for f in entity.linked_figures if f in doc.figure_map]

        for r_id in entity.linked_requirements:
            self._resolve_for_entity(doc.req_map[r_id], doc, depth + 1, visited.copy())
            
        for t_id in entity.linked_tables:
            self._resolve_for_entity(doc.table_map[t_id], doc, depth + 1, visited.copy())
            
        for f_id in entity.linked_figures:
            self._resolve_for_entity(doc.figure_map[f_id], doc, depth + 1, visited.copy())


class CrossReferenceBuilder:
    """Generates a global cross-reference index mapping entities to referencing requirement IDs."""
    
    def build(self, doc: Document) -> Dict[str, List[str]]:
        xref: Dict[str, List[str]] = {}

        # Initialize entries for known entities
        for req_id in doc.req_map:
            xref[req_id] = []
        for table_id in doc.table_map:
            xref[table_id] = []
        for fig_id in doc.figure_map:
            xref[fig_id] = []

        # Map references from requirements
        for req in doc.requirements:
            for r_id in req.linked_requirements:
                if r_id not in xref:
                    xref[r_id] = []
                if req.req_id not in xref[r_id]:
                    xref[r_id].append(req.req_id)

            for t_id in req.linked_tables:
                if t_id not in xref:
                    xref[t_id] = []
                if req.req_id not in xref[t_id]:
                    xref[t_id].append(req.req_id)

            for f_id in req.linked_figures:
                if f_id not in xref:
                    xref[f_id] = []
                if req.req_id not in xref[f_id]:
                    xref[f_id].append(req.req_id)

        return xref


class EntityIndexBuilder:
    """Generates a rich global entity index mapping Signals, Requirements, Tables, Figures, States, and LRUs."""
    
    def build(self, doc: Document) -> Dict[str, Dict[str, Any]]:
        entity_index: Dict[str, Dict[str, Any]] = {}

        # 1. Signals
        req_signal_map: Dict[str, List[str]] = {}
        for req in doc.requirements:
            for sig in req.signals:
                if sig not in req_signal_map:
                    req_signal_map[sig] = []
                if req.req_id not in req_signal_map[sig]:
                    req_signal_map[sig].append(req.req_id)

        for sig, used_reqs in req_signal_map.items():
            defined_in_tables = []
            for table in doc.tables:
                table_text = table.title + " " + " ".join(table.headers) + " " + " ".join(" ".join(row) for row in table.rows)
                if re.search(r"\b" + re.escape(sig) + r"\b", table_text):
                    defined_in_tables.append(table.table_id)

            entity_index[sig] = {
                "type": "signal",
                "defined_in_tables": defined_in_tables,
                "used_in_requirements": used_reqs
            }

        # 2. Requirements
        for req in doc.requirements:
            entity_index[req.req_id] = {
                "type": "requirement",
                "references_tables": req.linked_tables.copy(),
                "references_requirements": req.linked_requirements.copy(),
                "references_figures": req.linked_figures.copy()
            }

        # 3. Tables
        for table in doc.tables:
            referenced_by = [req.req_id for req in doc.requirements if table.table_id in req.linked_tables]
            defines = []
            for sig in req_signal_map:
                table_text = table.title + " " + " ".join(table.headers) + " " + " ".join(" ".join(row) for row in table.rows)
                if re.search(r"\b" + re.escape(sig) + r"\b", table_text):
                    defines.append(sig)

            entity_index[table.table_id] = {
                "type": "table",
                "referenced_by": referenced_by,
                "defines": defines
            }

        # 4. Figures
        for fig in doc.figures:
            referenced_by = [req.req_id for req in doc.requirements if fig.figure_id in req.linked_figures]
            entity_index[fig.figure_id] = {
                "type": "figure",
                "referenced_by": referenced_by
            }

        # 5. States
        state_map: Dict[str, List[str]] = {}
        for req in doc.requirements:
            if req.state_transition:
                for state_name in [req.state_transition.from_state, req.state_transition.to_state]:
                    if state_name not in state_map:
                        state_map[state_name] = []
                    if req.req_id not in state_map[state_name]:
                        state_map[state_name].append(req.req_id)

        for state_name, used_reqs in state_map.items():
            entity_index[state_name] = {
                "type": "state",
                "used_in_requirements": used_reqs
            }

        # 6. LRUs
        lru_map: Dict[str, List[str]] = {}
        for req in doc.requirements:
            for lru in req.lru_configuration:
                if lru not in lru_map:
                    lru_map[lru] = []
                if req.req_id not in lru_map[lru]:
                    lru_map[lru].append(req.req_id)

        for lru_name, used_reqs in lru_map.items():
            entity_index[lru_name] = {
                "type": "lru",
                "used_in_requirements": used_reqs
            }

        return entity_index



