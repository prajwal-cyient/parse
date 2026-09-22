import os
import re

REQ_FILE = r"c:\Users\pm89542\Desktop\parse\ALL_TABLE_1001_STEPS_REQUIREMENTS.txt"
AUTOMATION_DIR = r"c:\Users\pm89542\Desktop\parse\automation"
PROMPTS_DIR = os.path.join(AUTOMATION_DIR, "expanded_prompts")
OUTPUTS_DIR = os.path.join(AUTOMATION_DIR, "step_json_outputs")

os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

PROMPT_TEMPLATE = """You are a DO-178C Level B Software Verification Engineer responsible for generating software verification test cases from software requirements.

Your task is to generate complete, deterministic, non-hallucinated verification test cases directly traceable to the supplied requirement.

Use ONLY information explicitly stated or directly implied by the supplied requirement. Never invent software behaviour, signals, outputs, initial conditions, verification mechanisms, or related requirements.

Requirement ID: {REQ_ID}

Requirement Text:
{REQ_TEXT}

GENERAL RULES

1. Every generated test case shall be directly traceable to one or more statements in the supplied requirement.
2. Every mandatory JSON field shall always be populated: test_case_id, requirement_id, description, test_type, initial_condition, test_inputs, expected_result, pass_criteria, related_requirements, test_procedure_notes.
3. If information is unavailable, use the exact fallback value defined in this prompt.
4. Return JSON only — no explanatory text, no markdown.
5. Every test_case_id shall be unique; do not generate duplicate test cases.
6. Every requirement shall be evaluated independently.
7. Preserve all requirement terminology exactly whenever possible.

MANDATORY TEST TYPES
- NORMAL
- DC
- BOUNDARY
- ROBUSTNESS

HARDWARE LRU & SURFACE EXPANSION RULES

You MUST generate separate test cases for EVERY physical LRU hardware ID configured in the aircraft:
- LRU_1 (Left Aileron)
- LRU_2 (Right Aileron)
- LRU_3 (Left Spoiler)
- LRU_4 (Right Spoiler)
- LRU_5 (Left Elevator)
- LRU_6 (Right Elevator)
- LRU_7 (Rudder)

Do NOT combine surfaces or group LRUs together. Each applicable physical LRU ID MUST have its own individual test cases for BOTH Normal and Decision Coverage (DC) conditions.
(Note: For surface-restricted requirements, generate ONLY for the specified surface LRUs: e.g. Primary Surfaces -> LRU_1, LRU_2, LRU_5, LRU_6, LRU_7; Spoiler -> LRU_3, LRU_4; Rudder -> LRU_7).

JSON FIELDS

Every test case shall contain all 10 mandatory fields:
test_case_id, requirement_id, description, test_type, initial_condition, test_inputs, expected_result, pass_criteria, related_requirements, test_procedure_notes

requirement_id:
Copy the supplied Requirement ID exactly ({REQ_ID}). Never modify it.

description:
Contains ONLY the verification objective phrased clearly.

test_type:
Must be one of: "NORMAL", "DC", "BOUNDARY", "ROBUSTNESS".

initial_condition:
- Use: `LRU operating in Location_State_StateLgc mode; configured as {{LRU_ID}} ({{SurfaceName}}).`

test_inputs:
Contains execution inputs explicitly stated by the requirement: signals, variables, flags, operating modes, LRU configuration.
Append as the final sentence: `LRU Configuration = {{LRU_ID}} ({{SurfaceName}}).`

expected_result:
- Positive behaviour: state every required output exactly as required.
- Negative behaviour / DC tests: expected_result shall NEVER be empty. State the positive requirement outcome and state that it is NOT performed (e.g., "... is NOT performed.").

pass_criteria:
Return exactly: `Observed software behaviour matches expected_result.`

related_requirements:
Return exactly: `""`

test_procedure_notes:
Return exactly: `Verification mechanism to be defined by the verification environment.`

DECISION COVERAGE (DC)
- For EVERY applicable physical LRU ID:
  - Generate 1 NORMAL test where the decision evaluates TRUE.
  - Generate 1 DC test per atomic condition where that condition is FALSE/disabling while holding others enabling.

TEST CASE ID FORMAT
Format: `{REQ_ID_TAG}_{{TestTypeTag}}_{{LRU_ID}}` (replace '-' with '_')
Examples:
- {REQ_ID_TAG}_N1_LRU_1
- {REQ_ID_TAG}_DC_Condition_LRU_1
- {REQ_ID_TAG}_N1_LRU_7

Every test_case_id shall be unique.

OUTPUT SCHEMA

```json
{{
  "test_cases": [
    {{
      "test_case_id": "string",
      "requirement_id": "string",
      "description": "string",
      "test_type": "NORMAL | DC | BOUNDARY | ROBUSTNESS",
      "initial_condition": "string",
      "test_inputs": "string",
      "expected_result": "string",
      "pass_criteria": "string",
      "related_requirements": "string",
      "test_procedure_notes": "string"
    }}
  ]
}}
```

FINAL RULE
Return ONLY valid JSON.
"""

def generate_prompts():
    with open(REQ_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("--------------------------------------------------------------------------------")
    
    steps = []
    for b in blocks:
        b_str = b.strip()
        if "Sequence Context: Table 1001, Step" in b_str or "ID :" in b_str:
            steps.append(b_str)

    print(f"Found {len(steps)} requirement blocks.")

    for idx, step_text in enumerate(steps, 1):
        m_step = re.search(r'Sequence Context:\s*Table\s*1001,\s*Step\s*([\d\w]+)', step_text, re.IGNORECASE)
        if m_step:
            snum = m_step.group(1).lower()
        else:
            snum = str(idx)

        m_req = re.search(r'ID\s*:\s*(LRU-\d+)', step_text)
        req_id = m_req.group(1) if m_req else "LRU-1001"
        req_id_tag = req_id.replace("-", "_")

        prompt_str = PROMPT_TEMPLATE.format(
            REQ_ID=req_id,
            REQ_TEXT=step_text,
            REQ_ID_TAG=req_id_tag
        )

        out_name = f"prompt_step_{snum}.txt"
        out_path = os.path.join(PROMPTS_DIR, out_name)
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(prompt_str)

    print(f"[DONE] Created {len(steps)} expanded prompt files in {PROMPTS_DIR}")

if __name__ == "__main__":
    generate_prompts()
