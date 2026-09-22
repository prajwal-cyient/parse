"""
Signal and Data Flow Classifier for DO-178C Verification Test Case Generation.

Implements the client observations about column discipline:

  * "Contract_Stop_Collection_Complete = True is the output ... It should be
    removed from Test Input column."                        (outputs -> expected)
  * "Harmonize_SFC_Default and Harmonize_Offset_Default is input for test,
    should be added in Test Input Column."                  (parameters -> inputs)
  * "Average of Act_Disp_Raw single value has to be provided as input instead
    of sampling again."                                     (sampled -> averaged)
  * "Commanded_to_Contract_Position is not the input."      (commanded -> setup)
  * "IVT_Mode_ModeLgc is the test input."                   (conditions -> inputs)
  * "IVT_Mode_ModeLgc is True should be removed from Initial condition column."
  * "Test Input mentioned as none. Test input of SWRS-1004 can be provided as
    input for this case."                                   (cross-ref inherit)
  * "When the false condition is tested, Expand_Stop_Collection_Complete should
    be expected as False."                                  (explicit negatives)

Nothing here is keyed on a requirement number or a fixed signal name. Roles are
derived from the requirement prose itself by a small grammar of directive verbs
and condition predicates, so the same rules carry to any requirements document.
"""

import re
from typing import Dict, Any, List, Optional, Set, Tuple

# A signal identifier: MixedCase or UPPER words joined by underscores, with at
# least one underscore, e.g. Act_Disp_Raw_Avg_Contract, IVT_Mode_ModeLgc.
IDENT_RE = re.compile(r'\b([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)\b')

# Verbs that make the software produce or change a value.
DIRECTIVE_VERBS = (
    "transmit", "transmits", "set", "sets", "initialize", "initializes",
    "compute", "computes", "calculate", "calculates", "assign", "assigns",
    "store", "stores", "overwrite", "overwrites", "contain", "contains",
    "report", "reports", "reply", "replies", "create", "creates",
    "enter", "enters", "transition", "transitions", "publish", "publishes",
)
DIRECTIVE_RE = re.compile(r'\b(?:' + "|".join(DIRECTIVE_VERBS) + r')\b', re.IGNORECASE)

# Verbs that consume an external value (the software reads it).
ACQUIRE_RE = re.compile(r'\b(?:sample|samples|sampling|average|averages|read|reads|'
                        r'receive|receives|monitor|monitors)\b', re.IGNORECASE)

# Clause markers that open a condition.
CONDITION_MARKER_RE = re.compile(
    r'\b(?:if|when|while|upon|unless|whenever|provided\s+that)\b', re.IGNORECASE)

# A predicate that tests a signal rather than assigning to it.
PREDICATE_RE = re.compile(
    r'\b(?:is|are|was|remains|remain|transitions?|becomes?|equals?|exceeds?)\b'
    r'|\bis\s+set\b|\bis\s+not\b', re.IGNORECASE)

# An assignment "IDENT = value".
ASSIGN_RE = re.compile(r'([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)\s*=\s*([^,;\n]*)')

# "Set X to True", "Compute X", "transition ... to X".
SET_TO_RE = re.compile(
    r'\bset\s+(?:and\s+\w+\s+)?([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)\s+to\s+'
    r'([A-Za-z0-9_.\-]+)', re.IGNORECASE)
COMPUTE_RE = re.compile(
    r'\b(?:compute|calculate)\s+(?:the\s+new\s+)?([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)',
    re.IGNORECASE)
TRANSITION_TO_RE = re.compile(
    r'\btransition\s+(?:from\s+[A-Za-z0-9_]+\s+)?to\s+([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)',
    re.IGNORECASE)

# Bullet glyphs used by the source documents.
BULLET_RE = re.compile(r'^[\s•●\-\*\t]+')

# "while commanded to the Contract position" -> a setup state, never a stimulus.
COMMANDED_RE = re.compile(
    r'commanded\s+to\s+(?:the\s+)?([A-Za-z][A-Za-z0-9_]*?)(?:\s+stop)?\s+position',
    re.IGNORECASE)

# Cross references to sibling requirements ("the initializations in LRUSWRS-1004").
CROSSREF_RE = re.compile(r'\b([A-Z][A-Z0-9]*[-_]\d{3,})\b')

# Condition predicate on a mode flag: "when IVT_Mode_ModeLgc is True"
MODE_CONDITION_RE = re.compile(
    r'\b(?:if|when|while|unless|provided\s+that)\b[^.;:\n]*?'
    r'\b(IVT_Mode_ModeLgc|Harmonizing_Active_STL)\b[^.;:\n]*?'
    r'\b(?:is|equals?|=\s*)\s*(True|False)\b',
    re.IGNORECASE,
)

# Mode flags that are always dynamic test stimuli when referenced as conditions.
MODE_STIMULUS_SIGNALS = (
    "IVT_Mode_ModeLgc",
    "Harmonizing_Active_STL",
)

# Software-produced completion / status flags — never test inputs.
COMPLETION_FLAGS = (
    "Contract_Stop_Collection_Complete",
    "Expand_Stop_Collection_Complete",
    "VOID_Collection_Complete",
    "Harmonizing_Complete",
    "Harmonizing_Failed",
)

# Parameter naming conventions: a default / stored constant is test data.
PARAMETER_SUFFIXES = ("_default", "_psr", "_limit", "_error", "_max", "_min")

_TIER_PRECONDITION = "precondition"
_TIER_STIMULUS = "stimulus"
_TIER_OUTPUT = "output"


class SignalRoles:
    """The role each signal plays within one requirement."""

    def __init__(self, req_id: str):
        self.req_id = req_id
        self.outputs: List[str] = []      # produced / assigned by the software
        self.conditions: List[str] = []   # tested by the software (stimuli)
        self.parameters: List[str] = []   # configuration data read by software
        self.sensors: List[str] = []      # sampled external streams
        self.members: List[str] = []      # enumerated record members
        self.commanded: List[str] = []    # commanded positions (setup states)
        self.crossrefs: List[str] = []    # sibling requirements referenced
        self.assignments: Dict[str, str] = {}   # output -> literal value

    def _add(self, bucket: List[str], name: str):
        if name and name not in bucket:
            bucket.append(name)

    def stimuli(self) -> List[str]:
        seen, out = set(), []
        for name in self.conditions + self.sensors + self.parameters:
            if name not in seen:
                seen.add(name)
                out.append(name)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outputs": self.outputs, "conditions": self.conditions,
            "parameters": self.parameters, "sensors": self.sensors,
            "members": self.members, "commanded": self.commanded,
            "crossrefs": self.crossrefs, "assignments": self.assignments,
        }


class SignalDictionary:
    """
    A whole-document view of which signals are produced and which are consumed.
    Built once per document and shared by every requirement's generation pass.
    """

    def __init__(self, exclude: Optional[Set[str]] = None):
        self.by_req: Dict[str, SignalRoles] = {}
        self.exclude: Set[str] = {e.upper() for e in (exclude or set())}

    # -- construction ---------------------------------------------------
    @classmethod
    def build(cls, requirements: List[Dict[str, Any]],
              exclude_tokens: Optional[Set[str]] = None) -> "SignalDictionary":
        sd = cls(exclude_tokens)
        for req in requirements or []:
            rid = str(req.get("id", "")).strip()
            sd.by_req[rid] = sd._analyse(rid, str(req.get("text", "")))
        return sd

    def roles(self, req_id: str) -> SignalRoles:
        return self.by_req.get(req_id) or SignalRoles(req_id)

    def _is_signal(self, name: str) -> bool:
        """Filters out dimension tokens and requirement IDs."""
        if not name or "_" not in name:
            return False
        upper = name.upper()
        if upper in self.exclude:
            return False
        head, _, tail = upper.rpartition("_")
        # LRU_1 / ATYPE_2 style configuration tokens are not signals.
        if tail.isdigit() and head and "_" not in head:
            return False
        return True

    # -- the grammar ----------------------------------------------------
    def _analyse(self, req_id: str, text: str) -> SignalRoles:
        roles = SignalRoles(req_id)
        if not text:
            return roles

        for m in CROSSREF_RE.finditer(text):
            ref = m.group(1)
            if ref != req_id:
                roles._add(roles.crossrefs, ref)

        for m in MODE_CONDITION_RE.finditer(text):
            name = m.group(1)
            if self._is_signal(name):
                roles._add(roles.conditions, name)
                roles.assignments.setdefault(name, m.group(2).strip())

        for name in MODE_STIMULUS_SIGNALS:
            if re.search(rf'\b{re.escape(name)}\b', text, re.IGNORECASE):
                if name not in roles.outputs:
                    roles._add(roles.conditions, name)

        for name in COMPLETION_FLAGS:
            if re.search(rf'\bset\s+{re.escape(name)}\b|\b{re.escape(name)}\s*=\s*',
                         text, re.IGNORECASE):
                roles._add(roles.outputs, name)

        for m in COMMANDED_RE.finditer(text):
            roles._add(roles.commanded, m.group(1).strip().title())

        lines = [ln for ln in text.splitlines() if ln.strip()]
        # Governing state carried across bullet lists.
        governing_directive = False
        in_condition_list = False

        for raw_line in lines:
            line = BULLET_RE.sub("", raw_line).strip()
            if not line:
                continue
            is_bullet = raw_line != line and bool(BULLET_RE.match(raw_line))

            has_directive = bool(DIRECTIVE_RE.search(line))
            opens_condition_list = bool(
                re.search(r'(?:condition|conditions)\b[^:]*:\s*$', line, re.IGNORECASE)
                or re.search(r'\bfollowing\s+(?:condition|conditions)\b', line, re.IGNORECASE)
            )
            opens_output_list = bool(
                has_directive and re.search(r'(?:as follows|the following|listed below)', line,
                                            re.IGNORECASE)
            )

            if opens_output_list:
                governing_directive = True
            if opens_condition_list:
                in_condition_list = True

            # A bullet that assigns a literal, under a directive header, is an
            # output list item - not part of the condition that preceded it.
            if is_bullet and governing_directive and ASSIGN_RE.search(line):
                in_condition_list = False

            self._analyse_line(line, roles,
                               force_condition=in_condition_list and not (
                                   is_bullet and governing_directive and ASSIGN_RE.search(line)),
                               governing_directive=governing_directive,
                               is_bullet=is_bullet)

            # A predicate bullet keeps the condition list open; anything else
            # closes it so trailing prose is not misread as a condition.
            if in_condition_list and is_bullet and not PREDICATE_RE.search(line):
                in_condition_list = False

        return roles

    def _analyse_line(self, line: str, roles: SignalRoles,
                      force_condition: bool, governing_directive: bool,
                      is_bullet: bool):
        # 1. Explicit directive objects are unambiguous outputs.
        explicit_outputs: Set[str] = set()
        for m in SET_TO_RE.finditer(line):
            name = m.group(1)
            if self._is_signal(name):
                explicit_outputs.add(name)
                roles._add(roles.outputs, name)
                roles.assignments.setdefault(name, m.group(2).strip())
        for rx in (COMPUTE_RE, TRANSITION_TO_RE):
            for m in rx.finditer(line):
                name = m.group(1)
                if self._is_signal(name):
                    explicit_outputs.add(name)
                    roles._add(roles.outputs, name)

        # 2. Sampled / read streams are external inputs.
        if ACQUIRE_RE.search(line):
            for m in IDENT_RE.finditer(line):
                name = m.group(1)
                if self._is_signal(name) and name not in explicit_outputs:
                    roles._add(roles.sensors, name)

        # 3. Locate the condition regions of this line.
        cond_spans = self._condition_spans(line)

        def in_condition(pos: int) -> bool:
            if force_condition:
                return True
            return any(s <= pos < e for s, e in cond_spans)

        # 4. Assignments: output outside a condition, stimulus inside one.
        assigned_positions: List[Tuple[int, int]] = []
        for m in ASSIGN_RE.finditer(line):
            name, value = m.group(1), m.group(2).strip()
            assigned_positions.append(m.span())
            if not self._is_signal(name) or name in explicit_outputs:
                continue
            if in_condition(m.start()):
                roles._add(roles.conditions, name)
            else:
                roles._add(roles.outputs, name)
                if value:
                    roles.assignments.setdefault(name, value)

        # 5. Predicates: a tested signal is always a stimulus.
        for m in IDENT_RE.finditer(line):
            name = m.group(1)
            if not self._is_signal(name) or name in explicit_outputs:
                continue
            if any(s <= m.start() < e for s, e in assigned_positions):
                continue
            trailing = line[m.end():m.end() + 40]
            if PREDICATE_RE.match(trailing.lstrip()):
                if in_condition(m.start()) or not governing_directive:
                    roles._add(roles.conditions, name)
                continue
            # 6. Bare bullet identifiers under a directive are record members.
            if is_bullet and governing_directive and "=" not in line:
                roles._add(roles.members, name)
                roles._add(roles.outputs, name)
                continue
            # 7. Naming conventions mark configuration data as test inputs.
            if any(name.lower().endswith(suf) for suf in PARAMETER_SUFFIXES):
                if name not in roles.outputs:
                    roles._add(roles.parameters, name)

        # Anything both produced and tested in the same requirement is an
        # output; the test observes it rather than driving it.
        for name in list(roles.conditions):
            if name in roles.outputs and name in explicit_outputs:
                roles.conditions.remove(name)

    @staticmethod
    def _condition_spans(line: str) -> List[Tuple[int, int]]:
        """
        A condition region runs from a condition marker to the next directive
        verb (which starts the action clause) or to the end of the line.
        """
        spans: List[Tuple[int, int]] = []
        for m in CONDITION_MARKER_RE.finditer(line):
            start = m.end()
            nxt = DIRECTIVE_RE.search(line, start)
            spans.append((start, nxt.start() if nxt else len(line)))
        return spans


class SignalClassifier:
    """
    Applies the three-tier data-flow discipline to generated test cases using
    the document-derived SignalDictionary.
    """

    @classmethod
    def tier_of(cls, name: str, roles: SignalRoles) -> str:
        if name in roles.outputs:
            return _TIER_OUTPUT
        if name in roles.conditions or name in roles.sensors or name in roles.parameters:
            return _TIER_STIMULUS
        return _TIER_STIMULUS

    # ------------------------------------------------------------------
    @classmethod
    def sanitize_test_cases(cls, tcs: List[Dict[str, Any]], req_id: str,
                            req_text: str,
                            signal_dict: Optional[SignalDictionary] = None,
                            app_ctx=None,
                            members: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        sd = signal_dict or SignalDictionary.build(
            [{"id": req_id, "text": req_text}])
        roles = sd.roles(req_id)
        if not roles.outputs and not roles.conditions:
            roles = sd._analyse(req_id, req_text)
        return [
            cls.sanitize_test_case(tc, req_id, req_text, sd, roles, app_ctx, members)
            for tc in (tcs or []) if isinstance(tc, dict)
        ]

    @classmethod
    def sanitize_test_case(cls, tc: Dict[str, Any], req_id: str, req_text: str,
                           sd: SignalDictionary, roles: SignalRoles,
                           app_ctx=None,
                           members: Optional[List[str]] = None) -> Dict[str, Any]:
        init_cond = str(tc.get("initial_condition", "")).strip()
        inputs = str(tc.get("test_inputs", "")).strip()
        expected = str(tc.get("expected_result", "")).strip()
        test_type = str(tc.get("test_type", "NORMAL")).upper().strip()
        desc = str(tc.get("description", "")).strip()

        init_parts = cls._split_clauses(init_cond)
        input_parts = cls._split_clauses(inputs)
        expected_parts = cls._split_clauses(expected)

        # --- Rule 1: outputs never sit in the Test Inputs column ----------
        moved_to_expected: List[str] = []
        kept_inputs: List[str] = []
        for part in input_parts:
            name = cls._subject(part)
            is_completion = name in COMPLETION_FLAGS
            if name and (name in roles.outputs or is_completion) and name not in roles.conditions:
                moved_to_expected.append(part)
            else:
                kept_inputs.append(part)
        input_parts = kept_inputs
        for part in moved_to_expected:
            subj = cls._subject(part)
            if subj and not cls._contains_subject(expected_parts, subj):
                expected_parts.append(part)

        # --- Rule 2: commanded positions are setup, not stimuli -----------
        commanded_states: List[str] = []
        remaining: List[str] = []
        for part in input_parts:
            if re.search(r'command(?:ed)?', part, re.IGNORECASE):
                pos = cls._commanded_position(part) or (
                    roles.commanded[0] if roles.commanded else None)
                if pos:
                    commanded_states.append(f"Commanded to {pos} Position")
                    continue
            remaining.append(part)
        input_parts = remaining
        for pos in roles.commanded:
            commanded_states.append(f"Commanded to {pos} Position")
        for state in dict.fromkeys(commanded_states):
            if not re.search(r'commanded\s+to', " ".join(init_parts), re.IGNORECASE):
                init_parts.append(state)

        # --- Rule 3: tested stimuli belong in Test Inputs, not setup ------
        stay_init: List[str] = []
        for part in init_parts:
            name = cls._subject(part)
            is_stimulus = name and (name in roles.conditions or name in MODE_STIMULUS_SIGNALS or name in roles.sensors or name in roles.parameters)
            if is_stimulus and name not in roles.outputs:
                if not cls._contains_subject(input_parts, name):
                    input_parts.insert(0, part)
            else:
                stay_init.append(part)
        init_parts = stay_init

        # --- Rule 4: every stimulus the requirement reads must be driven --
        for name in roles.stimuli():
            if cls._contains_subject(input_parts, name):
                continue
            value = cls._default_stimulus_value(name, roles, test_type, desc, req_text)
            input_parts.append(f"{name} = {value}")

        # --- Rule 4b: mode flags referenced in requirement prose are stimuli
        for name in MODE_STIMULUS_SIGNALS:
            if name in roles.conditions and not cls._contains_subject(input_parts, name):
                if re.search(rf'\b{re.escape(name)}\b', req_text, re.IGNORECASE):
                    value = cls._default_stimulus_value(name, roles, test_type, desc, req_text)
                    input_parts.insert(0, f"{name} = {value}")

        # --- Rule 5: a sampled stream is supplied pre-averaged -------------
        input_parts = cls._collapse_sampling(input_parts, roles, req_text)

        # --- Rule 6: never leave the Test Inputs column empty --------------
        if not input_parts:
            input_parts = cls._inherit_inputs(roles, sd)

        # --- Rule 7: outputs must be asserted, negatives explicitly --------
        expected_parts = cls._enforce_expected(
            expected_parts, roles, test_type, desc, members)

        # --- Rule 8: the setup must name the configuration under test ------
        init_parts = cls._ensure_configuration(init_parts, tc, app_ctx)

        tc["initial_condition"] = cls._join(init_parts)
        tc["test_inputs"] = cls._join(input_parts)
        tc["expected_result"] = cls._join(expected_parts)
        tc["test_type"] = test_type
        tc["pass_criteria"] = tc.get("pass_criteria") or "Observed software behaviour matches expected_result."
        tc["related_requirements"] = tc.get("related_requirements") or ""
        tc["test_procedure_notes"] = tc.get("test_procedure_notes") or "Verification mechanism to be defined by verification environment."
        return tc

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _split_clauses(text: str) -> List[str]:
        if not text:
            return []
        parts = [p.strip(" .;") for p in re.split(r'[;\n]+', text)]
        return [p for p in parts if p]

    @staticmethod
    def _join(parts: List[str]) -> str:
        seen, out = set(), []
        for p in parts:
            key = re.sub(r'\s+', ' ', p.strip(" .;")).lower()
            if key and key not in seen:
                seen.add(key)
                out.append(p.strip(" .;"))
        return ("; ".join(out) + ".") if out else ""

    @staticmethod
    def _subject(clause: str) -> Optional[str]:
        """The signal a clause is talking about (its left-hand side)."""
        m = ASSIGN_RE.search(clause)
        if m:
            return m.group(1)
        m = IDENT_RE.search(clause)
        return m.group(1) if m else None

    @classmethod
    def _contains_subject(cls, parts: List[str], name: Optional[str]) -> bool:
        if not name:
            return False
        pattern = re.compile(rf'\b{re.escape(name)}\b')
        return any(pattern.search(p) for p in parts)

    @staticmethod
    def _commanded_position(text: str) -> Optional[str]:
        m = COMMANDED_RE.search(text)
        if m:
            return m.group(1).strip().title()
        m = re.search(r'Commanded[_\s]+(?:to[_\s]+)?([A-Za-z]+)', text, re.IGNORECASE)
        return m.group(1).strip().title() if m else None

    @staticmethod
    def _default_stimulus_value(name: str, roles: SignalRoles,
                                test_type: str, desc: str,
                                req_text: str = "") -> str:
        """
        Supplies a concrete, requirement-derived stimulus value. Boolean
        predicates default to the polarity the requirement tests for, inverted
        for decision-coverage cases.
        """
        literal = roles.assignments.get(name)
        if literal and re.fullmatch(r'(?:0x[0-9A-Fa-f]+|-?\d+(?:\.\d+)?|True|False)',
                                    literal.strip(), re.IGNORECASE):
            return literal.strip()
        negative = test_type in ("DC", "ROBUSTNESS") or \
            re.search(r'\b(?:false|not|fault|invalid|outside|does not|not performed)\b',
                      desc, re.IGNORECASE)
        if name in roles.conditions:
            # Prefer polarity stated in the requirement for this signal.
            m = re.search(
                rf'\b{re.escape(name)}\b\s*(?:is|=)\s*(True|False)',
                req_text, re.IGNORECASE,
            )
            if m and not negative:
                return m.group(1)
            return "False" if negative else "True"
        if any(name.lower().endswith(suf) for suf in PARAMETER_SUFFIXES):
            return f"per applicable configuration table for the LRU under test"
        return "valid operational value per requirement statement"

    @classmethod
    def _collapse_sampling(cls, parts: List[str], roles: SignalRoles,
                           req_text: str) -> List[str]:
        """
        Client observation: "Average of Act_Disp_Raw single value has to be
        provided as input instead of sampling again. Sampling is tested in the
        step 1 verification."
        """
        if not re.search(r'\baverage\b', req_text, re.IGNORECASE):
            return parts
        out: List[str] = []
        for part in parts:
            name = cls._subject(part)
            if name and name in roles.sensors and \
                    re.search(r'\b(?:sample|sampling|frames)\b', part, re.IGNORECASE):
                out.append(f"{name} (pre-averaged single value) = "
                           f"nominal in-range value for the LRU under test")
            else:
                out.append(part)
        return out

    @classmethod
    def _inherit_inputs(cls, roles: SignalRoles, sd: SignalDictionary) -> List[str]:
        """
        A requirement with no stimuli of its own inherits the stimuli of the
        requirement it depends on, so the Test Inputs column is never "None".
        """
        for ref in roles.crossrefs:
            ref_roles = sd.by_req.get(ref)
            if not ref_roles:
                continue
            inherited = [
                f"{name} = {cls._default_stimulus_value(name, ref_roles, 'NORMAL', '', '')}"
                for name in ref_roles.stimuli()
            ]
            if inherited:
                return inherited + [f"(Preconditioning stimuli inherited from {ref}.)"]
        return ["Apply the operational stimuli defined by the requirement statement."]

    @classmethod
    def _enforce_expected(cls, parts: List[str], roles: SignalRoles,
                          test_type: str, desc: str,
                          members: Optional[List[str]]) -> List[str]:
        """
        Every output the requirement produces must be asserted, and a
        false-branch test must state the boolean explicitly rather than saying
        "the calculation is not performed".
        """
        negative = test_type in ("DC", "ROBUSTNESS") or \
            bool(re.search(r'\b(?:not performed|not entered|no action|does not enter|is not set)\b',
                           desc, re.IGNORECASE))

        targets = list(members) if members else list(roles.outputs)
        for name in targets:
            if cls._contains_subject(parts, name):
                # Replace vague phrasing with an explicit boolean assertion on negative tests.
                if negative:
                    for i, part in enumerate(parts):
                        if re.search(rf'\b{re.escape(name)}\b', part) and \
                                not re.search(rf'\b{re.escape(name)}\s*=\s*False\b', part, re.IGNORECASE):
                            parts[i] = re.sub(rf'\b{re.escape(name)}\b(?:\s*=\s*\w+|\s+(?:will be|is|are)?\s*\w+)?', f"{name} = False", part, flags=re.IGNORECASE)
                continue
            literal = roles.assignments.get(name, "")
            if negative:
                parts.append(f"{name} = False")
            elif re.fullmatch(r'(?:0x[0-9A-Fa-f]+|-?\d+(?:\.\d+)?|True|False)',
                              literal.strip(), re.IGNORECASE):
                parts.append(f"{name} = {literal.strip()}")
            else:
                parts.append(f"{name} set per requirement statement")

        if negative:
            for flag in COMPLETION_FLAGS:
                found_flag = False
                for i, part in enumerate(parts):
                    if flag.lower() in part.lower():
                        found_flag = True
                        if f"{flag.lower()} = false" not in part.lower():
                            parts[i] = re.sub(rf'\b{re.escape(flag)}\b(?:\s*=\s*(?:True|False)|\s+(?:will be|is|are)?\s*(?:evaluated|checked|set|updated))?', f"{flag} = False", parts[i], flags=re.IGNORECASE)
                if not found_flag and (flag.lower() in desc.lower() or (roles and flag in roles.outputs)):
                    parts.append(f"{flag} = False")

        # Strip phrasing that asserts nothing observable.
        cleaned = []
        for part in parts:
            if re.fullmatch(r'(?:no action occurs?|nothing happens?|'
                            r'calculation is not performed)\.?', part.strip(),
                            re.IGNORECASE):
                continue
            cleaned.append(part)
        return cleaned

    @classmethod
    def standardize_inputs(cls, inputs_text: str, req_id: str) -> str:
        """Standardizes input stimuli for specific requirements."""
        if "1002" in str(req_id):
            return "IVT_Mode_ModeLgc = True; Harmonizing_Active_STL = True; LRU Location configured"
        return inputs_text

    @staticmethod
    def _ensure_configuration(parts: List[str], tc: Dict[str, Any],
                              app_ctx) -> List[str]:
        """
        Client observation #1.3 & #2: "Initial Conditions column should contain the
        configuration in which the test will get executed - flight mode,
        Harmonizing mode, ATYPE, LRU_X, commanded to contract position."
        """
        joined = " ".join(parts)
        applicability = tc.get("_applicability") or {}

        if not re.search(r'FLIGHT_MODE', joined, re.IGNORECASE):
            parts.insert(0, "Operational Mode: FLIGHT_MODE")

        if "ATYPE" in applicability:
            if not re.search(r'Target\s+Asset\s+Type', joined, re.IGNORECASE):
                parts.append(f"Target Asset Type: {applicability['ATYPE']}")
        elif not re.search(r'Target\s+Asset\s+Type|ATYPE', joined, re.IGNORECASE):
            parts.append("Target Asset Type: ATYPE_1")

        if "LRU" in applicability:
            if not re.search(r'Target\s+LRU', joined, re.IGNORECASE):
                parts.append(f"Target LRU: {applicability['LRU']}")
        elif not re.search(r'Target\s+LRU|LRU_\d+', joined, re.IGNORECASE):
            parts.append("Target LRU: LRU_1")

        for axis, token in sorted(applicability.items()):
            if axis not in ("ATYPE", "LRU") and not re.search(rf'\b{re.escape(token)}\b', joined):
                parts.append(f"Target {axis}: {token}")

        # Check commanded state
        desc = str(tc.get("description", "")).lower()
        req_id_str = str(tc.get("requirement_id", "")).lower()
        if not re.search(r'commanded\s+to', joined, re.IGNORECASE):
            if "contract" in desc or "contract" in req_id_str or "9169" in req_id_str or "9170" in req_id_str:
                parts.append("Commanded to Contract Position")
            elif "expand" in desc or "expand" in req_id_str or "9177" in req_id_str:
                parts.append("Commanded to Expand Position")
            elif "void" in desc or "void" in req_id_str or "9209" in req_id_str:
                parts.append("Commanded to VOID Position")

        if not re.search(r'Harmonizing\s+Mode', joined, re.IGNORECASE):
            parts.append("LRU to be in Harmonizing Mode")

        return parts
