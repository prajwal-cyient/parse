from dataclasses import asdict
from typing import Dict, Any, List

from .models import Document, Requirement, FinalRequirementJSON
from .mappers import CrossReferenceBuilder, EntityIndexBuilder

class ContextBuilder:
    """Builds the final normalized JSON schema for the entire document."""
    
    def __init__(self):
        self.xref_builder = CrossReferenceBuilder()
        self.entity_index_builder = EntityIndexBuilder()

    def build(self, doc: Document) -> Dict[str, Any]:
        """
        Builds the final normalized JSON structure containing:
        - requirements (lightweight requirement objects)
        - tables (global table repository keyed by table_id)
        - figures (global figure repository keyed by figure_id)
        - cross_reference (index of referencing requirements)
        - entity_index (rich knowledge graph of signals, requirements, tables, figures, states, LRUs)
        """
        req_list = []

        for req in doc.requirements:
            # Build dependencies list
            dependencies = []
            for r_id in req.linked_requirements:
                dependencies.append({"type": "requirement", "id": r_id})
            for t_id in req.linked_tables:
                dependencies.append({"type": "table", "id": t_id})
            for f_id in req.linked_figures:
                dependencies.append({"type": "figure", "id": f_id})

            # Format notes
            notes_formatted = []
            for n in req.notes:
                if hasattr(n, "text"):
                    notes_formatted.append({"type": "note", "text": n.text})
                elif isinstance(n, dict):
                    notes_formatted.append({
                        "type": n.get("type", "note"),
                        "text": n.get("text") or n.get("content", "")
                    })

            # Format conditions
            conds_formatted = []
            for c in req.conditions:
                conds_formatted.append({
                    "signal": c.signal,
                    "operator": c.operator,
                    "value": c.value
                })

            # Format expected outputs
            outs_formatted = []
            for o in req.expected_outputs:
                out_item = {
                    "signal": o.signal,
                    "value": o.value
                }
                if o.condition:
                    out_item["condition"] = o.condition
                outs_formatted.append(out_item)

            # Format logic_expression
            logic_expr_formatted = None
            if req.logic_expression:
                logic_expr_formatted = {
                    "operator": req.logic_expression.operator,
                    "operands": req.logic_expression.operands
                }

            # Format state_transition
            state_trans_formatted = None
            if req.state_transition:
                state_trans_formatted = {
                    "from": req.state_transition.from_state,
                    "to": req.state_transition.to_state
                }

            # Format timing_constraints
            timing_cons_formatted = []
            for tc in req.timing_constraints:
                tc_item = {
                    "value": tc.value,
                    "unit": tc.unit
                }
                if tc.tolerance is not None:
                    tc_item["tolerance"] = tc.tolerance
                if tc.type:
                    tc_item["type"] = tc.type
                timing_cons_formatted.append(tc_item)

            req_dict = {
                "requirement_id": req.req_id,
                "requirement_text": req.req_text,
                "conditions": conds_formatted,
                "expected_outputs": outs_formatted,
                "logic_expression": logic_expr_formatted,
                "state_transition": state_trans_formatted,
                "timing_constraints": timing_cons_formatted,
                "decision_type": req.decision_type,
                "signal_roles": req.signal_roles.copy(),
                "confidence": req.confidence.copy(),
                "linked_requirements": req.linked_requirements.copy(),
                "linked_tables": req.linked_tables.copy(),
                "linked_figures": req.linked_figures.copy(),
                "signals": req.signals.copy(),
                "notes": notes_formatted,
                "surface_applicability": req.surface_applicability.copy(),
                "lru_configuration": req.lru_configuration.copy(),
                "dependencies": dependencies,
                "metadata": req.metadata.copy(),
                "source_location": req.source_location.copy()
            }

            req_list.append(req_dict)

        # Format global tables dict (keyed by table_id)
        tables_dict = {}
        for table in doc.tables:
            tables_dict[table.table_id] = asdict(table)

        # Format global figures dict (keyed by figure_id)
        figures_dict = {}
        for figure in doc.figures:
            figures_dict[figure.figure_id] = asdict(figure)

        # Build global cross_reference and entity_index
        xref = self.xref_builder.build(doc)
        entity_index = self.entity_index_builder.build(doc)

        return {
            "requirements": req_list,
            "tables": tables_dict,
            "figures": figures_dict,
            "cross_reference": xref,
            "entity_index": entity_index
        }

    def to_dicts(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Returns the dictionary representation directly."""
        return output


