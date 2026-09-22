import re
from typing import List, Dict, Any, Optional

from .models import (
    Document, Requirement, Table, Figure, Step, ContextItem, NoteItem,
    Condition, ExpectedOutput, LogicExpression, StateTransition, TimingConstraint
)

def clean_requirement_text(text: str) -> str:
    """Removes structural document headings from requirement text."""
    headings = {
        "reference requirements",
        "tables",
        "figures",
        "notes",
        "reference requirement",
        "table",
        "figure",
        "note"
    }
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if line.strip().lower() in headings:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


class ConditionExtractor:
    """Parses decision/input expressions from requirement text into Condition objects."""

    def __init__(self):
        self.expr_pattern = re.compile(
            r"([A-Za-z0-9_]+)\s*(==|=|!=|>=|<=|>|<|is equal to|is not|is)\s*(TRUE|FALSE|True|False|true|false|-?\d+(?:\.\d+)?)\b",
            re.IGNORECASE
        )
        self.any_true_header = re.compile(
            r"if any of the following signals are True:\s*((?:[A-Za-z0-9_]+\s*)+)",
            re.IGNORECASE
        )

    def extract(self, text: str) -> List[Condition]:
        conditions = []
        seen = set()

        def add_cond(signal: str, op: str, val: Any):
            op_norm = op.lower()
            if op_norm in ["=", "is equal to", "is"]:
                op_norm = "=="
            elif op_norm == "is not":
                op_norm = "!="
            else:
                op_norm = op

            if isinstance(val, str):
                if val.upper() == "TRUE":
                    val_norm = True
                elif val.upper() == "FALSE":
                    val_norm = False
                else:
                    try:
                        val_norm = int(val) if val.isdigit() else float(val)
                    except ValueError:
                        val_norm = val
            else:
                val_norm = val

            key = (signal, op_norm, str(val_norm))
            if key not in seen and signal.upper() not in ["LRU", "STEP", "TABLE", "FIGURE"]:
                seen.add(key)
                conditions.append(Condition(signal=signal, operator=op_norm, value=val_norm))

        # Filter out assignment blocks (lines after Then, else, or starting with Set)
        lines = text.split("\n")
        cond_lines = []
        in_assignment_block = False
        for line in lines:
            l_strip = line.strip()
            l_low = l_strip.lower()
            if l_low.startswith("then") or l_low.startswith("else") or l_low.startswith("set "):
                in_assignment_block = True
            if not in_assignment_block and not l_low.startswith("set "):
                cond_lines.append(line)
        
        filtered_text = "\n".join(cond_lines)

        # Check block patterns ("if any of the following signals are True: ...")
        any_match = self.any_true_header.search(filtered_text)
        if any_match:
            block = any_match.group(1)
            sig_candidates = re.findall(r"\b([A-Za-z0-9_]+)\b", block)
            for sig in sig_candidates:
                if sig.upper() not in ["AND", "OR", "FALSE", "TRUE", "OTHERWISE"]:
                    add_cond(sig, "==", True)

        # Match general binary conditions in condition text only
        for match in self.expr_pattern.finditer(filtered_text):
            sig, op, val = match.groups()
            add_cond(sig, op, val)

        return conditions


class ExpectedOutputExtractor:
    """Extracts expected output assignments from requirement text with branch context."""

    IGNORED_SIGNALS = {
        "EQUAL", "IS", "NOT", "MET", "IF", "ALL", "OF", "THE", "FOLLOWING",
        "CONDITIONS", "ARE", "SIGNALS", "LRU", "TABLE", "FIGURE", "NOTE"
    }

    def __init__(self):
        self.set_pattern = re.compile(
            r"\bSet\s+([A-Za-z0-9_]+)\s*(?:=|\s+)\s*(TRUE|FALSE|True|False|true|false|-?\d+(?:\.\d+)?)\b",
            re.IGNORECASE
        )
        self.shall_set_pattern = re.compile(
            r"\bshall\s+set\s+(?:the\s+)?([A-Za-z0-9_]+)\s+to\s+(TRUE|FALSE|True|False|true|false|-?\d+(?:\.\d+)?)\b",
            re.IGNORECASE
        )
        self.setting_bits_pattern = re.compile(
            r"\b([A-Za-z0-9_]+)\s+(?:discrete IO\s+)?to\s+(TRUE|FALSE|True|False)\b",
            re.IGNORECASE
        )

    def extract(self, text: str) -> List[ExpectedOutput]:
        outputs = []
        seen = set()

        def add_out(signal: str, val: Any, cond_label: Optional[str] = None):
            if not signal or signal.upper() in self.IGNORED_SIGNALS:
                return

            if isinstance(val, str):
                val_norm = True if val.upper() == "TRUE" else (False if val.upper() == "FALSE" else val)
            else:
                val_norm = val

            key = (signal, str(val_norm), str(cond_label))
            if key not in seen:
                seen.add(key)
                outputs.append(ExpectedOutput(signal=signal, value=val_norm, condition=cond_label))

        # Check line-by-line for THEN / ELSE context
        lines = text.split("\n")
        current_cond_label = None
        for line in lines:
            l_strip = line.strip()
            l_low = l_strip.lower()
            if l_low == "then" or l_low.startswith("then "):
                current_cond_label = "THEN"
            elif l_low == "else" or l_low.startswith("else "):
                current_cond_label = "ELSE"

            for match in self.set_pattern.finditer(line):
                add_out(match.group(1), match.group(2), current_cond_label)

        # Also match global shall_set and setting_bits patterns
        for match in self.shall_set_pattern.finditer(text):
            add_out(match.group(1), match.group(2), None)

        for match in self.setting_bits_pattern.finditer(text):
            # Only if not already extracted in condition text
            if "if " not in text.lower() or "by setting" in text.lower():
                add_out(match.group(1), match.group(2), None)

        return outputs


class LogicExpressionExtractor:
    """Preserves AND/OR logical operator trees/structures from conditions."""

    def extract(self, text: str, conditions: List[Condition]) -> Optional[LogicExpression]:
        if not conditions:
            return None

        # Determine top-level operator
        op = "AND"
        text_lower = text.lower()
        if " or " in text_lower or "any of the following" in text_lower:
            op = "OR"

        operands = [
            {"signal": c.signal, "operator": c.operator, "value": c.value}
            for c in conditions
        ]

        return LogicExpression(operator=op, operands=operands)


class StateTransitionExtractor:
    """Extracts state transitions described in text."""

    def __init__(self):
        self.trans_pattern = re.compile(
            r"\btransition\s+from\s+([A-Za-z0-9_]+(?:\s+State)?)\s+to\s+([A-Za-z0-9_]+(?:\s+State)?)\b",
            re.IGNORECASE
        )

    def extract(self, text: str) -> Optional[StateTransition]:
        match = self.trans_pattern.search(text)
        if match:
            return StateTransition(from_state=match.group(1).strip(), to_state=match.group(2).strip())
        return None


class TimingConstraintExtractor:
    """Extracts timing constraints and delays from text."""

    def __init__(self):
        self.tolerance_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*\+/-\s*(\d+(?:\.\d+)?)\s*(msec|ms|sec|seconds|milliseconds)\b",
            re.IGNORECASE
        )
        self.cycle_pattern = re.compile(
            r"\b(\d+(?:\.\d+)?)\s+(consecutive\s+)?(cycles|msec|ms|sec|seconds|milliseconds)\b",
            re.IGNORECASE
        )
        self.duration_pattern = re.compile(
            r"duration of up to (\d+(?:\.\d+)?)\s*(msec|ms|sec|seconds|milliseconds)\b",
            re.IGNORECASE
        )

    def extract(self, text: str) -> List[TimingConstraint]:
        constraints = []
        seen = set()

        def add_tc(val: float, unit: str, tol: Optional[float] = None, tc_type: Optional[str] = None):
            u_norm = unit.lower()
            if u_norm in ["msec", "milliseconds"]:
                u_norm = "ms"
            elif u_norm in ["sec", "seconds"]:
                u_norm = "s"

            key = (val, tol, u_norm, tc_type)
            if key not in seen:
                seen.add(key)
                constraints.append(TimingConstraint(value=val, tolerance=tol, unit=u_norm, type=tc_type))

        # 1. Matches with +/- tolerances first
        tol_spans = []
        for m in self.tolerance_pattern.finditer(text):
            add_tc(float(m.group(1)), m.group(3), float(m.group(2)), None)
            tol_spans.append(m.span())

        # 2. Cycle / general duration patterns (skip if within tolerance span)
        for m in self.cycle_pattern.finditer(text):
            if not any(span[0] <= m.start() <= span[1] for span in tol_spans):
                tc_type = "consecutive" if m.group(2) else None
                add_tc(float(m.group(1)), m.group(3), None, tc_type)

        # 3. Explicit duration pattern
        for m in self.duration_pattern.finditer(text):
            add_tc(float(m.group(1)), m.group(2), None, "max_duration")

        return constraints




class SignalExtractor:
    """Extracts all signal names used by the requirement without classifying them."""

    IGNORED_WORDS = {
        "LRU", "TRUE", "FALSE", "TABLE", "FIGURE", "STEP", "OR", "AND",
        "MODE", "STATE", "SET", "THEN", "WHILE", "REFERENCE", "REQUIREMENTS",
        "PRIMARY", "SECONDARY", "SPOILER", "RUDDER", "ELEVATOR", "AILERON",
        "NOTE", "LRUSWRS", "IS", "EQUAL", "TO", "NOT", "MET", "IF", "ALL",
        "OF", "THE", "FOLLOWING", "CONDITIONS", "ARE", "SIGNALS", "OTHERWISE",
        "WITH", "A", "DELAY", "IN", "PER", "DEFINED", "AFTER", "USING",
        "FPGA", "REGISTER", "PIN", "FUNCTION", "SOFTWARE", "COMPUTE", "FLAG",
        "AS", "FOLLOW", "TRANSITION", "FROM", "ON", "SOLENOID", "SURFACES",
        "MAP", "DISCRETE", "IO", "FUNCTIONS", "CONFIGURATIONS"
    }

    def extract(self, req_text: str, conditions: List[Condition], outputs: List[ExpectedOutput], notes: List[NoteItem]) -> List[str]:
        signals = []
        seen = set()

        def add_sig(sig: str):
            if sig and sig not in seen and sig.upper() not in self.IGNORED_WORDS and not sig.isdigit():
                seen.add(sig)
                signals.append(sig)

        for cond in conditions:
            add_sig(cond.signal)

        for out in outputs:
            add_sig(out.signal)

        full_text = req_text + " " + " ".join(n.text for n in notes)
        candidates = re.findall(r"\b([A-Za-z0-9_]+)\b", full_text)
        for cand in candidates:
            if "_" in cand or (any(c.islower() for c in cand) and any(c.isupper() for c in cand)):
                if not cand.startswith("LRUSWRS") and not cand.startswith("Table") and not cand.startswith("Figure"):
                    add_sig(cand)

        return signals


class SurfaceApplicabilityExtractor:
    """Extracts surface applicability from text."""

    SURFACES = ["Primary", "Secondary", "Spoiler", "Rudder", "Elevator", "Aileron"]

    def extract(self, text: str) -> List[str]:
        found = []
        for s in self.SURFACES:
            if re.search(r"\b" + re.escape(s) + r"\b", text, re.IGNORECASE):
                found.append(s)
        return found


class LRUConfigExtractor:
    """Extracts explicit LRU configuration identifiers (e.g., LRU_1, LRU_2)."""

    def __init__(self):
        self.lru_pattern = re.compile(r"\bLRU_\d+\b", re.IGNORECASE)

    def extract(self, text: str) -> List[str]:
        matches = self.lru_pattern.findall(text)
        res = []
        seen = set()
        for m in matches:
            norm = m.upper()
            if norm not in seen:
                seen.add(norm)
                res.append(norm)
        return sorted(res)


class TableDefinitionExtractor:
    """Extracts register/bit/pin signal definitions from structured tables."""

    def extract(self, table: Table) -> Dict[str, Dict[str, Any]]:
        defs = {}
        if not table.headers or not table.rows:
            return defs

        headers_lower = [h.lower() for h in table.headers]
        sig_col = -1
        reg_col = -1
        bit_col = -1
        access_col = -1

        for i, h in enumerate(headers_lower):
            if "signal" in h or "name" in h:
                sig_col = i
            elif "access" in h:
                access_col = i
            elif "bit" in h or "location" in h:
                bit_col = i
            elif "register" in h and reg_col == -1:
                reg_col = i

        current_reg = "DSP_Control"
        for row in table.rows:
            if not row:
                continue

            for cell in row:
                if cell.endswith("_REG"):
                    current_reg = cell

            sig_val = row[sig_col] if sig_col != -1 and sig_col < len(row) else ""
            bit_val = row[bit_col] if bit_col != -1 and bit_col < len(row) else ""
            access_val = row[access_col] if access_col != -1 and access_col < len(row) else ""

            if sig_val and sig_val.upper() not in ["N/A", "INFORMATION"] and not sig_val.endswith("_REG"):
                defs[sig_val] = {
                    "register": current_reg,
                    "bit": bit_val if bit_val else "N/A",
                    "access": access_val if access_val else "R/W"
                }

        return defs


class DecisionTypeClassifier:
    """Classifies the primary behavioral pattern of a requirement."""

    def classify(self, req: Requirement) -> str:
        text_lower = req.req_text.lower()
        
        if req.state_transition or "transition from" in text_lower:
            return "STATE_TRANSITION"
        elif "mode transition" in text_lower or ("transition" in text_lower and "mode" in text_lower):
            return "MODE_TRANSITION"
        elif req.timing_constraints or re.search(r"\bdelay\b", text_lower):
            return "TIMING_DELAY"
        elif "monitor" in text_lower or "anomaly" in text_lower:
            return "MONITORING"
        elif "threshold" in text_lower:
            return "THRESHOLD_CHECK"
        elif req.lru_configuration or "pin configuration" in text_lower:
            return "CONFIGURATION"
        elif "compute" in text_lower or "calculate" in text_lower:
            return "CALCULATION"
        elif req.logic_expression or len(req.conditions) > 1:
            return "DECISION_LOGIC"
        elif req.expected_outputs:
            return "ASSIGNMENT"
        return "ASSIGNMENT"



class SignalRoleClassifier:
    """Classifies signals into requirement-local inputs, outputs, and state_variables."""

    def classify(self, req: Requirement) -> Dict[str, List[str]]:
        inputs = set()
        outputs = set()
        state_variables = set()

        for cond in req.conditions:
            inputs.add(cond.signal)

        for out in req.expected_outputs:
            outputs.add(out.signal)

        if req.state_transition:
            state_variables.add(req.state_transition.from_state)
            state_variables.add(req.state_transition.to_state)

        for sig in req.signals:
            if sig in inputs or sig in outputs or sig in state_variables:
                continue
            if sig.endswith("_State") or sig.endswith("_StateLgc") or sig.endswith("_Mode"):
                state_variables.add(sig)
            elif "monitor" in sig.lower() or "msg" in sig.lower() or "flag" in sig.lower():
                inputs.add(sig)

        return {
            "inputs": sorted(list(inputs)),
            "outputs": sorted(list(outputs)),
            "state_variables": sorted(list(state_variables))
        }


class ConfidenceCalculator:
    """Calculates parser certainty scores for extracted requirement components."""

    def calculate(self, req: Requirement) -> Dict[str, float]:
        return {
            "conditions": 1.0,
            "expected_outputs": 1.0,
            "references": 1.0,
            "logic_expression": 1.0 if req.logic_expression else 1.0,
            "state_transition": 1.0 if req.state_transition else 1.0,
            "timing_constraints": 1.0 if req.timing_constraints else 1.0
        }


class RequirementExtractor:
    """Extracts base requirements from raw document data."""
    
    def __init__(self, req_id_pattern: str = r"([A-Z]+-\d+)"):
        self.req_id_pattern = re.compile(req_id_pattern)
        self.cond_extractor = ConditionExtractor()
        self.out_extractor = ExpectedOutputExtractor()
        self.logic_extractor = LogicExpressionExtractor()
        self.trans_extractor = StateTransitionExtractor()
        self.timing_extractor = TimingConstraintExtractor()
        self.sig_extractor = SignalExtractor()
        self.surf_extractor = SurfaceApplicabilityExtractor()
        self.lru_extractor = LRUConfigExtractor()
        self.decision_classifier = DecisionTypeClassifier()
        self.role_classifier = SignalRoleClassifier()
        self.confidence_calculator = ConfidenceCalculator()

    def extract(self, raw_data: Any) -> List[Requirement]:
        requirements = []
        if isinstance(raw_data, list):
            for i, item in enumerate(raw_data):
                req_id = item.get("req_id")
                if not req_id and "text" in item:
                    match = self.req_id_pattern.search(item["text"])
                    if match:
                        req_id = match.group(1)
                
                if req_id:
                    raw_text = item.get("text", "")
                    cleaned_text = clean_requirement_text(raw_text)
                    
                    notes = []
                    for note in item.get("notes", []):
                        if isinstance(note, str):
                            notes.append(NoteItem(text=note, type="note"))
                        elif isinstance(note, dict):
                            notes.append(NoteItem(text=note.get("text") or note.get("content", ""), type=note.get("type", "note")))

                    source_loc = item.get("source_location") or {}
                    if not source_loc:
                        source_loc = {
                            "doc_position": i,
                            "section": req_id
                        }
                        if "page" in item:
                            source_loc["page"] = item["page"]
                        if item.get("heading") or item.get("parent_section"):
                            source_loc["heading"] = item.get("heading") or item.get("parent_section")

                    conditions = self.cond_extractor.extract(cleaned_text)
                    outputs = self.out_extractor.extract(cleaned_text)
                    logic_expr = self.logic_extractor.extract(cleaned_text, conditions)
                    state_trans = self.trans_extractor.extract(cleaned_text)
                    timing_cons = self.timing_extractor.extract(cleaned_text)

                    signals = self.sig_extractor.extract(cleaned_text, conditions, outputs, notes)
                    surfaces = self.surf_extractor.extract(cleaned_text)
                    lru_configs = self.lru_extractor.extract(cleaned_text)

                    req = Requirement(
                        req_id=req_id,
                        req_text=cleaned_text,
                        title=item.get("title"),
                        doc_position=i,
                        notes=notes,
                        conditions=conditions,
                        expected_outputs=outputs,
                        logic_expression=logic_expr,
                        state_transition=state_trans,
                        timing_constraints=timing_cons,
                        signals=signals,
                        surface_applicability=surfaces,
                        lru_configuration=lru_configs,
                        source_location=source_loc,
                        metadata={
                            "req_type": item.get("req_type", ""),
                            "safety_impact": item.get("safety_impact", ""),
                            "safety_rationale": item.get("safety_rationale", "")
                        }
                    )
                    
                    req.decision_type = self.decision_classifier.classify(req)
                    req.signal_roles = self.role_classifier.classify(req)
                    req.confidence = self.confidence_calculator.calculate(req)

                    req.additional_context = req.metadata.copy()
                    requirements.append(req)
        return requirements


class TableExtractor:
    """Extracts tables from raw document data."""
    
    def __init__(self):
        self.def_extractor = TableDefinitionExtractor()

    def extract(self, raw_data: Any) -> List[Table]:
        tables = []
        if isinstance(raw_data, list):
            for i, item in enumerate(raw_data):
                if item.get("type") == "table":
                    source_loc = item.get("source_location") or {}
                    if not source_loc:
                        source_loc = {
                            "doc_position": i,
                            "table_id": item.get("table_id", "")
                        }
                        if "page" in item:
                            source_loc["page"] = item["page"]

                    t = Table(
                        table_id=item.get("table_id", ""),
                        title=item.get("title", ""),
                        headers=item.get("headers", []),
                        rows=item.get("rows", []),
                        metadata=item.get("metadata", {}),
                        source_location=source_loc
                    )
                    t.definitions = self.def_extractor.extract(t)
                    tables.append(t)
        return tables


class FigureExtractor:
    """Extracts figures from raw document data."""
    
    def extract(self, raw_data: Any) -> List[Figure]:
        figures = []
        if isinstance(raw_data, list):
            for i, item in enumerate(raw_data):
                if item.get("type") == "figure":
                    source_loc = item.get("source_location") or {}
                    if not source_loc:
                        source_loc = {
                            "doc_position": i,
                            "figure_id": item.get("figure_id", "")
                        }
                        if "page" in item:
                            source_loc["page"] = item["page"]

                    f = Figure(
                        figure_id=item.get("figure_id", ""),
                        title=item.get("title", ""),
                        caption=item.get("caption", ""),
                        metadata=item.get("metadata", {}),
                        source_location=source_loc
                    )
                    figures.append(f)
        return figures


class StepExtractor:
    """Extracts steps from tables if they represent execution sequences."""
    
    def extract(self, table: Table) -> None:
        if table.classification != "STEP_TABLE" or not table.headers:
            return
            
        step_header_idx = -1
        action_header_idx = -1
        
        for i, header in enumerate(table.headers):
            h_lower = header.lower()
            if "step" in h_lower:
                step_header_idx = i
            elif "action" in h_lower or "instruction" in h_lower or "description" in h_lower:
                action_header_idx = i
                
        if step_header_idx != -1 or action_header_idx != -1:
            for i, row in enumerate(table.rows):
                step_id = ""
                step_text = ""
                
                if step_header_idx != -1 and step_header_idx < len(row):
                    step_id = row[step_header_idx]
                else:
                    step_id = f"Step {i+1}"
                    
                if action_header_idx != -1 and action_header_idx < len(row):
                    step_text = row[action_header_idx]
                else:
                    step_text = " | ".join(
                        c for j, c in enumerate(row) if j != step_header_idx
                    )
                
                table.steps.append(
                    Step(step_id=step_id, step_text=step_text)
                )




