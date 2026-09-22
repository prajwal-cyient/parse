import json
import os
import re
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gpt-oss:latest"
PROMPTS_DIR = r"c:\Users\pm89542\Desktop\parse\step_prompts_1001"
MASTER_JSON_PATH = r"c:\Users\pm89542\Desktop\parse\LRUSWRS-1001_grouped_step_testcases.json"
REPAIRED_JSON_PATH = r"c:\Users\pm89542\Desktop\parse\LRUSWRS-1001_grouped_step_testcases_perfect.json"

def fetch_step_cases_from_ollama(step_name):
    clean_name = step_name.replace(" ", "_")
    fpath = os.path.join(PROMPTS_DIR, f"prompt_step_{clean_name}.txt")
    if not os.path.exists(fpath):
        print(f"  [ERROR] File not found: {fpath}")
        return []
    
    with open(fpath, "r", encoding="utf-8") as f:
        ptext = f.read()

    # Append extra strict instruction for schema
    strict_prompt = ptext + "\n\nCRITICAL SYSTEM REQUIREMENT: Return strictly valid JSON containing a list of objects under key 'test_cases'. Every test case MUST include all 10 fields: test_case_id, requirement_id, description, test_type, initial_condition, test_inputs, expected_result, pass_criteria, related_requirements, test_procedure_notes. Never use 'expected_output'."

    payload = {
        "model": MODEL_NAME,
        "prompt": strict_prompt,
        "stream": False
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data_bytes, headers={"Content-Type": "application/json"})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                raw_response = res_json.get("response", "")
                match = re.search(r'\{[\s\S]*\}', raw_response)
                if match:
                    parsed = json.loads(match.group(0))
                    tcs = parsed.get("test_cases", [])
                    if len(tcs) > 0:
                        return tcs
        except Exception as e:
            print(f"  [RETRY {attempt+1}] Error for Step {step_name}: {e}")
    return []

def repair_and_perfect():
    with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
        master = json.load(f)

    steps_dict = master.get("steps_breakdown", {})

    target_repair_steps = ["17", "20", "23", "26", "35"]
    
    print(f"Starting targeted repair for steps: {target_repair_steps}...")

    for skey, sdata in steps_dict.items():
        snum = sdata.get("step_number")
        if snum in target_repair_steps or len(sdata.get("test_cases", [])) == 0:
            print(f"\nRe-generating test cases for Step {snum} ({sdata.get('requirement_id')})...")
            new_tcs = fetch_step_cases_from_ollama(snum)
            if len(new_tcs) > 0:
                sdata["test_cases"] = new_tcs
                sdata["total_test_cases"] = len(new_tcs)
                print(f"  [FIXED] Step {snum}: Re-generated {len(new_tcs)} test cases!")
            else:
                print(f"  [WARN] Step {snum}: Failed to re-generate automatically.")

    # Apply Schema & Rule Standardization across ALL steps
    print("\nApplying strict schema & rule standardization across all test cases...")

    all_tc_ids_seen = set()
    total_valid_tcs = 0

    for skey, sdata in steps_dict.items():
        snum = sdata.get("step_number")
        req_sub_id = sdata.get("requirement_id")
        tcs = sdata.get("test_cases", [])

        valid_tcs_for_step = []

        for tc_idx, tc in enumerate(tcs, 1):
            # 1. Field name fixes
            if "expected_output" in tc and "expected_result" not in tc:
                tc["expected_result"] = tc.pop("expected_output")

            # 2. Convert list expected_result to string
            if isinstance(tc.get("expected_result"), list):
                tc["expected_result"] = " ".join(tc["expected_result"])

            # 3. Requirement ID fix
            tc["requirement_id"] = req_sub_id

            # 4. Mandatory fields defaults
            if not tc.get("pass_criteria"):
                tc["pass_criteria"] = "Observed software behaviour matches expected_result."
            if tc.get("related_requirements") is None:
                tc["related_requirements"] = ""
            if not tc.get("test_procedure_notes"):
                tc["test_procedure_notes"] = "Verification mechanism to be defined by the verification environment."
            if not tc.get("test_type"):
                tc["test_type"] = "NORMAL" if tc_idx == 1 else "DC"

            # 5. Surface & Initial Condition Enforcer
            tc_inputs = str(tc.get("test_inputs", ""))
            tc_desc = str(tc.get("description", ""))
            
            surface_found = None
            for surf in ["Aileron", "Elevator", "Rudder", "Spoiler"]:
                if surf.lower() in tc_inputs.lower() or surf.lower() in tc_desc.lower() or surf.lower() in str(sdata.get("step_description", "")).lower():
                    surface_found = surf
                    break

            if surface_found and tc.get("initial_condition") in ["None", "", None]:
                tc["initial_condition"] = f"LRU to be configured as {surface_found}."

            # 6. Disambiguate test_case_id duplicates
            raw_id = tc.get("test_case_id") or f"{req_sub_id.replace('-', '_')}_TC_{tc_idx}"
            raw_id = raw_id.replace("-", "_")

            # Format ID properly with step name if shared
            if snum in ["4a", "4b", "9a", "9b", "14a", "14b"]:
                clean_snum = snum.replace("a", "_4a").replace("b", "_4b")
                if not re.search(r'_\d+[ab]', raw_id):
                    raw_id = raw_id.replace("_N1", f"_Step_{snum}_N1").replace("_DC", f"_Step_{snum}_DC")

            cand_id = raw_id
            suffix_counter = 1
            while cand_id in all_tc_ids_seen:
                cand_id = f"{raw_id}_{suffix_counter}"
                suffix_counter += 1

            tc["test_case_id"] = cand_id
            all_tc_ids_seen.add(cand_id)

            valid_tcs_for_step.append(tc)

        sdata["test_cases"] = valid_tcs_for_step
        sdata["total_test_cases"] = len(valid_tcs_for_step)
        total_valid_tcs += len(valid_tcs_for_step)

    master["total_test_cases"] = total_valid_tcs

    with open(REPAIRED_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2)

    print(f"\n[DONE] REPAIR COMPLETE!")
    print(f"Total Test Cases in Repaired Suite: {total_valid_tcs}")
    print(f"Total Unique Test Case IDs: {len(all_tc_ids_seen)}")
    print(f"Saved master perfected JSON to: {REPAIRED_JSON_PATH}")

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    repair_and_perfect()
