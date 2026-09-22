import json

test_cases_data = {
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

out_str = json.dumps(test_cases_data, indent=2)
print("Valid JSON check: SUCCESS!")
print(f"Total test cases: {len(test_cases_data['test_cases'])}")
