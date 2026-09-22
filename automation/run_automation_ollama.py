import os
import sys
import re
import json
import time
import urllib.request
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

AUTOMATION_DIR = r"c:\Users\pm89542\Desktop\parse\automation"
PROMPTS_DIR = os.path.join(AUTOMATION_DIR, "expanded_prompts")
OUTPUTS_DIR = os.path.join(AUTOMATION_DIR, "step_json_outputs")
MASTER_JSON_PATH = os.path.join(AUTOMATION_DIR, "ALL_TABLE_1001_EXPANDED_TESTCASES.json")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gpt-oss:latest"

def natural_sort_key(filename):
    m = re.search(r'step_([\d\w]+)', filename, re.IGNORECASE)
    if m:
        val = m.group(1).lower()
        num_part = re.search(r'\d+', val)
        alpha_part = re.search(r'[a-z]+', val)
        num = int(num_part.group(0)) if num_part else 0
        alpha = alpha_part.group(0) if alpha_part else ""
        return (num, alpha)
    return (999, filename)

def extract_json_object(text):
    if not text:
        return None
    # Strip markdown fences if present
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    
    start = cleaned.find('{')
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(cleaned)):
        char = cleaned[i]
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return cleaned[start:i+1]
    
    # Fallback to regex from first { to last }
    m = re.search(r'\{[\s\S]*\}', cleaned)
    if m:
        return m.group(0)
    return None

def auto_repair_json(json_str):
    if not json_str:
        return None
    # Fix missing commas between objects / arrays / strings
    s = re.sub(r'\}\s*\{', '},{', json_str)
    s = re.sub(r'\]\s*\[', '],[', s)
    s = re.sub(r'"\s*"', '","', s)
    s = re.sub(r'\}\s*"', '},"', s)
    s = re.sub(r'"\s*\{', '",{', s)
    return s

def query_ollama(prompt_text, max_retries=3):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_text,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 16384
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  --> Sending prompt to Ollama {MODEL_NAME} (attempt {attempt})...", flush=True)
            with urllib.request.urlopen(req, timeout=450) as resp:
                raw_bytes = resp.read()
                res_obj = json.loads(raw_bytes.decode("utf-8", errors="replace"), strict=False)
                raw_response = res_obj.get("response", "")
                
                # Extract first complete balanced JSON object
                json_str = extract_json_object(raw_response)
                if json_str:
                    fixed_str = auto_repair_json(json_str)
                    try:
                        parsed = json.loads(fixed_str, strict=False)
                    except Exception:
                        clean_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', fixed_str)
                        parsed = json.loads(clean_str, strict=False)

                    if "test_cases" in parsed and isinstance(parsed["test_cases"], list):
                        return parsed["test_cases"]
                print(f"  [RETRY {attempt}] JSON parsing failed. Retrying...", flush=True)
        except Exception as e:
            print(f"  [RETRY {attempt}] Query Error: {e}", flush=True)
        time.sleep(2)
    return None

def run_automation():
    print("=" * 80)
    print("STARTING OLLAMA AUTOMATION FOR ALL 38 EXPANDED STEPS")
    print(f"Model: {MODEL_NAME} | API: {OLLAMA_URL}")
    print("=" * 80)

    prompt_files = sorted(os.listdir(PROMPTS_DIR), key=natural_sort_key)
    print(f"Found {len(prompt_files)} prompt files to process.\n")

    master_breakdown = {}
    total_expanded_tcs = 0

    for idx, fname in enumerate(prompt_files, 1):
        prompt_path = os.path.join(PROMPTS_DIR, fname)
        m_step = re.search(r'step_([\d\w]+)', fname, re.IGNORECASE)
        snum = m_step.group(1) if m_step else str(idx)

        with open(prompt_path, "r", encoding="utf-8") as pf:
            prompt_content = pf.read()

        m_req = re.search(r'Requirement ID:\s*(LRU-\d+)', prompt_content)
        req_id = m_req.group(1) if m_req else "LRU-1001"

        print(f"[{idx}/{len(prompt_files)}] Processing Step {snum} ({req_id})...")

        out_json_path = os.path.join(OUTPUTS_DIR, f"step_{snum}_expanded_testcases.json")

        tcs = query_ollama(prompt_content)
        if tcs:
            print(f"  [SUCCESS] Step {snum}: Generated {len(tcs)} test cases!")
            step_output = {
                "step_number": snum,
                "requirement_id": req_id,
                "total_test_cases": len(tcs),
                "test_cases": tcs
            }
            with open(out_json_path, "w", encoding="utf-8") as out_f:
                json.dump(step_output, out_f, indent=2)
            
            skey = f"STEP_{snum.upper()}_REQUIREMENT_ID_{req_id.replace('-', '_')}"
            master_breakdown[skey] = step_output
            total_expanded_tcs += len(tcs)
        else:
            print(f"  [WARN] Step {snum}: Failed to generate test cases via Ollama.")

    # Master Compilation
    master = {
        "requirement_id": "LRUSWRS-1001",
        "requirement_title": "Primary/Spoiler Surface Electronic Harmonizing Sequence (Expanded Suite)",
        "total_steps": len(prompt_files),
        "total_test_cases": total_expanded_tcs,
        "steps_breakdown": master_breakdown
    }

    with open(MASTER_JSON_PATH, "w", encoding="utf-8") as mf:
        json.dump(master, mf, indent=2)

    print("\n" + "=" * 80)
    print(f"[DONE] AUTOMATION COMPLETE!")
    print(f"Total Steps Processed: {len(master_breakdown)} / {len(prompt_files)}")
    print(f"Total Expanded Test Cases: {total_expanded_tcs}")
    print(f"Master File Saved To: {MASTER_JSON_PATH}")
    print("=" * 80)

if __name__ == "__main__":
    run_automation()
