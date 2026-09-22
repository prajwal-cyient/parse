#!/usr/bin/env python3
"""Validate generated test cases against all 12 client observation changes."""
import json
import re
import sys
from collections import defaultdict

DEFAULT_PATH = r"c:\Users\pm89542\Desktop\parse\app\ui_outputs\SW_Requirements_Sample_1_generated_testcases.json"


def load_tcs(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("test_cases", [])


def blob(tc):
    return " ".join(str(tc.get(k, "")) for k in [
        "test_case_id", "requirement_id", "description",
        "initial_condition", "test_inputs", "expected_result"
    ])


def main(path=DEFAULT_PATH):
    tcs = load_tcs(path)
    results = []

    def report(change, criterion, status, detail):
        results.append({"change": change, "criterion": criterion, "status": status, "detail": detail})

    # --- CHANGE 1: LRU x ATYPE individual coverage ---
    matrix_1011 = [tc for tc in tcs if "1011" in tc.get("requirement_id", "") or "SWVCP_AAP_TC" in tc.get("test_case_id", "")]
    combos_1011 = set()
    for tc in matrix_1011:
        init = tc.get("initial_condition", "")
        m_at = re.search(r"ATYPE_(\d)", init)
        m_lru = re.search(r"LRU_(\d)", init)
        if m_at and m_lru:
            combos_1011.add((f"ATYPE_{m_at.group(1)}", f"LRU_{m_lru.group(1)}"))
    missing_combos = []
    for at in range(1, 4):
        for lru in range(1, 8):
            if (f"ATYPE_{at}", f"LRU_{lru}") not in combos_1011:
                missing_combos.append(f"ATYPE_{at}+LRU_{lru}")
    if len(combos_1011) >= 21:
        report(1, "1011 matrix: 21 LRU×ATYPE combinations", "RESOLVED", f"{len(combos_1011)} combinations found")
    else:
        report(1, "1011 matrix: 21 LRU×ATYPE combinations", "NOT RESOLVED",
               f"Only {len(combos_1011)} combos; missing: {missing_combos[:10]}...")

    generic_lru_phrase = [
        tc["test_case_id"] for tc in tcs
        if re.search(r"LRUs?\s*1[-–]7|LRU_1\s+to\s+LRU_7|LRU_1 through LRU_7", blob(tc), re.I)
        and "1011" not in tc.get("requirement_id", "")
    ]
    per_lru_reqs = ["LRU-9169", "LRU-9222", "LRU-6135", "LRU-9174"]
    per_lru_fail = []
    for req in per_lru_reqs:
        matching = [tc for tc in tcs if req in tc.get("requirement_id", "")]
        lrus = set()
        for tc in matching:
            for i in range(1, 8):
                if f"LRU_{i}" in tc.get("initial_condition", "") + tc.get("test_inputs", ""):
                    lrus.add(f"LRU_{i}")
        if len(lrus) < 7 and len(matching) < 7:
            per_lru_fail.append(f"{req}: only {sorted(lrus)} ({len(matching)} TCs)")

    if per_lru_fail:
        report(1, "Individual LRU coverage for applicable step reqs", "NOT RESOLVED", "; ".join(per_lru_fail))
    else:
        report(1, "Individual LRU coverage for applicable step reqs", "RESOLVED", "All sampled reqs have per-LRU TCs")

    if generic_lru_phrase:
        report(1, "No generic 'LRU_1 to LRU_7' phrasing", "PARTIALLY RESOLVED",
               f"{len(generic_lru_phrase)} TCs still use generic LRU 1-7 wording (e.g. {generic_lru_phrase[:3]})")
    else:
        report(1, "No generic 'LRU_1 to LRU_7' phrasing", "RESOLVED", "No generic phrasing found")

    atype_counts = {f"ATYPE_{i}": 0 for i in range(1, 4)}
    for tc in tcs:
        b = blob(tc)
        for at in atype_counts:
            if at in b:
                atype_counts[at] += 1
    if atype_counts["ATYPE_2"] > 0 and atype_counts["ATYPE_3"] > 0:
        report(1, "ATYPE_1/2/3 present in output", "RESOLVED", str(atype_counts))
    else:
        report(1, "ATYPE_1/2/3 present in output", "NOT RESOLVED", str(atype_counts))

    # --- CHANGE 2/9: Structure separation ---
    cmd_in_inputs = [
        (tc["test_case_id"], tc["requirement_id"])
        for tc in tcs
        if re.search(r"Commanded_(Contract|Expand|To_VOID|to_Contract|to_VOID|Position)\s*=", tc.get("test_inputs", ""), re.I)
    ]
    flags_in_inputs = [
        (tc["test_case_id"], tc["requirement_id"], m.group(0))
        for tc in tcs
        for m in re.finditer(
            r"(Contract_Stop_Collection_Complete|Expand_Stop_Collection_Complete|VOID_Collection_Complete)\s*=",
            tc.get("test_inputs", ""), re.I
        )
    ]
    if not cmd_in_inputs and not flags_in_inputs:
        report(2, "No outputs/commanded values in Test Inputs", "RESOLVED", "Clean")
    else:
        report(2, "No outputs/commanded values in Test Inputs", "NOT RESOLVED",
               f"Commanded in inputs: {len(cmd_in_inputs)}; flags in inputs: {len(flags_in_inputs)} "
               f"(e.g. {flags_in_inputs[:3]})")

    # --- CHANGE 3: LRU-9169 / LRU-9222 ---
    for req in ["LRU-9169", "LRU-9222"]:
        matching = [tc for tc in tcs if req in tc.get("requirement_id", "")]
        issues = []
        for tc in matching:
            inp = tc.get("test_inputs", "")
            if not ("Harmonize_SFC" in inp or "SFC" in inp):
                issues.append(f"{tc['test_case_id']}: missing SFC in inputs")
            if not ("Harmonize_Offset" in inp or "Offset" in inp):
                issues.append(f"{tc['test_case_id']}: missing Offset in inputs")
            if re.search(r"Commanded_", inp, re.I):
                issues.append(f"{tc['test_case_id']}: Commanded_* in inputs")
        if issues:
            report(3, f"{req} input/output classification", "PARTIALLY RESOLVED", "; ".join(issues))
        else:
            report(3, f"{req} input/output classification", "RESOLVED", f"{len(matching)} TCs OK")

    # --- CHANGE 4: LRU-9174 false condition ---
    dc_9174 = [tc for tc in tcs if "9174" in tc.get("requirement_id", "") and tc.get("test_type") == "DC"]
    if dc_9174 and all("expand_stop_collection_complete = false" in tc.get("expected_result", "").lower() for tc in dc_9174):
        report(4, "LRU-9174 false: Expand_Stop_Collection_Complete = False", "RESOLVED",
               dc_9174[0].get("expected_result", "")[:120])
    else:
        report(4, "LRU-9174 false: Expand_Stop_Collection_Complete = False", "NOT RESOLVED",
               f"DC cases: {len(dc_9174)}")

    # Also check 9174 has completion flag wrongly in inputs
    for tc in [t for t in tcs if "9174" in t.get("requirement_id", "")]:
        if "Expand_Stop_Collection_Complete" in tc.get("test_inputs", ""):
            report(4, "LRU-9174: completion flag not in Test Inputs", "NOT RESOLVED",
                   f"{tc['test_case_id']} has Expand_Stop_Collection_Complete in test_inputs")

    # --- CHANGE 5: LRU-9170/9171 consolidation ---
    for req in ["9170", "9171"]:
        standalone = [tc for tc in tcs if req in tc.get("requirement_id", "") and "clubbed" not in tc.get("description", "").lower()
                      and "TC-LRU-9170-9171" not in tc.get("test_case_id", "")]
    clubbed = [tc for tc in tcs if "TC-LRU-9170-9171" in tc.get("test_case_id", "")]
    if clubbed and len(clubbed) <= 2:
        report(5, "LRU-9170/9171 step consolidation", "RESOLVED", f"{len(clubbed)} clubbed TCs: {[c['test_case_id'] for c in clubbed]}")
    else:
        report(5, "LRU-9170/9171 step consolidation", "NOT RESOLVED", f"clubbed={len(clubbed)}")

    # --- CHANGE 6: LRUSWRS-1000 consolidation ---
    tc1000 = [tc for tc in tcs if tc.get("requirement_id") == "LRUSWRS-1000"]
    if len(tc1000) == 1:
        members = tc1000[0].get("expected_result", "")
        report(6, "LRUSWRS-1000 single consolidated TC", "RESOLVED",
               f"1 TC covering members in expected_result ({len(members)} chars)")
    elif len(tc1000) == 0:
        report(6, "LRUSWRS-1000 single consolidated TC", "NOT RESOLVED", "No TC found")
    else:
        report(6, "LRUSWRS-1000 single consolidated TC", "NOT RESOLVED", f"{len(tc1000)} separate TCs")

    # --- CHANGE 7: LRUSWRS-1002 inputs ---
    tc1002 = [tc for tc in tcs if tc.get("requirement_id") == "LRUSWRS-1002"]
    empty_1002 = [tc for tc in tc1002 if not tc.get("test_inputs", "").strip() or tc.get("test_inputs", "").strip().lower() in ("none", "n/a")]
    if tc1002 and not empty_1002:
        report(7, "LRUSWRS-1002 meaningful Test Inputs", "RESOLVED", tc1002[0].get("test_inputs", "")[:100])
    else:
        report(7, "LRUSWRS-1002 meaningful Test Inputs", "NOT RESOLVED",
               f"empty={len(empty_1002)}/{len(tc1002)}")

    # --- CHANGE 8: IVT_Mode_ModeLgc in Test Inputs ---
    for req in ["LRUSWRS-1003", "LRUSWRS-1004"]:
        matching = [tc for tc in tcs if tc.get("requirement_id") == req]
        bad = []
        good = []
        for tc in matching:
            init = tc.get("initial_condition", "")
            inp = tc.get("test_inputs", "")
            if "IVT_Mode_ModeLgc" in init:
                bad.append(tc["test_case_id"])
            if "IVT_Mode_ModeLgc" in inp:
                good.append(tc["test_case_id"])
        if req == "LRUSWRS-1003":
            if not bad and good:
                report(8, f"{req}: IVT_Mode_ModeLgc in Test Inputs", "RESOLVED", f"all {len(good)} TCs have IVT in inputs")
            else:
                report(8, f"{req}: IVT_Mode_ModeLgc in Test Inputs", "NOT RESOLVED",
                       f"in init: {bad}; in inputs: {good}")
        else:
            # 1004: IVT should be in test_inputs when it's the stimulus
            missing_ivt = [tc["test_case_id"] for tc in matching if "IVT_Mode_ModeLgc" not in tc.get("test_inputs", "")]
            if missing_ivt:
                report(8, f"{req}: IVT_Mode_ModeLgc in Test Inputs", "NOT RESOLVED",
                       f"{len(missing_ivt)}/{len(matching)} TCs missing IVT in test_inputs: {missing_ivt}")
            else:
                report(8, f"{req}: IVT_Mode_ModeLgc in Test Inputs", "RESOLVED", "all TCs have IVT in inputs")

    # --- CHANGE 10: Deduplication ---
    seen = {}
    dups = []
    for tc in tcs:
        key = (
            tc.get("requirement_id"),
            tc.get("test_type"),
            re.sub(r"\s+", " ", tc.get("initial_condition", "").lower()),
            re.sub(r"\s+", " ", tc.get("test_inputs", "").lower()),
        )
        if key in seen:
            dups.append((seen[key], tc.get("test_case_id")))
        else:
            seen[key] = tc.get("test_case_id")
    if len(dups) < 5:
        report(10, "Duplicate/overlap detection", "PARTIALLY RESOLVED", f"{len(dups)} exact duplicate fingerprints")
    else:
        report(10, "Duplicate/overlap detection", "NOT RESOLVED", f"{len(dups)} exact duplicates")

    # --- CHANGE 11: Coverage not lost (spot check) ---
    report(11, "Consolidation preserves coverage", "PARTIALLY RESOLVED",
           "Manual spot-check: 9170/9171 and 1000 consolidated; per-LRU expansion not verified for all reqs")

    # --- CHANGE 12: Validation before export ---
    try:
        sys.path.insert(0, r"c:\Users\pm89542\Desktop\parse\app\backend")
        from validation_engine import ValidationEngine
        has_audit = hasattr(ValidationEngine, "audit_test_cases")
        cleaned, report_obj = ValidationEngine.validate_and_sanitize(tcs)
        report(12, "ValidationEngine.validate_and_sanitize exists", "RESOLVED",
               f"structure_issues_fixed={report_obj.structure_issues_fixed}")
        if has_audit:
            report(12, "ValidationEngine.audit_test_cases exists", "RESOLVED", "Method present")
        else:
            report(12, "ValidationEngine.audit_test_cases exists", "NOT RESOLVED",
                   "main.py calls audit_test_cases() but method is missing — export pipeline will crash")
    except Exception as e:
        report(12, "Validation pipeline", "NOT RESOLVED", str(e))

    # --- CHANGE 9: Generalized classification (code exists?) ---
    try:
        from signal_classifier import SignalClassifier, SignalDictionary
        report(9, "Generalized SignalClassifier module", "RESOLVED", "signal_classifier.py present with grammar-based rules")
    except Exception as e:
        report(9, "Generalized SignalClassifier module", "NOT RESOLVED", str(e))

    # Print summary
    print("=" * 70)
    print("CLIENT OBSERVATION VALIDATION REPORT")
    print(f"File: {path}")
    print(f"Total test cases: {len(tcs)}")
    print("=" * 70)

    by_status = defaultdict(list)
    for r in results:
        by_status[r["status"]].append(r)

    for status in ["RESOLVED", "PARTIALLY RESOLVED", "NOT RESOLVED"]:
        items = by_status.get(status, [])
        if items:
            print(f"\n## {status} ({len(items)})")
            for r in items:
                print(f"  [Change {r['change']}] {r['criterion']}")
                print(f"    -> {r['detail']}")

    print("\n" + "=" * 70)
    print(f"SUMMARY: RESOLVED={len(by_status['RESOLVED'])}, "
          f"PARTIAL={len(by_status['PARTIALLY RESOLVED'])}, "
          f"NOT RESOLVED={len(by_status['NOT RESOLVED'])}")
    return results


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    main(path)
