import urllib.request
import json
import os
import re
import glob
import sys

# Force UTF-8 unbuffered stdout for real-time Windows console logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gpt-oss:latest"
PROMPTS_DIR = r"c:\Users\pm89542\Desktop\parse\step_prompts_1001"
OUTPUT_JSON_PATH = r"c:\Users\pm89542\Desktop\parse\LRUSWRS-1001_grouped_step_testcases.json"

def extract_first_json_object(text):
    m = re.search(r'\{', text)
    if not m:
        return None
    start = m.start()
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == '\\' and in_string:
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if not in_string:
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
    return None

def process_step_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        prompt_content = f.read()

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_content,
        "stream": False
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data_bytes, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_response = res_json.get("response", "")

            # Strip markdown code blocks if present
            cleaned_text = raw_response.strip()
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text, flags=re.IGNORECASE)
                cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

            json_str = extract_first_json_object(cleaned_text)
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    return parsed.get("test_cases", [])
                except Exception as je:
                    json_str_clean = re.sub(r'[\x00-\x1F\x7F]', ' ', json_str)
                    try:
                        parsed = json.loads(json_str_clean)
                        return parsed.get("test_cases", [])
                    except Exception:
                        print(f"  [WARN] JSON parse error for {os.path.basename(file_path)}: {je}", flush=True)
                        return []
            else:
                print(f"  [WARN] No JSON found in response for {os.path.basename(file_path)}", flush=True)
                return []
    except Exception as e:
        print(f"  [ERROR] Processing {os.path.basename(file_path)}: {e}", flush=True)
        return []

def main():
    prompt_files = glob.glob(os.path.join(PROMPTS_DIR, "prompt_step_*.txt"))
    
    def natural_step_key(path):
        name = os.path.basename(path).replace("prompt_step_", "").replace(".txt", "")
        match = re.match(r'(\d+)([a-zA-Z]*)', name)
        if match:
            return (int(match.group(1)), match.group(2))
        return (999, name)

    prompt_files.sort(key=natural_step_key)

    print(f"Found {len(prompt_files)} step prompt files to process using Ollama model '{MODEL_NAME}'.", flush=True)

    steps_dict = {}
    total_tc_count = 0

    for idx, fpath in enumerate(prompt_files, 1):
        step_name = os.path.basename(fpath).replace("prompt_step_", "").replace(".txt", "")
        print(f"\n[{idx}/{len(prompt_files)}] Processing Step {step_name}...", flush=True)
        
        # Read step prompt for exact sub-req ID & description
        with open(fpath, "r", encoding="utf-8") as f:
            ptext = f.read()
            m_id = re.search(r'Requirement ID:\s*(LRU-[^\s\n]+|LRUSWRS-[^\s\n]+)', ptext)
            req_sub_id = m_id.group(1) if m_id else f"LRUSWRS-1001_Step_{step_name}"
            
            m_desc = re.search(r'Text:\s*\n([^\n]+)', ptext)
            step_desc = m_desc.group(1) if m_desc else ""

        test_cases = process_step_file(fpath)
        if not test_cases:
            # Retry once on empty response or timeout
            print(f"  [RETRY] Retrying Step {step_name}...", flush=True)
            test_cases = process_step_file(fpath)

        # Ensure requirement_id is set on every test case
        for tc in test_cases:
            if isinstance(tc, dict) and not tc.get("requirement_id"):
                tc["requirement_id"] = req_sub_id

        print(f"  [OK] Step {step_name} ({req_sub_id}): Generated {len(test_cases)} test case(s).", flush=True)
        for tc in test_cases:
            if not isinstance(tc, dict):
                continue
            desc_str = str(tc.get('description') or '')[:70]
            print(f"    - [{tc.get('test_case_id')}] Type: {tc.get('test_type')} | {desc_str}", flush=True)
        
        total_tc_count += len(test_cases)

        step_key = f"STEP_{step_name}_REQUIREMENT_ID_{req_sub_id.replace('-', '_')}"

        steps_dict[step_key] = {
            "step_number": step_name,
            "requirement_id": req_sub_id,
            "step_description": step_desc,
            "total_test_cases": len(test_cases),
            "test_cases": test_cases
        }

    master_output = {
        "requirement_id": "LRUSWRS-1001",
        "requirement_title": "Primary/Spoiler Surface Electronic Harmonizing Sequence",
        "total_steps": len(steps_dict),
        "total_test_cases": total_tc_count,
        "steps_breakdown": steps_dict
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(master_output, f, indent=2)

    print(f"\n[DONE] Generated {total_tc_count} total test cases across {len(steps_dict)} steps.", flush=True)
    print(f"Saved JSON to: {OUTPUT_JSON_PATH}", flush=True)

if __name__ == "__main__":
    main()
