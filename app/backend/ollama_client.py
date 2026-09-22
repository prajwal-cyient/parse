import urllib.request
import json
import re
import time
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from applicability_engine import ApplicabilityEngine
from signal_classifier import SignalClassifier, SignalDictionary
from consolidation_engine import ConsolidationEngine

class OllamaClient:
    """
    Client for querying SSH tunneled or local Ollama models.
    Zero-hallucination (temperature=0.0), extended 20-minute timeouts,
    and automatic SSH network retry logic.
    """
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL_NAME = "gpt-oss:latest"

    @classmethod
    def get_endpoint(cls) -> str:
        for host in ["127.0.0.1", "localhost"]:
            try:
                url = f"http://{host}:11434/api/tags"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        return f"http://{host}:11434/api/generate"
            except Exception:
                continue
        return "http://127.0.0.1:11434/api/generate"

    PROMPT_TEMPLATE = """You are a DO-178C Level B Aerospace Verification Senior Lead Test Engineer responsible for generating software verification test cases from aerospace software requirements.

Your objective is to generate 100% requirement-traceable, deterministic, reviewable and auditor-compliant verification test cases.

The generated test cases must be based ONLY on evidence contained in the supplied requirement statement, explicitly referenced requirements, or applicability tables.

---

# ABSOLUTE RULE – STRICT BAN ON GENERIC PLACEHOLDERS

NEVER output generic template terms or placeholder variables under any circumstances.
FORBIDDEN STRINGS:
- NEVER write `Operational_Stimulus = True` or `Operational_Stimulus = False` or `Operational_Stimulus = Threshold_Value`
- NEVER write `Complete_Flag = True` or `Complete_Flag = False`
- NEVER write `Threshold_Value`
- NEVER write `valid operational value per requirement statement`
- NEVER write `Operational outputs match required specification` or `required specification`
- NEVER write `Mode_Active = True` or `Output_Fault = False`

YOU MUST EXTRACT AND USE ONLY REAL VARIABLE NAMES, HEX NUMBERS, TIMING VALUES, FRAME COUNTS, AND FORMULAS FROM THE REQUIREMENT PROSE:
- Real input signals: `IVT_Mode_ModeLgc`, `Harmonizing_Active_STL`, `Act_Disp_Raw`, `Harmonize_SFC_Default`, `Harmonize_Offset_Default`, `IVT_Command_ISM`
- Real output signals: `Harmonizing_Complete`, `Contract_Stop_Collection_Complete`, `Expand_Stop_Collection_Complete`, `Act_Disp_Range_Contract_Fault`, `Act_Disp_Range_Expand_Fault`, `Harmonizing_Failed`
- Real hex / timing values: `0x0020`, `0x0017`, `50 consecutive frames`, `25 ms`, `10 consecutive STL frames`

---

# CLIENT OBSERVATION 1 – LRU × ATYPE (TABLE 1011) & NOT-EQUAL
- Generate 21 standalone test cases for LRU_1..7 × ATYPE_1..3 when Table 1011 applicability applies.
- Include ATYPE and LRU in test case ID.
- Cover `IVT_Command_ISM == 0x0020` with two separate not-equal scenarios: `0x0000` (below) and `0x0030` (above).

# CLIENT OBSERVATION 2 – INITIAL CONDITIONS
- Contains ONLY setup state: flight mode, ATYPE, LRU_X, commanded position (Contract, Expand, or VOID), Harmonizing Mode state.
- Preset expected variable to a DIFFERENT value from Expected Result.
- NEVER put command positions, completion flags, or test stimuli in Initial Conditions.

# CLIENT OBSERVATION 3 – INPUT VERSUS OUTPUT COLUMNS
- `initial_condition`: ONLY static setup (Operational Mode: FLIGHT_MODE; Target ATYPE; Target LRU; Commanded Position; Harmonizing Mode active).
- `test_inputs`: ONLY dynamic stimuli (e.g. `IVT_Mode_ModeLgc = True; Harmonizing_Active_STL = True`, `Act_Disp_Raw (pre-averaged) = -12.5; Harmonize_SFC_Default = 1.0; Harmonize_Offset_Default = 0.0`).
- `expected_result`: ONLY observable outputs and completion booleans (e.g. `Contract_Stop_Collection_Complete = True; IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017`).

# CLIENT OBSERVATION 4 – STEP CLUBBING FOR CONTRACT AND EXPAND
- Contract Steps: Club Step 3 + Step 4A + Step 4B into unified test cases for `LRUSWRS-1001`, `LRU-9170`, `LRU-9171`.
- Expand Steps: Club Step 8 + Step 9A + Step 9B into unified test cases for `LRUSWRS-1001`, `LRU-9177`, `LRU-9895`, `LRU-9209`, `LRU-9210`.
- Must verify range check, fault boolean, completion boolean, and transmission of IVT Response frame `0x0017` on `STL_Bus`.

# CLIENT OBSERVATION 5 – PSR HARMONIZING DATA RECORD (LRUSWRS-1000)
- Consolidate all 9 PSR Harmonizing data members into exactly 1 single test case with test inputs `IVT_Mode_ModeLgc = True; Harmonizing_Active_STL = True`.

# CLIENT OBSERVATION 6 – 10 CONSECUTIVE STL FRAMES (LRUSWRS-1003)
- Requirement: `IVT_Mode_ModeLgc = True` and `Harmonizing_Active_STL = True` must remain True for **10 consecutive STL frames** before entering Harmonizing mode.
- Test Inputs: `IVT_Mode_ModeLgc = True; Frames 1-10: Harmonizing_Active_STL = True.`
- Expected Result: `LRU enters Harmonizing mode at frame 10; Harmonizing_Active_STL = True.`
- Boundary / DC cases: Test 9 frames (mode entry suppressed) and `IVT_Mode_ModeLgc = False`.

# CLIENT OBSERVATION 7 – NO EMPTY TEST INPUTS
- Never leave `test_inputs` blank or None. Inherit stimuli from referenced requirements (e.g. SWRS-1004) when missing.

---

OUTPUT JSON SCHEMA:
{
  "test_cases": [
    {
      "test_case_id": "SWVCP_AAP_TC_{req_id}_NORMAL_01",
      "requirement_id": "{req_id}",
      "description": "<requirement-specific verification objective>",
      "test_type": "NORMAL",
      "initial_condition": "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1; System in baseline operational state.",
      "test_inputs": "<EXACT_REQUIREMENT_INPUT_SIGNAL> = <REQUIREMENT_DERIVED_VALUE>.",
      "expected_result": "<EXACT_REQUIREMENT_OUTPUT_SIGNAL> = <EXPECTED_VALUE>; <COMPLETION_FLAG> = True.",
      "pass_criteria": "Observed software outputs match expected_result.",
      "related_requirements": "",
      "test_procedure_notes": "Verify via STL_Bus telemetry frame 0x0017 and internal registers."
    }
  ]
}

SUPPLIED REQUIREMENT:
Requirement ID: {req_id}
Requirement Statement:
{req_text}
"""

    @classmethod
    def set_active_model(cls, model_name: str):
        """Sets the active model dynamically."""
        if model_name and str(model_name).strip():
            cls.MODEL_NAME = str(model_name).strip()
            return True
        return False

    @classmethod
    def get_available_models(cls):
        """Fetches list of available generative models from Ollama."""
        try:
            endpoint = cls.get_endpoint().replace("/api/generate", "/api/tags")
            req = urllib.request.Request(endpoint)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    raw_models = [m.get('name', '') for m in data.get('models', []) if m.get('name')]
                    gen_models = [m for m in raw_models if "embed" not in m.lower()]
                    return gen_models if gen_models else raw_models
        except Exception:
            pass
        return [cls.MODEL_NAME]

    @classmethod
    def get_active_model_or_fallback(cls) -> str:
        """Returns the active model or the best available fallback."""
        available = cls.get_available_models()
        if cls.MODEL_NAME in available:
            return cls.MODEL_NAME
        for cand in ["llama3:latest", "qwen2.5-coder:14b", "qwen2.5:7b", "gpt-oss:latest"]:
            if cand in available:
                return cand
        return available[0] if available else cls.MODEL_NAME

    @classmethod
    def check_ssh_tunnel(cls) -> bool:
        """
        Verifies if Ollama is actively running and responding on port 11434.
        Returns True when models are available.
        """
        try:
            models = cls.get_available_models()
            return len(models) > 0
        except Exception:
            return False

    @staticmethod
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

    @classmethod
    def auto_repair_json(cls, text):
        cleaned_text = str(text or "").strip()
        cleaned_text = re.sub(r'\{\{', '{', cleaned_text)
        cleaned_text = re.sub(r'\}\}', '}', cleaned_text)

        m_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_text, re.IGNORECASE)
        if m_block:
            cleaned_text = m_block.group(1).strip()

        m_tc = re.search(r'\{\s*"test_cases"[\s\S]*?\]\s*\}', cleaned_text)
        if m_tc:
            cand = re.sub(r',\s*([\]}])', r'\1', m_tc.group(0))
            try:
                json.loads(cand)
                return cand
            except Exception:
                pass

        first_obj = cls.extract_first_json_object(cleaned_text)
        if first_obj:
            first_obj_clean = re.sub(r',\s*([\]}])', r'\1', first_obj)
            try:
                parsed_test = json.loads(first_obj_clean)
                if isinstance(parsed_test, dict) and ("test_cases" in parsed_test or "test_case_id" in parsed_test):
                    return first_obj_clean
            except Exception:
                pass

        cleaned_text = re.sub(r',\s*([\]}])', r'\1', cleaned_text)
        return cleaned_text

    @classmethod
    def _build_app_context(cls, tables=None, full_text="", req_ids=None):
        return ApplicabilityEngine.build_context(
            tables=tables or [],
            full_text=full_text or "",
            req_ids=req_ids or [],
        )

    @classmethod
    def _finalize_test_cases(cls, raw_cases: List[Dict[str, Any]], req_id: str,
                              req_text: str, app_ctx, signal_dict) -> List[Dict[str, Any]]:
        sd = signal_dict or SignalDictionary.build([{"id": req_id, "text": req_text}])
        members, _ = ApplicabilityEngine.applicable_members(req_text, app_ctx)
        sanitized = SignalClassifier.sanitize_test_cases(
            raw_cases or [], req_id, req_text, sd, app_ctx, members=members)
        return ConsolidationEngine.deduplicate_test_cases(sanitized)

    @classmethod
    def query_requirement(cls, req_id, req_text, timeout=180, retries=2,
                          tables=None, full_text="", req_ids=None,
                          app_ctx=None, signal_dict=None, bypass_cache=False,
                          log_cb=None):
        def emit(msg: str):
            print(msg, flush=True)
            if log_cb:
                try:
                    log_cb(msg)
                except Exception:
                    pass

        obs_num = "Obs#8"
        obs_name = f"{req_id}"
        if ApplicabilityEngine.is_matrix_applicability(req_id, req_text, tables):
            obs_num = "Obs#1"
            obs_name = f"Matrix Applicability 21 Combinations for {req_id}"
        elif any(k in str(req_id).lower() for k in ["9170", "9171", "9177", "9895", "9209", "9210", "1001-step"]):
            obs_num = "Obs#4"
            obs_name = f"Clubbing Contract/Expand Steps ({req_id})"
        elif "1000" in str(req_id) or "psr" in str(req_text).lower():
            obs_num = "Obs#2"
            obs_name = f"Multi-Member Harmonizing Data Record ({req_id})"

        emit(f"\n[GEN] {obs_num} {obs_name} ...")

        def log_cases(prefix: str, cases: List[Dict[str, Any]]):
            if prefix:
                emit(f"  [{prefix}] Using hardened template for {obs_num} {obs_name}")
            for tc in cases:
                tc_id = tc.get("test_case_id", "")
                r_id = tc.get("requirement_id", req_id)
                t_type = tc.get("test_type", "NORMAL")
                t_in = tc.get("test_inputs", "")
                t_out = tc.get("expected_result", "")
                emit(f"    - {tc_id} | {r_id} | {t_type}")
                if t_in:
                    emit(f"      IN: {t_in}")
                if t_out:
                    emit(f"      OUT: {t_out}")

        if not cls.check_ssh_tunnel():
            emit("    [WARN] SSH Tunnel is NOT connected on http://localhost:11434")
            raise Exception("Ollama / SSH Tunnel is NOT connected. Connect terminal tunnel first!")

        if app_ctx is None:
            app_ctx = cls._build_app_context(tables, full_text or req_text, req_ids)

        # 1. Applicability Matrix Check (Discovers combination tables e.g. Table 1011)
        if ApplicabilityEngine.is_matrix_applicability(req_id, req_text, tables):
            matrix_cases = ApplicabilityEngine.generate_matrix_test_cases(
                req_id, req_text, app_ctx)
            finalized = cls._finalize_test_cases(
                matrix_cases, req_id, req_text, app_ctx, signal_dict)
            log_cases("", finalized)
            return finalized

        # 2. Multi-member data record consolidation (e.g. PSR Harmonizing data in LRUSWRS-1000)
        psr_cases = ConsolidationEngine.consolidate_multi_member_records(
            [], req_id, req_text)
        if psr_cases:
            finalized = cls._finalize_test_cases(
                psr_cases, req_id, req_text, app_ctx, signal_dict)
            log_cases("", finalized)
            return finalized

        # 3. Multi-step sequence clubbing (Contract Steps 3+4A+4B, Expand Steps 8+9A+9B)
        seq_cases = ConsolidationEngine.consolidate_sequential_steps(
            [], req_id, req_text)
        if seq_cases:
            finalized = cls._finalize_test_cases(
                seq_cases, req_id, req_text, app_ctx, signal_dict)
            log_cases("", finalized)
            return finalized

        # 4. Master DO-178C Multi-Test Suite Check (Bypassed on Force Reprocess)
        if not bypass_cache:
            try:
                ks_path = os.path.join(os.path.dirname(__file__), "knowledge_suite.json")
                if os.path.exists(ks_path):
                    with open(ks_path, "r", encoding="utf-8") as kf:
                        ks_data = json.load(kf)
                        if req_id in ks_data and len(ks_data[req_id]) > 0:
                            finalized = cls._finalize_test_cases(
                                ks_data[req_id], req_id, req_text, app_ctx, signal_dict)
                            log_cases("", finalized)
                            return finalized
            except Exception:
                pass

        prompt_template = cls.PROMPT_TEMPLATE
        prompt = prompt_template.replace("{req_id}", req_id).replace("{req_text}", req_text)
        endpoint = cls.get_endpoint()
        model_to_use = cls.get_active_model_or_fallback()

        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_ctx": 4096, "num_predict": 2048},
        }
        data = json.dumps(payload).encode('utf-8')

        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(
                    endpoint, data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    res_body = resp.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    raw_resp = str(res_json.get('response', '') or '').strip()
                    raw_think = str(res_json.get('thinking', '') or '').strip()
                    raw_output = raw_resp or raw_think
                    if not raw_output:
                        emit(f"    [WARN] Attempt {attempt}/{retries} failed: empty output response")
                        continue
                    repaired = cls.auto_repair_json(raw_output)
                    parsed = None
                    try:
                        parsed = json.loads(repaired)
                    except Exception as parse_err:
                        obj_cand = cls.extract_first_json_object(repaired)
                        if obj_cand:
                            try:
                                parsed = json.loads(repaired)
                            except Exception:
                                pass
                        if not parsed:
                            emit(f"    [WARN] Attempt {attempt}/{retries} failed: JSON parse error: {parse_err}")

                    tcs = []
                    if isinstance(parsed, dict):
                        if "test_cases" in parsed and isinstance(parsed["test_cases"], list):
                            tcs = parsed["test_cases"]
                        elif "testCases" in parsed and isinstance(parsed["testCases"], list):
                            tcs = parsed["testCases"]
                        elif "test_case_list" in parsed and isinstance(parsed["test_case_list"], list):
                            tcs = parsed["test_case_list"]
                        elif "test_case_id" in parsed:
                            tcs = [parsed]
                    elif isinstance(parsed, list):
                        tcs = parsed

                    if tcs:
                        finalized = cls._finalize_test_cases(
                            tcs, req_id, req_text, app_ctx, signal_dict)
                        log_cases("", finalized)
                        return finalized
                    else:
                        emit(f"    [WARN] Attempt {attempt}/{retries} failed: no test_cases found in response")
            except Exception as e:
                emit(f"    [WARN] Attempt {attempt}/{retries} failed: {e}")

        if not bypass_cache:
            try:
                ks_path = os.path.join(os.path.dirname(__file__), "knowledge_suite.json")
                if os.path.exists(ks_path):
                    with open(ks_path, "r", encoding="utf-8") as kf:
                        ks_data = json.load(kf)
                        if req_id in ks_data and len(ks_data[req_id]) > 0:
                            finalized = cls._finalize_test_cases(
                                ks_data[req_id], req_id, req_text, app_ctx, signal_dict)
                            log_cases("FALLBACK", finalized)
                            return finalized
            except Exception:
                pass

        generic_cases = cls.generate_generic_do178c_suite(req_id, req_text, app_ctx)
        finalized = cls._finalize_test_cases(
            generic_cases, req_id, req_text, app_ctx, signal_dict)
        log_cases("FALLBACK", finalized)
        return finalized

    @classmethod
    def generate_generic_do178c_suite(cls, req_id: str, req_text: str, app_ctx=None) -> List[Dict[str, Any]]:
        """Generates requirement-specific DO-178C Level B test cases dynamically from requirement prose without generic placeholders."""
        text_lower = req_text.lower()
        tcs = []

        raw_idents = re.findall(r'\b([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)\b', req_text)
        idents = [
            i for i in dict.fromkeys(raw_idents)
            if not any(ign in i.upper() for ign in ["LRUSWRS", "DO_178C", "FLIGHT_MODE", "ATYPE", "LRU_"])
        ]

        hex_vals = re.findall(r'0x[0-9A-Fa-f]+', req_text)
        frames = re.findall(r'\b\d+\s*(?:consecutive\s*)?(?:STL\s*)?frames\b', req_text, re.IGNORECASE)
        times = re.findall(r'\b\d+\s*ms\b', req_text, re.IGNORECASE)

        inputs_list = []
        outputs_list = []

        for ident in idents:
            if any(k in ident.lower() for k in ["complete", "fault", "result", "output", "failed", "status", "envelope"]):
                outputs_list.append(f"{ident} = True")
            elif any(k in ident.lower() for k in ["mode", "active", "enable", "cmd", "command", "stimulus", "input"]):
                inputs_list.append(f"{ident} = True")
            else:
                inputs_list.append(f"{ident} = nominal in-range value")

        if hex_vals:
            inputs_list.append(f"Command / Envelope = {hex_vals[0]}")
        if frames:
            inputs_list.append(f"Timing / Frame Duration = {frames[0]}")
        if times and not frames:
            inputs_list.append(f"Sample Interval = {times[0]}")

        in_str = "; ".join(inputs_list) if inputs_list else f"Apply operational stimuli for {req_id} per requirement statement."
        out_str = "; ".join(outputs_list) if outputs_list else f"Verify observable outputs for {req_id} match requirement specification."

        tcs.append({
            "test_case_id": f"{req_id}_NORMAL_01",
            "requirement_id": req_id,
            "test_type": "NORMAL",
            "description": f"Verify nominal execution for requirement {req_id}.",
            "initial_condition": "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1; System in baseline operational state.",
            "test_inputs": in_str,
            "expected_result": out_str,
            "pass_criteria": f"Observed software behavior for {req_id} matches expected result.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus telemetry frame 0x0017 and internal memory registers."
        })

        dc_in = re.sub(r'= True', '= False', in_str)
        dc_out = re.sub(r'= True', '= False', out_str)
        tcs.append({
            "test_case_id": f"{req_id}_DC_01",
            "requirement_id": req_id,
            "test_type": "DC",
            "description": f"Decision coverage: Verify behavior suppressed when condition evaluates False for {req_id}.",
            "initial_condition": "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1; System in baseline operational state.",
            "test_inputs": dc_in,
            "expected_result": dc_out if dc_out != out_str else f"Action suppressed for {req_id}; output flag = False.",
            "pass_criteria": f"Software output remains unasserted/False when input condition evaluates False.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus telemetry."
        })

        return tcs

    @classmethod
    def enforce_client_observations(cls, tcs, req_id, req_text, app_ctx=None,
                                    signal_dict=None):
        """Compatibility wrapper delegating directly to modular engines."""
        if tcs is None:
            return cls.query_requirement(req_id, req_text)
        return cls._finalize_test_cases(tcs, req_id, req_text, app_ctx, signal_dict)
