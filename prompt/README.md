# DO-178C Test Case Generation Prompts: Old vs New

This folder contains the two benchmark prompts used in the DO-178C verification project:

| File | Associated Deliverable | Total TCs | Status & Description |
|---|---|---|---|
| [`OLD_PROMPT_300_PLUS_TESTCASES.txt`](file:///c:/Users/pm89542/Desktop/parse/prompt/OLD_PROMPT_300_PLUS_TESTCASES.txt) | `SW_Requirements_Sample_1_Test_Cases_20260804_185720.xlsx` | 338 rows (~336 TCs) | **Legacy Baseline Prompt (Pre-Observations):** Multiplied cases by surface names (Aileron, Elevator, Rudder, Spoiler) without enforcing the 8 client observations. Had output leakage in inputs and missing pin-strap combinations. |
| [`NEW_PROMPT_180_OBSERVATIONS_FIXED.txt`](file:///c:/Users/pm89542/Desktop/parse/prompt/NEW_PROMPT_180_OBSERVATIONS_FIXED.txt) | `app/outputs/SW_Requirements_Sample_1_Test_Cases.xlsx` | 180 TCs | **Current Master Prompt (100% Fixed):** Enforces strict 3-tier data separation, full pin-strap matrix expansion (ATYPE 1..3 × LRU 1..7), sub-step sequence clubbing (4A+4B, 9A+9B), explicit boolean false assertions (`[Flag] = False`), and zero placeholders. |

---

## Detailed Comparison

| Feature / Rule | Old Prompt (300+ TCs) | New Prompt (180 TCs) |
|---|---|---|
| **Hardware Pin-Strapping** | Generic surface multiplication (Aileron / Elevator / Rudder) | Full combinatorial matrix: **LRU 1..7 × ATYPE 1..3** matching `.tst` test harness scripts |
| **Data Separation** | Outputs leaked into `test_inputs` (e.g. `Contract_Stop_Collection_Complete`) | Strict 3-tier separation (Initial Conditions, Test Inputs, Expected Results) |
| **Negative Decisions (DC)** | Phrased as "is NOT sampled and averaged" | Explicitly asserts boolean false state: `[Signal_Name] = False` |
| **Sequence Clubbing** | Steps 4A+4B and 9A+9B generated as fragmented, disconnected steps | Clubbed into cohesive end-to-end nominal and fault flows |
| **Multi-Member Records** | PSR data members tested one by one | Consolidated into 1 unified test case verifying all 9 members simultaneously |
| **Placeholders** | Had fallback: `"Verification mechanism to be defined"` | Zero placeholders; concrete units (`in`, `ms`, `0xHex`, `STL_Bus frame 0x0017`) |
