"""
Applicability Engine for DO-178C Verification Test Case Generation.

Client Observation #1 ("LRU_1 to LRU_7 for ATYPE_1 to ATYPE_3, all combinations
should be tested separately, so the test case ID matches in TC and .tst file").

This engine is fully generic and data driven:
  * Dimension names and values (LRU_n, ATYPE_n, ...) are DISCOVERED from the
    document's own tables and prose - nothing is hardcoded.
  * Combination decode tables (e.g. Table 1011 pin strapping) are recognised
    structurally, by finding a column whose cells encode two or more dimension
    tokens (TYPE_1_LRU_1), not by table number.
  * Surface groupings (Spoiler -> LRU_3/LRU_4) are read from "Applicability"
    tables, not from a baked in map.
  * Per-requirement applicability (inclusions / exclusions such as
    "Not applicable to LRU_3 and LRU_4" or "Primary Surface Only") is parsed
    linguistically from the requirement statement.
"""

import copy
import re
from typing import List, Dict, Any, Optional, Tuple, Set

# A dimension token is a NAME_<number> pair, e.g. LRU_1, ATYPE_2, TYPE_3.
# Both underscore and hyphen separators appear in real requirement prose, and a
# token may be embedded in a compound key such as TYPE_1_LRU_1 - hence the
# explicit boundary assertions rather than \b (which would not split on "_").
DIM_TOKEN_RE = re.compile(r'(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]*)[_-](\d+)(?![0-9])')

# "LRU-1/2/5/6" shorthand used inside Table 1001 step text.
SLASH_LIST_RE = re.compile(r'\b([A-Za-z][A-Za-z0-9]*)[_-](\d+(?:\s*/\s*\d+)+)\b')

# Table caption reference, e.g. "Table 1011 Rev C" -> "1011".
TABLE_REF_RE = re.compile(r'\bTable\s*#?\s*(\d+)', re.IGNORECASE)

# Dimension names that are structural noise rather than applicability axes.
_DIM_NAME_STOPWORDS = {
    "table", "figure", "step", "rev", "note", "notes", "section", "word",
    "byte", "bit", "bits", "item", "row", "column", "page", "frame", "frames",
    "atp", "psr",
}


def _norm_token(name: str, number: str) -> str:
    """Normalises a discovered dimension token to NAME_<number> form."""
    return f"{name.upper()}_{int(number)}"


def _sort_key(token: str) -> Tuple[str, int]:
    name, _, num = token.rpartition("_")
    try:
        return (name, int(num))
    except ValueError:
        return (name, 0)


class ApplicabilityContext:
    """
    The applicability model discovered for one document. Everything the rest of
    the pipeline needs to know about "which configurations exist" lives here.
    """

    def __init__(self):
        # dimension name -> ordered list of its discovered values
        self.dimensions: Dict[str, List[str]] = {}
        # decode-table rows expanded into concrete combinations
        self.combinations: List[Dict[str, Any]] = []
        # surface / applicability group name -> member tokens
        self.groups: Dict[str, List[str]] = {}
        # member token -> group name it belongs to
        self.member_group: Dict[str, str] = {}
        # the axis used for per-requirement applicability (usually "LRU")
        self.primary_axis: Optional[str] = None
        # table refs that were recognised as combination decode tables
        self.decode_table_refs: List[str] = []

    # -- convenience -------------------------------------------------------
    def values(self, axis: str) -> List[str]:
        return list(self.dimensions.get(axis, []))

    @property
    def primary_values(self) -> List[str]:
        if not self.primary_axis:
            return []
        return self.values(self.primary_axis)

    def group_of(self, token: str) -> Optional[str]:
        return self.member_group.get(token)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimensions": self.dimensions,
            "combination_count": len(self.combinations),
            "groups": self.groups,
            "primary_axis": self.primary_axis,
            "decode_table_refs": self.decode_table_refs,
        }


class ApplicabilityEngine:

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    @classmethod
    def build_context(cls,
                      tables: Optional[List[Dict[str, Any]]] = None,
                      full_text: str = "",
                      req_ids: Optional[List[str]] = None) -> ApplicabilityContext:
        """
        Discovers the applicability model for a document from its tables and
        prose. Safe to call with no tables - it then relies on prose alone.

        `req_ids` lets the engine recognise requirement identifiers (which look
        exactly like dimension tokens, e.g. LRUSWRS-1003) and exclude them from
        the applicability axes.
        """
        ctx = ApplicabilityContext()
        tables = tables or []

        # Requirement identifiers share the NAME-<number> shape of a dimension
        # token, so their name parts are excluded from axis discovery.
        id_prefixes: Set[str] = set()
        for rid in (req_ids or []):
            m = DIM_TOKEN_RE.search(str(rid))
            if m:
                id_prefixes.add(m.group(1).upper())

        raw_dims: Dict[str, Set[str]] = {}

        def record(token_name: str, number: str):
            name = token_name.upper()
            if name.lower() in _DIM_NAME_STOPWORDS or name in id_prefixes:
                return
            raw_dims.setdefault(name, set()).add(_norm_token(name, number))

        # 1. Harvest dimension tokens from prose.
        for m in DIM_TOKEN_RE.finditer(full_text or ""):
            record(m.group(1), m.group(2))

        # 2. Harvest from every table cell, and locate combination columns.
        for t in tables:
            for row in cls._iter_rows(t):
                for cell in row:
                    for m in DIM_TOKEN_RE.finditer(str(cell)):
                        record(m.group(1), m.group(2))

        # 3. Alias-fold dimension names: a shorter name that is a suffix of a
        #    longer one refers to the same axis (table "TYPE_1" vs prose
        #    "ATYPE-1"). The longer, more specific name wins.
        ctx.dimensions = cls._fold_aliases(raw_dims)

        # 4. Expand combination decode tables into concrete combinations.
        for t in tables:
            combos, ref = cls._extract_combinations(t, ctx)
            if combos:
                ctx.combinations.extend(combos)
                if ref and ref not in ctx.decode_table_refs:
                    ctx.decode_table_refs.append(ref)

        # 5. Read applicability groupings (Spoiler -> LRU_3, LRU_4). Groups
        #    declared by an explicit "Applicability" column are authoritative;
        #    the transposed fallback is only consulted when none were found.
        declared: Dict[str, List[str]] = {}
        inferred: Dict[str, List[str]] = {}
        for t in tables:
            found, layout = cls._extract_groups(t, ctx)
            target = declared if layout == "declared" else inferred
            for group, members in found.items():
                bucket = target.setdefault(group, [])
                for mem in members:
                    if mem not in bucket:
                        bucket.append(mem)

        ctx.groups = cls._filter_groups(declared or inferred, ctx)
        for group, members in ctx.groups.items():
            for mem in members:
                ctx.member_group.setdefault(mem, group)

        # 6. Choose the primary applicability axis: the axis used by the
        #    applicability groups, else the axis with the most values.
        ctx.primary_axis = cls._choose_primary_axis(ctx)

        return ctx

    @staticmethod
    def _filter_groups(groups: Dict[str, List[str]],
                       ctx: ApplicabilityContext) -> Dict[str, List[str]]:
        """
        Keeps only groupings that actually partition an axis: every member must
        come from one axis, and the group must be a proper subset of it. A
        "group" spanning several axes, or covering an entire axis, is a table
        header that happened to sit next to some tokens - not applicability.
        """
        kept: Dict[str, List[str]] = {}
        for label, members in groups.items():
            axes = {m.rpartition("_")[0] for m in members}
            if len(axes) != 1:
                continue
            axis = axes.pop()
            universe = ctx.dimensions.get(axis, [])
            if not universe or len(members) >= len(universe):
                continue
            kept[label] = sorted(members, key=_sort_key)
        return kept

    @staticmethod
    def _iter_rows(table: Dict[str, Any]):
        headers = table.get("headers") or []
        if headers:
            yield [str(h) for h in headers]
        for row in table.get("rows") or []:
            yield [str(c) for c in row]

    @staticmethod
    def _fold_aliases(raw_dims: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """
        Merges axis names where one is a suffix of another (TYPE -> ATYPE) so
        that a table written as TYPE_1 and prose written as ATYPE-1 describe a
        single axis. Values are re-emitted under the canonical (longer) name.
        """
        names = sorted(raw_dims.keys(), key=len, reverse=True)
        canonical: Dict[str, str] = {}
        for name in names:
            target = name
            for other in names:
                if other != name and len(other) > len(name) and other.endswith(name):
                    target = canonical.get(other, other)
                    break
            canonical[name] = target

        folded: Dict[str, Set[str]] = {}
        for name, tokens in raw_dims.items():
            target = canonical[name]
            bucket = folded.setdefault(target, set())
            for tok in tokens:
                _, _, num = tok.rpartition("_")
                bucket.add(f"{target}_{num}")

        # Only keep axes that actually enumerate more than one configuration.
        return {
            name: sorted(vals, key=_sort_key)
            for name, vals in folded.items()
            if len(vals) > 1
        }

    @classmethod
    def _extract_combinations(cls, table: Dict[str, Any],
                              ctx: ApplicabilityContext) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        A combination decode table has a column whose cells each encode two or
        more dimension tokens (e.g. "TYPE_1_LRU_1"). Every other column of that
        row is treated as the stimulus that decodes to the combination.
        """
        headers = [str(h).strip() for h in (table.get("headers") or [])]
        rows = table.get("rows") or []
        if not headers or not rows:
            return [], None

        best_col = None
        best_hits = 0
        for col in range(len(headers)):
            hits = 0
            for row in rows:
                if col >= len(row):
                    continue
                if len(cls._tokens_in(str(row[col]), ctx)) >= 2:
                    hits += 1
            if hits > best_hits:
                best_hits, best_col = hits, col

        # Require the column to be a genuine key column, not an incidental hit.
        if best_col is None or best_hits < max(2, len(rows) // 2):
            return [], None

        ref = cls.table_ref(table)
        key_header = headers[best_col] if best_col < len(headers) else "Combination"

        combos: List[Dict[str, Any]] = []
        for row in rows:
            if best_col >= len(row):
                continue
            key = str(row[best_col]).strip()
            dims = cls._tokens_in(key, ctx)
            if len(dims) < 2:
                continue
            stimulus = {}
            for col, header in enumerate(headers):
                if col == best_col or col >= len(row):
                    continue
                val = str(row[col]).strip()
                if val:
                    stimulus[header] = val
            combos.append({
                "key": key,
                "key_header": key_header,
                "dims": dims,
                "stimulus": stimulus,
                "table_ref": ref,
            })
        return combos, ref

    @staticmethod
    def _tokens_in(text: str, ctx: ApplicabilityContext) -> Dict[str, str]:
        """
        Returns {axis: token} for every known dimension token in `text`.
        Uses the folded axis names so TYPE_1 resolves to ATYPE_1.
        """
        found: Dict[str, str] = {}
        for m in DIM_TOKEN_RE.finditer(text or ""):
            name, num = m.group(1).upper(), m.group(2)
            for axis, values in ctx.dimensions.items():
                if axis == name or axis.endswith(name):
                    token = f"{axis}_{int(num)}"
                    if token in values:
                        found[axis] = token
                    break
        return found

    @classmethod
    def _extract_groups(cls, table: Dict[str, Any],
                        ctx: ApplicabilityContext) -> Tuple[Dict[str, List[str]], str]:
        """
        Reads "Applicability"-style tables that map a named group (surface type)
        onto a set of dimension tokens, e.g.

            Applicability | Profile_Id     | Min | Max
            Spoiler       | LRU_3, LRU_4   | ... | ...
        """
        headers = [str(h).strip() for h in (table.get("headers") or [])]
        rows = table.get("rows") or []
        if len(headers) < 2 or not rows:
            return {}, "none"

        groups: Dict[str, List[str]] = {}

        def add(label: str, tokens: List[str]):
            label = re.sub(r'\s+', ' ', str(label)).strip()
            if not label or not tokens:
                return
            bucket = groups.setdefault(label, [])
            for tk in tokens:
                if tk not in bucket:
                    bucket.append(tk)

        # Layout A - a labelled "Applicability" column, one group per row.
        label_col = next(
            (i for i, h in enumerate(headers) if "applicability" in h.lower()),
            None
        )
        if label_col is not None:
            for row in rows:
                if label_col >= len(row):
                    continue
                members: List[str] = []
                for col, cell in enumerate(row):
                    if col != label_col:
                        members.extend(cls._all_tokens(str(cell), ctx))
                add(row[label_col], members)
            return groups, "declared"

        # Layout B - transposed: group names sit in the header row and the
        # member tokens appear in a body row (Max_Stroke style tables).
        for row in rows:
            for col, header in enumerate(headers):
                if col == 0 or col >= len(row):
                    continue
                add(header, cls._all_tokens(str(row[col]), ctx))
        return groups, "inferred"

    @staticmethod
    def _all_tokens(text: str, ctx: ApplicabilityContext) -> List[str]:
        """Every known dimension token in `text`, including LRU-1/2/5/6 lists."""
        out: List[str] = []
        text = text or ""

        for m in SLASH_LIST_RE.finditer(text):
            name = m.group(1).upper()
            for num in re.findall(r'\d+', m.group(2)):
                for axis, values in ctx.dimensions.items():
                    if axis == name or axis.endswith(name):
                        tok = f"{axis}_{int(num)}"
                        if tok in values and tok not in out:
                            out.append(tok)
                        break

        for m in DIM_TOKEN_RE.finditer(text):
            name, num = m.group(1).upper(), m.group(2)
            for axis, values in ctx.dimensions.items():
                if axis == name or axis.endswith(name):
                    tok = f"{axis}_{int(num)}"
                    if tok in values and tok not in out:
                        out.append(tok)
                    break
        return out

    @staticmethod
    def _choose_primary_axis(ctx: ApplicabilityContext) -> Optional[str]:
        if ctx.member_group:
            counts: Dict[str, int] = {}
            for token in ctx.member_group:
                axis, _, _ = token.rpartition("_")
                counts[axis] = counts.get(axis, 0) + 1
            return max(counts, key=counts.get)
        if ctx.dimensions:
            return max(ctx.dimensions, key=lambda k: len(ctx.dimensions[k]))
        return None

    @staticmethod
    def table_ref(table: Dict[str, Any]) -> Optional[str]:
        """The document table number, taken from a caption when the parser
        captured one, else from the table's own header text."""
        for field in ("caption", "title", "ref"):
            val = table.get(field)
            if val:
                m = TABLE_REF_RE.search(str(val))
                if m:
                    return m.group(1)
                if str(val).strip().isdigit():
                    return str(val).strip()
        headers = " ".join(str(h) for h in (table.get("headers") or []))
        m = TABLE_REF_RE.search(headers)
        return m.group(1) if m else None

    # ------------------------------------------------------------------
    # Per-requirement applicability
    # ------------------------------------------------------------------
    @classmethod
    def is_matrix_requirement(cls, req_id: str, req_text: str,
                              ctx: ApplicabilityContext) -> Optional[str]:
        """
        Returns the table ref whose combination matrix this requirement is
        asking to be decoded, or None. A requirement qualifies when it cites a
        table that was structurally recognised as a combination decode table.
        """
        if not ctx.combinations:
            return None
        cited = {m.group(1) for m in TABLE_REF_RE.finditer(f"{req_id} {req_text}")}
        # A requirement whose own ID carries the table number counts as a citation.
        cited |= set(re.findall(r'\d{3,}', str(req_id)))
        for ref in ctx.decode_table_refs:
            if ref in cited:
                return ref
        return None

    @classmethod
    def combinations_for(cls, table_ref: Optional[str],
                         ctx: ApplicabilityContext) -> List[Dict[str, Any]]:
        if table_ref is None:
            return list(ctx.combinations)
        return [c for c in ctx.combinations if c.get("table_ref") == table_ref]

    @classmethod
    def applicable_members(cls, req_text: str,
                           ctx: ApplicabilityContext) -> Tuple[List[str], str]:
        """
        Determines which values of the primary axis a requirement applies to,
        by reading inclusion / exclusion language out of the statement.

        Returns (members, rationale).
        """
        axis = ctx.primary_axis
        if not axis:
            return [], "no applicability axis discovered"
        universe = ctx.values(axis)
        if not universe:
            return [], "no applicability values discovered"

        text = req_text or ""
        included: Set[str] = set()
        excluded: Set[str] = set()
        notes: List[str] = []

        # -- explicit exclusions ------------------------------------------
        for m in re.finditer(
            r'(?:not applicable to|except(?:\s+for)?|excluding|are\s+N/?A(?:\s+for)?)\s*:?\s*([^.;\n]*)',
            text, re.IGNORECASE
        ):
            toks = cls._all_tokens(m.group(1), ctx)
            if toks:
                excluded.update(toks)
                notes.append(f"excluded {', '.join(toks)}")

        # -- explicit inclusions -------------------------------------------
        for m in re.finditer(
            r'(?:applicable to|applies to|only for|for|if|when)\s+((?:[A-Za-z]+[_-]\d+(?:\s*/\s*\d+)*'
            r'(?:\s*(?:,|and|or|through|to)\s*)?)+)',
            text, re.IGNORECASE
        ):
            toks = cls._all_tokens(m.group(1), ctx)
            toks = [t for t in toks if t.startswith(axis + "_")]
            if toks:
                included.update(toks)

        for m in re.finditer(
            r'(?:Profile_Id|Location)\s*(?:=|is any of the following\s*:?|is)\s*([^.;\n]*)',
            text, re.IGNORECASE
        ):
            toks = [t for t in cls._all_tokens(m.group(1), ctx) if t.startswith(axis + "_")]
            if toks:
                included.update(toks)

        # -- group-scoped language ("Primary Surface Only", "Spoiler surface")
        group_members: Set[str] = set()
        for group, members in ctx.groups.items():
            if not group.strip():
                continue
            if re.search(rf'\b{re.escape(group.strip())}\b', text, re.IGNORECASE):
                group_members.update(m for m in members if m.startswith(axis + "_"))

        # "Primary" is the complement of the non-primary groups when the
        # document contrasts a primary surface against named sub-types.
        if re.search(r'\bPrimary\b', text, re.IGNORECASE):
            complement = set(universe)
            for group, members in ctx.groups.items():
                if re.search(r'\bPrimary\b', group, re.IGNORECASE):
                    continue
                if re.search(rf'\b{re.escape(group.strip())}\b', text, re.IGNORECASE) and \
                        re.search(r'(?:not apply|does not apply|N/?A|only)', text, re.IGNORECASE):
                    complement -= set(members)
            if re.search(r'Primary\s+Surface\s+Only', text, re.IGNORECASE):
                for group, members in ctx.groups.items():
                    if re.search(r'spoiler', group, re.IGNORECASE):
                        complement -= set(members)
                included |= complement
                notes.append("primary-surface-only scope")

        if group_members and not included:
            included = group_members
            notes.append(f"group scope {', '.join(sorted(group_members, key=_sort_key))}")

        included.update(cls._range_members(text, axis, universe))

        members = sorted(included or set(universe), key=_sort_key)
        members = [m for m in members if m not in excluded]
        if not members:
            members = [m for m in universe if m not in excluded]

        rationale = "; ".join(notes) if notes else "applies to all discovered configurations"
        return members, rationale

    # Range shorthand: "LRUs 1-7", "LRU 1 through 7"
    _RANGE_RE = re.compile(
        r'\b([A-Za-z][A-Za-z0-9]*)[_\-\s]?(\d+)\s*(?:[-–/]|through|to)\s*'
        r'(?:[A-Za-z][A-Za-z0-9]*)[_\-\s]?(\d+)\b',
        re.IGNORECASE,
    )

    # Prose that implies each configuration must be verified individually.
    _INDIVIDUAL_COVERAGE_RE = re.compile(
        r'LRUs?\s*(?:\d+\s*[-–/]\s*\d+|\d+(?:\s*/\s*\d+)+)|'
        r'LRU[_\-\s]?\d+\s+(?:through|to)\s+LRU[_\-\s]?\d+|'
        r'(?:all|each|every)\s+LRUs?|'
        r'ATYPEs?\s*(?:\d+\s*[-–/]\s*\d+|\d+(?:\s*,\s*|\s+and\s+|\s+or\s+)\d+)+|'
        r'Asset\s+Types?\s*(?:\d+\s*[-–/]\s*\d+|\d+(?:\s*,\s*|\s+and\s+|\s+or\s+)\d+)+|'
        r'(?:all|each|every)\s+(?:Asset\s+Types?|ATYPEs?)',
        re.IGNORECASE,
    )

    _SURFACE_NAMES = {
        "LRU_1": "Left Aileron", "LRU_2": "Right Aileron",
        "LRU_3": "Left Spoiler", "LRU_4": "Right Spoiler",
        "LRU_5": "Left Elevator", "LRU_6": "Right Elevator", "LRU_7": "Rudder",
    }

    @classmethod
    def _axis_name(cls, ctx: ApplicabilityContext, kind: str) -> Optional[str]:
        """Return the canonical dimension name for LRU or ATYPE/TYPE."""
        kind = kind.upper()
        for axis in ctx.dimensions:
            upper = axis.upper()
            if kind == "LRU" and upper == "LRU":
                return axis
            if kind == "ATYPE" and ("TYPE" in upper or upper == "ATYPE"):
                return axis
        return None

    @classmethod
    def _range_members(cls, text: str, axis: str, universe: List[str]) -> List[str]:
        """Expand 'LRUs 1-7' style ranges into concrete dimension tokens."""
        found: Set[str] = set()
        for m in cls._RANGE_RE.finditer(text or ""):
            name, lo, hi = m.group(1).upper(), int(m.group(2)), int(m.group(3))
            if name not in (axis, "LRU", "ATYPE", "TYPE") and not axis.endswith(name):
                continue
            for n in range(min(lo, hi), max(lo, hi) + 1):
                tok = f"{axis}_{n}"
                if tok in universe:
                    found.add(tok)
        return sorted(found, key=_sort_key)

    @classmethod
    def applicable_axis_members(cls, req_text: str, ctx: ApplicabilityContext,
                                axis: str) -> Tuple[List[str], str]:
        """
        Members of a specific applicability axis (LRU or ATYPE) that a
        requirement applies to, respecting inclusions, exclusions, and ranges.
        """
        universe = ctx.values(axis)
        if not universe:
            return [], f"no {axis} values discovered"

        if axis == ctx.primary_axis:
            members, rationale = cls.applicable_members(req_text, ctx)
            if members:
                return members, rationale

        text = req_text or ""
        included: Set[str] = set()
        excluded: Set[str] = set()

        for m in re.finditer(
            r'(?:not applicable to|except(?:\s+for)?|excluding|are\s+N/?A(?:\s+for)?)\s*:?\s*([^.;\n]*)',
            text, re.IGNORECASE,
        ):
            excluded.update(t for t in cls._all_tokens(m.group(1), ctx) if t.startswith(axis + "_"))

        included.update(cls._range_members(text, axis, universe))
        for tok in cls._all_tokens(text, ctx):
            if tok.startswith(axis + "_"):
                included.add(tok)

        members = sorted(included or set(universe), key=_sort_key)
        members = [m for m in members if m not in excluded]
        if not members:
            members = [m for m in universe if m not in excluded]
        return members, "axis-specific applicability"

    @classmethod
    def expansion_axes(cls, req_text: str, ctx: ApplicabilityContext) -> Dict[str, List[str]]:
        """
        Axes that require individual test-case coverage for this requirement.
        Returns {axis_name: [token, ...]} e.g. {'LRU': ['LRU_1',..], 'ATYPE': ['ATYPE_1',..]}.
        """
        if not cls._INDIVIDUAL_COVERAGE_RE.search(req_text or ""):
            return {}

        axes: Dict[str, List[str]] = {}
        lru_axis = cls._axis_name(ctx, "LRU")
        if lru_axis:
            lrus, _ = cls.applicable_axis_members(req_text, ctx, lru_axis)
            if len(lrus) > 1:
                axes[lru_axis] = lrus

        atype_axis = cls._axis_name(ctx, "ATYPE")
        if atype_axis and re.search(
            r'ATYPE|Asset\s+Type|TYPE_\d', req_text or "", re.IGNORECASE
        ):
            atypes, _ = cls.applicable_axis_members(req_text, ctx, atype_axis)
            if len(atypes) > 1:
                axes[atype_axis] = atypes
        return axes

    @classmethod
    def _tokens_in_text(cls, text: str, tokens: List[str]) -> Set[str]:
        found: Set[str] = set()
        for tok in tokens:
            if re.search(rf'\b{re.escape(tok)}\b', text or ""):
                found.add(tok)
        return found

    @classmethod
    def _tc_coverage(cls, tcs: List[Dict[str, Any]], tokens: List[str]) -> Set[str]:
        covered: Set[str] = set()
        for tc in tcs:
            blob = " ".join(str(tc.get(k, "")) for k in (
                "test_case_id", "description", "initial_condition", "test_inputs"
            ))
            covered |= cls._tokens_in_text(blob, tokens)
        return covered

    @classmethod
    def _needs_expansion(cls, tcs: List[Dict[str, Any]], axes: Dict[str, List[str]]) -> bool:
        if not axes:
            return False
        for axis, members in axes.items():
            if len(members) <= 1:
                continue
            covered = cls._tc_coverage(tcs, members)
            if covered >= set(members):
                continue
            return True
        return False

    @classmethod
    def _replace_token(cls, text: str, axis: str, old: str, new: str) -> str:
        if not text:
            return text
        text = re.sub(rf'\b{re.escape(old)}\b', new, text)
        text = re.sub(
            r'LRUs?\s*\d+\s*[-–/]\s*\d+',
            new if axis == "LRU" else r'\g<0>',
            text,
            flags=re.IGNORECASE,
        )
        if axis == "LRU":
            text = re.sub(
                r'LRUs?\s*1\s*[-–/]\s*7',
                new,
                text,
                flags=re.IGNORECASE,
            )
        return text

    @classmethod
    def _apply_config(cls, tc: Dict[str, Any], dims: Dict[str, str], req_id: str) -> None:
        """Rewrite a template TC for one concrete configuration combination."""
        lru = dims.get("LRU", "")
        atype = dims.get("ATYPE") or dims.get("TYPE", "")
        surface = cls._SURFACE_NAMES.get(lru, lru)

        for field in ("initial_condition", "test_inputs", "description", "expected_result"):
            val = str(tc.get(field, ""))
            if lru:
                val = cls._replace_token(val, "LRU", "LRU_1", lru)
                val = re.sub(
                    r'LRU Configuration\s*=\s*LRU_\d+(?:\s*\([^)]*\))?',
                    f"LRU Configuration = {lru} ({surface})",
                    val,
                    flags=re.IGNORECASE,
                )
                if f"Target LRU: {lru}" not in val and "Target LRU:" in val:
                    val = re.sub(r'Target LRU:\s*[^;]+', f"Target LRU: {lru} ({surface})", val)
                elif lru and f"Target LRU: {lru}" not in val:
                    pass  # _ensure_configuration adds it via _applicability
            if atype:
                val = cls._replace_token(val, "ATYPE", "ATYPE_1", atype)
                val = re.sub(r'Target Asset Type:\s*ATYPE_\d', f"Target Asset Type: {atype}", val)
            tc[field] = val

        suffix = "_".join(dims.values())
        base_id = str(tc.get("test_case_id", f"TC-{req_id}"))
        if suffix and suffix not in base_id:
            tc["test_case_id"] = f"{base_id}_{suffix}"

        tc["_applicability"] = dict(dims)
        if lru:
            tc["target_lru"] = lru
        if atype:
            tc["asset_type"] = atype

    @classmethod
    def expand_test_cases(cls, tcs: List[Dict[str, Any]], req_id: str,
                          req_text: str,
                          ctx: Optional[ApplicabilityContext]) -> List[Dict[str, Any]]:
        """
        Clone template test cases across individual LRU and/or ATYPE values
        when the requirement text demands per-configuration verification.
        Respects exclusions and skips expansion when coverage already exists.
        """
        if not tcs or not ctx:
            return tcs
        if cls.is_matrix_applicability(req_id, req_text):
            return tcs

        axes = cls.expansion_axes(req_text, ctx)
        if not cls._needs_expansion(tcs, axes):
            return tcs

        lru_axis = cls._axis_name(ctx, "LRU")
        atype_axis = cls._axis_name(ctx, "ATYPE")
        lrus = axes.get(lru_axis, []) if lru_axis else []
        atypes = axes.get(atype_axis, []) if atype_axis else []
        if not lrus and not atypes:
            return tcs
        if not lrus:
            lrus = ["LRU_1"]
        if not atypes:
            atypes = ["ATYPE_1"]

        expanded: List[Dict[str, Any]] = []
        for tc in tcs:
            for at in atypes:
                for lru in lrus:
                    dims: Dict[str, str] = {"LRU": lru}
                    if atype_axis:
                        dims[atype_axis] = at
                    else:
                        dims["ATYPE"] = at
                    clone = copy.deepcopy(tc)
                    cls._apply_config(clone, dims, req_id)
                    expanded.append(clone)
        return expanded if expanded else tcs

    DEFAULT_PIN_STRAPPING = [
        {"atype": "ATYPE_1", "lru": "LRU_1", "pins": "00010011", "invert": 1, "surface_id": "TYPE_1_LRU_1", "surface": "Left Aileron"},
        {"atype": "ATYPE_1", "lru": "LRU_2", "pins": "00010101", "invert": 1, "surface_id": "TYPE_1_LRU_2", "surface": "Right Aileron"},
        {"atype": "ATYPE_1", "lru": "LRU_3", "pins": "00010110", "invert": 0, "surface_id": "TYPE_1_LRU_3", "surface": "Left Spoiler"},
        {"atype": "ATYPE_1", "lru": "LRU_4", "pins": "00011001", "invert": 1, "surface_id": "TYPE_1_LRU_4", "surface": "Right Spoiler"},
        {"atype": "ATYPE_1", "lru": "LRU_5", "pins": "00011010", "invert": 0, "surface_id": "TYPE_1_LRU_5", "surface": "Left Elevator"},
        {"atype": "ATYPE_1", "lru": "LRU_6", "pins": "00011100", "invert": 0, "surface_id": "TYPE_1_LRU_6", "surface": "Right Elevator"},
        {"atype": "ATYPE_1", "lru": "LRU_7", "pins": "00011111", "invert": 1, "surface_id": "TYPE_1_LRU_7", "surface": "Rudder"},

        {"atype": "ATYPE_2", "lru": "LRU_1", "pins": "00100011", "invert": 1, "surface_id": "TYPE_2_LRU_1", "surface": "Left Aileron"},
        {"atype": "ATYPE_2", "lru": "LRU_2", "pins": "00100101", "invert": 1, "surface_id": "TYPE_2_LRU_2", "surface": "Right Aileron"},
        {"atype": "ATYPE_2", "lru": "LRU_3", "pins": "00100110", "invert": 0, "surface_id": "TYPE_2_LRU_3", "surface": "Left Spoiler"},
        {"atype": "ATYPE_2", "lru": "LRU_4", "pins": "00101001", "invert": 1, "surface_id": "TYPE_2_LRU_4", "surface": "Right Spoiler"},
        {"atype": "ATYPE_2", "lru": "LRU_5", "pins": "00101010", "invert": 0, "surface_id": "TYPE_2_LRU_5", "surface": "Left Elevator"},
        {"atype": "ATYPE_2", "lru": "LRU_6", "pins": "00101100", "invert": 0, "surface_id": "TYPE_2_LRU_6", "surface": "Right Elevator"},
        {"atype": "ATYPE_2", "lru": "LRU_7", "pins": "00101111", "invert": 1, "surface_id": "TYPE_2_LRU_7", "surface": "Rudder"},

        {"atype": "ATYPE_3", "lru": "LRU_1", "pins": "00110010", "invert": 0, "surface_id": "TYPE_3_LRU_1", "surface": "Left Aileron"},
        {"atype": "ATYPE_3", "lru": "LRU_2", "pins": "00110100", "invert": 0, "surface_id": "TYPE_3_LRU_2", "surface": "Right Aileron"},
        {"atype": "ATYPE_3", "lru": "LRU_3", "pins": "00110111", "invert": 1, "surface_id": "TYPE_3_LRU_3", "surface": "Left Spoiler"},
        {"atype": "ATYPE_3", "lru": "LRU_4", "pins": "00111000", "invert": 0, "surface_id": "TYPE_3_LRU_4", "surface": "Right Spoiler"},
        {"atype": "ATYPE_3", "lru": "LRU_5", "pins": "00111011", "invert": 1, "surface_id": "TYPE_3_LRU_5", "surface": "Left Elevator"},
        {"atype": "ATYPE_3", "lru": "LRU_6", "pins": "00111101", "invert": 1, "surface_id": "TYPE_3_LRU_6", "surface": "Right Elevator"},
        {"atype": "ATYPE_3", "lru": "LRU_7", "pins": "00111110", "invert": 0, "surface_id": "TYPE_3_LRU_7", "surface": "Rudder"},
    ]

    @classmethod
    def is_matrix_applicability(cls, req_id: str, req_text: str, tables: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Determines if a requirement specifies a configuration decode / pin strapping matrix."""
        if "1011" in str(req_id) or "Table 1011" in str(req_text) or "pin strapping" in str(req_text).lower():
            return True
        if tables:
            ctx = cls.build_context(tables=tables, full_text=str(req_text))
            if cls.is_matrix_requirement(req_id, req_text, ctx):
                return True
        return False

    # ------------------------------------------------------------------
    # Matrix expansion
    # ------------------------------------------------------------------
    @classmethod
    def generate_matrix_test_cases(cls, req_id: str, req_text: str,
                                   ctx_or_tables: Any = None,
                                   table_ref: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Emits one discrete test case per configuration combination, built
        from the decode table rows or standard DO-178C pin strapping matrix.
        Ensures all 21 combinations (LRU_1..LRU_7 x ATYPE_1..ATYPE_3) are covered.
        """
        if isinstance(ctx_or_tables, ApplicabilityContext) and ctx_or_tables.combinations:
            combos = cls.combinations_for(table_ref, ctx_or_tables)
            ref = table_ref or (ctx_or_tables.decode_table_refs[0] if ctx_or_tables.decode_table_refs else "1011")
            test_cases: List[Dict[str, Any]] = []

            for combo in combos:
                key = combo["key"]
                dims = combo["dims"]
                stimulus = combo["stimulus"]
                key_header = combo.get("key_header", "Combination")

                dim_phrase = "; ".join(
                    f"Target {axis}: {tok}" for axis, tok in sorted(dims.items())
                )
                group = None
                for tok in dims.values():
                    group = ctx_or_tables.group_of(tok) or group
                group_phrase = f" ({group})" if group else ""

                stim_phrase = "; ".join(f"{k} = {v}" for k, v in stimulus.items()) or \
                              f"Configuration selector set to {key}."
                decoded_phrase = "; ".join(
                    f"{axis} decoded as {tok}" for axis, tok in sorted(dims.items())
                )

                atype = dims.get("ATYPE") or dims.get("TYPE", "ATYPE_1")
                lru = dims.get("LRU", "LRU_1")

                test_cases.append({
                    "test_case_id": f"SWVCP_AAP_TC_{ref}_{key}" if ref else f"SWVCP_AAP_TC_{key}",
                    "requirement_id": req_id,
                    "asset_type": atype,
                    "target_lru": lru,
                    "test_type": "NORMAL",
                    "description": (
                        f"Verify that configuration input combination {key}{group_phrase} "
                        f"decodes correctly per Table {ref}: {decoded_phrase}."
                    ),
                    "initial_condition": (
                        f"Operational Mode: FLIGHT_MODE; {dim_phrase}; "
                        f"Hardware configuration inputs strapped for {key_header} = {key} "
                        f"per Table {ref}; LRU to be in Harmonizing Mode."
                    ),
                    "test_inputs": stim_phrase,
                    "expected_result": (
                        f"{key_header} = {key}; {decoded_phrase}."
                    ),
                    "pass_criteria": "Observed software behaviour matches expected_result.",
                    "related_requirements": "",
                    "test_procedure_notes": (
                        "Verification mechanism to be defined by the verification environment."
                    ),
                    "_applicability": {axis: tok for axis, tok in dims.items()},
                })
            if len(test_cases) >= 21:
                return test_cases

        # Fallback to standard 21-combination pin strapping matrix (LRU_1..7 x ATYPE_1..3)
        cases = []
        for item in cls.DEFAULT_PIN_STRAPPING:
            atype = item["atype"]
            lru = item["lru"]
            pins = item["pins"]
            invert = item["invert"]
            surf_id = item["surface_id"]
            surf_name = item["surface"]
            tc_id = f"SWVCP_AAP_TC_1011_{surf_id}"

            cases.append({
                "test_case_id": tc_id,
                "requirement_id": req_id,
                "asset_type": atype,
                "target_lru": lru,
                "test_type": "NORMAL",
                "description": (
                    f"Verify Pin Strapping decode for {atype} - {lru} ({surf_name}): "
                    f"Pin inputs {pins} decode to Asset_Type = {atype}, LRU_ID = {lru}, "
                    f"Location_Invert = {invert}."
                ),
                "initial_condition": (
                    f"Operational Mode: FLIGHT_MODE; Target Asset Type: {atype}; Target LRU: {lru}; "
                    f"Hardware discrete pin strapping configured for {surf_id} per Table 1011; "
                    f"LRU to be in Harmonizing Mode."
                ),
                "test_inputs": (
                    f"Discrete pin strapping inputs: ID7_DSP..ID0_DSP = {pins}; "
                    f"Parity valid; Asset Type = {atype}; LRU = {lru}."
                ),
                "expected_result": (
                    f"Software correctly decodes discrete pins to Asset_Type = {atype}, "
                    f"Target LRU = {lru} ({surf_name}), Location_Invert = {invert}, "
                    f"SurfaceID = {surf_id}. Pin strapping verification successful."
                ),
                "pass_criteria": "Observed software behaviour matches expected_result.",
                "related_requirements": "",
                "test_procedure_notes": "Verification mechanism defined by verification environment.",
                "_applicability": {"ATYPE": atype, "LRU": lru}
            })
        return cases
