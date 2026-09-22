import os
import json
import zipfile

req_1001_text = """

5.requirement:
ID :  LRUSWRS-1001
The electronic Harmonizing sequence for both Primary and Spoiler surface types are defined in the table below.  The prerequisite condition for execution of this Harmonizing sequence is that Harmonizing mode (LRUSWRS-1003) must be active.  The steps occur in blocks, 1 to 5, 6 to 10, 11 to 15, followed by 16 to 35.  The first three blocks are started by LRU_2 messages and can occur in any order. The last block occurs automatically after all three of the other blocks are completed.  Not all steps are applicable to both surface types.  The block steps not applicable to both surface types are noted following the requirement. 
The LRU software shall implement the electronic Harmonizing sequence as shown in Table 1001.
Req Type :  Verbatim
Safety Impact :  No
Safety Rationale :  This is a detailed implementation requirement.


{
  "test_cases": [
    {
      "test_case_id": "LRUSWRS-1001_N1_Aileron",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software implements the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is active for Aileron.",
      "test_type": "NORMAL",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = True. Surface = Aileron.",
      "expected_result": "LRU software implements the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_N1_Elevator",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software implements the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is active for Elevator.",
      "test_type": "NORMAL",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = True. Surface = Elevator.",
      "expected_result": "LRU software implements the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_N1_Rudder",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software implements the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is active for Rudder.",
      "test_type": "NORMAL",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = True. Surface = Rudder.",
      "expected_result": "LRU software implements the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_N1_Spoiler",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software implements the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is active for Spoiler.",
      "test_type": "NORMAL",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = True. Surface = Spoiler.",
      "expected_result": "LRU software implements the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_DC_HARM_Aileron",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software does not implement the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is not active for Aileron.",
      "test_type": "DC",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = False. Surface = Aileron.",
      "expected_result": "LRU software does not implement the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_DC_HARM_Elevator",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software does not implement the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is not active for Elevator.",
      "test_type": "DC",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = False. Surface = Elevator.",
      "expected_result": "LRU software does not implement the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_DC_HARM_Rudder",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software does not implement the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is not active for Rudder.",
      "test_type": "DC",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = False. Surface = Rudder.",
      "expected_result": "LRU software does not implement the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    },
    {
      "test_case_id": "LRUSWRS-1001_DC_HARM_Spoiler",
      "requirement_id": "LRUSWRS-1001",
      "description": "Verifies the LRU software does not implement the electronic Harmonizing sequence per Table 1001 when Harmonizing mode is not active for Spoiler.",
      "test_type": "DC",
      "initial_condition": "None",
      "test_inputs": "Harmonizing mode active = False. Surface = Spoiler.",
      "expected_result": "LRU software does not implement the electronic Harmonizing sequence per Table 1001.",
      "pass_criteria": "Observed software behaviour matches expected_result.",
      "related_requirements": "LRUSWRS-1003",
      "test_procedure_notes": "Verification mechanism to be defined by the verification environment."
    }
  ]
}
"""

sample1_path = 'extracted_samples/sample 1.txt'

# Read current content
with open(sample1_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

if 'LRUSWRS-1001' not in content:
    content += req_1001_text
    with open(sample1_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Appended LRUSWRS-1001 to sample 1.txt")
else:
    print("LRUSWRS-1001 already in sample 1.txt")

# Update samples.zip
zip_path = 'c:/Users/pm89542/Desktop/parse/samples.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for fname in sorted(os.listdir('extracted_samples')):
        z.write(os.path.join('extracted_samples', fname), fname)
print("Updated samples.zip with new sample 1.txt")
