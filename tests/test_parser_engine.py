import unittest
from parser_engine import ParsingPipeline
from parser_engine.models import Requirement, Table, Figure, Document

class TestParserEngine(unittest.TestCase):
    def setUp(self):
        self.pipeline = ParsingPipeline()
        
        self.raw_data = [
            {
                "req_id": "LRUSWRS-1001",
                "text": "While in Running Mode, the LRU shall transition from Idle_State to Speed_State on Primary and Spoiler surfaces for LRU_1 and LRU_2 with a delay of 4 +/- 2 msec if Bus_OK_Message == TRUE as per Table 1 and refer LRUSWRS-1002.\nReference Requirements\n",
                "notes": ["Note: Rotor_Ref_Bad_Monitor is in Table 1 as per Figure 1."]
            },
            {
                "req_id": "LRUSWRS-1002",
                "text": "The LRU software shall compute Speed_Loop_Clear as follow:\nif (Low_Threshold_Anomaly_NodeB_Monitor = TRUE OR Hi_Enable_Delay_Envelope = FALSE)\nThen\nSet Speed_Loop_Clear = TRUE\nelse\nSet Speed_Loop_Clear = FALSE\n"
            },
            {
                "type": "table",
                "table_id": "Table 1",
                "title": "Operational Configuration Steps",
                "headers": ["Step", "Action", "Result"],
                "rows": [
                    ["1", "Turn on power", "System boots"],
                    ["2", "Check logs", "Logs are clear"]
                ]
            },
            {
                "type": "table",
                "table_id": "Table 1401",
                "title": "FPGA Discrete IO Register Access",
                "headers": ["SW Read/Write Register Access", "Register Type/Bit Location", "Register/Bit Signal Name"],
                "rows": [
                    ["R/W", "0", "Valve_On"],
                    ["R/W", "2", "Location_State_StateLgc"]
                ]
            },
            {
                "type": "table",
                "table_id": "Table 2",
                "title": "Revision History",
                "headers": ["Version", "Date"],
                "rows": [
                    ["1.0", "2026-07-16"]
                ]
            },
            {
                "type": "figure",
                "figure_id": "Figure 1",
                "title": "System Architecture",
                "caption": "Shows system boot process linked to LRUSWRS-1002."
            }
        ]

    def test_normalized_top_level_schema(self):
        result = self.pipeline.process(self.raw_data)
        
        self.assertIn("requirements", result)
        self.assertIn("tables", result)
        self.assertIn("figures", result)
        self.assertIn("cross_reference", result)
        self.assertIn("entity_index", result)
        
        self.assertEqual(len(result["requirements"]), 2)

    def test_lightweight_requirement_structure(self):
        result = self.pipeline.process(self.raw_data)
        req1 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1001")
        
        expected_keys = {
            "requirement_id", "requirement_text", "conditions", "expected_outputs",
            "logic_expression", "state_transition", "timing_constraints",
            "decision_type", "signal_roles", "confidence",
            "linked_requirements", "linked_tables", "linked_figures", "signals",
            "notes", "surface_applicability", "lru_configuration", "dependencies",
            "metadata", "source_location"
        }
        self.assertEqual(set(req1.keys()), expected_keys)
        
        self.assertNotIn("tables", req1)
        self.assertNotIn("figures", req1)

    def test_decision_type_and_signal_roles(self):
        result = self.pipeline.process(self.raw_data)
        req1 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1001")
        req2 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1002")
        
        # Check decision types
        self.assertEqual(req1["decision_type"], "STATE_TRANSITION")
        self.assertIn(req2["decision_type"], ["CALCULATION", "DECISION_LOGIC", "MONITORING"])

        # Check signal roles in req2
        self.assertIn("Low_Threshold_Anomaly_NodeB_Monitor", req2["signal_roles"]["inputs"])
        self.assertIn("Hi_Enable_Delay_Envelope", req2["signal_roles"]["inputs"])
        self.assertIn("Speed_Loop_Clear", req2["signal_roles"]["outputs"])


    def test_confidence_scores(self):
        result = self.pipeline.process(self.raw_data)
        req1 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1001")
        
        self.assertIn("conditions", req1["confidence"])
        self.assertIn("expected_outputs", req1["confidence"])
        self.assertIn("references", req1["confidence"])
        self.assertEqual(req1["confidence"]["conditions"], 1.0)

    def test_structured_table_definitions(self):
        result = self.pipeline.process(self.raw_data)
        table1401 = result["tables"]["Table 1401"]
        
        self.assertIn("definitions", table1401)
        self.assertIn("Valve_On", table1401["definitions"])
        self.assertEqual(table1401["definitions"]["Valve_On"]["bit"], "0")
        self.assertEqual(table1401["definitions"]["Valve_On"]["access"], "R/W")

    def test_condition_and_output_separation_with_branching(self):
        result = self.pipeline.process(self.raw_data)
        req2 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1002")
        
        cond_signals = [c["signal"] for c in req2["conditions"]]
        self.assertIn("Low_Threshold_Anomaly_NodeB_Monitor", cond_signals)
        self.assertIn("Hi_Enable_Delay_Envelope", cond_signals)
        self.assertNotIn("Speed_Loop_Clear", cond_signals)

        self.assertEqual(len(req2["expected_outputs"]), 2)
        then_out = next(o for o in req2["expected_outputs"] if o["condition"] == "THEN")
        else_out = next(o for o in req2["expected_outputs"] if o["condition"] == "ELSE")
        
        self.assertEqual(then_out["signal"], "Speed_Loop_Clear")
        self.assertEqual(then_out["value"], True)
        self.assertEqual(else_out["signal"], "Speed_Loop_Clear")
        self.assertEqual(else_out["value"], False)

    def test_logic_expression_preserves_structure(self):
        result = self.pipeline.process(self.raw_data)
        req2 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1002")
        
        self.assertIsNotNone(req2["logic_expression"])
        self.assertEqual(req2["logic_expression"]["operator"], "OR")
        self.assertEqual(len(req2["logic_expression"]["operands"]), 2)

    def test_state_transition_extraction(self):
        result = self.pipeline.process(self.raw_data)
        req1 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1001")
        
        self.assertIsNotNone(req1["state_transition"])
        self.assertEqual(req1["state_transition"]["from"], "Idle_State")
        self.assertEqual(req1["state_transition"]["to"], "Speed_State")

    def test_timing_constraints_extraction(self):
        result = self.pipeline.process(self.raw_data)
        req1 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1001")
        
        self.assertEqual(len(req1["timing_constraints"]), 1)
        tc = req1["timing_constraints"][0]
        self.assertEqual(tc["value"], 4.0)
        self.assertEqual(tc["tolerance"], 2.0)
        self.assertEqual(tc["unit"], "ms")

    def test_expanded_entity_index(self):
        result = self.pipeline.process(self.raw_data)
        e_index = result["entity_index"]
        
        self.assertIn("LRUSWRS-1001", e_index)
        self.assertEqual(e_index["LRUSWRS-1001"]["type"], "requirement")
        self.assertIn("Table 1", e_index["LRUSWRS-1001"]["references_tables"])
        
        self.assertIn("Table 1", e_index)
        self.assertEqual(e_index["Table 1"]["type"], "table")
        self.assertIn("LRUSWRS-1001", e_index["Table 1"]["referenced_by"])

    def test_enhanced_source_location(self):
        result = self.pipeline.process(self.raw_data)
        req1 = next(r for r in result["requirements"] if r["requirement_id"] == "LRUSWRS-1001")
        
        self.assertIn("doc_position", req1["source_location"])
        self.assertIn("section", req1["source_location"])
        self.assertEqual(req1["source_location"]["section"], "LRUSWRS-1001")

    def test_nested_resolver_prevents_loops(self):
        doc = Document()
        req_a = Requirement(req_id="A", req_text="refs B", linked_requirements=["B"])
        req_b = Requirement(req_id="B", req_text="refs A", linked_requirements=["A"])
        doc.requirements = [req_a, req_b]
        doc.register()
        
        self.pipeline.nested_resolver.resolve(doc)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()



