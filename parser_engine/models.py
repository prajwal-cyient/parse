from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ContextItem:
    """Represents a generic context item (Note, Warning, Caution, List, etc.)."""
    type: str  # e.g., 'note', 'warning', 'list', 'caption'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NoteItem:
    """Represents a note in a requirement."""
    text: str
    type: str = "note"

@dataclass
class Condition:
    """Represents a logical condition in a requirement."""
    signal: str
    operator: str
    value: Any

@dataclass
class ExpectedOutput:
    """Represents an expected output assignment in a requirement."""
    signal: str
    value: Any
    condition: Optional[str] = None  # Optional branch label, e.g., "THEN", "ELSE"

@dataclass
class LogicExpression:
    """Represents a logical expression AST preserving AND/OR relationships."""
    operator: str
    operands: List[Any]

@dataclass
class StateTransition:
    """Represents a state transition extracted from a requirement."""
    from_state: str
    to_state: str

@dataclass
class TimingConstraint:
    """Represents a timing constraint extracted from a requirement."""
    value: float
    unit: str
    tolerance: Optional[float] = None
    type: Optional[str] = None

@dataclass
class Dependency:
    """Represents a single dependency reference."""
    type: str
    id: str

@dataclass
class Step:
    """Represents a step extracted from a table."""
    step_id: str
    step_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Table:
    """Represents an extracted table."""
    table_id: str
    title: str
    headers: List[str]
    rows: List[List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_location: Dict[str, Any] = field(default_factory=dict)
    classification: str = "UNKNOWN"
    steps: List[Step] = field(default_factory=list)
    definitions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    linked_requirements: List[str] = field(default_factory=list)
    linked_tables: List[str] = field(default_factory=list)
    linked_figures: List[str] = field(default_factory=list)

@dataclass
class Figure:
    """Represents an extracted figure."""
    figure_id: str
    title: str
    caption: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_location: Dict[str, Any] = field(default_factory=dict)
    linked_requirements: List[str] = field(default_factory=list)
    linked_tables: List[str] = field(default_factory=list)
    linked_figures: List[str] = field(default_factory=list)

@dataclass
class Requirement:
    """Primary requirement object."""
    req_id: str
    req_text: str
    title: Optional[str] = None
    section_num: Optional[str] = None
    parent_section: Optional[str] = None
    doc_position: int = -1
    
    notes: List[NoteItem] = field(default_factory=list)
    warnings: List[ContextItem] = field(default_factory=list)
    cautions: List[ContextItem] = field(default_factory=list)
    lists: List[ContextItem] = field(default_factory=list)
    
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)

    conditions: List[Condition] = field(default_factory=list)
    expected_outputs: List[ExpectedOutput] = field(default_factory=list)
    logic_expression: Optional[LogicExpression] = None
    state_transition: Optional[StateTransition] = None
    timing_constraints: List[TimingConstraint] = field(default_factory=list)

    decision_type: Optional[str] = None
    signal_roles: Dict[str, List[str]] = field(default_factory=dict)
    confidence: Dict[str, float] = field(default_factory=dict)

    linked_requirements: List[str] = field(default_factory=list)
    linked_tables: List[str] = field(default_factory=list)
    linked_figures: List[str] = field(default_factory=list)
    
    signals: List[str] = field(default_factory=list)
    surface_applicability: List[str] = field(default_factory=list)
    lru_configuration: List[str] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)
    source_location: Dict[str, Any] = field(default_factory=dict)
    additional_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Document:
    """A generic representation of a parsed document."""
    requirements: List[Requirement] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    # Allows fast lookups
    req_map: Dict[str, Requirement] = field(default_factory=dict)
    table_map: Dict[str, Table] = field(default_factory=dict)
    figure_map: Dict[str, Figure] = field(default_factory=dict)

    def register(self):
        for req in self.requirements:
            self.req_map[req.req_id] = req
        for table in self.tables:
            self.table_map[table.table_id] = table
        for fig in self.figures:
            self.figure_map[fig.figure_id] = fig

@dataclass
class FinalRequirementJSON:
    """The final consolidated schema for an individual requirement object."""
    requirement_id: str
    requirement_text: str
    
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    expected_outputs: List[Dict[str, Any]] = field(default_factory=list)
    logic_expression: Optional[Dict[str, Any]] = None
    state_transition: Optional[Dict[str, Any]] = None
    timing_constraints: List[Dict[str, Any]] = field(default_factory=list)

    decision_type: Optional[str] = None
    signal_roles: Dict[str, List[str]] = field(default_factory=dict)
    confidence: Dict[str, float] = field(default_factory=dict)

    linked_requirements: List[str] = field(default_factory=list)
    linked_tables: List[str] = field(default_factory=list)
    linked_figures: List[str] = field(default_factory=list)
    
    signals: List[str] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    surface_applicability: List[str] = field(default_factory=list)
    lru_configuration: List[str] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_location: Dict[str, Any] = field(default_factory=dict)



